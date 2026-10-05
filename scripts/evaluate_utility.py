#!/usr/bin/env python3
"""Deterministic offline replay and literal-anchor scoring for utility-v0.1.1 runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import HttpUrl, ValidationError

from company_bi.evidence import build_profile
from company_bi.models import CompanyIdentity, CompanyResearchRun, Source
from company_bi.renderer import render_json, render_markdown
from company_bi.sources import SourceStore

BUSINESS_FIELDS = ("business_description", "products_services", "industries", "markets")


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return " ".join(value.split()).casefold()


def has_anchor(value: str, anchor: str) -> bool:
    haystack, needle = normalized(value), normalized(anchor)
    return bool(
        needle and re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", haystack, flags=re.UNICODE)
    )


def observations_from_dump(dump: dict[str, Any]) -> list[dict[str, str]]:
    result: dict[tuple[str, str], dict[str, str]] = {}

    def add(field: str, value: Any, state: Any) -> None:
        if value is None:
            return
        text = (
            value
            if isinstance(value, str)
            else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
        key = (field, normalized(text))
        candidate = {
            "field": field,
            "value": text,
            "state": state if state in {"supported", "uncertain", "unknown"} else "unknown",
        }
        old = result.get(key)
        if old is None or (old["state"] != "supported" and candidate["state"] == "supported"):
            result[key] = candidate

    for field in BUSINESS_FIELDS:
        fact = dump.get(field)
        if isinstance(fact, dict):
            value = fact.get("value")
            for item in value if isinstance(value, list) else [value]:
                add(field, item, fact.get("state"))
    employees = dump.get("employees")
    if isinstance(employees, dict):
        value = employees.get("value")
        if value is not None:
            add(
                "employees",
                {"value": value, "as_of": employees.get("as_of")},
                employees.get("state"),
            )
    for financial in dump.get("financials", []):
        if not isinstance(financial, dict):
            continue
        period = financial.get("period") or {}
        field = f"financials.{financial.get('metric')}@{period.get('start')}:{period.get('end')}"
        value = {key: financial.get(key) for key in ("value", "currency", "unit")}
        add(field, value, financial.get("state"))
    for event in dump.get("recent_developments", []):
        if not isinstance(event, dict):
            continue
        value = event.get("value")
        if value is not None:
            add(f"recent_developments@{value.get('published_on')}", value, event.get("state"))
    return list(result.values())


def run_source_binding(run: CompanyResearchRun, case: dict[str, Any]) -> dict[str, str]:
    corpus: dict[tuple[str, str], str] = {}

    def own(url: str, digest: str, source_id: str) -> None:
        key = (str(HttpUrl(url)), digest)
        previous = corpus.get(key)
        if previous is not None and previous != source_id:
            raise ValueError("frozen sources ambiguously share URL/content ownership")
        corpus[key] = source_id

    for source in case["sources"]:
        source_id = source["source_id"]
        material = source["material"]
        digest = hashlib.sha256(material["content"].encode("utf-8")).hexdigest()
        if digest != source["content_sha256"]:
            raise ValueError(f"frozen source {source_id} has inconsistent content hash")
        own(str(material["source"]["url"]), digest, source_id)
        discovery = source["discovery"]
        discovery_digest = hashlib.sha256(discovery["content"].encode("utf-8")).hexdigest()
        own(discovery["url"], discovery_digest, source_id)
    expected_identity = CompanyIdentity.model_validate(case["identity"])
    if run.identity.model_dump(mode="json") != expected_identity.model_dump(mode="json"):
        raise ValueError("run identity does not match frozen case identity")
    expected_registry = Source.model_validate(case["registry_source"])
    expected_materials = SourceStore(expected_identity, [expected_registry]).snapshots()
    registry_materials = [material for material in run.sources if material.kind == "registry"]
    if len(registry_materials) != 1:
        raise ValueError("run must retain exactly one frozen registry snapshot")
    expected_dump = expected_materials[0].model_dump(mode="json")
    registry_dump = registry_materials[0].model_dump(mode="json")
    if registry_dump != expected_dump:
        raise ValueError("run registry material does not match frozen identity/source snapshot")
    binding: dict[str, str] = {}
    for material in run.sources:
        if material.kind == "registry":
            continue
        key = (
            str(material.source.url),
            hashlib.sha256(material.content.encode("utf-8")).hexdigest(),
        )
        owner = corpus.get(key)
        if owner is None:
            raise ValueError(
                f"run source {material.source.source_id} URL/content hash is not in frozen corpus"
            )
        previous = binding.get(material.source.source_id)
        if previous is not None and previous != owner:
            raise ValueError(
                f"run source ID {material.source.source_id} "
                "ambiguously owns multiple corpus sources"
            )
        binding[material.source.source_id] = owner
    for fact in _iter_run_facts(run):
        for ref in fact.get("evidence", []):
            if ref["source_id"] not in {s.source.source_id for s in run.sources}:
                raise ValueError(f"evidence references absent run source ID {ref['source_id']}")
    return binding


def _iter_run_facts(run: CompanyResearchRun) -> list[dict[str, Any]]:
    dump = run.model_dump(mode="json")
    identity = dump["identity"]
    return (
        [
            identity[key]
            for key in (
                "legal_name",
                "krs",
                "regon",
                "registered_city",
                "registered_address",
                "website",
            )
        ]
        + [dump["draft"][field] for field in BUSINESS_FIELDS]
        + [
            dump["draft"]["employees"],
            *dump["draft"]["financials"],
            *dump["draft"]["recent_developments"],
        ]
    )


def stages(
    claims: list[dict[str, Any]],
    observations: list[dict[str, str]],
    field_states: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    result = []
    for claim in claims:
        matching = [
            item
            for item in observations
            if item["field"] == claim["field"]
            and has_anchor(item["value"], claim["expected_value"])
        ]
        state = next(
            (item["state"] for item in matching if item["state"] == "supported"),
            matching[0]["state"]
            if matching
            else "unknown"
            if (field_states or {}).get(claim["field"]) == "unknown"
            else "missing",
        )
        result.append(
            {
                "claim_id": claim["id"],
                "stage": state,
                "matching_values": [item["value"] for item in matching],
            }
        )
    return result


def gold_backed_matches(
    observations: list[dict[str, str]], claims: list[dict[str, Any]]
) -> set[tuple[str, str]]:
    return {
        (item["field"], normalized(item["value"]))
        for item in observations
        if item["state"] == "supported"
        and any(
            claim["field"] == item["field"]
            and normalized(item["value"]) == normalized(claim["expected_value"])
            for claim in claims
        )
    }


def gold_credit(
    claims: list[dict[str, Any]],
    observations: list[dict[str, str]],
    matched: set[tuple[str, str]],
    assessments: dict[tuple[str, str], str],
) -> dict[str, str]:
    credits: dict[str, str] = {}
    for claim in claims:
        candidates = [
            item
            for item in observations
            if item["field"] == claim["field"]
            and item["state"] == "supported"
            and has_anchor(item["value"], claim["expected_value"])
        ]
        for item in candidates:
            key = (item["field"], normalized(item["value"]))
            if key in matched:
                credits[claim["id"]] = "gold_backed"
                break
            if assessments.get(key) == "supported":
                credits[claim["id"]] = "externally_assessed"
                break
        else:
            if candidates:
                credits[claim["id"]] = (
                    "externally_assessed_unsupported"
                    if all(
                        assessments.get((item["field"], normalized(item["value"]))) == "unsupported"
                        for item in candidates
                    )
                    else "unassessed_broader_support"
                )
    return credits


def credited_count(credits: dict[str, str]) -> int:
    return sum(reason in {"gold_backed", "externally_assessed"} for reason in credits.values())


def fact_states_from_dump(dump: dict[str, Any]) -> dict[str, str]:
    return {
        field: fact["state"]
        for field in BUSINESS_FIELDS
        if isinstance((fact := dump.get(field)), dict) and isinstance(fact.get("state"), str)
    }


def gold_stage_records(
    claims: list[dict[str, Any]],
    draft_observations: list[dict[str, str]] | None = None,
    draft_states: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    draft = stages(claims, draft_observations or [], draft_states)
    return [
        {"id": claim["id"], "draft": stage["stage"], "final": "missing", "matching_values": []}
        for claim, stage in zip(claims, draft, strict=True)
    ]


def gold_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        state: sum(item["final"] == state for item in records)
        for state in ("supported", "uncertain", "unknown", "missing")
    }


def empty_run_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    precision = precision_counts([], set(), {})
    gold = gold_counts(records)
    return {
        "gold": gold,
        "correct_supported_gold_claims": 0,
        "recall": ratio(0, sum(gold.values())),
        **precision,
        "precision": ratio(0, 0),
    }


def precision_counts(
    observations: list[dict[str, str]],
    matched: set[tuple[str, str]],
    assessments: dict[tuple[str, str], str],
) -> dict[str, int]:
    supported = [item for item in observations if item["state"] == "supported"]
    backed = sum((item["field"], normalized(item["value"])) in matched for item in supported)
    assessed = sum(
        assessments.get((item["field"], normalized(item["value"]))) == "supported"
        and (item["field"], normalized(item["value"])) not in matched
        for item in supported
    )
    denied = sum(
        assessments.get((item["field"], normalized(item["value"]))) == "unsupported"
        for item in supported
    )
    return {
        "supported_observations": len(supported),
        "gold_backed_support": backed,
        "externally_assessed_support": assessed,
        "externally_assessed_unsupported": denied,
        "unassessed_support": len(supported) - backed - assessed - denied,
    }


def _assessment_map(
    path: Path | None,
    run_sha: str,
    observations: list[dict[str, str]],
    matched: set[tuple[str, str]],
    company_id: str | None = None,
) -> dict[tuple[str, str], str]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if "runs" in data:
        data = data["runs"].get(company_id)
        if data is None:
            return {}
    if data.get("run_sha256") != run_sha:
        raise ValueError("assessments are not bound to the exact run SHA-256")
    existing = {
        (item["field"], normalized(item["value"])): item
        for item in observations
        if item["state"] == "supported"
    }
    judgments: dict[tuple[str, str], str] = {}
    for item in data.get("assessments", []):
        if not isinstance(item, dict) or item.get("judgment") not in {"supported", "unsupported"}:
            raise ValueError("assessment requires a supported/unsupported judgment")
        key = (
            item.get("field"),
            normalized(item.get("value", "")) if isinstance(item.get("value"), str) else "",
        )
        if key not in existing:
            raise ValueError(
                "assessment does not bind to an exact supported field/value observation"
            )
        judgment = item["judgment"]
        if key in judgments and judgments[key] != judgment:
            raise ValueError("contradictory assessments for one observation")
        if key in matched and judgment == "unsupported":
            raise ValueError("assessment contradicts independently reviewed gold-backed support")
        judgments[key] = judgment
    return judgments


def ratio(n: int, d: int) -> dict[str, Any]:
    return {"numerator": n, "denominator": d, "rate": n / d if d else None}


def evaluate_company(
    company: dict[str, Any],
    case: dict[str, Any],
    gold: list[dict[str, Any]],
    runs_dir: Path,
    output_dir: Path,
    assessment_path: Path | None,
) -> dict[str, Any]:
    local_gold = [claim for claim in gold if claim["company"] == company["id"]]
    if case.get("company") != company["id"] or case.get("nip") != company["nip"]:
        stage_records = gold_stage_records(local_gold)
        return {
            "company": company["id"],
            "run_status": "rejected",
            "error": "frozen case identity does not match dataset company/NIP",
            "final_files": [],
            "gold_stages": stage_records,
            "counts": empty_run_counts(stage_records),
        }
    run_path = runs_dir / f"{company['id']}.json"
    if not run_path.is_file():
        stage_records = gold_stage_records(local_gold)
        return {
            "company": company["id"],
            "run_status": "missing",
            "final_files": [],
            "gold_stages": stage_records,
            "counts": empty_run_counts(stage_records),
        }
    raw = run_path.read_bytes()
    run_sha = hashlib.sha256(raw).hexdigest()
    try:
        run = CompanyResearchRun.model_validate_json(raw)
        if run.identity.nip != company["nip"]:
            raise ValueError(
                f"run NIP {run.identity.nip} does not match dataset NIP {company['nip']}"
            )
        binding = run_source_binding(run, case)
    except (ValidationError, ValueError, KeyError, TypeError) as exc:
        stage_records = gold_stage_records(local_gold)
        return {
            "company": company["id"],
            "run_status": "rejected",
            "error": str(exc),
            "run_sha256": run_sha,
            "final_files": [],
            "gold_stages": stage_records,
            "counts": empty_run_counts(stage_records),
        }
    draft_obs = observations_from_dump(run.draft.model_dump(mode="json"))
    if run.diagnostics.status == "failed":
        stage_records = gold_stage_records(
            local_gold, draft_obs, fact_states_from_dump(run.draft.model_dump(mode="json"))
        )
        return {
            "company": company["id"],
            "run_status": "failed",
            "run_sha256": run_sha,
            "diagnostics": run.diagnostics.model_dump(mode="json"),
            "source_id_binding": binding,
            "final_files": [],
            "gold_stages": stage_records,
            "counts": empty_run_counts(stage_records),
        }
    try:
        profile = build_profile(run)
    except (ValueError, TypeError) as exc:
        stage_records = gold_stage_records(
            local_gold, draft_obs, fact_states_from_dump(run.draft.model_dump(mode="json"))
        )
        return {
            "company": company["id"],
            "run_status": "unpublishable",
            "error": str(exc),
            "run_sha256": run_sha,
            "source_id_binding": binding,
            "final_files": [],
            "gold_stages": stage_records,
            "counts": empty_run_counts(stage_records),
        }
    company_out = output_dir / company["id"]
    company_out.mkdir(parents=True, exist_ok=True)
    (company_out / "profile.json").write_text(render_json(profile), encoding="utf-8")
    (company_out / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
    final_dump = profile.model_dump(mode="json")
    draft_dump = run.draft.model_dump(mode="json")
    final_obs = observations_from_dump(final_dump)
    final_stages = stages(local_gold, final_obs, fact_states_from_dump(final_dump))
    draft_stages = stages(local_gold, draft_obs, fact_states_from_dump(draft_dump))
    matched = gold_backed_matches(final_obs, local_gold)
    try:
        assessments = _assessment_map(assessment_path, run_sha, final_obs, matched, company["id"])
    except (ValueError, KeyError, TypeError) as exc:
        credits = gold_credit(local_gold, final_obs, matched, {})
        rejected_stages = [
            {
                "id": item["claim_id"],
                "draft": next(
                    stage["stage"]
                    for stage in draft_stages
                    if stage["claim_id"] == item["claim_id"]
                ),
                "final": item["stage"],
                "matching_values": item["matching_values"],
                "correct_supported": credits.get(item["claim_id"])
                in {"gold_backed", "externally_assessed"},
                "credit_reason": credits.get(item["claim_id"]),
            }
            for item in final_stages
        ]
        gold_counts_for_run = gold_counts(rejected_stages)
        precision_for_run = precision_counts(final_obs, matched, {})
        correct = credited_count(credits)
        return {
            "company": company["id"],
            "run_status": "assessment_rejected",
            "error": str(exc),
            "run_sha256": run_sha,
            "source_id_binding": binding,
            "final_files": [f"{company['id']}/profile.json", f"{company['id']}/profile.md"],
            "gold_stages": rejected_stages,
            "counts": {
                "gold": gold_counts_for_run,
                "correct_supported_gold_claims": correct,
                "recall": ratio(correct, len(local_gold)),
                **precision_for_run,
                "precision": ratio(
                    precision_for_run["gold_backed_support"],
                    precision_for_run["supported_observations"],
                ),
            },
        }
    precision = precision_counts(final_obs, matched, assessments)
    supports = [item for item in final_obs if item["state"] == "supported"]
    counts = {
        state: sum(item["stage"] == state for item in final_stages)
        for state in ("supported", "uncertain", "unknown", "missing")
    }
    credits = gold_credit(local_gold, final_obs, matched, assessments)
    correct = credited_count(credits)
    return {
        "company": company["id"],
        "run_status": "published",
        "run_sha256": run_sha,
        "diagnostics": run.diagnostics.model_dump(mode="json"),
        "source_id_binding": binding,
        "final_files": [f"{company['id']}/profile.json", f"{company['id']}/profile.md"],
        "gold_stages": [
            {
                "id": item["claim_id"],
                "draft": next(
                    stage["stage"]
                    for stage in draft_stages
                    if stage["claim_id"] == item["claim_id"]
                ),
                "final": item["stage"],
                "matching_values": item["matching_values"],
                "correct_supported": credits.get(item["claim_id"])
                in {"gold_backed", "externally_assessed"},
                "credit_reason": credits.get(item["claim_id"]),
            }
            for item in final_stages
        ],
        "counts": {
            "gold": counts,
            "correct_supported_gold_claims": correct,
            "recall": ratio(correct, len(local_gold)),
            **precision,
            "precision": ratio(
                precision["gold_backed_support"] + precision["externally_assessed_support"],
                precision["supported_observations"],
            ),
        },
        "unmatched_supported": [
            {
                **item,
                "assessment": assessments.get(
                    (item["field"], normalized(item["value"])), "unassessed"
                ),
                "unassessed": (item["field"], normalized(item["value"])) not in matched
                and (item["field"], normalized(item["value"])) not in assessments,
            }
            for item in supports
            if (item["field"], normalized(item["value"])) not in matched
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("examples/utility_v011/dataset.json"))
    parser.add_argument("--runs-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--assessments", type=Path, help="optional run-SHA-bound external support assessments JSON"
    )
    args = parser.parse_args()
    dataset_path = args.dataset.resolve()
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    runs_dir = args.runs_dir or (dataset_path.parent / dataset["default_runs_dir"])
    if not runs_dir.is_absolute():
        runs_dir = (Path.cwd() / runs_dir).resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    gold = json.loads((dataset_path.parent / dataset["gold_file"]).read_text(encoding="utf-8"))[
        "claims"
    ]
    reports = []
    for company in dataset["cases"]:
        case = json.loads((dataset_path.parent / company["case_file"]).read_text(encoding="utf-8"))
        assessment_path = args.assessments
        if assessment_path is not None and assessment_path.is_dir():
            candidate = assessment_path / f"{company['id']}.json"
            assessment_path = candidate if candidate.is_file() else None
        reports.append(evaluate_company(company, case, gold, runs_dir, output_dir, assessment_path))
    totals = defaultdict(int)
    total_gold = len(gold)
    for report in reports:
        counts = report.get("counts")
        if not counts:
            continue
        for key, value in counts["gold"].items():
            totals[f"gold_{key}"] += value
        for key in (
            "correct_supported_gold_claims",
            "supported_observations",
            "gold_backed_support",
            "externally_assessed_support",
            "externally_assessed_unsupported",
            "unassessed_support",
        ):
            totals[key] += counts[key]
    aggregate = {
        "gold": {
            key: totals[f"gold_{key}"] for key in ("supported", "uncertain", "unknown", "missing")
        },
        "correct_supported_gold_claims": totals["correct_supported_gold_claims"],
        "recall": ratio(totals["correct_supported_gold_claims"], total_gold),
        "supported_observations": totals["supported_observations"],
        "gold_backed_support": totals["gold_backed_support"],
        "externally_assessed_support": totals["externally_assessed_support"],
        "externally_assessed_unsupported": totals["externally_assessed_unsupported"],
        "unassessed_support": totals["unassessed_support"],
        "precision": ratio(
            totals["gold_backed_support"] + totals["externally_assessed_support"],
            totals["supported_observations"],
        ),
    }
    report = {
        "dataset": str(dataset_path),
        "runs_dir": str(runs_dir),
        "companies": reports,
        "aggregate": aggregate,
    }
    (output_dir / "evaluation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    invalid_statuses = {"rejected", "unpublishable", "assessment_rejected"}
    return 1 if any(item["run_status"] in invalid_statuses for item in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
