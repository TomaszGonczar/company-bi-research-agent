import asyncio
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook

from company_bi import batch
from company_bi.models import (
    CompanyProfile,
    CompanyResearchDraft,
    CompanyResearchRun,
    ResearchDiagnostics,
    RetrievedSource,
)

NIPS = ["5220003782", "5831014898", "1234563218"]


def _profile(status: str = "complete", nip: str = NIPS[0]) -> CompanyProfile:
    fixture = "partial.json" if status == "partial" else "complete.json"
    data = json.loads(Path(f"examples/profiles/{fixture}").read_text(encoding="utf-8"))
    data["identity"]["nip"] = nip
    return CompanyProfile.model_validate(data)


def _run(profile: CompanyProfile, state: str = "completed") -> Any:
    diagnostics = ResearchDiagnostics(
        model="fake",
        status=state,
        model_requests=1,
        searches=2,
        page_reads=3,
        dynamic_reads=0,
        output_retries=0,
        input_tokens=10,
        output_tokens=10,
        duration_seconds=0.25,
    )
    unknown = {"state": "unknown", "reason": "No fixture finding"}
    draft = CompanyResearchDraft.model_validate(
        {
            "business_description": unknown,
            "products_services": unknown,
            "industries": unknown,
            "markets": unknown,
            "employees": unknown,
            "financials": [
                {**unknown, "metric": "revenue"},
                {**unknown, "metric": "net_result"},
            ],
            "recent_developments": [],
            "limitations": ["Fixture research contains no findings"],
        }
    )
    sources = [
        RetrievedSource(
            source=source,
            kind=source.kind,
            content="Fixture retained material",
            fetch_mode={
                "registry": "registry",
                "full_page": "static",
                "search_snippet": "tavily",
            }[source.kind],
        )
        for source in profile.sources
    ]
    return CompanyResearchRun(
        identity=profile.identity,
        draft=draft,
        sources=sources,
        diagnostics=diagnostics,
        generated_at=datetime.now(UTC),
    )


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fail: set[str] | None = None,
    state: str = "completed",
    partial: set[str] | None = None,
) -> dict[str, int]:
    calls = {"lookup": 0, "research": 0}
    failed_nips = fail or set()
    partial_nips = partial or set()

    def lookup(nip: str, as_of: object) -> tuple[Any, Any]:
        calls["lookup"] += 1
        if nip in failed_nips:
            raise batch.RegistryLookupError("REGISTRY_NETWORK_ERROR", "offline")
        profile = _profile(nip=nip)
        return profile.identity, profile.sources[0]

    async def research(identity: Any, sources: list[Any], *, model: str) -> Any:
        calls["research"] += 1
        run_state = "partial" if identity.nip in partial_nips else state
        return _run(_profile(nip=identity.nip), run_state)

    monkeypatch.setattr(batch, "lookup_company", lookup)
    monkeypatch.setattr(batch, "research_company", research)
    monkeypatch.setattr(
        batch,
        "build_profile",
        lambda run: _profile(
            status="partial" if run.diagnostics.status == "partial" else "complete",
            nip=run.identity.nip,
        ),
    )
    monkeypatch.setattr(batch, "render_json", lambda profile: profile.model_dump_json() + "\n")
    monkeypatch.setattr(batch, "render_markdown", lambda profile: f"# {profile.identity.nip}\n")
    return calls


def _input(path: Path, values: list[str]) -> Path:
    path.write_text("nip\n" + "\n".join(values) + "\n", encoding="utf-8")
    return path


def test_csv_and_xlsx_publish_and_checkpoint_each_original_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for suffix in ("csv", "xlsx"):
        calls = _setup(monkeypatch)
        path = tmp_path / f"input.{suffix}"
        if suffix == "csv":
            _input(path, NIPS[:1])
        else:
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["NIP"])
            sheet.append([NIPS[1]])
            workbook.save(path)
        result = asyncio.run(
            batch.run_batch(
                path, output_dir=tmp_path / f"out-{suffix}", runs_dir=tmp_path / f"runs-{suffix}"
            )
        )
        assert result[0].status == "complete"
        assert Path(result[0].json_path or "").is_file()
        assert Path(result[0].markdown_path or "").is_file()
        assert Path(result[0].research_path or "").is_file()
        assert calls == {"lookup": 1, "research": 1}


def test_per_company_failure_partial_and_duplicate_rows_are_isolated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch, fail={NIPS[1]}, partial={NIPS[2]})
    path = _input(tmp_path / "input.csv", [NIPS[0], NIPS[1], NIPS[2], NIPS[0]])
    results = asyncio.run(
        batch.run_batch(path, output_dir=tmp_path / "out", runs_dir=tmp_path / "runs")
    )
    assert [row.status for row in results] == ["complete", "failed", "partial", "complete"]
    assert [row.row_number for row in results] == [2, 3, 4, 5]
    assert calls == {"lookup": 3, "research": 2}


def test_partial_profiles_publish_and_default_resume_avoids_research(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch, state="partial")
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    first = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    assert first[0].status == "partial"
    monkeypatch.setattr(
        batch, "lookup_company", lambda *args: pytest.fail("cache should skip lookup")
    )
    monkeypatch.setattr(
        batch, "research_company", lambda *args, **kwargs: pytest.fail("cache should skip research")
    )
    again = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    assert again[0].status == "partial"
    assert calls == {"lookup": 1, "research": 1}


def test_force_and_explicit_partial_retry_repeat_research(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch, state="partial")
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs, retry_partial=True))
    asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs, force=True))
    assert calls == {"lookup": 3, "research": 3}


def test_failed_retry_preserves_previous_usable_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    _setup(monkeypatch)
    first = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    prior_json = Path(first.json_path or "").read_bytes()
    prior_markdown = Path(first.markdown_path or "").read_bytes()
    calls = _setup(monkeypatch, fail={NIPS[0]})
    failed = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs, force=True))[0]
    assert failed.status == "failed"
    assert Path(first.json_path or "").read_bytes() == prior_json
    assert Path(first.markdown_path or "").read_bytes() == prior_markdown
    assert calls["lookup"] == 1


@pytest.mark.parametrize(
    "damage", ["missing_json", "missing_markdown", "wrong_nip", "corrupt_json"]
)
def test_invalid_cached_pair_is_not_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    saved = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    json_path, md_path = Path(saved.json_path or ""), Path(saved.markdown_path or "")
    if damage == "missing_json":
        json_path.unlink()
    elif damage == "missing_markdown":
        md_path.unlink()
    elif damage == "corrupt_json":
        json_path.write_text("{", encoding="utf-8")
    else:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        payload["identity"]["nip"] = NIPS[1]
        json_path.write_text(json.dumps(payload), encoding="utf-8")
    again = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    repaired = CompanyProfile.model_validate_json(json_path.read_bytes())
    assert again[0].status == repaired.status == "complete"
    assert repaired.identity.nip == NIPS[0]
    assert batch.render_markdown(repaired) == md_path.read_text(encoding="utf-8")
    assert calls == {"lookup": 1, "research": 1}


def test_summary_distinguishes_available_zero_from_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(monkeypatch, fail={NIPS[1]})
    path = _input(tmp_path / "input.csv", [NIPS[0], NIPS[1], "bad"])
    out, runs = tmp_path / "out", tmp_path / "runs"
    asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    with (out / "batch_summary.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["supported_count"] == "13" and rows[0]["unknown_count"] == "1"
    assert rows[1]["searches"] == "" and rows[1]["duration_seconds"] == ""
    assert rows[2]["supported_count"] == "" and rows[2]["unknown_count"] == ""


def test_checkpoint_survives_interruption_before_next_company(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", NIPS[:2])
    out, runs = tmp_path / "out", tmp_path / "runs"
    original_research = batch.research_company
    invocation = 0

    async def interrupted(identity: Any, sources: list[Any], *, model: str) -> Any:
        nonlocal invocation
        invocation += 1
        if invocation == 2:
            raise KeyboardInterrupt
        return await original_research(identity, sources, model=model)

    monkeypatch.setattr(batch, "research_company", interrupted)
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    monkeypatch.setattr(batch, "research_company", original_research)
    results = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    assert [row.status for row in results] == ["complete", "complete"]
    assert calls == {"lookup": 3, "research": 2}


def test_retry_failed_retries_only_with_opt_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    _setup(monkeypatch, fail={NIPS[0]})
    assert asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0].status == "failed"
    _setup(monkeypatch)
    assert asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0].status == "failed"
    result = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs, retry_failed=True))[0]
    assert result.status == "complete"


def test_publication_without_checkpoint_recovers_from_retained_research(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    original_replace = batch._replace_pair

    def publish_then_interrupt(*args: Any) -> None:
        original_replace(*args)
        raise KeyboardInterrupt

    monkeypatch.setattr(batch, "_replace_pair", publish_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    assert not (out / "_batch_state.json").exists()
    monkeypatch.setattr(batch, "_replace_pair", original_replace)
    monkeypatch.setattr(
        batch, "build_profile", lambda run: _profile(status="partial", nip=run.identity.nip)
    )
    recovered = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert recovered.status == "partial"
    assert recovered.diagnostics is not None
    assert recovered.diagnostics.searches == 2
    assert recovered.research_path is not None
    assert Path(recovered.research_path).is_file()
    assert recovered.json_path == str(out / f"{NIPS[0]}.json")
    assert recovered.markdown_path == str(out / f"{NIPS[0]}.md")
    assert (
        CompanyProfile.model_validate_json(Path(recovered.json_path).read_bytes()).status
        == "partial"
    )
    assert calls == {"lookup": 1, "research": 1}


def test_checkpoint_without_research_path_uses_raw_gate_not_pair_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    saved = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    partial = _profile(status="partial")
    Path(saved.json_path or "").write_text(batch.render_json(partial), encoding="utf-8")
    Path(saved.markdown_path or "").write_text(batch.render_markdown(partial), encoding="utf-8")
    state_path = out / "_batch_state.json"
    checkpoint = json.loads(state_path.read_text(encoding="utf-8"))
    checkpoint[0]["research_path"] = None
    state_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    recovered = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    updated = CompanyProfile.model_validate_json(Path(recovered.json_path or "").read_bytes())
    assert recovered.status == updated.status == "complete"
    assert recovered.diagnostics == saved.diagnostics
    assert recovered.research_path == saved.research_path
    assert calls == {"lookup": 1, "research": 1}


def test_missing_retained_research_cannot_reuse_schema_valid_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    saved = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    stale = _profile(status="partial")
    Path(saved.json_path or "").write_text(batch.render_json(stale), encoding="utf-8")
    Path(saved.markdown_path or "").write_text(batch.render_markdown(stale), encoding="utf-8")
    Path(saved.research_path or "").unlink()
    state_path = out / "_batch_state.json"
    checkpoint = json.loads(state_path.read_text(encoding="utf-8"))
    checkpoint[0]["research_path"] = None
    state_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    refreshed = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert refreshed.status == "complete"
    assert calls == {"lookup": 2, "research": 2}


def test_cached_research_is_regated_and_pair_refreshed_without_research(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    first = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    old_json = CompanyProfile.model_validate_json(Path(first.json_path or "").read_bytes())
    assert old_json.status == "complete"
    monkeypatch.setattr(
        batch, "build_profile", lambda run: _profile(status="partial", nip=run.identity.nip)
    )
    refreshed = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    updated = CompanyProfile.model_validate_json(Path(refreshed.json_path or "").read_bytes())
    assert refreshed.status == updated.status == "partial"
    assert refreshed.diagnostics == first.diagnostics
    assert calls == {"lookup": 1, "research": 1}


def test_corrupt_cached_research_is_not_used_as_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    first = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    Path(first.research_path or "").write_text("{", encoding="utf-8")
    refreshed = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert refreshed.status == "complete"
    assert calls == {"lookup": 2, "research": 2}


def test_separate_output_directory_regates_shared_research_into_its_own_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    runs = tmp_path / "shared-runs"
    asyncio.run(batch.run_batch(path, output_dir=tmp_path / "one", runs_dir=runs))
    result = asyncio.run(batch.run_batch(path, output_dir=tmp_path / "two", runs_dir=runs))[0]
    assert Path(result.json_path or "").parent == tmp_path / "two"
    assert Path(result.markdown_path or "").parent == tmp_path / "two"
    assert calls == {"lookup": 1, "research": 1}


def test_summary_input_collision_preserves_original_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    out = tmp_path / "out"
    out.mkdir()
    summary_input = out / "batch_summary.csv"
    summary_input.write_text(f"nip\n{NIPS[0]}\n", encoding="utf-8")
    original = summary_input.read_bytes()
    with pytest.raises(batch.InputFileError):
        asyncio.run(batch.run_batch(summary_input, output_dir=out, runs_dir=tmp_path / "runs"))
    assert summary_input.read_bytes() == original
    assert calls == {"lookup": 0, "research": 0}


def test_identity_stage_resolved_checkpoint_is_not_a_final_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))
    checkpoint = out / "_batch_state.json"
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    profile = _profile()
    payload[0]["status"] = "resolved"
    payload[0]["identity"] = profile.identity.model_dump(mode="json")
    payload[0]["sources"] = [
        source.model_dump(mode="json", exclude={"kind"}) for source in profile.sources
    ]
    payload[0]["json_path"] = None
    payload[0]["markdown_path"] = None
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    result = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert result.status == "complete"
    assert result.identity is None
    assert calls == {"lookup": 2, "research": 2}


def test_subset_checkpoint_preserves_omitted_failures_and_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _setup(monkeypatch, fail={NIPS[1]}, partial={NIPS[2]})
    full_input = _input(tmp_path / "all.csv", NIPS)
    out, runs = tmp_path / "out", tmp_path / "runs"
    initial = asyncio.run(batch.run_batch(full_input, output_dir=out, runs_dir=runs))
    assert [result.status for result in initial] == ["complete", "failed", "partial"]

    subset = _input(tmp_path / "subset.csv", [NIPS[2]])
    asyncio.run(batch.run_batch(subset, output_dir=out, runs_dir=runs))
    persisted = json.loads((out / "_batch_state.json").read_text(encoding="utf-8"))
    by_nip = {result["nip"]: result for result in persisted}
    assert set(by_nip) == set(NIPS)
    assert by_nip[NIPS[0]]["diagnostics"]["searches"] == 2
    assert by_nip[NIPS[1]]["status"] == "failed"

    monkeypatch.setattr(
        batch, "lookup_company", lambda *args: pytest.fail("omitted failure should remain cached")
    )
    monkeypatch.setattr(
        batch,
        "research_company",
        lambda *args, **kwargs: pytest.fail("omitted failure should remain cached"),
    )
    resumed = asyncio.run(batch.run_batch(full_input, output_dir=out, runs_dir=runs))
    assert [result.status for result in resumed] == ["complete", "failed", "partial"]
    assert calls == {"lookup": 3, "research": 2}


def test_gate_failure_is_sanitized_and_distinct_from_artifact_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    secret = "provider payload authorization=top-secret"

    monkeypatch.setattr(
        batch, "build_profile", lambda run: (_ for _ in ()).throw(ValueError(secret))
    )
    result = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert result.status == "failed"
    assert result.error_code == "EVIDENCE_VALIDATION_FAILURE"
    assert result.reason is not None and secret not in result.reason
    assert result.diagnostics is not None


def test_artifact_io_failure_is_not_reported_as_evidence_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(monkeypatch)
    path = _input(tmp_path / "input.csv", [NIPS[0]])
    out, runs = tmp_path / "out", tmp_path / "runs"
    original_write_text = Path.write_text

    def fail_research_artifact(self: Path, data: str, *args: Any, **kwargs: Any) -> int:
        if self.name == "research.json":
            raise OSError("secret filesystem details")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_research_artifact)
    result = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))[0]
    assert result.status == "failed"
    assert result.error_code != "EVIDENCE_VALIDATION_FAILURE"
    assert "secret filesystem details" not in (result.reason or "")


def test_failed_research_company_keeps_diagnostics_and_later_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _setup(monkeypatch)

    async def research(identity: Any, sources: list[Any], *, model: str) -> Any:
        run = _run(_profile(nip=identity.nip), "failed" if identity.nip == NIPS[1] else "completed")
        if identity.nip == NIPS[1]:
            diagnostics = run.diagnostics.model_copy(update={"failure_code": "MODEL_FAILURE"})
            return run.model_copy(update={"diagnostics": diagnostics})
        return run

    monkeypatch.setattr(batch, "research_company", research)
    path = _input(tmp_path / "input.csv", NIPS)
    out, runs = tmp_path / "out", tmp_path / "runs"
    results = asyncio.run(batch.run_batch(path, output_dir=out, runs_dir=runs))

    assert [result.status for result in results] == ["complete", "failed", "complete"]
    assert results[1].error_code == "MODEL_FAILURE"
    assert results[1].diagnostics is not None
    assert results[1].diagnostics.failure_code == "MODEL_FAILURE"
    assert results[2].json_path is not None and Path(results[2].json_path).exists()
    persisted = json.loads((out / "_batch_state.json").read_text(encoding="utf-8"))
    by_nip = {item["nip"]: item for item in persisted}
    assert by_nip[NIPS[1]]["status"] == "failed"
    assert by_nip[NIPS[1]]["diagnostics"]["failure_code"] == "MODEL_FAILURE"
