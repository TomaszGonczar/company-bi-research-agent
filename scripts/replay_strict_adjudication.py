"""Replay one explicitly adjudicated strict-view population without changing historical gold."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_bi.evaluation import run_strict_view


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("population", type=Path, help="strict-view JSON file")
    parser.add_argument("--output", type=Path, required=True, help="raw replay JSON output")
    args = parser.parse_args()
    report = run_strict_view(args.population)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["counts"], indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
