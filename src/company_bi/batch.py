"""Sequential research and publication for CSV/XLSX NIP batches."""

import csv
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter, ValidationError

from company_bi.agent import research_company
from company_bi.evidence import build_profile
from company_bi.ingest import InputFileError, read_input
from company_bi.models import (
    BatchResult,
    CompanyProfile,
    CompanyResearchRun,
    Fact,
    InputRow,
)
from company_bi.nip import InvalidNIP, validate_nip
from company_bi.registry import RegistryLookupError, lookup_company
from company_bi.renderer import render_json, render_markdown

SUMMARY_COLUMNS = (
    "row_number",
    "input_nip",
    "nip",
    "status",
    "json_path",
    "markdown_path",
    "reason",
    "completed_at",
    "legal_name",
    "supported_count",
    "uncertain_count",
    "unknown_count",
    "searches",
    "page_reads",
    "duration_seconds",
    "error_code",
)
_RESULTS = TypeAdapter(list[BatchResult])


def _now() -> datetime:
    return datetime.now(UTC)


def _read_state(path: Path) -> list[BatchResult]:
    try:
        return _RESULTS.validate_json(path.read_bytes())
    except FileNotFoundError:
        return []
    except (OSError, ValidationError, ValueError):
        return []


def _profile_pair(nip: str, json_path: Path, markdown_path: Path) -> CompanyProfile | None:
    try:
        json_content = json_path.read_text(encoding="utf-8")
        markdown_content = markdown_path.read_text(encoding="utf-8")
        profile = CompanyProfile.model_validate_json(json_content)
        if json_content != render_json(profile) or markdown_content != render_markdown(profile):
            return None
    except (OSError, UnicodeError, ValidationError, ValueError):
        return None
    return profile if profile.identity.nip == nip else None


def _load_research(path: str, nip: str, runs_dir: Path) -> CompanyResearchRun | None:
    artifact = Path(path)
    try:
        if artifact.name != "research.json" or not artifact.resolve().is_relative_to(
            (runs_dir / nip).resolve()
        ):
            return None
        run = CompanyResearchRun.model_validate_json(artifact.read_bytes())
    except (OSError, ValidationError, ValueError):
        return None
    return run if run.identity.nip == nip else None


def _latest_research(nip: str, runs_dir: Path) -> tuple[Path, CompanyResearchRun] | None:
    company_dir = runs_dir / nip
    try:
        candidates = sorted(
            (
                child / "research.json"
                for child in company_dir.iterdir()
                if child.is_dir()
                and _is_research_timestamp(child.name)
                and (child / "research.json").is_file()
            ),
            key=lambda path: path.parent.name,
            reverse=True,
        )
    except OSError:
        return None
    for artifact in candidates:
        run = _load_research(str(artifact), nip, runs_dir)
        if run is not None:
            return artifact, run
    return None


def _is_research_timestamp(value: str) -> bool:
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%S%fZ").strftime("%Y%m%dT%H%M%S%fZ") == value
    except ValueError:
        return False


def _recovery_reason(run: CompanyResearchRun, profile: CompanyProfile) -> str | None:
    if run.diagnostics.status == "partial" and profile.status == "complete":
        return "Research completed with limitations"
    if profile.status == "partial":
        return "Profile has incomplete or uncertain core coverage"
    return None


def _counts(profile: CompanyProfile) -> tuple[int, int, int]:
    facts: list[Fact[Any]] = [
        profile.identity.legal_name,
        profile.identity.krs,
        profile.identity.regon,
        profile.identity.registered_city,
        profile.identity.registered_address,
        profile.identity.website,
        profile.business_description,
        profile.products_services,
        profile.industries,
        profile.markets,
        profile.employees,
        *profile.financials,
        *profile.recent_developments,
    ]
    return (
        sum(fact.state == "supported" for fact in facts),
        sum(fact.state == "uncertain" for fact in facts),
        sum(fact.state == "unknown" for fact in facts),
    )


def _write_summary(path: Path, results: list[BatchResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=SUMMARY_COLUMNS)
            writer.writeheader()
            for result in results:
                diagnostics = result.diagnostics
                profile = None
                if result.json_path and result.markdown_path:
                    profile = _profile_pair(
                        result.nip or "", Path(result.json_path), Path(result.markdown_path)
                    )
                supported, uncertain, unknown = _counts(profile) if profile else (None, None, None)
                writer.writerow(
                    {
                        "row_number": result.row_number,
                        "input_nip": result.input_nip,
                        "nip": result.nip or "",
                        "status": result.status,
                        "json_path": result.json_path or "",
                        "markdown_path": result.markdown_path or "",
                        "reason": result.reason or "",
                        "completed_at": result.completed_at.isoformat(),
                        "legal_name": profile.identity.legal_name.value
                        if profile and profile.identity.legal_name.state == "supported"
                        else "",
                        "supported_count": supported if supported is not None else "",
                        "uncertain_count": uncertain if uncertain is not None else "",
                        "unknown_count": unknown if unknown is not None else "",
                        "searches": diagnostics.searches if diagnostics else "",
                        "page_reads": diagnostics.page_reads if diagnostics else "",
                        "duration_seconds": diagnostics.duration_seconds if diagnostics else "",
                        "error_code": result.error_code or "",
                    }
                )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _replace_pair(
    json_path: Path, json_content: str, markdown_path: Path, markdown_content: str
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    old_json = json_path.read_bytes() if json_path.exists() else None
    old_markdown = markdown_path.read_bytes() if markdown_path.exists() else None
    staged: list[Path] = []
    try:
        for destination, content in ((json_path, json_content), (markdown_path, markdown_content)):
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=destination.parent, delete=False
            ) as file:
                file.write(content)
                staged.append(Path(file.name))
        os.replace(staged[0], json_path)
        os.replace(staged[1], markdown_path)
    except OSError:
        for path, previous in ((json_path, old_json), (markdown_path, old_markdown)):
            try:
                if previous is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(previous)
            except OSError:
                pass
        raise
    finally:
        for path in staged:
            path.unlink(missing_ok=True)


async def run_batch(
    input_path: Path,
    *,
    output_dir: Path = Path("outputs"),
    runs_dir: Path = Path("runs"),
    model: str = "openai-codex:gpt-6-luna",
    retry_partial: bool = False,
    retry_failed: bool = False,
    force: bool = False,
) -> list[BatchResult]:
    state_path = output_dir / "_batch_state.json"
    summary_path = output_dir / "batch_summary.csv"
    if input_path.resolve() == summary_path.resolve():
        raise InputFileError("Batch summary must not overwrite the input file")
    rows = read_input(input_path)
    prior = _read_state(state_path)
    outcomes_by_nip: dict[str, BatchResult] = {}
    for previous in prior:
        if previous.nip is not None:
            outcomes_by_nip[previous.nip] = previous
    as_of = datetime.now(ZoneInfo("Europe/Warsaw")).date()
    results: list[BatchResult] = []
    done: dict[str, BatchResult] = {}

    async def checkpoint() -> None:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = state_path.with_name(state_path.name + ".tmp")
        try:
            temporary.write_bytes(
                _RESULTS.dump_json(list(outcomes_by_nip.values()), indent=2) + b"\n"
            )
            os.replace(temporary, state_path)
        finally:
            temporary.unlink(missing_ok=True)
        _write_summary(summary_path, results)

    for row_number, value in rows:
        input_nip = "" if value is None else str(value)
        try:
            nip = validate_nip(value)
            InputRow(row_number=row_number, nip=nip)
        except (InvalidNIP, ValidationError) as error:
            results.append(
                BatchResult(
                    row_number=row_number,
                    input_nip=input_nip,
                    status="invalid_input",
                    error_code="INVALID_NIP",
                    reason=str(error),
                    completed_at=_now(),
                )
            )
            await checkpoint()
            continue

        if nip in done:
            result = done[nip].model_copy(
                update={"row_number": row_number, "input_nip": input_nip, "completed_at": _now()}
            )
            results.append(result)
            outcomes_by_nip[nip] = result
            await checkpoint()
            continue

        cached = outcomes_by_nip.get(nip)
        retry = (
            force
            or bool(cached and cached.status == "partial" and retry_partial)
            or bool(cached and cached.status in {"failed", "unresolved"} and retry_failed)
        )
        expected_json = output_dir / f"{nip}.json"
        expected_markdown = output_dir / f"{nip}.md"
        if cached is not None and not retry:
            if cached.status in {"complete", "partial"}:
                matches_expected = (
                    cached.json_path is not None
                    and cached.markdown_path is not None
                    and Path(cached.json_path).resolve() == expected_json.resolve()
                    and Path(cached.markdown_path).resolve() == expected_markdown.resolve()
                )
                if matches_expected and cached.research_path is not None:
                    run = _load_research(cached.research_path, nip, runs_dir)
                    if run is not None and run.diagnostics.status != "failed":
                        try:
                            profile = build_profile(run)
                            if profile.identity.nip != nip:
                                raise ValueError("Rebuilt profile NIP does not match the input NIP")
                            json_content = render_json(profile)
                            markdown_content = render_markdown(profile)
                            current_pair: tuple[str | None, str | None]
                            try:
                                current_pair = (
                                    expected_json.read_text(encoding="utf-8"),
                                    expected_markdown.read_text(encoding="utf-8"),
                                )
                            except (OSError, UnicodeError):
                                current_pair = (None, None)
                            if current_pair != (json_content, markdown_content):
                                _replace_pair(
                                    expected_json,
                                    json_content,
                                    expected_markdown,
                                    markdown_content,
                                )
                            result = cached.model_copy(
                                update={
                                    "row_number": row_number,
                                    "input_nip": input_nip,
                                    "status": profile.status,
                                    "json_path": str(expected_json),
                                    "markdown_path": str(expected_markdown),
                                    "reason": _recovery_reason(run, profile),
                                    "diagnostics": run.diagnostics,
                                    "research_path": cached.research_path,
                                    "completed_at": _now(),
                                }
                            )
                        except Exception as error:
                            result = BatchResult(
                                row_number=row_number,
                                input_nip=input_nip,
                                nip=nip,
                                status="failed",
                                error_code="PROFILE_REFRESH_ERROR",
                                reason=f"{type(error).__name__}: {error}"[:500],
                                completed_at=_now(),
                                diagnostics=run.diagnostics,
                                research_path=cached.research_path,
                            )
                        outcomes_by_nip[nip] = result
                        done[nip] = result
                        results.append(result)
                        await checkpoint()
                        continue
            elif cached.status in {"failed", "unresolved"}:
                result = cached.model_copy(
                    update={
                        "row_number": row_number,
                        "input_nip": input_nip,
                        "completed_at": _now(),
                    }
                )
                outcomes_by_nip[nip] = result
                done[nip] = result
                results.append(result)
                await checkpoint()
                continue

        # A publication pair is only rendered output, never authorization.
        may_recover_raw = (
            (cached is None or cached.research_path is None)
            and not retry
            and not (cached and cached.status in {"failed", "unresolved"})
        )
        retained = _latest_research(nip, runs_dir) if may_recover_raw else None
        if retained is not None:
            recovered_artifact, run = retained
            if run.diagnostics.status != "failed":
                try:
                    profile = build_profile(run)
                    if profile.identity.nip != nip:
                        raise ValueError("Rebuilt profile NIP does not match the input NIP")
                    if not (retry_partial and profile.status == "partial"):
                        _replace_pair(
                            expected_json,
                            render_json(profile),
                            expected_markdown,
                            render_markdown(profile),
                        )
                        result = BatchResult(
                            row_number=row_number,
                            input_nip=input_nip,
                            nip=nip,
                            status=profile.status,
                            json_path=str(expected_json),
                            markdown_path=str(expected_markdown),
                            reason=_recovery_reason(run, profile),
                            completed_at=_now(),
                            diagnostics=run.diagnostics,
                            research_path=str(recovered_artifact),
                        )
                        outcomes_by_nip[nip] = result
                        done[nip] = result
                        results.append(result)
                        await checkpoint()
                        continue
                except Exception:
                    pass

        artifact: Path | None = None
        artifact_persisted = False
        run = None
        try:
            identity, source = lookup_company(nip, as_of)
            if identity is None:
                result = BatchResult(
                    row_number=row_number,
                    input_nip=input_nip,
                    nip=nip,
                    status="unresolved",
                    sources=[source],
                    error_code="COMPANY_NOT_FOUND",
                    reason="No entity returned by the MF VAT register for this NIP and query date",
                    completed_at=_now(),
                )
            else:
                run = await research_company(identity, [source], model=model)
                artifact = (
                    runs_dir
                    / nip
                    / run.generated_at.astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                    / "research.json"
                )
                artifact.parent.mkdir(parents=True, exist_ok=True)
                artifact.write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
                artifact_persisted = True
                if run.diagnostics.status == "failed":
                    result = BatchResult(
                        row_number=row_number,
                        input_nip=input_nip,
                        nip=nip,
                        status="failed",
                        error_code="RESEARCH_FAILED",
                        reason=run.diagnostics.stop_reason or "Research failed",
                        completed_at=_now(),
                        diagnostics=run.diagnostics,
                        research_path=str(artifact),
                    )
                else:
                    profile = build_profile(run)
                    if profile.identity.nip != nip:
                        raise ValueError("Published profile NIP does not match the input NIP")
                    json_path, markdown_path = output_dir / f"{nip}.json", output_dir / f"{nip}.md"
                    _replace_pair(
                        json_path, render_json(profile), markdown_path, render_markdown(profile)
                    )
                    reason = (
                        "Research completed with limitations"
                        if run.diagnostics.status == "partial" and profile.status == "complete"
                        else (
                            "Profile has incomplete or uncertain core coverage"
                            if profile.status == "partial"
                            else None
                        )
                    )
                    result = BatchResult(
                        row_number=row_number,
                        input_nip=input_nip,
                        nip=nip,
                        status=profile.status,
                        json_path=str(json_path),
                        markdown_path=str(markdown_path),
                        reason=reason,
                        completed_at=_now(),
                        diagnostics=run.diagnostics,
                        research_path=str(artifact),
                    )
        except RegistryLookupError as error:
            result = BatchResult(
                row_number=row_number,
                input_nip=input_nip,
                nip=nip,
                status="failed",
                error_code=error.code,
                reason=str(error),
                completed_at=_now(),
            )
        except Exception as error:
            result = BatchResult(
                row_number=row_number,
                input_nip=input_nip,
                nip=nip,
                status="failed",
                error_code=getattr(error, "code", "PUBLICATION_ERROR"),
                reason=f"{type(error).__name__}: {error}"[:500],
                completed_at=_now(),
                diagnostics=run.diagnostics if run else None,
                research_path=str(artifact) if artifact_persisted and artifact else None,
            )
        result = result.model_copy(update={"completed_at": _now()})
        outcomes_by_nip[nip] = result
        done[nip] = result
        results.append(result)
        await checkpoint()
    return results
