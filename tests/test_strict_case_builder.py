from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

from company_bi.models import CompanyResearchRun

ROOT = Path(__file__).resolve().parents[1]
_BUILDER = runpy.run_path(str(ROOT / "scripts/strict_case_builder.py"))
build_case = _BUILDER["build_case"]
build_file = _BUILDER["build_file"]


def spec(field_path: str, value: object, **extra: object) -> dict[str, object]:
    return {
        "case_id": "author-case",
        "classification": "SUPPORTED_CONTRACT_POSITIVE",
        "source_assertion": {"text": "The company reports this observation."},
        "candidate_fact": {
            "field_path": field_path,
            "value": value,
            "context": "The company reports this observation.",
        },
        "expected_action": "publish",
        **extra,
    }


def preflight(cases: list[dict[str, object]], path: Path) -> tuple[list[dict[str, object]], bool]:
    path.write_text(json.dumps(cases), encoding="utf-8")
    return runpy.run_path(str(ROOT / "scripts/preflight_strict_cases.py"))["preflight"](path)


@pytest.mark.parametrize(
    ("field_path", "value", "candidate_extras", "expected_path"),
    [
        ("draft.business_description", "Business consulting.", {}, "business_description"),
        ("draft.products_services", ["Business consulting"], {}, "products_services"),
        ("draft.industries", ["Consulting"], {}, "industries"),
        ("draft.markets", ["Poland"], {}, "markets"),
        ("draft.employees", {"kind": "exact", "count": 9}, {"as_of": "2026-09-01"}, "employees"),
        (
            "draft.financials.revenue",
            "1250.00",
            {
                "context_fields": {
                    "period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "currency": "PLN",
                    "unit": "units",
                    "scope": "legal_entity",
                }
            },
            "financials.0",
        ),
        (
            "draft.financials.net_result",
            "12.50",
            {
                "context_fields": {
                    "period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "currency": "PLN",
                    "unit": "thousands",
                    "scope": "group",
                    "group_name": "Example Group",
                }
            },
            "financials.1",
        ),
        (
            "draft.recent_developments",
            {
                "title": "New location",
                "summary": "A new location opened.",
                "published_on": "2026-09-25",
                "occurred_on": "2026-09-24",
            },
            {},
            "recent_developments.0",
        ),
    ],
)
def test_author_fact_families_build_valid_public_run(
    field_path: str,
    value: object,
    candidate_extras: dict[str, object],
    expected_path: str,
    tmp_path: Path,
) -> None:
    case = build_case(
        spec(
            field_path,
            value,
            candidate_fact={
                "field_path": field_path,
                "value": value,
                "context": "The company reports this observation.",
                **candidate_extras,
            },
        )
    )
    run = CompanyResearchRun.model_validate_json(json.dumps(case["run"]))
    assert case["path"] == expected_path
    assert (
        run.diagnostics.model_requests
        == run.diagnostics.searches
        == run.diagnostics.page_reads
        == 0
    )
    results, successful = preflight([case], tmp_path / "cases.json")
    assert successful
    assert results[0]["status"] == "VALID"


def test_all_semantic_classes_preflight_as_schema_valid_without_semantic_judgment(
    tmp_path: Path,
) -> None:
    classes = [
        ("SUPPORTED_CONTRACT_POSITIVE", "publish"),
        ("OUT_OF_CONTRACT_TRUE", "abstain"),
        ("UNSAFE_NEGATIVE", "abstain"),
    ]
    cases = [
        build_case(
            spec(
                "draft.business_description",
                "Consulting",
                case_id=f"semantic-{index}",
                classification=classification,
                expected_action=action,
            )
        )
        for index, (classification, action) in enumerate(classes)
    ]
    results, successful = preflight(cases, tmp_path / "semantic-classes.json")
    assert successful
    assert [result["status"] for result in results] == ["VALID", "VALID", "VALID"]


def test_unknown_baseline_reason_and_evidence_roundtrip() -> None:
    case = build_case(spec("draft.products_services", ["Business consulting"]))
    run = CompanyResearchRun.model_validate_json(json.dumps(case["run"]))
    assert run.draft.business_description.state == "unknown"
    assert run.draft.business_description.reason
    assert run.draft.products_services.evidence[0].source_id == "synthetic-evidence"


def test_unknown_candidate_value_is_not_silently_dropped() -> None:
    with pytest.raises(ValueError, match="unknown candidate facts must use a null value"):
        build_case(
            spec(
                "draft.business_description",
                "provided value",
                candidate_fact={
                    "field_path": "draft.business_description",
                    "state": "unknown",
                    "value": "provided value",
                },
            )
        )


def test_semantic_envelope_overrides_are_rejected() -> None:
    with pytest.raises(ValueError, match="reserved for identity/provenance boundary controls"):
        build_case(
            spec(
                "draft.business_description",
                "Consulting",
                envelope={"identity": {"nip": "0000000000"}},
            )
        )


def test_valid_boundary_envelope_is_valid_without_semantic_judgment(tmp_path: Path) -> None:
    case = build_case(
        spec(
            "draft.business_description",
            "Consulting",
            classification="PROVENANCE_INVALID",
            expected_action="reject",
            publication_metadata={"kind": "search_snippet", "fetch_mode": "tavily"},
        )
    )
    results, successful = preflight([case], tmp_path / "valid-boundary.json")
    assert successful
    assert results[0]["status"] == "VALID"


def test_intentional_invalid_boundary_controls_are_annotated_not_semantic_proofs(
    tmp_path: Path,
) -> None:
    identity_case = build_case(
        spec(
            "draft.business_description",
            "Consulting",
            case_id="identity-control",
            classification="IDENTITY_INVALID",
            expected_action="reject",
            envelope={"identity": {"nip": "0000000000"}},
        )
    )
    provenance_case = build_case(
        spec(
            "draft.business_description",
            "Consulting",
            case_id="provenance-control",
            classification="PROVENANCE_INVALID",
            expected_action="reject",
            envelope={"sources": [{"index": 1, "changes": {"kind": "registry"}}]},
        )
    )
    results, successful = preflight([identity_case, provenance_case], tmp_path / "boundary.json")
    assert successful
    assert [result["status"] for result in results] == ["INVALID", "INVALID"]
    assert all(
        "not evidence that the verifier rejects" in result["annotation"] for result in results
    )


def test_invalid_boundary_without_reject_action_fails_readiness(tmp_path: Path) -> None:
    case = build_case(
        spec(
            "draft.business_description",
            "Consulting",
            classification="IDENTITY_INVALID",
            expected_action="abstain",
            envelope={"identity": {"nip": "0000000000"}},
        )
    )
    results, successful = preflight([case], tmp_path / "boundary-action.json")
    assert not successful
    assert results[0]["status"] == "INVALID"


def test_semantic_classification_with_invalid_envelope_fails_preflight(tmp_path: Path) -> None:
    case = build_case(spec("draft.financials.revenue", "12.50"))
    results, successful = preflight([case], tmp_path / "semantic.json")
    assert not successful
    assert results[0]["status"] == "INVALID"


def test_cli_does_not_execute_semantic_production_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    case = build_case(spec("draft.business_description", "Consulting"))
    corpus = tmp_path / "valid.json"
    corpus.write_text(json.dumps([case]), encoding="utf-8")
    for module in ("company_bi.verification", "company_bi.evidence", "company_bi.assertions"):
        monkeypatch.setitem(sys.modules, module, None)
    monkeypatch.setattr(sys, "argv", ["preflight_strict_cases.py", str(corpus)])
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(ROOT / "scripts/preflight_strict_cases.py"), run_name="__main__")
    assert exit_info.value.code == 0
    assert "VALID author-case" in capsys.readouterr().out


def test_preflight_rejects_missing_path_and_duplicate_ids(tmp_path: Path) -> None:
    case = build_case(spec("draft.business_description", "Consulting"))
    del case["path"]
    duplicate = build_case(spec("draft.business_description", "Consulting"))
    results, successful = preflight([case, duplicate, duplicate], tmp_path / "shape.json")
    assert not successful
    assert [result["status"] for result in results] == ["INVALID", "VALID", "INVALID"]


def test_builder_never_overwrites_existing_authored_output(tmp_path: Path) -> None:
    input_path, output_path = tmp_path / "spec.json", tmp_path / "output.json"
    input_path.write_text(
        json.dumps(spec("draft.business_description", "Consulting")), encoding="utf-8"
    )
    output_path.write_text("author-owned bytes", encoding="utf-8")
    with pytest.raises(FileExistsError):
        build_file(input_path, output_path)
    assert output_path.read_text(encoding="utf-8") == "author-owned bytes"
