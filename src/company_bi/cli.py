"""Deterministic identity, research, and publication batch commands."""

import argparse
import asyncio
import os
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

from company_bi.agent import research_company
from company_bi.batch import run_batch
from company_bi.ingest import InputFileError, resolve_file
from company_bi.models import BatchResult
from company_bi.nip import InvalidNIP, validate_nip
from company_bi.registry import RegistryLookupError, lookup_company


def _research(nip_value: str, output: Path | None, model: str) -> int:
    try:
        nip = validate_nip(nip_value)
    except InvalidNIP as error:
        print(f"INVALID_NIP: {error}", file=sys.stderr)
        return 2
    if not os.environ.get("TAVILY_API_KEY"):
        print("CONFIG_ERROR: TAVILY_API_KEY is required", file=sys.stderr)
        return 2
    if model.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
        print("CONFIG_ERROR: OPENAI_API_KEY is required for the selected model", file=sys.stderr)
        return 2
    try:
        identity, source = lookup_company(nip, datetime.now(ZoneInfo("Europe/Warsaw")).date())
    except RegistryLookupError as error:
        print(f"{error.code}: {error}", file=sys.stderr)
        return 2
    if identity is None:
        print("COMPANY_NOT_FOUND: no identity resolved in the MF register", file=sys.stderr)
        return 2
    run = asyncio.run(research_company(identity, [source], model=model))
    path = output or (
        Path("runs") / nip / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") / "research.json"
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"FILE_ERROR: {error}", file=sys.stderr)
        return 2
    print(f"Wrote one research draft and retained sources to {path}")
    print(run.diagnostics.model_dump_json())
    return 1 if run.diagnostics.status == "failed" else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="company-bi")
    commands = parser.add_subparsers(dest="command", required=True)
    resolve = commands.add_parser("resolve", help="Resolve CSV/XLSX NIPs into identity records")
    resolve.add_argument("input", type=Path)
    resolve.add_argument("--output", type=Path, default=Path("outputs/identities.json"))
    research = commands.add_parser("research", help="Research one deterministically resolved NIP")
    research.add_argument("nip")
    research.add_argument("--output", type=Path)
    research.add_argument(
        "--model", default=os.environ.get("COMPANY_BI_MODEL", "openai-codex:gpt-6-luna")
    )
    batch = commands.add_parser("batch", help="Research and publish a CSV/XLSX NIP batch")
    batch.add_argument("input", type=Path)
    batch.add_argument("--output-dir", type=Path, default=Path("outputs"))
    batch.add_argument("--runs-dir", type=Path, default=Path("runs"))
    batch.add_argument(
        "--model", default=os.environ.get("COMPANY_BI_MODEL", "openai-codex:gpt-6-luna")
    )
    batch.add_argument("--retry-partial", action="store_true")
    batch.add_argument("--retry-failed", action="store_true")
    batch.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "research":
        return _research(args.nip, args.output, args.model)
    if args.command == "batch":
        if not os.environ.get("TAVILY_API_KEY"):
            print("CONFIG_ERROR: TAVILY_API_KEY is required", file=sys.stderr)
            return 2
        if args.model.startswith("openai:") and not os.environ.get("OPENAI_API_KEY"):
            print(
                "CONFIG_ERROR: OPENAI_API_KEY is required for the selected model", file=sys.stderr
            )
            return 2
        try:
            results = asyncio.run(
                run_batch(
                    args.input,
                    output_dir=args.output_dir,
                    runs_dir=args.runs_dir,
                    model=args.model,
                    retry_partial=args.retry_partial,
                    retry_failed=args.retry_failed,
                    force=args.force,
                )
            )
        except (InputFileError, OSError, ValueError) as error:
            print(f"BATCH_ERROR: {error}", file=sys.stderr)
            return 2
        counts = dict(Counter(result.status for result in results))
        print(f"Processed {len(results)} input rows: {counts}")
        return 1 if any(result.status == "failed" for result in results) else 0
    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        if input_path.resolve() == output_path.resolve():
            raise InputFileError("Identity output must not overwrite the input file")
        results = resolve_file(input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(TypeAdapter(list[BatchResult]).dump_json(results, indent=2) + b"\n")
    except (InputFileError, OSError) as error:
        print(f"FILE_ERROR: {error}", file=sys.stderr)
        return 2
    counts = dict(Counter(result.status for result in results))
    print(f"Wrote {len(results)} identity records to {output_path}: {counts}")
    return 0
