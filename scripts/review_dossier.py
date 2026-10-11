"""Exercise the real CLI in network/model-blocked subprocesses; no new research."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from company_bi.dossier import build_dossier_view
from company_bi.models import CompanyProfile, CompanyResearchRun
from company_bi.verification import verify_run

ROOT = Path(__file__).resolve().parents[1]
# The real CLI parser/dispatch runs in a fresh process, with inherited live entrypoints denied.
OFFLINE_CLI = """
import socket
import urllib.request
import pydantic_ai.models
import company_bi.agent as agent
import company_bi.fetch as fetch
import company_bi.registry as registry

def deny(*args, **kwargs):
    raise AssertionError('Offline dossier attempted external access')

socket.create_connection = deny
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.getaddrinfo = deny
urllib.request.urlopen = deny
registry.urlopen = deny
agent.OpenAICodexProvider = deny
agent.AsyncTavilyClient.search = deny
fetch.AsyncFetcher.get = deny
fetch.DynamicFetcher.async_fetch = deny
pydantic_ai.models.ALLOW_MODEL_REQUESTS = False
from company_bi.cli import main
raise SystemExit(main())
"""


def body_text(reader: PdfReader) -> str:
    parts: list[str] = []

    def visit(text: str, cm: Any, tm: Any, font: Any, size: float) -> None:
        if tm[4] * cm[1] + tm[5] * cm[3] + cm[5] > 35:
            parts.append(text)

    for page in reader.pages:
        page.extract_text(visitor_text=visit)
    return "".join(parts)


def check_case(output: Path, source: Path, expected_exit: int, synthetic: bool) -> dict[str, Any]:
    raw = source.read_bytes()
    command = [
        sys.executable,
        "-c",
        OFFLINE_CLI,
        "dossier",
        str(source),
        "--output-dir",
        str(output),
    ]
    if synthetic:
        command.append("--synthetic")
    env = dict(
        os.environ,
        TAVILY_API_KEY="",
        OPENAI_API_KEY="",
        LOGFIRE_TOKEN="",
        CODEX_HOME=str(output.parent / "unused-codex-home"),
    )
    process = subprocess.run(command, env=env, capture_output=True, text=True, timeout=60, cwd=ROOT)
    findings: list[str] = []
    row: dict[str, Any] = {
        "input": source.relative_to(ROOT).as_posix(),
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "synthetic": synthetic,
        "exit_code": process.returncode,
        "expected_exit": expected_exit,
        "profile_status": None,
        "supported_research_count": None,
        "artifact_paths": [],
        "artifact_hashes": {},
        "pdf_pages": 0,
        "main_pages": 0,
        "findings": findings,
    }
    if process.returncode != expected_exit:
        findings.append(f"Expected exit {expected_exit}, observed {process.returncode}")
    if expected_exit == 2:
        if output.exists():
            findings.append("Invalid input produced an output directory")
        if "DOSSIER_ERROR:" not in process.stderr:
            findings.append("Invalid input lacked bounded dossier error")
        return row
    manifest_path = output / "dossier-manifest.json"
    if not manifest_path.is_file():
        findings.append("Missing completion manifest")
        return row
    manifest = json.loads(manifest_path.read_bytes())
    hashes = manifest["artifacts"]
    if manifest["bundle_status"] != "complete" or manifest["input_sha256"] != row["input_sha256"]:
        findings.append("Incorrect completion/input hash")
    if set(p.name for p in output.iterdir()) != {*hashes, "dossier-manifest.json"}:
        findings.append("Unexpected or missing bundle files")
    for name, expected in hashes.items():
        if hashlib.sha256((output / name).read_bytes()).hexdigest() != expected:
            findings.append(f"Artifact hash mismatch: {name}")
    row["artifact_paths"] = [f"{output.name}/{name}" for name in sorted(hashes)]
    row["artifact_hashes"] = hashes
    run = CompanyResearchRun.model_validate_json(raw)
    final, verification = verify_run(run, input_sha256=row["input_sha256"], input_name=source.name)
    if (output / "verification.json").read_text() != verification.model_dump_json(indent=2) + "\n":
        findings.append("Verification report differs from existing verifier")
    if final is None:
        if set(hashes) != {"verification.json", "verification.md"}:
            findings.append("Failed run produced company artifacts")
        if manifest["publication_status"] != "not_published":
            findings.append("Failed run labelled published")
        return row
    profile = CompanyProfile.model_validate_json((output / "profile.json").read_bytes())
    if profile != final:
        findings.append("Companion profile differs from final verifier result")
    view = build_dossier_view(final, synthetic=synthetic)
    row["profile_status"] = final.status
    row["supported_research_count"] = view.research_support_count
    row["research_generated_at"] = final.generated_at.isoformat()
    pdf = PdfReader(output / f"{view.nip}.dossier.pdf")
    row["pdf_pages"] = len(pdf.pages)
    row["main_pages"] = sum("Dossier • strona" in page.extract_text() for page in pdf.pages)
    if not 1 <= row["main_pages"] <= 2:
        findings.append("Main page count outside 1–2")
    text = "".join(body_text(pdf).split())
    for fact in view.facts:
        for value in (*fact.values, *(citation.excerpt for citation in fact.citations)):
            if "".join(value.split()) not in text:
                findings.append(f"Missing full approved content: {fact.path}")
    for item in view.sources:
        for value in (
            item.source_id,
            item.title,
            item.url,
            item.retrieved_at,
            *item.redirect_chain,
        ):
            if "".join(value.split()) not in text:
                findings.append(f"Missing final source metadata: {item.source_id}")
    for gap in view.gaps:
        if "".join(gap.reason.split()) not in text:
            findings.append(f"Missing final gap reason: {gap.path}")
    return row


def review(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=False)
    cases = [
        (
            name,
            ROOT / "examples/strict_contract" / f"{name}.json",
            2 if name == "identity_invalid" else 0,
            True,
        )
        for name in ("supported", "out_of_contract", "unsafe", "identity_invalid")
    ]
    cases.extend(
        (name, ROOT / "examples/dossier" / f"{name}.json", 1 if name == "failed-run" else 0, True)
        for name in ("rich", "failed-run", "stress", "zero-finance")
    )
    # Existing public capture, not new research and never repaired into a positive.
    cases.append(("real-asseco", ROOT / "examples/evals/retained/asseco-poland.json", 0, False))
    rows = {}
    for name, source, expected, synthetic in cases:
        try:
            rows[name] = check_case(output_dir / name, source, expected, synthetic)
        except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
            rows[name] = {
                "findings": [f"Review failed: {type(error).__name__}"],
                "input": str(source.relative_to(ROOT)),
            }
        print(name, json.dumps(rows[name], ensure_ascii=False))
    summary = {
        "purpose": "Offline presentation QA; not research accuracy or new holdout certification",
        "network_and_model_entrypoints": "blocked in every CLI subprocess",
        "cases": rows,
        "passed": all(not row["findings"] for row in rows.values()),
    }
    (output_dir / "review-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if summary["passed"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return review(args.output_dir.absolute())


if __name__ == "__main__":
    raise SystemExit(main())
