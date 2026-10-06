"""Build public-model-valid CompanyResearchRun JSON from concise author specifications."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLASSES = {
    "SUPPORTED_CONTRACT_POSITIVE",
    "OUT_OF_CONTRACT_TRUE",
    "UNSAFE_NEGATIVE",
    "IDENTITY_INVALID",
    "PROVENANCE_INVALID",
}
EXPECTED_ACTIONS = {"publish", "abstain", "reject"}


def _unknown(reason: str) -> dict[str, Any]:
    return {"state": "unknown", "value": None, "evidence": [], "reason": reason}


def _fact(
    state: str, value: Any, source_id: str, context: str, reason: str | None
) -> dict[str, Any]:
    if state == "unknown":
        return _unknown(reason or "The source does not provide this information.")
    if state == "uncertain":
        return {
            "state": state,
            "value": value,
            "evidence": [{"source_id": source_id, "excerpt": context}],
            "reason": reason or "The available evidence is inconclusive.",
        }
    if state != "supported":
        raise ValueError("candidate_fact.state must be supported, uncertain or unknown")
    return {
        "state": state,
        "value": value,
        "evidence": [{"source_id": source_id, "excerpt": context}],
    }


def build_case(spec: dict[str, Any]) -> dict[str, Any]:
    """Return a serialized run envelope; no evidence or publication decision is made."""
    if not isinstance(spec, dict):
        raise ValueError("each author specification must be an object")
    required = {
        "case_id",
        "classification",
        "source_assertion",
        "candidate_fact",
        "expected_action",
    }
    missing = required - spec.keys()
    if missing:
        raise ValueError(f"missing author fields: {', '.join(sorted(missing))}")
    if not isinstance(spec["classification"], str) or spec["classification"] not in CLASSES:
        raise ValueError("classification must be one of the five strict classifications")
    if (
        not isinstance(spec["expected_action"], str)
        or spec["expected_action"] not in EXPECTED_ACTIONS
    ):
        raise ValueError("expected_action must be publish, abstain or reject")
    assertion = spec["source_assertion"]
    candidate = spec["candidate_fact"]
    if (
        not isinstance(assertion, dict)
        or not isinstance(assertion.get("text"), str)
        or not assertion["text"].strip()
    ):
        raise ValueError("source_assertion.text is required")
    if not isinstance(candidate, dict) or not isinstance(candidate.get("field_path"), str):
        raise ValueError("candidate_fact.field_path is required")

    generated = datetime(2026, 10, 6, 12, tzinfo=UTC)
    registry_id, evidence_id = "synthetic-registry", "synthetic-evidence"
    nip, name = "5220003782", "Example Company sp. z o.o."
    registry = {"result": {"subject": {"nip": nip, "name": name}}}
    registry_content = json.dumps(registry, ensure_ascii=False, separators=(",", ":"))
    identity = {
        "nip": nip,
        "legal_name": {
            "state": "supported",
            "value": name,
            "evidence": [{"source_id": registry_id, "excerpt": name}],
        },
        "krs": _unknown("The synthetic registry record does not include a KRS number."),
        "regon": _unknown("The synthetic registry record does not include a REGON number."),
        "registered_city": _unknown("The synthetic registry record does not include a city."),
        "registered_address": _unknown(
            "The synthetic registry record does not include an address."
        ),
        "website": _unknown("The synthetic registry record does not include a website."),
        "resolved_at": generated.isoformat(),
    }
    publication = spec.get("publication_metadata") or {}
    source = {
        "source_id": evidence_id,
        "url": publication.get("url", "https://example.invalid/research"),
        "title": publication.get("title", "Synthetic source"),
        "retrieved_at": generated.isoformat(),
        "published_on": publication.get("published_on", assertion.get("published_on")),
    }
    content = assertion["text"]
    if candidate.get("state", "supported") == "unknown" and candidate.get("value") is not None:
        raise ValueError("unknown candidate facts must use a null value")
    evidence = _fact(
        candidate.get("state", "supported"),
        candidate.get("value"),
        evidence_id,
        candidate.get("context", content),
        candidate.get("reason"),
    )
    draft: dict[str, Any] = {
        "business_description": _unknown("No business description was supplied in this case."),
        "products_services": _unknown("No products or services were supplied in this case."),
        "industries": _unknown("No industry information was supplied in this case."),
        "markets": _unknown("No market information was supplied in this case."),
        "employees": {
            **_unknown("No employee information was supplied in this case."),
            "as_of": None,
        },
        "financials": [
            {
                **_unknown("No financial observation was supplied in this case."),
                "metric": "revenue",
            },
            {
                **_unknown("No financial observation was supplied in this case."),
                "metric": "net_result",
            },
        ],
        "recent_developments": [],
        "limitations": [],
    }
    path = candidate["field_path"].removeprefix("draft.")
    if path in {
        "business_description",
        "products_services",
        "industries",
        "markets",
        "employees",
        "recent_developments",
    }:
        if path == "employees":
            draft[path] = {**evidence, "as_of": candidate.get("as_of")}
        elif path == "recent_developments":
            draft[path] = [evidence]
        else:
            draft[path] = evidence
    elif path in {"financials.revenue", "financials.net_result"}:
        metric = path.split(".")[1]
        idx = next(i for i, item in enumerate(draft["financials"]) if item["metric"] == metric)
        financial = {**evidence, "metric": metric}
        financial.update(candidate.get("context_fields", {}))
        draft["financials"][idx] = financial
    else:
        raise ValueError("candidate_fact.field_path must name a supported draft field")

    run: dict[str, Any] = {
        "identity": identity,
        "draft": draft,
        "sources": [
            {
                "source": {
                    "source_id": registry_id,
                    "url": "https://registry.example.test/company",
                    "title": "Synthetic registry",
                    "retrieved_at": generated.isoformat(),
                },
                "kind": "registry",
                "fetch_mode": "registry",
                "content": registry_content,
            },
            {
                "source": source,
                "kind": publication.get("kind", "full_page"),
                "fetch_mode": publication.get("fetch_mode", "static"),
                "content": content,
            },
        ],
        "diagnostics": {
            "model": "author-synthetic",
            "status": "completed",
            "model_requests": 0,
            "searches": 0,
            "page_reads": 0,
            "dynamic_reads": 0,
            "output_retries": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "duration_seconds": 0,
        },
        "generated_at": generated.isoformat(),
    }
    envelope = spec.get("envelope", {})
    if not isinstance(envelope, dict) or set(envelope) - {"identity", "sources"}:
        raise ValueError("envelope may mutate only identity or sources")
    if envelope and spec["classification"] not in {"IDENTITY_INVALID", "PROVENANCE_INVALID"}:
        raise ValueError(
            "envelope mutations are reserved for identity/provenance boundary controls"
        )
    identity_changes = envelope.get("identity", {})
    if not isinstance(identity_changes, dict):
        raise ValueError("envelope.identity must be a partial identity object")
    run["identity"].update(deepcopy(identity_changes))
    source_changes = envelope.get("sources", [])
    if not isinstance(source_changes, list):
        raise ValueError("envelope.sources must be a list of indexed source mutations")
    for mutation in source_changes:
        if (
            not isinstance(mutation, dict)
            or not isinstance(mutation.get("index"), int)
            or not 0 <= mutation["index"] < len(run["sources"])
            or not isinstance(mutation.get("changes"), dict)
        ):
            raise ValueError("each source mutation requires a valid index and changes object")
        item = run["sources"][mutation["index"]]
        changes = deepcopy(mutation["changes"])
        if "source" in changes:
            source_metadata = changes.pop("source")
            if not isinstance(source_metadata, dict):
                raise ValueError("source metadata mutation must be an object")
            item["source"].update(source_metadata)
        item.update(changes)
    target_paths = {
        "business_description": "business_description",
        "products_services": "products_services",
        "industries": "industries",
        "markets": "markets",
        "employees": "employees",
        "financials.revenue": "financials.0",
        "financials.net_result": "financials.1",
        "recent_developments": "recent_developments.0",
    }
    return {
        "case_id": spec["case_id"],
        "classification": spec["classification"],
        "path": target_paths[path],
        "expected_action": spec["expected_action"],
        "run": run,
    }


def build_file(spec_path: Path, output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {output_path}")
    specs = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(specs, list):
        specs = [specs]
    cases = [build_case(spec) for spec in specs]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as output:
        output.write(json.dumps(cases, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_file(args.spec, args.output)


if __name__ == "__main__":
    main()
