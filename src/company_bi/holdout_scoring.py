"""Deterministic component-only scoring; not included in the public toolkit package."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from company_bi.holdout_oracle import HoldoutCase, HoldoutOracle, ProfileExpectation
from company_bi.strict_cases import resolve_fact_path


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    semantic_execution: str
    passed: bool | None
    failures: tuple[str, ...]


def _fact_component(fact: dict[str, Any], component: str) -> Any:
    if component in {"published_on", "occurred_on"}:
        value = fact.get("value")
        return value.get(component) if isinstance(value, dict) else None
    return fact.get(component)


def _json_exact(expected: Any, observed: Any) -> bool:
    if type(expected) is not type(observed):
        return False
    if isinstance(expected, dict):
        return expected.keys() == observed.keys() and all(
            _json_exact(expected[key], observed[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(expected) == len(observed) and all(
            _json_exact(left, right) for left, right in zip(expected, observed, strict=True)
        )
    return bool(expected == observed)


def _value_equal(expected: Any, observed: Any, *, financial: bool) -> bool:
    if financial:
        if expected is None or observed is None:
            return expected is None and observed is None
        if not isinstance(expected, str) or not isinstance(observed, str):
            return False
        try:
            return Decimal(expected) == Decimal(observed)
        except (InvalidOperation, ValueError):
            return False
    return _json_exact(expected, observed)


def score_case(
    case: HoldoutCase,
    *,
    profile: dict[str, Any] | None = None,
    rejection_stage: str | None = None,
    output_missing: bool = False,
) -> CaseScore:
    """Score one explicit observation; absent/crashed output is never rejection."""
    if rejection_stage is not None and rejection_stage not in {"model", "run"}:
        raise ValueError("rejection_stage must be 'model' or 'run'")
    if sum((profile is not None, rejection_stage is not None, output_missing)) != 1:
        raise ValueError("provide exactly one profile, rejection_stage, or output_missing")

    boundary = case.classification in {"IDENTITY_INVALID", "PROVENANCE_INVALID"}
    if output_missing:
        execution = "not_applicable" if boundary else "unassessed"
        return CaseScore(case.case_id, execution, False if boundary else None, ("output_missing",))
    if rejection_stage is not None:
        if boundary:
            passed = case.expected.kind == "reject" and case.expected.stage == rejection_stage
            failure = () if passed else ("unexpected_rejection_stage",)
            return CaseScore(case.case_id, "not_applicable", passed, failure)
        if rejection_stage == "model":
            return CaseScore(case.case_id, "unexercised", None, ("rejected_at_model",))
        if case.expected.kind == "reject" and case.expected.stage == "run":
            return CaseScore(case.case_id, "executed", True, ())
        return CaseScore(case.case_id, "executed", False, ("unexpected_run_rejection",))
    if profile is None:
        raise ValueError("profile observation is required")
    try:
        profile_fact = resolve_fact_path(profile, case.target)
    except ValueError:
        execution = "not_applicable" if boundary else "executed"
        return CaseScore(case.case_id, execution, False, ("target_missing",))
    if case.expected.kind == "reject":
        execution = "not_applicable" if boundary else "executed"
        return CaseScore(
            case.case_id, execution, False, ("expected_rejection_but_profile_observed",)
        )
    expected: ProfileExpectation = case.expected
    failures: list[str] = []
    if "value" not in profile_fact:
        failures.append("value")
    elif not _value_equal(
        expected.value, profile_fact["value"], financial=case.target.startswith("financials.")
    ):
        failures.append("value")
    if expected.reason_nonempty is not None:
        reason = profile_fact.get("reason")
        if (isinstance(reason, str) and bool(reason.strip())) != expected.reason_nonempty:
            failures.append("reason_nonempty")
    if "evidence_source_ids" in expected.model_fields_set:
        evidence = profile_fact.get("evidence")
        if not isinstance(evidence, list):
            failures.append("evidence_source_ids")
        elif any(
            not isinstance(item, dict)
            or not isinstance(item.get("source_id"), str)
            or not item["source_id"]
            for item in evidence
        ):
            failures.append("evidence_source_ids")
        elif expected.evidence_source_ids is None:
            failures.append("evidence_source_ids")
        elif {item["source_id"] for item in evidence} != set(expected.evidence_source_ids):
            failures.append("evidence_source_ids")

    for component in (
        "period",
        "currency",
        "unit",
        "scope",
        "group_name",
        "as_of",
        "published_on",
        "occurred_on",
    ):
        if component in expected.model_fields_set and not _json_exact(
            getattr(expected, component), _fact_component(profile_fact, component)
        ):
            failures.append(component)
    return CaseScore(
        case.case_id, "not_applicable" if boundary else "executed", not failures, tuple(failures)
    )


def score_oracle(oracle: HoldoutOracle, observations: dict[str, dict[str, Any]]) -> list[CaseScore]:
    """Score all cases and reject missing or extra observation IDs."""
    expected_ids = [case.case_id for case in oracle.cases]
    if len(expected_ids) != len(set(expected_ids)):
        raise ValueError("oracle contains duplicate case IDs")
    missing = set(expected_ids) - set(observations)
    extra = set(observations) - set(expected_ids)
    if missing or extra:
        raise ValueError(
            f"observation IDs mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    result: list[CaseScore] = []
    for case in oracle.cases:
        observation = observations[case.case_id]
        if set(observation) == {"profile"}:
            result.append(score_case(case, profile=observation["profile"]))
        elif set(observation) == {"rejection_stage"} and observation["rejection_stage"] in {
            "model",
            "run",
        }:
            result.append(score_case(case, rejection_stage=observation["rejection_stage"]))
        elif set(observation) == {"output_missing"} and observation["output_missing"] is True:
            result.append(score_case(case, output_missing=True))
        else:
            raise ValueError(f"invalid observation for {case.case_id}")
    return result
