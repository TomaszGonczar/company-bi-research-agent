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


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda value: value.update(publication_metdata={}), "publication_metdata"),
        (lambda value: value.update(contex="typo"), "contex"),
        (lambda value: value["candidate_fact"].update(typo=True), "typo"),
        (lambda value: value["candidate_fact"].update(as_of="2026-01-01"), "as_of"),
        (
            lambda value: value["candidate_fact"].update(context_fields={"currency": "PLN"}),
            "context_fields",
        ),
    ],
)
def test_author_schema_rejects_unknown_and_misplaced_fields_with_case_id(
    mutator: object, match: str
) -> None:
    authored = spec("draft.business_description", "Consulting")
    mutator(authored)  # type: ignore[operator]
    with pytest.raises(ValueError, match="case_id=author-case") as error:
        build_case(authored)
    assert match in str(error.value)


@pytest.mark.parametrize("bad_value", [10, 10.0, True])
def test_financial_non_null_values_must_be_decimal_strings(bad_value: object) -> None:
    with pytest.raises(ValueError, match="case_id=author-case"):
        build_case(spec("draft.financials.revenue", bad_value))


def test_financial_context_cannot_override_primary_fact() -> None:
    authored = spec(
        "draft.financials.revenue",
        "10",
        candidate_fact={
            "field_path": "draft.financials.revenue",
            "value": "10",
            "context_fields": {"value": "999"},
        },
    )
    with pytest.raises(ValueError, match="case_id=author-case"):
        build_case(authored)


def test_financial_decimal_lexical_precision_survives_builder_and_public_model() -> None:
    amount = "123456789012345678.123456"
    case = build_case(
        spec(
            "draft.financials.revenue",
            amount,
            candidate_fact={
                "field_path": "draft.financials.revenue",
                "value": amount,
                "context_fields": {
                    "period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "currency": "PLN",
                    "unit": "units",
                    "scope": "legal_entity",
                },
            },
        )
    )
    assert case["run"]["draft"]["financials"][0]["value"] == amount
    serialized = CompanyResearchRun.model_validate_json(json.dumps(case["run"])).model_dump_json()
    assert amount in serialized


def test_preflight_rejects_nonexistent_paths_even_for_boundary_controls(tmp_path: Path) -> None:
    case = build_case(
        spec(
            "draft.business_description",
            "Consulting",
            case_id="bad-target",
            classification="IDENTITY_INVALID",
            expected_action="reject",
            envelope={"identity": {"nip": "0000000000"}},
        )
    )
    case["path"] = "financials.99"
    results, successful = preflight([case], tmp_path / "bad-target.json")
    assert not successful
    assert results[0]["status"] == "INVALID"
    assert "case_id=bad-target" in results[0]["detail"]


def test_shared_fact_path_resolver_accepts_supported_locations_and_rejects_bad_indices() -> None:
    from company_bi.strict_cases import resolve_fact_path

    case = build_case(spec("draft.business_description", "Consulting"))
    run = case["run"]
    assert resolve_fact_path(run, "business_description") is run["draft"]["business_description"]
    assert resolve_fact_path(run, "financials.0") is run["draft"]["financials"][0]
    assert resolve_fact_path(run, "identity.legal_name") is run["identity"]["legal_name"]
    profile = {"business_description": run["draft"]["business_description"]}
    assert resolve_fact_path(profile, "business_description") is profile["business_description"]
    for invalid in ("financials.-1", "financials.00", "financials.2", "financials", "limitations"):
        with pytest.raises(ValueError):
            resolve_fact_path(run, invalid)


def test_missing_case_id_errors_use_explicit_index_marker() -> None:
    authored = spec("draft.business_description", "Consulting")
    del authored["case_id"]
    with pytest.raises(ValueError, match=r"<missing-case-id:index=4>"):
        build_case(authored, case_index=4)


@pytest.mark.parametrize(
    "envelope",
    [
        {"identity": {"nipp": "0000000000"}},
        {"sources": [{"index": 1, "changes": {"kind": "registry", "typo": True}}]},
        {
            "sources": [
                {"index": 1, "changes": {"source": {"url": "https://example.test", "typo": True}}}
            ]
        },
    ],
)
def test_envelope_patch_unknown_fields_fail_with_case_id(envelope: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="case_id=author-case"):
        build_case(
            spec(
                "draft.business_description",
                "Consulting",
                classification="PROVENANCE_INVALID",
                expected_action="reject",
                envelope=envelope,
            )
        )


@pytest.mark.parametrize("amount", ["not-a-decimal", "NaN", "Infinity"])
def test_financial_values_must_be_finite_decimal_strings(amount: str) -> None:
    with pytest.raises(ValueError, match="case_id=author-case"):
        build_case(spec("draft.financials.revenue", amount))


@pytest.mark.parametrize(
    "authored",
    [
        spec(
            "draft.employees",
            {"kind": "exact", "count": 9, "typo": True},
        ),
        spec(
            "draft.recent_developments",
            {"title": "Event", "summary": "Summary", "published_on": "2026-09-25", "typo": True},
        ),
        spec(
            "draft.financials.revenue",
            "10",
            candidate_fact={
                "field_path": "draft.financials.revenue",
                "value": "10",
                "context_fields": {
                    "period": {"start": "2025-01-01", "end": "2025-12-31", "typo": True}
                },
            },
        ),
        spec(
            "draft.business_description",
            "Consulting",
            classification="IDENTITY_INVALID",
            expected_action="reject",
            envelope={
                "identity": {
                    "legal_name": {"state": "supported", "value": "X", "evidence": [], "typo": True}
                }
            },
        ),
        spec(
            "draft.business_description",
            "Consulting",
            classification="IDENTITY_INVALID",
            expected_action="reject",
            envelope={
                "identity": {
                    "legal_name": {
                        "state": "supported",
                        "value": "X",
                        "evidence": [{"source_id": "id", "excerpt": "X", "typo": True}],
                    }
                }
            },
        ),
        spec(
            "draft.business_description",
            "Consulting",
            classification="PROVENANCE_INVALID",
            expected_action="reject",
            envelope={"sources": [{"index": 1, "changes": {"url": "https://example.test"}}]},
        ),
    ],
)
def test_nested_and_misplaced_object_fields_fail_at_builder_boundary(
    authored: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="case_id=author-case"):
        build_case(authored)
