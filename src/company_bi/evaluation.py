"""Offline deterministic evaluation of retained company research runs."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

from pydantic import BaseModel, ConfigDict, Field
from pydantic_evals import Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from company_bi.models import CompanyIdentity, CompanyProfile, CompanyResearchRun
from company_bi.nip import InvalidNIP, validate_nip
from company_bi.registry import RegistryLookupError, lookup_company

BASELINE_ID = "59e76de"
EVAL_ROOT = Path("examples/evals")


class EvalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nip: Any
    run_file: str | None = None
    run_data: dict[str, Any] | None = None
    registry_file: str | None = None


class GoldClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str
    eligible: bool
    supported_fields: dict[str, Any] | None
    allowed_states: list[Literal["supported", "uncertain", "unknown", "missing"]]
    required_fields: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, str]]
    note: str
    failure_layer: Literal["retrieval", "extraction", "gate", "unavailable"] | None = None
    failure_category: str | None = None


class EvalMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provenance: Literal["controlled", "retained_live"]
    categories: list[str]
    expected_outcome: Literal["published", "rejected", "invalid_input", "unresolved"]
    identity: dict[str, str | None]
    claims: list[GoldClaim]


class EvalOutput(BaseModel):
    outcome: Literal["published", "rejected", "invalid_input", "unresolved", "input_error"]
    profile: dict[str, Any] | None = None
    identity: dict[str, Any] | None = None
    error: str | None = None
    diagnostics: dict[str, Any] | None = None


STRICT_CLASSIFICATIONS = (
    "SUPPORTED_CONTRACT_POSITIVE",
    "OUT_OF_CONTRACT_TRUE",
    "UNSAFE_NEGATIVE",
    "IDENTITY_INVALID",
    "PROVENANCE_INVALID",
)


def evaluate_strict_case(case: dict[str, Any], output: EvalOutput) -> dict[str, Any]:
    """Score one explicitly adjudicated contract case, separately from historical gold."""
    classification = case["classification"]
    if classification not in STRICT_CLASSIFICATIONS:
        raise ValueError(f"unknown strict classification: {classification!r}")
    expected = case["expected"]
    facts = _facts(output)
    fact = facts.get(case["path"])
    state = "missing" if fact is None else fact.get("state", "missing")
    supported = state == "supported"
    expected_outcome = expected["outcome"]
    published = output.outcome == "published"
    boundary_only = classification in ("IDENTITY_INVALID", "PROVENANCE_INVALID")
    result = {
        "case_id": case["case_id"],
        "classification": classification,
        "outcome": output.outcome,
        "path": case["path"],
        "state": state,
        "value": fact.get("value") if fact else None,
        "assertion_domain": "identity" if case["path"].startswith("identity.") else "research",
        "expected": expected,
        "semantic_execution": (
            "not_applicable" if boundary_only else "executed" if published else "unexercised"
        ),
        "raw_output": output.model_dump(mode="json"),
        **{
            key: case[key]
            for key in (
                "family",
                "shape",
                "original_gold_claim",
                "original_assertion",
                "source_path",
                "source_sha256",
                "source_provenance",
            )
            if key in case
        },
    }
    result["eligible"] = classification == "SUPPORTED_CONTRACT_POSITIVE"
    allowed_states = expected.get("allowed_states")
    allowed_state_ok = allowed_states is None or state in allowed_states
    if "state" in expected:
        allowed_state_ok = allowed_state_ok and state == expected["state"]
    required_ok = _matches_required(fact, expected.get("required_fields", {}))
    if classification == "SUPPORTED_CONTRACT_POSITIVE":
        result["correct"] = bool(
            published
            and expected_outcome == "published"
            and supported
            and _matches_required(fact, expected.get("supported_fields", {}))
            and required_ok
            and allowed_state_ok
        )
    elif classification in ("OUT_OF_CONTRACT_TRUE", "UNSAFE_NEGATIVE"):
        if not published:
            result["correct"] = None
        elif classification == "UNSAFE_NEGATIVE" and expected.get("state") == "supported":
            result["correct"] = bool(
                supported
                and expected.get("supported_fields")
                and expected.get("required_fields")
                and _matches_required(fact, expected["supported_fields"])
                and required_ok
            )
        else:
            result["correct"] = bool(not supported and required_ok and allowed_state_ok)
    elif classification == "PROVENANCE_INVALID":
        if expected_outcome in ("rejected", "invalid_input", "unresolved"):
            result["correct"] = output.outcome == expected_outcome
        elif not published:
            result["correct"] = None
        elif "state" in expected:
            result["correct"] = bool(state == expected["state"] and not supported and required_ok)
        else:
            result["correct"] = bool(not supported and required_ok and allowed_state_ok)
    else:  # IDENTITY_INVALID
        result["correct"] = (
            output.outcome == expected_outcome
            if expected_outcome in ("rejected", "invalid_input", "unresolved")
            else output.outcome != "published"
        )
    result["assessment"] = (
        "unassessed" if result["correct"] is None else "correct" if result["correct"] else "failed"
    )
    return result


def _raw_value_at(root: Any, dotted_path: str) -> Any:
    value = root
    for part in dotted_path.split("."):
        if isinstance(value, list):
            if not part.isdecimal():
                return None
            index = int(part)
            if index >= len(value):
                return None
            value = value[index]
        elif isinstance(value, dict):
            if part not in value:
                return None
            value = value[part]
        else:
            return None
    return value


def _historical_gold_cases(
    eval_root: Path,
    dataset_path: str,
    adjudications: dict[str, Any],
) -> list[dict[str, Any]]:
    dataset = json.loads(_case_path(eval_root, dataset_path).read_text(encoding="utf-8"))
    historical_case_names = {item["name"] for item in dataset["cases"]}
    if historical_case_names != set(adjudications):
        raise ValueError(
            "historical adjudication case coverage mismatch; "
            f"missing={sorted(historical_case_names - set(adjudications))}, "
            f"extra={sorted(set(adjudications) - historical_case_names)}"
        )
    cases = []
    for historical_case in dataset["cases"]:
        case_id = historical_case["name"]
        grouped = adjudications.get(case_id)
        if grouped is None:
            raise ValueError(f"missing strict adjudications for historical case {case_id}")
        path_rules = {}
        for classification, rule in grouped.items():
            if classification not in STRICT_CLASSIFICATIONS:
                raise ValueError(f"{case_id}: invalid classification {classification!r}")
            for claim_path in rule["paths"]:
                if claim_path in path_rules:
                    raise ValueError(f"{case_id}: duplicate adjudication for {claim_path}")
                path_rules[claim_path] = (classification, rule)
        claims = historical_case["metadata"]["claims"]
        gold_paths = {claim["path"] for claim in claims}
        if gold_paths != set(path_rules):
            missing = sorted(gold_paths - set(path_rules))
            extra = sorted(set(path_rules) - gold_paths)
            raise ValueError(
                f"{case_id}: gold adjudication coverage mismatch; missing={missing}, extra={extra}"
            )
        for claim in claims:
            classification, rule = path_rules[claim["path"]]
            expected: dict[str, Any] = {
                "outcome": rule.get("expected_outcome", "published"),
                "required_fields": claim.get("required_fields", {}),
            }
            if classification == "SUPPORTED_CONTRACT_POSITIVE":
                expected["supported_fields"] = claim.get("supported_fields") or {}
            elif classification in (
                "OUT_OF_CONTRACT_TRUE",
                "UNSAFE_NEGATIVE",
                "PROVENANCE_INVALID",
            ):
                expected["allowed_states"] = ["uncertain", "unknown", "missing"]
            cases.append(
                {
                    "case_id": f"historical:{case_id}:{claim['path']}",
                    "inputs": historical_case["inputs"],
                    "classification": classification,
                    "family": historical_case["metadata"]["categories"],
                    "shape": claim["path"],
                    "path": claim["path"],
                    "expected": expected,
                    "rationale": rule["rationale"],
                    "original_gold_claim": claim,
                    "source_provenance": {
                        "historical_case": case_id,
                        "evidence": claim.get("evidence", []),
                        "gold_note": claim.get("note"),
                    },
                }
            )
    return cases


def run_strict_view(path: Path) -> dict[str, Any]:
    """Replay a separate adjudicated view; its raw cases never alter historical gold."""
    global EVAL_ROOT
    EVAL_ROOT = path.resolve().parent
    document = json.loads(path.read_text(encoding="utf-8"))
    if "gold_claim_adjudications" in document:
        cases = _historical_gold_cases(
            EVAL_ROOT,
            document["source_dataset"],
            document["gold_claim_adjudications"],
        )
    else:
        cases = document["cases"]
    results = []
    for population_case in cases:
        assertions = population_case.get("assertions", [population_case])
        for assertion in assertions:
            case = {**population_case, **assertion}
            source_raw = case.get("run")
            source_reference = None
            if source_raw is not None:
                case_inputs = {"nip": source_raw["identity"]["nip"], "run_data": source_raw}
            elif case.get("source_path"):
                source_reference = _case_path(EVAL_ROOT, case["source_path"])
                source_raw = json.loads(source_reference.read_text(encoding="utf-8"))
                case_inputs = {"nip": source_raw["identity"]["nip"], "run_data": source_raw}
            else:
                case_inputs = case["inputs"]
                if case_inputs.get("run_file"):
                    source_reference = _case_path(EVAL_ROOT, case_inputs["run_file"])
                    source_raw = json.loads(source_reference.read_text(encoding="utf-8"))
                elif case_inputs.get("registry_file"):
                    source_reference = _case_path(EVAL_ROOT, case_inputs["registry_file"])
            if source_raw is not None:
                root = (
                    source_raw.get("identity", {})
                    if case["path"].startswith("identity.")
                    else source_raw.get("draft", {})
                )
                raw_path = (
                    case["path"].removeprefix("identity.")
                    if case["path"].startswith("identity.")
                    else case["path"]
                )
                original_assertion = _raw_value_at(root, raw_path)
                if isinstance(original_assertion, dict) and original_assertion.get("state") in (
                    "unknown",
                    "missing",
                ):
                    original_assertion = None
                case["original_assertion"] = original_assertion
            if source_reference is not None:
                provenance = case.setdefault("source_provenance", {})
                provenance.update(
                    {
                        "input": str(source_reference.relative_to(EVAL_ROOT)),
                        "sha256": hashlib.sha256(source_reference.read_bytes()).hexdigest(),
                    }
                )
            inputs = EvalInput.model_validate(case_inputs)
            results.append(evaluate_strict_case(case, _predict(inputs)))
    counts: dict[str, int] = defaultdict(int)
    for result in results:
        classification = result["classification"]
        domain = result["assertion_domain"]
        counts[f"classification_{classification}"] += 1
        counts[f"{domain}_assertions"] += 1
        counts[f"{domain}_assessment_{result['assessment']}"] += 1
        counts[f"assessment_{result['assessment']}"] += 1
        if result["assessment"] == "correct":
            counts[f"correct_{classification}"] += 1
        elif result["assessment"] == "failed":
            counts[f"failed_{classification}"] += 1
        else:
            counts[f"unassessed_{classification}"] += 1
        if result["eligible"]:
            counts["eligible_positive"] += 1
            counts["eligible_positive_correct"] += int(result["correct"] is True)
            counts[f"eligible_{domain}_positive"] += 1
            counts[f"eligible_{domain}_positive_correct"] += int(result["correct"] is True)
        if classification == "UNSAFE_NEGATIVE" and result["state"] == "supported":
            counts["unsafe_supports"] += 1
        counts[f"semantic_execution_{result['semantic_execution']}"] += 1
        if classification == "PROVENANCE_INVALID":
            if result["outcome"] == "rejected":
                counts["provenance_rejected"] += 1
            elif result["outcome"] == "published" and result["state"] != "supported":
                counts["provenance_fact_withheld"] += 1
        if result["outcome"] == "input_error":
            counts["wrapper_input_errors"] += 1
    return {
        "view": "strict_adjudicated",
        "source": str(path),
        "historical_scoring": "separate; not included",
        "cases": results,
        "counts": dict(counts),
        "eligible_positive_recall": _ratio(
            counts.get("eligible_positive_correct", 0), counts.get("eligible_positive", 0)
        ),
        "eligible_identity_positive_recall": _ratio(
            counts.get("eligible_identity_positive_correct", 0),
            counts.get("eligible_identity_positive", 0),
        ),
        "eligible_research_positive_recall": _ratio(
            counts.get("eligible_research_positive_correct", 0),
            counts.get("eligible_research_positive", 0),
        ),
    }


def _case_path(root: Path, relative: str) -> Path:
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"evaluation input escapes dataset directory: {relative}")
    return path


def _predict(inputs: EvalInput) -> EvalOutput:
    try:
        nip = validate_nip(inputs.nip)
    except (InvalidNIP, TypeError, ValueError) as exc:
        return EvalOutput(outcome="invalid_input", error=f"INVALID_NIP: {exc}")

    if inputs.run_file or inputs.run_data is not None:
        try:
            if inputs.run_file:
                raw = json.loads(_case_path(EVAL_ROOT, inputs.run_file).read_text(encoding="utf-8"))
            elif inputs.run_data is not None:
                raw = inputs.run_data
            else:
                return EvalOutput(outcome="input_error", error="RUN_INPUT_ERROR: missing run data")
        except (OSError, ValueError) as exc:
            return EvalOutput(outcome="input_error", error=f"RUN_INPUT_ERROR: {exc}")
        trusted_identity: CompanyIdentity | None = None
        try:
            trusted_identity = CompanyIdentity.model_validate(raw["identity"])
            run = CompanyResearchRun.model_validate(raw)
            if run.identity != trusted_identity or trusted_identity.nip != nip:
                raise ValueError("fixture identity is inconsistent with the run or case NIP")
        except (ValueError, KeyError, TypeError) as exc:
            return EvalOutput(
                outcome="rejected",
                error=f"RUN_REJECTED: {exc}",
                identity=trusted_identity.model_dump(mode="json") if trusted_identity else None,
                diagnostics=raw.get("diagnostics") if isinstance(raw, dict) else None,
            )
        from company_bi.evidence import build_profile

        try:
            profile = CompanyProfile.model_validate(build_profile(run))
        except (ValueError, TypeError) as exc:
            return EvalOutput(
                outcome="rejected",
                error=f"GATE_REJECTED: {exc}",
                identity=trusted_identity.model_dump(mode="json"),
                diagnostics=run.diagnostics.model_dump(mode="json"),
            )
        return EvalOutput(
            outcome="published",
            profile=profile.model_dump(mode="json"),
            identity=trusted_identity.model_dump(mode="json"),
            diagnostics=run.diagnostics.model_dump(mode="json"),
        )

    if inputs.registry_file:
        try:
            body = _case_path(EVAL_ROOT, inputs.registry_file).read_bytes()
        except (OSError, ValueError) as exc:
            return EvalOutput(outcome="input_error", error=f"REGISTRY_INPUT_ERROR: {exc}")
        response = BytesIO(body)
        try:
            with patch("company_bi.registry.urlopen", return_value=response):
                identity, _source = lookup_company(nip, date(2025, 1, 1))
        except RegistryLookupError as exc:
            return EvalOutput(outcome="input_error", error=f"{exc.code}: {exc}")
        if identity is None:
            return EvalOutput(outcome="unresolved")
        return EvalOutput(outcome="published", identity=identity.model_dump(mode="json"))

    return EvalOutput(outcome="input_error", error="EVAL_INPUT_ERROR: no run_file or registry_file")


def _facts(output: EvalOutput) -> dict[str, dict[str, Any]]:
    if output.outcome != "published":
        return {}
    if output.profile is None:
        identity = output.identity
        if identity is None:
            return {}
        facts = {
            f"identity.{key}": value
            for key, value in identity.items()
            if isinstance(value, dict) and "state" in value
        }
        return facts
    profile = output.profile
    profile_identity = profile.get("identity") or {}
    facts = {
        f"identity.{key}": profile_identity[key]
        for key in (
            "legal_name",
            "krs",
            "regon",
            "registered_city",
            "registered_address",
            "website",
        )
        if key in profile_identity
    }
    facts.update(
        {
            key: profile[key]
            for key in (
                "business_description",
                "products_services",
                "industries",
                "markets",
                "employees",
            )
            if key in profile
        }
    )
    facts.update(
        {f"financials.{i}": fact for i, fact in enumerate(profile.get("financials") or [])}
    )
    facts.update(
        {
            f"recent_developments.{i}": fact
            for i, fact in enumerate(profile.get("recent_developments") or [])
        }
    )
    return facts


def _value(identity: dict[str, Any] | None, key: str) -> Any:
    item = (identity or {}).get(key)
    return item.get("value") if isinstance(item, dict) else item


def _approved(fact: dict[str, Any] | None, claim: GoldClaim) -> bool:
    return bool(
        fact is not None
        and fact.get("state") == "supported"
        and claim.supported_fields is not None
        and all(fact.get(key) == value for key, value in claim.supported_fields.items())
    )


def _all_null_requirement(expected: Any) -> bool:
    if isinstance(expected, dict):
        return all(_all_null_requirement(value) for value in expected.values())
    return expected is None


def _matches_required(actual: Any, expected: Any) -> bool:
    if not isinstance(expected, dict):
        return bool(actual == expected)
    if actual is None:
        return _all_null_requirement(expected)
    if not isinstance(actual, dict):
        return False
    return all(_matches_required(actual.get(key), value) for key, value in expected.items())


def evaluate_case(metadata: EvalMetadata, output: EvalOutput) -> dict[str, Any]:
    facts = _facts(output)
    claims = {claim.path: claim for claim in metadata.claims}
    counts: dict[str, int] = defaultdict(int)
    counts[f"output_outcome_{output.outcome}"] = 1
    counts[f"expected_outcome_{metadata.expected_outcome}"] = 1
    safety: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    fields: list[dict[str, Any]] = []

    observed_identity = (
        output.profile.get("identity") if output.profile is not None else output.identity
    )
    expected_resolved = any(value is not None for value in metadata.identity.values())
    identity_fields_match = all(
        _value(observed_identity, key) == value for key, value in metadata.identity.items()
    )
    counts["identity_fields_total"] += len(metadata.identity)
    counts["identity_fields_correct"] += sum(
        _value(observed_identity, key) == value for key, value in metadata.identity.items()
    )
    if expected_resolved:
        counts["identity_cases_total"] += 1
        counts["identity_cases_correct"] += int(
            observed_identity is not None and identity_fields_match
        )

    for path in sorted(set(facts) | set(claims)):
        fact = facts.get(path)
        claim = claims.get(path)
        state = "missing" if fact is None else fact.get("state", "missing")
        approved = claim is not None and _approved(fact, claim)
        registry = path.startswith("identity.")
        if fact is not None and state == "supported":
            counts["supported_registry" if registry else "supported_researched"] += 1
            if approved:
                counts[
                    "correct_supported_registry" if registry else "correct_supported_researched"
                ] += 1
            else:
                counts["unsupported_as_supported"] += 1
        if claim is None:
            continue

        required_ok = all(
            _matches_required(fact.get(key) if fact is not None else None, expected)
            for key, expected in claim.required_fields.items()
        )
        allowed = state in claim.allowed_states
        safety_failure = (
            state == "supported" and "supported" not in claim.allowed_states
        ) or not required_ok
        correct_uncertain = allowed and required_ok
        if "uncertain" in claim.allowed_states:
            safety["uncertain"]["total"] += 1
            safety["uncertain"]["correct"] += int(correct_uncertain)
        if set(claim.allowed_states) == {"unknown"}:
            safety["unknown"]["total"] += 1
            safety["unknown"]["correct"] += int(state == "unknown" and required_ok)

        if claim.eligible and not registry:
            counts["eligible_researched"] += 1
            if approved:
                counts["eligible_supported"] += 1
            elif state == "supported":
                counts["eligible_supported_wrong"] += 1
            elif state in ("uncertain", "unknown"):
                counts[f"eligible_{state}"] += 1
                counts["over_downgraded"] += 1
            else:
                counts["eligible_missing"] += 1
        fields.append(
            {
                "path": path,
                "state": state,
                "value": fact.get("value") if fact else None,
                "context": {
                    k: v
                    for k, v in (fact or {}).items()
                    if k not in {"state", "value", "evidence", "reason"}
                },
                "reason": fact.get("reason") if fact else output.error,
                "supported_approved": approved,
                "eligible": claim.eligible,
                "state_allowed": allowed,
                "required_fields_satisfied": required_ok,
                "safety_failure": safety_failure,
                "gold_loss": {
                    "failure_layer": claim.failure_layer,
                    "failure_category": claim.failure_category,
                },
                "evidence": claim.evidence,
                "note": claim.note,
            }
        )
    return {
        "counts": dict(counts),
        "safety": {k: dict(v) for k, v in safety.items()},
        "fields": fields,
    }


@dataclass
class DeterministicEvaluator(Evaluator):
    def evaluate(
        self, ctx: EvaluatorContext[EvalInput, EvalOutput, EvalMetadata]
    ) -> dict[str, bool | int]:
        if ctx.metadata is None:
            return {"no_unsupported_as_supported": False, "required_state_safety": False}
        values = evaluate_case(ctx.metadata, ctx.output)
        scores: dict[str, bool | int] = {
            "no_unsupported_as_supported": values["counts"].get("unsupported_as_supported", 0) == 0,
            "required_state_safety": all(not item["safety_failure"] for item in values["fields"]),
        }
        scores.update({f"count_{key}": value for key, value in values["counts"].items()})
        for name, value in values["safety"].items():
            scores[f"safety_{name}_correct"] = value["correct"]
            scores[f"safety_{name}_total"] = value["total"]
        return scores


def load_dataset(path: Path) -> Dataset[EvalInput, EvalOutput, EvalMetadata]:
    global EVAL_ROOT
    EVAL_ROOT = path.resolve().parent
    return Dataset[EvalInput, EvalOutput, EvalMetadata].from_file(path)


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def _add_counts(total: dict[str, int], counts: dict[str, int]) -> None:
    for key, value in counts.items():
        total[key] = total.get(key, 0) + value


def run_dataset(path: Path) -> tuple[Any, dict[str, Any]]:
    dataset = load_dataset(path)
    dataset.add_evaluator(DeterministicEvaluator())
    report = dataset.evaluate_sync(_predict, max_concurrency=1, progress=False)
    totals: dict[str, int] = defaultdict(int)
    safety: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    cases = []
    for case in report.cases:
        metadata = case.metadata
        if metadata is None:
            raise ValueError(f"Gold metadata is required for evaluation case {case.name}")
        evaluation_error = None
        try:
            score = evaluate_case(metadata, case.output)
        except Exception as exc:
            score = {"counts": {}, "safety": {}, "fields": []}
            evaluation_error = str(exc)
        evaluator_failures = [
            {"name": item.name, "error": item.error_message, "stacktrace": item.error_stacktrace}
            for item in case.evaluator_failures
        ]
        if evaluation_error is not None:
            evaluator_failures.append(
                {"name": "DeterministicEvaluator", "error": evaluation_error, "stacktrace": ""}
            )
        cases.append(
            {
                "name": case.name,
                "outcome": "evaluation_failed" if evaluator_failures else case.output.outcome,
                "prediction_outcome": case.output.outcome,
                "error": case.output.error
                or evaluation_error
                or (evaluator_failures[0]["error"] if evaluator_failures else None),
                "counts": score["counts"],
                "safety": score["safety"],
                "fields": score["fields"],
                "diagnostics": case.output.diagnostics,
                "replay_task_seconds": case.task_duration,
                "replay_total_seconds": case.total_duration,
                "evaluator_failures": evaluator_failures,
            }
        )
        if not evaluator_failures:
            case_counts = {}
            for key, result in case.scores.items():
                if key.startswith("count_"):
                    case_counts[key.removeprefix("count_")] = int(result.value)
                elif key.startswith("safety_") and key.endswith("_correct"):
                    safety[key.removeprefix("safety_").removesuffix("_correct")]["correct"] += int(
                        result.value
                    )
                elif key.startswith("safety_") and key.endswith("_total"):
                    safety[key.removeprefix("safety_").removesuffix("_total")]["total"] += int(
                        result.value
                    )
            _add_counts(totals, case_counts)
        else:
            totals["evaluator_failure_cases"] += 1
            totals["output_outcome_evaluator_failed"] += 1
            totals[f"expected_outcome_{metadata.expected_outcome}"] += 1
            totals["identity_fields_total"] += len(metadata.identity)
            if any(value is not None for value in metadata.identity.values()):
                totals["identity_cases_total"] += 1
            eligible = [
                claim
                for claim in metadata.claims
                if claim.eligible and not claim.path.startswith("identity.")
            ]
            totals["eligible_researched"] += len(eligible)
            totals["eligible_missing"] += len(eligible)
    failed_cases = []
    for failure in report.failures:
        metadata = failure.metadata
        eligible = (
            [
                claim
                for claim in metadata.claims
                if claim.eligible and not claim.path.startswith("identity.")
            ]
            if metadata
            else []
        )
        totals["output_outcome_evaluation_failed"] += 1
        totals["failed_cases"] += 1
        totals["eligible_researched"] += len(eligible)
        totals["eligible_missing"] += len(eligible)
        if metadata:
            totals[f"expected_outcome_{metadata.expected_outcome}"] += 1
            totals["identity_fields_total"] += len(metadata.identity)
            if any(value is not None for value in metadata.identity.values()):
                totals["identity_cases_total"] += 1
        failure_fields = [
            {
                "path": claim.path,
                "state": "missing",
                "value": None,
                "context": {},
                "reason": failure.error_message,
                "supported_approved": False,
                "eligible": claim.eligible,
                "state_allowed": "missing" in claim.allowed_states,
                "required_fields_satisfied": not claim.required_fields,
                "safety_failure": bool(claim.required_fields),
                "gold_loss": {
                    "failure_layer": claim.failure_layer,
                    "failure_category": claim.failure_category,
                },
                "evidence": claim.evidence,
                "note": claim.note,
            }
            for claim in (metadata.claims if metadata else [])
        ]
        failed_cases.append(
            {
                "name": failure.name,
                "outcome": "evaluation_failed",
                "error": failure.error_message,
                "stacktrace": failure.error_stacktrace,
                "expected_outcome": metadata.expected_outcome if metadata else None,
                "eligible_missing": len(eligible),
                "fields": failure_fields,
                "evaluator_failures": [],
                "diagnostics": None,
            }
        )
    report_evaluator_failures = [
        {
            "name": item.name,
            "error": item.error_message,
            "stacktrace": item.error_stacktrace,
            "error_type": item.error_type,
        }
        for item in report.report_evaluator_failures
    ]
    totals["report_evaluator_failures"] += len(report_evaluator_failures)
    safety["uncertain"]
    safety["unknown"]
    counts = dict(totals)
    metrics = {
        "identity_correctness": _ratio(
            counts.get("identity_cases_correct", 0), counts.get("identity_cases_total", 0)
        ),
        "identity_field_correctness": _ratio(
            counts.get("identity_fields_correct", 0), counts.get("identity_fields_total", 0)
        ),
        "supported_precision": _ratio(
            counts.get("correct_supported_registry", 0)
            + counts.get("correct_supported_researched", 0),
            counts.get("supported_registry", 0) + counts.get("supported_researched", 0),
        ),
        "registry_precision": _ratio(
            counts.get("correct_supported_registry", 0), counts.get("supported_registry", 0)
        ),
        "researched_precision": _ratio(
            counts.get("correct_supported_researched", 0), counts.get("supported_researched", 0)
        ),
        "unsupported_as_supported": counts.get("unsupported_as_supported", 0),
        "researched_recall": _ratio(
            counts.get("eligible_supported", 0), counts.get("eligible_researched", 0)
        ),
        "over_downgrade_rate": _ratio(
            counts.get("over_downgraded", 0), counts.get("eligible_researched", 0)
        ),
        "eligible_outcomes": {
            key: counts.get(key, 0)
            for key in (
                "eligible_supported",
                "eligible_supported_wrong",
                "eligible_uncertain",
                "eligible_unknown",
                "eligible_missing",
            )
        },
        "correct_uncertain_handling": _ratio(
            safety["uncertain"]["correct"], safety["uncertain"]["total"]
        ),
        "correct_unknown_handling": _ratio(
            safety["unknown"]["correct"], safety["unknown"]["total"]
        ),
        "safety": {
            key: {**value, "rate": _ratio(value["correct"], value["total"])}
            for key, value in safety.items()
        },
    }
    return report, {
        "view": "historical_earlier_contract",
        "cases": cases + failed_cases,
        "failed_cases": failed_cases,
        "report_evaluator_failures": report_evaluator_failures,
        "counts": counts,
        "metrics": metrics,
    }


def write_reports(dataset_path: Path, output_dir: Path) -> bool:
    report, result = run_dataset(dataset_path)
    hashes = {str(dataset_path): hashlib.sha256(dataset_path.read_bytes()).hexdigest()}
    package = Path(__file__).parent
    source_hashes = {}
    for filename in (
        "assertions.py",
        "evidence.py",
        "models.py",
        "nip.py",
        "registry.py",
        "agent.py",
        "renderer.py",
    ):
        source = package / filename
        relative = f"src/company_bi/{filename}"
        source_hashes[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    input_hash_errors = []
    for case in [*report.cases, *report.failures]:
        for relative in (case.inputs.run_file, case.inputs.registry_file):
            if relative:
                try:
                    hashes[relative] = hashlib.sha256(
                        _case_path(dataset_path.resolve().parent, relative).read_bytes()
                    ).hexdigest()
                except (OSError, ValueError) as exc:
                    input_hash_errors.append({"input": relative, "error": str(exc)})
    result.update(
        {
            "reference_production_commit": BASELINE_ID,
            "runtime_source_hashes": source_hashes,
            "hashes": hashes,
            "input_hash_errors": input_hash_errors,
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        f"# Historical earlier-contract evaluation baseline {BASELINE_ID}",
        "",
        f"Dataset SHA-256: `{hashes[str(dataset_path)]}`",
        "",
        "## Aggregate metrics",
        "",
    ]
    for name, metric in result["metrics"].items():
        if isinstance(metric, dict) and "numerator" in metric:
            rate = "N/A" if metric["rate"] is None else f"{metric['rate']:.1%}"
            lines.append(f"- {name}: {metric['numerator']}/{metric['denominator']} ({rate})")
            print(f"{name}: {metric['numerator']}/{metric['denominator']} ({rate})")
        else:
            lines.append(f"- {name}: `{json.dumps(metric, ensure_ascii=False)}`")
            if name == "unsupported_as_supported":
                print(f"{name}: {metric}")
    lines += ["", "## Runtime source hashes", ""]
    lines.extend(f"- `{name}`: `{digest}`" for name, digest in source_hashes.items())
    if result["report_evaluator_failures"]:
        lines.extend(["", "## Report evaluator failures", ""])
        lines.extend(
            f"- {item['name']}: {item['error']}" for item in result["report_evaluator_failures"]
        )
    if input_hash_errors:
        lines.extend(["", "## Input hash errors", ""])
        lines.extend(f"- `{item['input']}`: {item['error']}" for item in input_hash_errors)
    lines += ["", "## Cases", ""]
    for case in result["cases"]:
        lines.append(f"### {case['name']} — {case['outcome']}")
        if case["error"]:
            lines.append(f"\nError: `{case['error']}`")
        for error in case["evaluator_failures"]:
            lines.append(f"\nEvaluator failure: {error['name']}: `{error['error']}`")
        for field in case["fields"]:
            lines.append(
                f"\n- `{field['path']}`: {field['state']}; value={field['value']!r}; "
                f"context={field['context']!r}; reason={field['reason']!r}; "
                f"loss={field['gold_loss']}"
            )
    (output_dir / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return bool(
        input_hash_errors
        or report.failures
        or report.report_evaluator_failures
        or any(
            case.evaluator_failures
            or case.metadata.expected_outcome != case.output.outcome
            or case.assertions.get("no_unsupported_as_supported") is None
            or case.assertions["no_unsupported_as_supported"].value is False
            or case.assertions.get("required_state_safety") is None
            or case.assertions["required_state_safety"].value is False
            for case in report.cases
        )
    )
