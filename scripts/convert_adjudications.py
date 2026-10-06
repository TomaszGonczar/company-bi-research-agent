"""Convert one retained corpus using explicit per-case human adjudication overrides."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from company_bi.evaluation import STRICT_CLASSIFICATIONS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="retained corpus JSON with a cases array")
    parser.add_argument("overrides", type=Path, help="JSON object keyed by source case id")
    parser.add_argument("--output", type=Path, required=True, help="separate strict-view JSON")
    args = parser.parse_args()

    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    overrides = json.loads(args.overrides.read_text(encoding="utf-8"))
    if not isinstance(overrides, dict):
        raise ValueError("overrides must be a JSON object keyed by source case id")
    cases = []
    unadjudicated = []
    for original in corpus["cases"]:
        case_id = original.get("id")
        override = overrides.get(case_id)
        if override is None:
            unadjudicated.append(case_id)
            continue
        classification = override.get("classification")
        if classification not in STRICT_CLASSIFICATIONS:
            raise ValueError(f"{case_id}: explicit valid classification is required")
        if not override.get("rationale") or not override.get("source_reference"):
            raise ValueError(f"{case_id}: source_reference and rationale are required")
        if "expected" not in override or "target_path" not in original or "run" not in original:
            raise ValueError(
                f"{case_id}: explicit expected behavior and source run/path are required"
            )
        cases.append(
            {
                "case_id": case_id,
                "classification": classification,
                "family": original.get("family", "unspecified"),
                "shape": original.get("focus", original.get("role", "unspecified")),
                "path": original["target_path"],
                "run": original["run"],
                "expected": override["expected"],
                "rationale": override["rationale"],
                "original_label": original.get("role"),
                "source_provenance": {
                    "corpus": str(args.corpus),
                    "case_id": case_id,
                    "reference": override["source_reference"],
                },
            }
        )
    result = {
        "view": "strict_adjudicated",
        "population": corpus.get("population", args.corpus.stem),
        "source": str(args.corpus),
        "adjudication_method": (
            "explicit per-case source-backed overrides; never inferred from replay outcome"
        ),
        "cases": cases,
        "unadjudicated_case_ids": unadjudicated,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"adjudicated={len(cases)} unadjudicated={len(unadjudicated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
