"""Consumer-visible publication assertions for the finite strict contract."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import pytest
from contract_matrix import matrix_cases

from company_bi.evidence import build_profile
from company_bi.models import CompanyResearchRun

CASES = matrix_cases()
PREDICATE_CLASSIFICATIONS = {
    "SUPPORTED_CONTRACT_POSITIVE": 3,
    "UNSAFE_NEGATIVE": 3,
    "OUT_OF_CONTRACT_TRUE": 2,
}


def _profile_fact(profile: Any, case: dict[str, Any]) -> Any:
    path = case["path"]
    if path.startswith("financials."):
        return profile.financials[int(path.rsplit(".", 1)[1])]
    if path.startswith("recent_developments."):
        return profile.recent_developments[int(path.rsplit(".", 1)[1])]
    return getattr(profile, path)


def test_every_literal_predicate_shape_has_required_adjudicated_coverage() -> None:
    shapes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in CASES:
        if not case["case_id"].startswith("ctl-") and case["family"] in {
            "products_services",
            "business_description",
            "industries",
            "markets",
            "employees",
            "financials",
            "recent_developments",
        }:
            shapes[case["shape"]].append(case)

    assert len(shapes) == 32
    for shape, cases in shapes.items():
        assert len(cases) == 8, shape
        assert Counter(case["classification"] for case in cases) == Counter(
            PREDICATE_CLASSIFICATIONS
        ), shape
        assert len({case["case_id"] for case in cases}) == 8, shape
        assert all(case["rationale"].strip() for case in cases), shape

    assert sum(case["classification"] == "SUPPORTED_CONTRACT_POSITIVE" for case in CASES) >= 96
    assert sum(case["classification"] == "UNSAFE_NEGATIVE" for case in CASES) >= 96
    assert sum(case["classification"] == "OUT_OF_CONTRACT_TRUE" for case in CASES) >= 64


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_public_profile_obeys_adjudicated_matrix_case(case: dict[str, Any]) -> None:
    expected = case["expected"]
    try:
        run = CompanyResearchRun.model_validate(case["run"])
        profile = build_profile(run)
    except (ValueError, TypeError) as error:
        assert expected["outcome"] == "rejected", f"{case['case_id']}: {error}"
        return

    assert expected["outcome"] == "published", case["case_id"]
    fact = _profile_fact(profile, case)
    assert fact.state == expected["state"], case["case_id"]
    expected_fields = expected.get("supported_fields", expected.get("required_fields"))
    actual_fields = fact.model_dump(mode="json", exclude={"evidence", "reason", "state"})
    for name, wanted in expected_fields.items():
        assert actual_fields[name] == wanted, f"{case['case_id']}: {name}"
