"""Review committed inputs offline, including a controlled local provider interruption."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

from pydantic_ai.models.function import FunctionModel

from company_bi import agent, fetch, registry
from company_bi.evidence import build_profile
from company_bi.ingest import read_input
from company_bi.models import CompanyProfile, CompanyResearchRun
from company_bi.nip import InvalidNIP, validate_nip
from company_bi.renderer import render_json, render_markdown

ROOT = Path(__file__).resolve().parents[1]
STRICT_DIR = ROOT / "examples" / "strict_contract"
RETAINED_DIR = ROOT / "examples" / "evals" / "retained"
RETAINED_NAMES = ("asseco-poland", "lpp", "orlen")
STRICT_NAMES = ("supported", "out_of_contract")


async def _deny_network_async(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("network access is disabled by the offline review")


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("network access is disabled by the offline review")


def _sample_inputs() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    input_path = ROOT / "examples" / "nips.csv"
    for _, value in read_input(input_path):
        raw = "" if value is None else str(value)
        try:
            normalized = validate_nip(value)
        except InvalidNIP as error:
            rows.append({"input": raw, "result": "rejected", "reason": str(error)})
        else:
            rows.append({"input": raw, "result": "accepted", "nip": normalized})
    return rows


def _render(profile: CompanyProfile, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(render_json(profile), encoding="utf-8")
    markdown_path.write_text(render_markdown(profile), encoding="utf-8")


async def _interrupted_research(run: CompanyResearchRun) -> CompanyResearchRun:
    registry_sources = [material.source for material in run.sources if material.kind == "registry"]
    if not registry_sources:
        raise ValueError(f"{run.identity.nip} retained snapshot has no registry source")

    def interrupt(_messages: Any, _info: Any) -> Any:
        raise RuntimeError("controlled offline provider interruption")

    with ExitStack() as stack:
        stack.enter_context(patch.object(registry, "urlopen", _deny_network))
        stack.enter_context(patch.object(urllib.request, "urlopen", _deny_network))
        stack.enter_context(patch.object(socket, "create_connection", _deny_network))
        stack.enter_context(patch.object(socket.socket, "connect", _deny_network))
        stack.enter_context(patch.object(socket.socket, "connect_ex", _deny_network))
        stack.enter_context(patch.object(agent, "OpenAICodexProvider", _deny_network))
        stack.enter_context(patch.object(socket, "getaddrinfo", _deny_network))
        stack.enter_context(patch.object(agent.AsyncTavilyClient, "search", _deny_network_async))
        stack.enter_context(patch.object(fetch.AsyncFetcher, "get", _deny_network_async))
        stack.enter_context(patch.object(fetch.DynamicFetcher, "async_fetch", _deny_network_async))
        stack.enter_context(patch.dict(os.environ, {"TAVILY_API_KEY": ""}))
        failed = await agent.research_company(
            run.identity,
            registry_sources,
            model=FunctionModel(interrupt),
            max_seconds=10,
        )
    if failed.diagnostics.status != "failed":
        raise RuntimeError("controlled FunctionModel interruption did not yield failed research")
    return failed


def _load_run(path: Path) -> CompanyResearchRun:
    return CompanyResearchRun.model_validate_json(path.read_text(encoding="utf-8"))


def review(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    provenance: dict[str, Any] = {
        "purpose": (
            "offline review; current strict-contract probes and separately labeled "
            "historical earlier-contract inputs"
        ),
        "external_network_calls": 0,
        "paid_or_live_provider_calls": 0,
        "controlled_function_model_invocations": 1,
        "sample_input": (
            "examples/nips.csv; read with company_bi.ingest.read_input "
            "and checked with company_bi.nip.validate_nip"
        ),
        "sample_rows": _sample_inputs(),
        "strict_contract_runs": {},
        "historical_retained_runs": {},
        "historical_prebuilt_profile": {
            "input": "examples/profiles/complete.json",
            "status": (
                "historical COMPLETE profile; rendered only as historical, "
                "not strict-contract evidence"
            ),
            "limitation": "prebuilt earlier-contract COMPLETE profile is not proof of the new gate",
            "json": None,
            "markdown": None,
        },
        "controlled_failed_research": None,
        "controlled_failure_timing": (
            "Preserves the observed generated_at and duration_seconds; these vary per execution."
        ),
        "evaluation": (
            "Run separately: uv run --frozen company-bi eval "
            "--dataset examples/evals/dataset.json --output-dir outputs/evals"
        ),
    }

    historical_complete = CompanyProfile.model_validate_json(
        (ROOT / "examples" / "profiles" / "complete.json").read_text(encoding="utf-8")
    )
    if historical_complete.status != "complete":
        raise RuntimeError("historical prebuilt profile must remain COMPLETE")
    complete_json = output_dir / "historical" / "prebuilt-complete.json"
    complete_markdown = output_dir / "historical" / "prebuilt-complete.md"
    _render(historical_complete, complete_json, complete_markdown)
    provenance["historical_prebuilt_profile"].update(
        json=str(complete_json.relative_to(output_dir)),
        markdown=str(complete_markdown.relative_to(output_dir)),
    )
    valid_strict_runs: list[tuple[str, CompanyResearchRun]] = []
    for name in STRICT_NAMES:
        input_path = STRICT_DIR / f"{name}.json"
        record: dict[str, Any] = {"input": input_path.relative_to(ROOT).as_posix()}
        try:
            run = _load_run(input_path)
            profile = build_profile(run)
        except (OSError, ValueError) as error:
            record.update(
                status="rejected",
                rejection=f"{type(error).__name__}: {error}",
                semantic_execution="unexercised",
                json=None,
                markdown=None,
            )
        else:
            stem = output_dir / "strict_contract" / name
            json_path, markdown_path = stem.with_suffix(".json"), stem.with_suffix(".md")
            _render(profile, json_path, markdown_path)
            record.update(
                status=profile.status,
                purpose="current finite-contract probe; not a real-company yield claim",
                semantic_execution="rendered",
                json=str(json_path.relative_to(output_dir)),
                markdown=str(markdown_path.relative_to(output_dir)),
            )
            valid_strict_runs.append((name, run))
        provenance["strict_contract_runs"][name] = record

    for name in RETAINED_NAMES:
        input_path = RETAINED_DIR / f"{name}.json"
        record = {
            "input": input_path.relative_to(ROOT).as_posix(),
            "purpose": "historical earlier-contract input",
        }
        try:
            run = _load_run(input_path)
            profile = build_profile(run)
        except (OSError, ValueError) as error:
            record.update(
                status="rejected",
                rejection=f"{type(error).__name__}: {error}",
                semantic_execution="unexercised",
                json=None,
                markdown=None,
            )
        else:
            stem = output_dir / "historical" / name
            json_path, markdown_path = stem.with_suffix(".json"), stem.with_suffix(".md")
            _render(profile, json_path, markdown_path)
            record.update(
                status=profile.status,
                semantic_execution="historical earlier-contract replay; not strict evidence",
                json=str(json_path.relative_to(output_dir)),
                markdown=str(markdown_path.relative_to(output_dir)),
            )
        provenance["historical_retained_runs"][name] = record

    if not valid_strict_runs:
        raise RuntimeError(
            "no current strict-contract run passed validation for the controlled interruption"
        )
    interruption_name, interruption_run = valid_strict_runs[0]
    failed = asyncio.run(_interrupted_research(interruption_run))
    failed_path = output_dir / "controlled" / "provider-interruption-research.json"
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.write_text(failed.model_dump_json(indent=2) + "\n", encoding="utf-8")
    provenance["controlled_failed_research"] = {
        "input_identity_and_registry_source": (
            f"examples/strict_contract/{interruption_name}.json"
        ),
        "method": (
            "actual research_company path with a guarded FunctionModel "
            "raising provider interruption"
        ),
        "status": failed.diagnostics.status,
        "failure_code": failed.diagnostics.failure_code,
        "typed_failures": [
            failure.model_dump(mode="json") for failure in failed.diagnostics.failures
        ],
        "research_json": str(failed_path.relative_to(output_dir)),
        "company_profile_or_report": None,
    }
    manifest = output_dir / "review-manifest.json"
    manifest.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "OFFLINE REVIEW — external network calls: 0; paid/live provider calls: 0; "
        "one controlled local FunctionModel interruption"
    )
    for name in STRICT_NAMES:
        print(
            f"current strict-contract probe: {name} → "
            f"strict_contract/{name}.json + .md (or rejection in manifest)"
        )
    for name in RETAINED_NAMES:
        print(f"historical input: {name} → historical/{name}.json + .md (or rejection in manifest)")
    print(
        "historical prebuilt COMPLETE → historical/prebuilt-complete.json + .md "
        "(not strict evidence)"
    )
    print(
        "controlled failed research → controlled/provider-interruption-research.json "
        "(FunctionModel only; no profile/report)"
    )
    print(f"manifest → {manifest}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render committed offline review examples")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    review(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
