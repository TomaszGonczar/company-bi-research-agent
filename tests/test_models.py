import json
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from company_bi.models import (
    BatchResult,
    CompanyProfile,
    EmployeeFact,
    Fact,
    FinancialFact,
    InputRow,
    ReportingPeriod,
)


@pytest.fixture
def complete_data() -> dict[str, Any]:
    path = Path(__file__).parents[1] / "examples/profiles/complete.json"
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def profile(data: dict[str, Any]) -> CompanyProfile:
    return CompanyProfile.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("value", [0, False])
def test_unknown_never_asserts_zero_or_false(value: object) -> None:
    with pytest.raises(ValidationError):
        Fact[Any](state="unknown", value=value, reason="No evidence obtained")


@pytest.mark.parametrize(
    "payload",
    [
        {"state": "supported", "value": "A claim", "evidence": []},
        {"state": "supported", "value": None, "evidence": [{"source_id": "s1", "excerpt": "x"}]},
        {"state": "uncertain", "value": None, "evidence": [], "reason": "Conflict"},
        {"state": "uncertain", "evidence": [{"source_id": "s1", "excerpt": "x"}]},
        {
            "state": "unknown",
            "reason": "Missing",
            "evidence": [{"source_id": "s1", "excerpt": "x"}],
        },
    ],
)
def test_state_requires_appropriate_value_evidence_and_reason(payload: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        Fact[str].model_validate(payload)


def test_confidence_percentages_are_not_accepted() -> None:
    with pytest.raises(ValidationError):
        Fact[str].model_validate({"state": "unknown", "reason": "Missing", "confidence": 0.9})


def test_supported_explicit_zero_is_not_missing(complete_data: dict[str, Any]) -> None:
    fact = deepcopy(complete_data["financials"][0])
    fact["value"] = "0.00"
    result = FinancialFact.model_validate_json(json.dumps(fact))
    assert result.value == Decimal("0.00")
    assert json.loads(result.model_dump_json())["value"] == "0.00"


def test_employee_range_is_not_replaced_by_a_point_estimate(complete_data: dict[str, Any]) -> None:
    employee = EmployeeFact.model_validate_json(json.dumps(complete_data["employees"]))
    assert json.loads(employee.model_dump_json())["value"] == {
        "kind": "range",
        "minimum": 51,
        "maximum": 200,
    }


@pytest.mark.parametrize(
    "value",
    [
        {"kind": "range", "minimum": 200, "maximum": 51},
        {"kind": "range", "minimum": None, "maximum": None},
        {"kind": "exact", "count": -1},
        {"kind": "exact", "count": False},
        {"kind": "exact", "count": 12.5},
    ],
)
def test_invalid_employee_quantities_are_rejected(
    complete_data: dict[str, Any],
    value: dict[str, Any],
) -> None:
    complete_data["employees"]["value"] = value
    with pytest.raises(ValidationError):
        profile(complete_data)


@pytest.mark.parametrize("field", ["metric", "period", "currency", "unit", "scope"])
def test_financial_amount_requires_all_context(complete_data: dict[str, Any], field: str) -> None:
    del complete_data["financials"][0][field]
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_group_financials_cannot_omit_group_name(complete_data: dict[str, Any]) -> None:
    complete_data["financials"][0]["scope"] = "group"
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_net_loss_preserves_decimal_precision(complete_data: dict[str, Any]) -> None:
    complete_data["financials"][1]["value"] = "-1234567890.123456789"
    fact = profile(complete_data).financials[1]
    assert fact.value == Decimal("-1234567890.123456789")
    assert json.loads(fact.model_dump_json())["value"] == "-1234567890.123456789"


def test_nonfinite_financial_amount_is_rejected(complete_data: dict[str, Any]) -> None:
    complete_data["financials"][0]["value"] = "NaN"
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_reporting_period_cannot_be_reversed() -> None:
    with pytest.raises(ValidationError):
        ReportingPeriod.model_validate_json('{"start":"2025-12-31","end":"2025-01-01"}')


def test_financials_cannot_cover_four_periods(complete_data: dict[str, Any]) -> None:
    for year in (2024, 2023, 2022):
        fact = deepcopy(complete_data["financials"][0])
        fact["period"] = {"start": f"{year}-01-01", "end": f"{year}-12-31"}
        complete_data["financials"].append(fact)
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_conflicting_financial_values_cannot_be_separate_supported_records(
    complete_data: dict[str, Any],
) -> None:
    alternative = deepcopy(complete_data["financials"][0])
    alternative["value"] = "99.00"
    complete_data["financials"].append(alternative)
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_dangling_source_reference_is_not_publishable(complete_data: dict[str, Any]) -> None:
    complete_data["employees"]["evidence"][0]["source_id"] = "never-retrieved"
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_duplicate_source_ids_are_ambiguous(complete_data: dict[str, Any]) -> None:
    complete_data["sources"][1]["source_id"] = complete_data["sources"][0]["source_id"]
    with pytest.raises(ValidationError):
        profile(complete_data)


@pytest.mark.parametrize(
    ("target", "timestamp"),
    [
        ("retrieved_at", None),
        ("retrieved_at", "2026-10-02T12:00:00"),
        ("generated_at", "2026-10-02T12:10:00"),
        ("retrieved_at", "2026-10-03T12:00:00Z"),
    ],
)
def test_retrieval_and_generation_timestamps_are_explicit_and_consistent(
    complete_data: dict[str, Any],
    target: str,
    timestamp: str | None,
) -> None:
    if target == "generated_at":
        complete_data[target] = timestamp
    else:
        complete_data["sources"][0][target] = timestamp
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_unresolved_identity_cannot_be_a_profile(complete_data: dict[str, Any]) -> None:
    complete_data["identity"]["legal_name"] = {
        "state": "unknown",
        "value": None,
        "reason": "No registry match",
    }
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_complete_cannot_hide_unknown_financials(complete_data: dict[str, Any]) -> None:
    complete_data["financials"][1] = {
        "state": "unknown",
        "value": None,
        "metric": "net_result",
        "reason": "Unavailable",
    }
    with pytest.raises(ValidationError):
        profile(complete_data)


@pytest.mark.parametrize("published_on", ["2025-10-01", "2026-10-03"])
def test_recent_items_cannot_be_outdated_or_future_dated(
    complete_data: dict[str, Any],
    published_on: str,
) -> None:
    complete_data["recent_developments"][0]["value"]["published_on"] = published_on
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_no_news_is_a_gap_not_a_claim_of_no_events(complete_data: dict[str, Any]) -> None:
    complete_data["status"] = "partial"
    complete_data["recent_developments"] = []
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_four_recent_developments_exceed_product_contract(complete_data: dict[str, Any]) -> None:
    item = complete_data["recent_developments"][0]
    complete_data["recent_developments"] = [
        {**deepcopy(item), "value": {**item["value"], "title": f"Event {index}"}}
        for index in range(4)
    ]
    with pytest.raises(ValidationError):
        profile(complete_data)


def test_nip_input_shape_does_not_silently_coerce_or_pad() -> None:
    with pytest.raises(ValidationError):
        InputRow.model_validate({"row_number": 1, "nip": 1234563218})
    with pytest.raises(ValidationError):
        InputRow.model_validate({"row_number": 1, "nip": "123"})


@pytest.mark.parametrize(
    "updates",
    [
        {"status": "unresolved", "json_path": "outputs/company.json", "reason": "No match"},
        {"status": "partial", "json_path": "outputs/company.json", "reason": "Missing facts"},
        {"status": "invalid_input", "reason": "Bad checksum"},
        {"status": "failed"},
    ],
)
def test_batch_summary_cannot_claim_an_inconsistent_outcome(updates: dict[str, Any]) -> None:
    payload = {
        "row_number": 1,
        "input_nip": "1234563218",
        "nip": "1234563218",
        "completed_at": datetime(2026, 10, 2, 12, 10, tzinfo=UTC),
        **updates,
    }
    with pytest.raises(ValidationError):
        BatchResult.model_validate(payload)


def test_unknown_optional_identifiers_do_not_force_partial(complete_data: dict[str, Any]) -> None:
    complete_data["identity"]["krs"] = {"state": "unknown", "reason": "Not supplied"}
    complete_data["identity"]["regon"] = {"state": "unknown", "reason": "Not supplied"}
    complete_data["identity"]["website"] = {"state": "unknown", "reason": "Not supplied"}
    assert profile(complete_data).status == "complete"


def test_complete_financial_coverage_requires_a_shared_reporting_interval(
    complete_data: dict[str, Any],
) -> None:
    complete_data["financials"][1]["period"] = {
        "start": "2024-01-01",
        "end": "2024-12-31",
    }
    with pytest.raises(ValidationError):
        profile(complete_data)
