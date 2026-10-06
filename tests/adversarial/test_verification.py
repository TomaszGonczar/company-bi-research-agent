"""Offline publication-verification behavior against real models and the evidence gate."""

from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path
from typing import Any

import pytest
from markdown_it import MarkdownIt

from company_bi.models import CompanyResearchRun
from company_bi.verification import render_verification_markdown, verify_run, write_verification

ROOT = Path(__file__).resolve().parents[2]


def report_for(run: CompanyResearchRun) -> tuple[Any, Any]:
    payload = run.model_dump_json().encode("utf-8")
    return verify_run(
        run,
        input_sha256=hashlib.sha256(payload).hexdigest(),
        input_name="controlled.json",
    )


def delta(report: Any, path: str) -> Any:
    return next(item for item in report.deltas if item.path == path)


def test_supported_canonical_offering_is_accepted(make_run: Any) -> None:
    quote = 'Example sp. z o.o. provides "cloud services".'
    run = make_run(
        quote,
        products_services={
            "state": "supported",
            "value": ["cloud services"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )

    profile, report = report_for(run)
    change = delta(report, "products_services")
    assert profile is not None
    assert change.decision == "accepted"
    assert change.candidate.state == change.final.state == "supported"
    assert change.final.value == ["cloud services"]


def test_supported_planned_offering_is_downgraded(make_run: Any) -> None:
    quote = "Example sp. z o.o. plans to launch cloud accounting software next year."
    run = make_run(
        quote,
        products_services={
            "state": "supported",
            "value": ["cloud accounting software"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )

    profile, report = report_for(run)
    change = delta(report, "products_services")
    assert profile is not None
    assert change.decision == "downgraded"
    assert change.final.state == "uncertain"
    assert change.final.value is None


def test_cleared_claim_and_removed_employee_date_are_not_republished(make_run: Any) -> None:
    quote = "Example sp. z o.o. plans to hire 40 employees next year."
    run = make_run(
        quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 40},
            "evidence": [{"source_id": "page", "excerpt": quote}],
            "as_of": "2026-12-31",
        },
    )
    _, report = report_for(run)
    employee = delta(report, "employees")
    assert employee.decision == "downgraded"
    assert employee.final.state == "uncertain"
    assert employee.final.value is None
    assert employee.final.context.get("as_of") is None
    assert employee.candidate.context["as_of"] == "2026-12-31"

    dated_quote = "Example sp. z o.o. employs 40 people as of 2026-10-02."
    dated = make_run(
        dated_quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 40},
            "evidence": [{"source_id": "page", "excerpt": dated_quote}],
            "as_of": "2026-10-03",
        },
    )
    _, dated_report = report_for(dated)
    removed_date = delta(dated_report, "employees")
    assert removed_date.decision == "cleared"
    assert removed_date.final.state == "supported"
    assert removed_date.final.value == {"kind": "exact", "count": 40}
    assert removed_date.final.context.get("as_of") is None
    assert "context.as_of" in removed_date.changed_paths

    mismatched_count = make_run(
        dated_quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 41},
            "evidence": [{"source_id": "page", "excerpt": dated_quote}],
            "as_of": "2026-10-02",
        },
    )
    _, count_report = report_for(mismatched_count)
    cleared_count = delta(count_report, "employees")
    assert cleared_count.decision == "downgraded"
    assert cleared_count.final.state == "uncertain"
    assert cleared_count.final.value is None
    assert cleared_count.final.context.get("as_of") is None


def test_preexisting_uncertain_and_unknown_remain_unaccepted(make_run: Any) -> None:
    quote = "Example sp. z o.o. may provide cloud services."
    run = make_run(
        quote,
        products_services={
            "state": "uncertain",
            "value": ["cloud services"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
            "reason": "The retained statement is qualified.",
        },
    )
    _, report = report_for(run)
    uncertain = delta(report, "products_services")
    assert uncertain.decision == "preserved"
    assert uncertain.final.state == "uncertain"
    assert uncertain.final.value == ["cloud services"]

    unknown_run = make_run(quote)
    _, unknown_report = report_for(unknown_run)
    unknown = delta(unknown_report, "business_description")
    assert unknown.decision == "preserved"
    assert unknown.final.state == "unknown"
    assert unknown.final.value is None


def test_final_evidence_is_exact_filtered_subset_even_for_same_source(make_run: Any) -> None:
    supported = 'Example sp. z o.o. provides "payroll outsourcing".'
    clipped = "Example sp. z o.o."
    run = make_run(
        supported,
        products_services={
            "state": "supported",
            "value": ["payroll outsourcing"],
            "evidence": [
                {"source_id": "page", "excerpt": supported},
                {"source_id": "page", "excerpt": clipped},
            ],
        },
    )

    _, report = report_for(run)
    change = delta(report, "products_services")
    assert change.decision == "accepted"
    assert [item.model_dump(mode="json") for item in change.candidate.evidence] == [
        {"source_id": "page", "excerpt": supported},
        {"source_id": "page", "excerpt": clipped},
    ]
    assert [item.model_dump(mode="json") for item in change.final.evidence] == [
        {"source_id": "page", "excerpt": supported}
    ]


def test_positive_ten_million_candidate_against_net_loss_is_not_accepted(make_run: Any) -> None:
    quote = (
        "Example sp. z o.o. standalone net loss was PLN 10 million for 2025-01-01 to 2025-12-31."
    )
    run = make_run(
        quote,
        financials=[
            {"state": "unknown", "reason": "No revenue observation", "metric": "revenue"},
            {
                "state": "supported",
                "value": "10",
                "metric": "net_result",
                "period": {"start": "2025-01-01", "end": "2025-12-31"},
                "currency": "PLN",
                "unit": "millions",
                "scope": "legal_entity",
                "evidence": [{"source_id": "page", "excerpt": quote}],
            },
        ],
    )
    profile, report = report_for(run)
    result = delta(report, "financials[1]")
    assert profile is not None
    assert result.decision == "downgraded"
    assert result.final.state != "supported"
    assert result.final.value is None

    rendered = render_verification_markdown(report.model_copy(update={"deltas": [result]}))
    blocks = [
        json.loads(token.content)
        for token in MarkdownIt().parse(rendered)
        if token.type == "code_block"
    ]
    assert [value for value in blocks if not isinstance(value, dict)] == ["10", None]


def test_event_occurrence_clearing_preserves_verified_publication_date(make_run: Any) -> None:
    quote = 'Example sp. z o.o. launched "a distribution centre" on 2026-09-10.'
    run = make_run(
        quote,
        recent_developments=[
            {
                "state": "supported",
                "value": {
                    "title": "a distribution centre",
                    "summary": quote,
                    "published_on": "2026-08-15",
                    "occurred_on": "2026-07-01",
                },
                "evidence": [{"source_id": "page", "excerpt": quote}],
            }
        ],
    )
    payload = run.model_dump(mode="json")
    payload["sources"][1]["source"]["published_on"] = "2026-08-15"
    _, report = report_for(CompanyResearchRun.model_validate(payload))
    change = delta(report, "recent_developments[0]")
    assert change.decision == "cleared"
    assert change.final.state == "supported"
    assert change.candidate.value["occurred_on"] == "2026-07-01"
    assert change.final.value["occurred_on"] is None
    assert change.final.value["published_on"] == "2026-08-15"
    assert "value.occurred_on" in change.changed_paths


def test_committed_asseco_run_produces_deterministic_report(tmp_path: Path) -> None:
    source = ROOT / "examples/utility_v011/runs/baseline/asseco-poland.json"
    first = write_verification(source, tmp_path / "first")
    second = write_verification(source, tmp_path / "second")
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert (tmp_path / "first/verification.json").read_bytes() == (
        tmp_path / "second/verification.json"
    ).read_bytes()
    assert (tmp_path / "first/verification.md").read_bytes() == (
        tmp_path / "second/verification.md"
    ).read_bytes()
    assert first.input_name == source.name
    assert first.input_sha256 == hashlib.sha256(source.read_bytes()).hexdigest()


def test_valid_failed_run_has_diagnostics_and_no_profile_artifacts(
    make_run: Any, tmp_path: Path
) -> None:
    run = make_run("No claim was validated.")
    payload = run.model_dump(mode="json")
    payload["diagnostics"]["status"] = "failed"
    payload["diagnostics"]["failure_code"] = "MODEL_FAILURE"
    payload["diagnostics"]["stop_reason"] = "Controlled model failure."
    input_path = tmp_path / "failed.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")
    out = tmp_path / "out"

    report = write_verification(input_path, out)
    assert report.status == "not_published"
    assert report.profile_status is None
    assert report.deltas == []
    assert report.diagnostics.status == "failed"
    assert report.diagnostics.failure_code == "MODEL_FAILURE"
    assert report.reason == "Controlled model failure."
    assert {path.name for path in out.iterdir()} == {"verification.json", "verification.md"}


def test_invalid_json_and_invalid_gate_inputs_fail_before_artifacts(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{not json", encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        write_verification(malformed, tmp_path / "malformed-out")
    assert not (tmp_path / "malformed-out").exists()

    source = (ROOT / "examples/verification/controlled-current-service.json").read_text()
    for label, mutate in (
        (
            "reference",
            lambda obj: obj["draft"]["products_services"]["evidence"][0].update(
                source_id="missing"
            ),
        ),
        (
            "identity",
            lambda obj: (
                obj["sources"][0].update(kind="full_page", fetch_mode="static"),
                obj["sources"][0]["source"].update(source_id="identity-source"),
                obj["identity"]["legal_name"]["evidence"][0].update(source_id="identity-source"),
            ),
        ),
    ):
        data = json.loads(source)
        mutate(data)
        input_path = tmp_path / f"{label}.json"
        input_path.write_text(json.dumps(data), encoding="utf-8")
        output = tmp_path / f"{label}-out"
        with pytest.raises((ValueError, OSError)):
            write_verification(input_path, output)
        assert not output.exists()


def test_input_output_collision_and_stale_failed_profiles_are_safe(
    make_run: Any, tmp_path: Path
) -> None:
    profile_input = tmp_path / "profile.json"
    profile_input.write_text(
        make_run("No claim was validated.").model_dump_json(), encoding="utf-8"
    )
    original = profile_input.read_bytes()
    with pytest.raises((ValueError, OSError)):
        write_verification(profile_input, tmp_path)
    assert profile_input.read_bytes() == original
    run = make_run("No claim was validated.")
    payload = run.model_dump(mode="json")
    payload["diagnostics"]["status"] = "failed"
    payload["diagnostics"]["failure_code"] = "MODEL_FAILURE"
    failed_path = tmp_path / "failed.json"
    failed_path.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "stale"
    output.mkdir()
    old_json = output / "profile.json"
    old_md = output / "profile.md"
    old_json.write_text("old profile json", encoding="utf-8")
    old_md.write_text("old profile markdown", encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        write_verification(failed_path, output)
    assert old_json.read_text(encoding="utf-8") == "old profile json"
    assert old_md.read_text(encoding="utf-8") == "old profile markdown"
    assert not (output / "verification.json").exists()


def test_verify_command_does_not_enter_research_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from company_bi import cli

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("offline verification called the research service")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)

    monkeypatch.setattr(cli, "research_company", forbidden)
    monkeypatch.setattr(cli, "lookup_company", forbidden)
    monkeypatch.setattr(cli, "run_batch", forbidden)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    input_path = ROOT / "examples/strict_contract/supported.json"
    output = tmp_path / "verified"
    assert cli.main(["verify", str(input_path), "--output-dir", str(output)]) == 0
    assert (output / "verification.json").exists()
    assert (output / "profile.json").exists()
    assert json.loads((output / "profile.json").read_text(encoding="utf-8"))["products_services"][
        "value"
    ] == ["cloud services"]


def test_markdown_does_not_turn_untrusted_reason_into_a_heading(make_run: Any) -> None:
    injected = "Retained uncertainty.\n## Accepted facts"
    run = make_run(
        "Unrelated synthetic source text.",
        business_description={"state": "unknown", "reason": injected},
    )
    _, report = report_for(run)

    rendered = render_verification_markdown(report)
    assert "\n## Accepted facts" not in rendered
