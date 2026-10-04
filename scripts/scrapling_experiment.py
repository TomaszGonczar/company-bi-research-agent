#!/usr/bin/env python3
"""Matched replay experiment: isolate full-page availability from live discovery."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from tavily import AsyncTavilyClient

from company_bi import agent as agent_module
from company_bi.evidence import build_profile
from company_bi.models import (
    CompanyIdentity,
    CompanyProfile,
    CompanyResearchRun,
    OperationalFailure,
    PageReadResult,
    Source,
)
from company_bi.renderer import render_json, render_markdown
from company_bi.search import search_web
from company_bi.sources import ResearchBudget, SourceStore

COMPANIES = (
    ("Asseco", "5220003782", "asseco-poland.json", ("A", "B")),
    ("LPP", "5831014898", "lpp.json", ("B", "A")),
    ("ORLEN", "7740001454", "orlen.json", ("A", "B")),
)
MODEL = "openai-codex:gpt-6-luna"
DISCOVERY_TEMPLATE = (
    "{legal_name} NIP {nip} business products services employees financial results news"
)
RETAINED_DIR = Path("examples/evals/retained")


def _safe_url(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username
        or parts.password
    ):
        raise ValueError("Search result URL is not a safe public web URL")
    return value


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_sha256(results: list[dict[str, Any]]) -> str:
    canonical = json.dumps(results, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_inputs() -> list[dict[str, Any]]:
    inputs = []
    for name, nip, filename, arm_order in COMPANIES:
        path = RETAINED_DIR / filename
        raw = json.loads(path.read_text(encoding="utf-8"))
        identity = CompanyIdentity.model_validate(raw["identity"])
        if identity.nip != nip:
            raise ValueError(f"Retained identity NIP mismatch for {name}")
        sources = [
            Source.model_validate(item["source"])
            for item in raw["sources"]
            if item["kind"] == "registry"
        ]
        if not sources:
            raise ValueError(f"No retained registry source for {name}")
        inputs.append(
            {
                "name": name,
                "nip": nip,
                "identity": identity,
                "registry_sources": sources,
                "input_path": path,
                "input_sha256": _hash(path),
                "arm_order": arm_order,
            }
        )
    return inputs


async def _discover(item: dict[str, Any]) -> dict[str, Any]:
    identity: CompanyIdentity = item["identity"]
    query = DISCOVERY_TEMPLATE.format(legal_name=str(identity.legal_name.value), nip=item["nip"])
    retrieved_at = datetime.now(UTC)
    record: dict[str, Any] = {
        "company": item["name"],
        "nip": item["nip"],
        "query": query,
        "retrieved_at": retrieved_at.isoformat(),
        "provider_calls": 0,
        "results": [],
        "error": None,
        "candidate_sha256": _candidate_sha256([]),
    }
    client: AsyncTavilyClient | None = None
    try:
        client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        store = SourceStore(identity, item["registry_sources"])
        budget = ResearchBudget(max_seconds=25)
        record["provider_calls"] = 1
        async with asyncio.timeout(25):
            search_results = await search_web(query, client=client, store=store, budget=budget)
        record["error"] = search_results.error
        if search_results.failure is not None:
            record["failure"] = search_results.failure.model_dump(mode="json")
        try:
            for hit in search_results.results:
                _safe_url(str(hit.url))
        except ValueError:
            record["results"] = []
            record["error"] = "UnsafeURLInSearchResults"
            record["failure"] = {
                "code": "SEARCH_FAILURE",
                "stage": "search",
                "reason": "Discovery included a URL with unsafe user information",
            }
        else:
            source_times = {
                material.source.source_id: material.source.retrieved_at
                for material in store.snapshots()
                if material.kind == "search_snippet"
            }
            record["results"] = [
                {
                    "rank": rank,
                    "title": hit.title,
                    "url": str(hit.url),
                    "snippet": hit.content,
                    "score": hit.score,
                    "retrieved_at": source_times[hit.source_id].isoformat(),
                }
                for rank, hit in enumerate(search_results.results, start=1)
            ]
    except TimeoutError:
        record["error"] = "SearchTimeout"
    except Exception as error:
        record["error"] = type(error).__name__
    finally:
        if client is not None:
            try:
                async with asyncio.timeout(2):
                    await client.close()
            except Exception as error:
                record["cleanup_error"] = type(error).__name__
    record["candidate_sha256"] = _candidate_sha256(record["results"])
    return record


def _counts_for_facts(facts: list[tuple[str, Any]], news_count: int) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_field: dict[str, Counter[str]] = {}
    for field, fact in facts:
        counts[fact.state] += 1
        by_field.setdefault(field, Counter())[fact.state] += 1
    return {
        "researched_fact_count": len(facts),
        "states": {state: counts.get(state, 0) for state in ("supported", "uncertain", "unknown")},
        "by_field": {
            field: {state: values.get(state, 0) for state in ("supported", "uncertain", "unknown")}
            for field, values in by_field.items()
        },
        "news_fact_count": news_count,
        "news_count_varies_by_model_output": True,
    }


def _candidate_fact_counts(run: CompanyResearchRun) -> dict[str, Any]:
    facts = [
        ("business_description", run.draft.business_description),
        ("products_services", run.draft.products_services),
        ("industries", run.draft.industries),
        ("markets", run.draft.markets),
        ("employees", run.draft.employees),
    ]
    facts.extend(("financials", fact) for fact in run.draft.financials)
    facts.extend(("recent_developments", fact) for fact in run.draft.recent_developments)
    return _counts_for_facts(facts, len(run.draft.recent_developments))


def _published_fact_counts(profile: CompanyProfile | None) -> dict[str, Any] | None:
    if profile is None:
        return None
    facts = [
        ("business_description", profile.business_description),
        ("products_services", profile.products_services),
        ("industries", profile.industries),
        ("markets", profile.markets),
        ("employees", profile.employees),
    ]
    facts.extend(("financials", fact) for fact in profile.financials)
    facts.extend(("recent_developments", fact) for fact in profile.recent_developments)
    researched_ids = {source.source_id for source in profile.sources if source.kind != "registry"}
    if any(ref.source_id in researched_ids for ref in profile.identity.website.evidence):
        facts.append(("website_nonregistry_evidence", profile.identity.website))
    return _counts_for_facts(facts, len(profile.recent_developments))


async def _run_arm(
    item: dict[str, Any], discovery: dict[str, Any], arm: str, directory: Path
) -> dict[str, Any]:
    frozen = discovery["results"]
    urls = {entry["url"] for entry in frozen}
    replay_calls = 0
    denied_reads = 0
    page_requests = 0
    original_search = AsyncTavilyClient.search
    original_fetch = agent_module.fetch_page

    async def replay_search(client: AsyncTavilyClient, query: str, **kwargs: Any) -> dict[str, Any]:
        nonlocal replay_calls
        replay_calls += 1
        return {
            "results": [
                {
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["snippet"],
                    "score": result["score"],
                }
                for result in frozen
            ]
        }

    async def counted_fetch(source_id: str, *, store: Any, budget: Any) -> PageReadResult:
        nonlocal denied_reads, page_requests
        known = store.get(source_id)
        allowed = (
            known is not None and str(known.source.url) in urls and source_id in store.known_ids()
        )
        if arm == "A" and allowed:
            denied_reads += 1
            return PageReadResult(
                error="Full-page extraction denied by Arm A experiment policy",
                failure=OperationalFailure(
                    code="FETCH_FAILURE",
                    stage="static_fetch",
                    reason="Full-page extraction denied by Arm A experiment policy",
                    source_id=source_id,
                ),
            )
        if not allowed:
            # Preserve the production validator's unknown-source behavior; never fetch it.
            return await original_fetch(source_id, store=store, budget=budget)
        page_requests += 1
        result = await original_fetch(source_id, store=store, budget=budget)
        return result

    # Patching is scoped to this single research call and restored even on failure.
    AsyncTavilyClient.search = replay_search  # type: ignore[method-assign]
    agent_module.fetch_page = counted_fetch
    started = time.monotonic()
    try:
        run = await agent_module.research_company(
            item["identity"], item["registry_sources"], model=MODEL, max_seconds=180
        )
    finally:
        AsyncTavilyClient.search = original_search  # type: ignore[method-assign]
        agent_module.fetch_page = original_fetch
    wall_seconds = max(0.0, time.monotonic() - started)
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "research.json").write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    profile: CompanyProfile | None = None
    gate_error = None
    if run.diagnostics.status != "failed":
        try:
            profile = build_profile(run)
            (directory / "profile.json").write_text(render_json(profile), encoding="utf-8")
            (directory / "profile.md").write_text(render_markdown(profile), encoding="utf-8")
        except Exception as error:
            gate_error = type(error).__name__
    else:
        gate_error = "RunFailed; profile rendering skipped"
    fetched = [source for source in run.sources if source.kind == "full_page"]
    summary = {
        "company": item["name"],
        "nip": item["nip"],
        "arm": arm,
        "status": run.diagnostics.status,
        "gate_render_error": gate_error,
        "frozen_candidates": {
            "sha256": discovery["candidate_sha256"],
            "count": len(discovery["results"]),
            "urls_in_rank_order": [result["url"] for result in discovery["results"]],
            "paired_arms_equal": True,
            "paired_url_set_equal": True,
            "equality_basis": (
                "Both arms replay this same frozen discovery record; see discovery.json."
            ),
        },
        "facts": {
            "published": _published_fact_counts(profile),
            "candidate_pre_gate": _candidate_fact_counts(run),
            "published_unavailable_reason": (
                "Run failed or canonical gate/render did not produce a profile"
                if profile is None
                else None
            ),
            "counting_convention": (
                "Published counts use post-gate profile research facts, count each Fact once "
                "(including each financial/news Fact), exclude registry-only identity facts, "
                "and include website only when it has non-registry evidence. The profile schema "
                "has no social field. Candidate counts are pre-gate and not correctness claims."
            ),
        },
        "counts": {
            "actual_provider_search_calls": 0,
            "model_search_tool_calls_replayed": replay_calls,
            "page_tool_calls": page_requests,
            "denied_page_tool_requests": denied_reads,
            "page_reads": run.diagnostics.page_reads,
            "dynamic_reads": run.diagnostics.dynamic_reads,
            "full_page_materials": len(fetched),
            "search_snippet_materials": sum(
                source.kind == "search_snippet" for source in run.sources
            ),
            "registry_materials": sum(source.kind == "registry" for source in run.sources),
        },
        "usage": {
            "model": run.diagnostics.model,
            "instructions_sha256": hashlib.sha256(
                agent_module._AGENT_INSTRUCTIONS.encode("utf-8")
            ).hexdigest(),
            "requests": run.diagnostics.model_requests,
            "input_tokens": run.diagnostics.input_tokens,
            "output_tokens": run.diagnostics.output_tokens,
            "repairs": run.diagnostics.output_retries,
            "research_seconds": run.diagnostics.duration_seconds,
            "wall_seconds": wall_seconds,
            "cost_usd": str(run.diagnostics.cost_usd)
            if run.diagnostics.cost_usd is not None
            else None,
            "cost_unavailable_reason": "Provider does not report cost"
            if run.diagnostics.cost_usd is None
            else None,
        },
        "fetched_urls": [str(source.source.url) for source in fetched],
        "operational_failures": [
            failure.model_dump(mode="json") for failure in run.diagnostics.failures
        ],
        "artifacts": {
            "research_json": "research.json",
            "profile_json": "profile.json" if gate_error is None else None,
            "profile_markdown": "profile.md" if gate_error is None else None,
            "research_evidence": (
                "research.json includes retained snippets, fetched page contents, "
                "and fact citations for independent review."
            ),
        },
        "limitations": [
            "Supported status is not a correctness or precision claim; inspect evidence manually.",
            "Fresh model phrasing and discovery do not make frozen gold recall directly "
            "transferable; denominator unavailable.",
            "Research fact counts exclude trusted registry identity facts.",
        ],
    }
    (directory / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


async def _execute(output_dir: Path) -> int:
    if output_dir.exists():
        raise FileExistsError("Experiment output directory already exists; refusing overwrite")
    output_dir.mkdir(parents=True)
    inputs = _load_inputs()
    discoveries = []
    for item in inputs:
        discoveries.append(await _discover(item))
    discovery_by_nip = {record["nip"]: record for record in discoveries}
    (output_dir / "discovery.json").write_text(
        json.dumps(
            {
                "query_template": DISCOVERY_TEMPLATE,
                "searches_per_company": 1,
                "discoveries": discoveries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    provenance = {
        "retained_snapshot_paths": [item["input_path"].as_posix() for item in inputs],
        "retained_snapshot_sha256": {
            item["input_path"].as_posix(): item["input_sha256"] for item in inputs
        },
        "model": MODEL,
        "instructions_sha256": hashlib.sha256(
            agent_module._AGENT_INSTRUCTIONS.encode("utf-8")
        ).hexdigest(),
        "order_by_company": {item["nip"]: list(item["arm_order"]) for item in inputs},
        "budgets": {
            "research_seconds": 180,
            "searches": 6,
            "page_reads": 10,
            "dynamic_reads": 2,
            "model_requests": 12,
            "tool_calls": 24,
            "output_repairs": 1,
        },
        "gold_recall_denominator": "unavailable for fresh arbitrary model phrasing and discovery",
    }
    (output_dir / "provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    summaries = []
    for item in inputs:
        for arm in item["arm_order"]:
            summaries.append(
                await _run_arm(
                    item,
                    discovery_by_nip[item["nip"]],
                    arm,
                    output_dir / item["name"].lower() / arm,
                )
            )
    (output_dir / "summary.json").write_text(
        json.dumps(
            {
                "capture_provider_calls_total": sum(
                    record["provider_calls"] for record in discoveries
                ),
                "capture_provider_calls_counted_once_shared": True,
                "arms": summaries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return 1 if any(summary["status"] == "failed" for summary in summaries) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return asyncio.run(_execute(args.output_dir))
    except (OSError, ValueError, KeyError) as error:
        print(f"EXPERIMENT_ERROR: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
