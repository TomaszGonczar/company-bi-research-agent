import json
from dataclasses import asdict
from pathlib import Path

import pytest

from company_bi.dossier import build_dossier_view
from company_bi.models import CompanyResearchRun
from company_bi.verification import verify_run


def final_view(path: str, mutate=None):
    data = json.loads(Path(path).read_bytes())
    if mutate:
        mutate(data)
    run = CompanyResearchRun.model_validate(data)
    profile, _ = verify_run(run, input_sha256="test", input_name=Path(path).name)
    assert profile is not None
    return profile, build_dossier_view(profile, synthetic=True)


@pytest.mark.parametrize("case,count", [("supported", 1), ("out_of_contract", 0), ("unsafe", 0)])
def test_final_state_not_candidate_value(case, count):
    profile, view = final_view(f"examples/strict_contract/{case}.json")
    assert view.research_support_count == count
    assert view.status == profile.status == "partial"
    products = [f for f in view.facts if f.path == "products_services"]
    if case == "supported":
        assert products[0].values == ("cloud services",)
        assert products[0].citations[0].source_id == "page"
    else:
        assert products == []
        gap = next(g for g in view.gaps if g.path == "products_services")
        assert gap.state == "uncertain" and gap.references
        assert "excerpt" not in asdict(gap)
    assert len(view.questions) == 3


def test_exact_finance_and_registry_are_separate():
    _, view = final_view("examples/dossier/rich.json")
    assert view.research_support_count == 8
    assert view.status == "complete" and view.questions == ()
    result = next(f for f in view.facts if f.label == "Wynik netto")
    assert result.values == (
        "-0.7500 PLN; skala: miliony (millions); okres: 2025-01-01 – 2025-12-31; "
        "zakres: jednostka prawna (legal_entity)",
    )
    assert result.citations[0].source_id == "net_result"
    _, zero = final_view("examples/dossier/zero-finance.json")
    assert next(f for f in zero.facts if f.label == "Przychody").values[0].startswith("0.0000 PLN;")


def test_cleared_optional_dates_do_not_reappear():
    def change(data):
        data["draft"]["employees"]["as_of"] = "2026-09-29"
        data["draft"]["recent_developments"][0]["value"]["occurred_on"] = "2026-09-17"

    profile, view = final_view("examples/dossier/rich.json", change)
    assert profile.employees.as_of is None
    assert profile.recent_developments[0].value.occurred_on is None
    employee = next(f for f in view.facts if f.path == "employees")
    event = next(f for f in view.facts if f.section == "events")
    assert employee.values == ("25; data obserwacji: nieokreślona",)
    assert event.values[-1] == "Publikacja: 2026-09-20; zdarzenie: data nieokreślona"
    assert "2026-09-29" not in str(asdict(view))
    assert "2026-09-17" not in str(asdict(view))


@pytest.mark.parametrize("change_kind", ["uncertain", "wrong_amount", "group", "range"])
def test_unsupported_context_is_not_an_observation(change_kind):
    def change(data):
        if change_kind == "range":
            data["draft"]["employees"]["value"] = {"kind": "range", "minimum": 20, "maximum": 30}
        else:
            fact = data["draft"]["financials"][0]
            if change_kind == "uncertain":
                fact.update(state="uncertain", reason="Syntetyczna niepewność.")
            elif change_kind == "wrong_amount":
                fact["value"] = "987654.321"
            else:
                fact.update(scope="group", group_name="Niepotwierdzona Grupa")

    profile, view = final_view("examples/dossier/rich.json", change)
    path = "employees" if change_kind == "range" else "financials[0]"
    assert not any(f.path == path for f in view.facts)
    gap = next(g for g in view.gaps if g.path == path)
    assert gap.state == "uncertain"
    assert "987654.321" not in str(asdict(view))
    assert "Niepotwierdzona Grupa" not in str(asdict(view))
    if change_kind != "range":
        assert profile.financials[0].period is not None
        assert not hasattr(gap, "period")
        assert view.questions == (
            "Czy dostępne są jednostkowe wyniki finansowe za ostatni zamknięty okres?",
        )


def test_sources_and_large_lists_are_not_discarded():
    profile, view = final_view("examples/dossier/stress.json")
    services = next(f for f in view.facts if f.path == "products_services")
    assert services.values == tuple(profile.products_services.value)
    assert len(services.values) == 40
    assert view.research_support_count == 8  # Not 47: one list is one supported field.
    assert [s.source_id for s in view.sources] == sorted(s.source_id for s in profile.sources)
    mapping = {s.number: s.source_id for s in view.sources}
    assert all(mapping[r.number] == r.source_id for f in view.facts for r in f.citations)


def test_quarantine_and_uncited_metadata_are_not_evidence():
    def change(data):
        source = data["sources"][1]["source"]
        source["publication_blocked_reason"] = "unproven_legacy_url_relationship"
        data["sources"].append(
            {
                "source": {
                    "source_id": "unused",
                    "url": "https://unused.example/",
                    "title": "Materiał niecytowany",
                    "retrieved_at": data["generated_at"],
                    "publication_blocked_reason": "unproven_legacy_url_relationship",
                },
                "kind": "search_snippet",
                "fetch_mode": "tavily",
                "content": "Nie dowodzi faktu.",
            }
        )

    profile, view = final_view("examples/dossier/rich.json", change)
    assert profile.business_description.state == "uncertain"
    source = next(s for s in view.sources if s.source_id == "business_description")
    assert source.publication_blocked_reason == "unproven_legacy_url_relationship"
    assert "Kwarantanna publikacyjna" in source.usage
    assert not any(r.source_id == source.source_id for f in view.facts for r in f.citations)
    unused = next(s for s in view.sources if s.source_id == "unused")
    assert unused.usage == (
        "Niewykorzystane w faktach — samo pobranie nie potwierdza treści",
        "Kwarantanna publikacyjna",
    )
