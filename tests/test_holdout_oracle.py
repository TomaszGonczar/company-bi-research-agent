"""Tests for the public component oracle and its deterministic local scorer."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from company_bi.holdout_oracle import HoldoutOracle
from company_bi.holdout_scoring import score_case, score_oracle


def _case(
    target: str,
    expected: dict,
    *,
    classification: str = "SUPPORTED_CONTRACT_POSITIVE",
    case_id: str = "c1",
) -> dict:
    return {
        "case_id": case_id,
        "classification": classification,
        "target": target,
        "expected": expected,
    }


def _oracle(*cases: dict) -> HoldoutOracle:
    return HoldoutOracle.model_validate({"cases": list(cases)})


def _full_profile(target: str, fact: dict) -> dict:
    if target.startswith("identity."):
        return {"identity": {target.removeprefix("identity."): fact}}
    if "." not in target:
        return {target: fact}
    family, index_text = target.split(".")
    facts = [None] * (int(index_text) + 1)
    facts[int(index_text)] = fact
    return {family: facts}


def test_supported_state_does_not_hide_wrong_value_and_component_failures() -> None:
    case = _oracle(
        _case(
            "business_description",
            {
                "kind": "profile",
                "state": "supported",
                "value": "expected",
                "evidence_source_ids": ["source-a", "source-b"],
                "reason_nonempty": False,
            },
        )
    ).cases[0]
    result = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": "wrong",
                "reason": "unexpected",
                "evidence": [{"source_id": "source-a"}],
            },
        ),
    )
    assert result.passed is False
    assert result.failures == ("value", "reason_nonempty", "evidence_source_ids")


def test_repeated_citations_from_one_source_compare_as_one_source_id() -> None:
    case = _oracle(
        _case(
            "business_description",
            {
                "kind": "profile",
                "state": "supported",
                "value": "Example",
                "evidence_source_ids": ["source-a"],
            },
        )
    ).cases[0]
    scored = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": "Example",
                "evidence": [{"source_id": "source-a"}, {"source_id": "source-a"}],
            },
        ),
    )
    assert scored.passed is True


def test_missing_value_key_does_not_satisfy_expected_null() -> None:
    case = _oracle(_case("markets", {"kind": "profile", "state": "unknown", "value": None})).cases[
        0
    ]
    scored = score_case(case, profile=_full_profile(case.target, {"state": "unknown"}))
    assert scored.failures == ("value",)


def test_financial_decimal_comparison_is_numeric_without_precision_loss() -> None:
    case = _oracle(
        _case(
            "financials.0",
            {
                "kind": "profile",
                "state": "supported",
                "value": "12345678901234567890.1200",
                "period": {"start": "2024-01-01", "end": "2024-12-31"},
                "currency": "PLN",
                "unit": "units",
                "scope": "legal_entity",
                "group_name": None,
            },
        )
    ).cases[0]
    result = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": "12345678901234567890.12",
                "period": {"start": "2024-01-01", "end": "2024-12-31"},
                "currency": "PLN",
                "unit": "units",
                "scope": "legal_entity",
                "group_name": None,
            },
        ),
    )
    assert result.passed is True


def test_financial_float_and_json_bool_number_coercion_cannot_pass() -> None:
    financial = _oracle(
        _case(
            "financials.0",
            {
                "kind": "profile",
                "state": "supported",
                "value": "9007199254740993",
            },
        )
    ).cases[0]
    result = score_case(
        financial,
        profile=_full_profile(
            financial.target,
            {
                "state": "supported",
                "value": 9007199254740992.0,
            },
        ),
    )
    assert result.failures == ("value",)

    text = _oracle(_case("markets", {"kind": "profile", "state": "supported", "value": [1]})).cases[
        0
    ]
    result = score_case(
        text,
        profile=_full_profile(
            text.target,
            {
                "state": "supported",
                "value": [True],
            },
        ),
    )
    assert result.failures == ("value",)


def test_employee_as_of_is_an_independent_component() -> None:
    case = _oracle(
        _case(
            "employees",
            {
                "kind": "profile",
                "state": "supported",
                "value": {"kind": "exact", "count": 12},
                "as_of": "2025-02-01",
            },
        )
    ).cases[0]
    result = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": {"kind": "exact", "count": 12},
                "as_of": None,
            },
        ),
    )
    assert result.failures == ("as_of",)


def test_dates_are_checked_and_explicit_null_clears_supported_parent() -> None:
    case = _oracle(
        _case(
            "recent_developments.0",
            {
                "kind": "profile",
                "state": "supported",
                "value": {
                    "title": "A",
                    "summary": "B",
                    "published_on": "2025-01-03",
                    "occurred_on": None,
                },
                "published_on": "2025-01-03",
                "occurred_on": None,
            },
        )
    ).cases[0]
    result = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": {
                    "title": "A",
                    "summary": "B",
                    "published_on": "2025-01-03",
                    "occurred_on": None,
                },
                "evidence": [{"source_id": "s"}],
            },
        ),
    )
    assert result.passed is True
    retained_date = score_case(
        case,
        profile=_full_profile(
            case.target,
            {
                "state": "supported",
                "value": {
                    "title": "A",
                    "summary": "B",
                    "published_on": "2025-01-03",
                    "occurred_on": "2025-01-02",
                },
                "evidence": [{"source_id": "s"}],
            },
        ),
    )
    assert retained_date.passed is False
    assert "occurred_on" in retained_date.failures


def test_rejection_is_explicit_and_semantic_model_rejection_is_unexercised() -> None:
    semantic = _oracle(
        _case("markets", {"kind": "profile", "state": "supported", "value": ["EU"]})
    ).cases[0]
    result = score_case(semantic, rejection_stage="model")
    assert result.semantic_execution == "unexercised"
    assert result.passed is None
    absent = score_case(semantic, output_missing=True)
    assert absent.semantic_execution == "unassessed"
    assert absent.passed is None

    boundary = _oracle(
        _case(
            "identity.krs", {"kind": "reject", "stage": "model"}, classification="IDENTITY_INVALID"
        )
    ).cases[0]
    assert score_case(boundary, rejection_stage="model").semantic_execution == "not_applicable"
    assert score_case(boundary, output_missing=True).passed is False


def test_boundary_controls_can_assert_profile_components_or_run_rejection() -> None:
    component_control = _oracle(
        _case(
            "identity.krs",
            {"kind": "profile", "state": "unknown", "value": None},
            classification="IDENTITY_INVALID",
        )
    ).cases[0]
    scored = score_case(
        component_control, profile={"identity": {"krs": {"state": "unknown", "value": None}}}
    )
    assert scored.semantic_execution == "not_applicable"
    assert scored.passed is True

    rejection_control = _oracle(
        _case(
            "identity.krs",
            {"kind": "reject", "stage": "run"},
            classification="PROVENANCE_INVALID",
        )
    ).cases[0]
    assert score_case(rejection_control, rejection_stage="run").passed is True


def test_reject_expectation_requires_observed_stage_not_missing_output() -> None:
    case = _oracle(_case("markets", {"kind": "reject", "stage": "run"})).cases[0]
    assert score_case(case, rejection_stage="run").passed is True
    assert score_case(case, rejection_stage="model").passed is None
    assert (
        score_case(
            case, profile=_full_profile(case.target, {"state": "unknown", "value": None})
        ).passed
        is False
    )
    with pytest.raises(ValueError, match="rejection_stage"):
        score_case(case, rejection_stage="crashed")


def test_schema_rejects_bad_targets_duplicates_and_inapplicable_components() -> None:
    with pytest.raises(ValidationError):
        _oracle(_case("financials.00", {"kind": "profile", "state": "unknown", "value": None}))
    with pytest.raises(ValidationError):
        _oracle(
            _case(
                "markets", {"kind": "profile", "state": "unknown", "value": None, "currency": None}
            )
        )
    with pytest.raises(ValidationError):
        _oracle(
            _case(
                "markets", {"kind": "profile", "state": "unknown", "value": None}, case_id="same"
            ),
            _case(
                "industries", {"kind": "profile", "state": "unknown", "value": None}, case_id="same"
            ),
        )
    with pytest.raises(ValidationError):
        _oracle(
            _case(
                "markets",
                {
                    "kind": "profile",
                    "state": "unknown",
                    "value": None,
                    "evidence_source_ids": ["s", "s"],
                },
            )
        )
    with pytest.raises(ValidationError):
        _oracle(
            _case(
                "markets",
                {
                    "kind": "profile",
                    "state": "unknown",
                    "value": None,
                    "evidence_source_ids": None,
                },
            )
        )
    with pytest.raises(ValidationError):
        _oracle(
            _case(
                "markets",
                {
                    "kind": "profile",
                    "state": "unknown",
                    "value": None,
                    "unrecognized": True,
                },
            )
        )


def test_collection_scoring_rejects_missing_and_extra_ids() -> None:
    oracle = _oracle(_case("markets", {"kind": "profile", "state": "supported", "value": ["EU"]}))
    with pytest.raises(ValueError, match="IDs mismatch"):
        score_oracle(oracle, {})
    with pytest.raises(ValueError, match="IDs mismatch"):
        score_oracle(oracle, {"c1": {"output_missing": True}, "extra": {"output_missing": True}})
    assert score_oracle(oracle, {"c1": {"output_missing": True}})[0].passed is None
    missing_target = score_oracle(oracle, {"c1": {"profile": {}}})[0]
    assert missing_target.semantic_execution == "executed"
    assert missing_target.passed is False
    assert missing_target.failures == ("target_missing",)
