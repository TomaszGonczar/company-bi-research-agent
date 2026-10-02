"""Identity-stage CLI only; no research or BI report generation."""

import argparse
import sys
from collections import Counter
from pathlib import Path

from pydantic import TypeAdapter

from company_bi.ingest import InputFileError, resolve_file
from company_bi.models import BatchResult


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="company-bi")
    commands = parser.add_subparsers(dest="command", required=True)
    resolve = commands.add_parser("resolve", help="Resolve CSV/XLSX NIPs into identity records")
    resolve.add_argument("input", type=Path)
    resolve.add_argument("--output", type=Path, default=Path("outputs/identities.json"))
    args = parser.parse_args(argv)
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
