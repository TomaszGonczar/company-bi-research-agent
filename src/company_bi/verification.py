"""Deterministic comparison of retained research candidates with publication-gate output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import AwareDatetime, JsonValue

from company_bi.evidence import build_profile
from company_bi.models import (
    CompanyProfile,
    CompanyResearchRun,
    EvidenceRef,
    Fact,
    Model,
    ProfileSource,
    ResearchDiagnostics,
)
from company_bi.renderer import _link, _md, render_json, render_markdown

VerificationDecision = Literal["accepted", "downgraded", "cleared", "preserved"]


def _safe(value: object) -> str:
    return _md(value)


class FactSnapshot(Model):
    state: Literal["supported", "uncertain", "unknown"]
    value: JsonValue | None
    evidence: list[EvidenceRef]
    reason: str | None
    context: dict[str, JsonValue]


class VerificationDelta(Model):
    path: str
    candidate: FactSnapshot
    final: FactSnapshot
    decision: VerificationDecision
    reason: str
    changed_paths: list[str]


class VerificationSources(Model):
    candidate: list[ProfileSource]
    final: list[ProfileSource]


class VerificationReport(Model):
    status: Literal["verified", "not_published"]
    nip: str
    legal_name: str
    input_name: str
    input_sha256: str
    generated_at: AwareDatetime
    diagnostics: ResearchDiagnostics
    profile_status: Literal["complete", "partial"] | None
    reason: str | None
    deltas: list[VerificationDelta]
    sources: VerificationSources
    candidate_limitations: list[str]
    final_limitations: list[str] | None


def _snapshot(fact: Fact[Any]) -> FactSnapshot:
    data = fact.model_dump(mode="json")
    return FactSnapshot(
        state=fact.state,
        value=data["value"],
        evidence=fact.evidence,
        reason=fact.reason,
        context={
            key: value
            for key, value in data.items()
            if key not in {"state", "value", "evidence", "reason"}
        },
    )


def _different_paths(left: object, right: object, prefix: str = "") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        paths: list[str] = []
        for key in sorted(left.keys() | right.keys()):
            child = f"{prefix}.{key}" if prefix else key
            if key not in left or key not in right:
                paths.append(child)
            else:
                paths.extend(_different_paths(left[key], right[key], child))
        return paths
    if isinstance(left, list) and isinstance(right, list):
        paths = []
        for index in range(max(len(left), len(right))):
            child = f"{prefix}[{index}]"
            if index >= len(left) or index >= len(right):
                paths.append(child)
            else:
                paths.extend(_different_paths(left[index], right[index], child))
        return paths
    return [] if left == right else [prefix]


def _removed(old: JsonValue | None, new: JsonValue | None) -> bool:
    if old is not None and new is None:
        return True
    if isinstance(old, dict) and isinstance(new, dict):
        return any(_removed(old.get(key), new.get(key)) for key in old.keys() | new.keys())
    if isinstance(old, list) and isinstance(new, list):
        return len(old) > len(new) or any(
            _removed(left, right) for left, right in zip(old, new, strict=False)
        )
    return False


def _delta(path: str, candidate: FactSnapshot, final: FactSnapshot) -> VerificationDelta:
    before = candidate.model_dump(mode="json")
    after = final.model_dump(mode="json")
    changed = _different_paths(before, after)
    decision: VerificationDecision
    if candidate.state == "supported" and final.state != "supported":
        decision = "downgraded"
    elif candidate.state == final.state and (
        _removed(candidate.value, final.value)
        or any(
            _removed(candidate.context.get(key), final.context.get(key))
            for key in candidate.context.keys() | final.context.keys()
        )
    ):
        decision = "cleared"
    elif final.state == "supported":
        decision = "accepted"
    else:
        decision = "preserved"
    reason = (
        final.reason
        or {
            "accepted": "The publication gate retained this supported fact.",
            "downgraded": "The publication gate changed the candidate to a non-supported state.",
            "cleared": "The publication gate removed an asserted value or context field.",
            "preserved": "The non-supported candidate remains unverified, not accepted.",
        }[decision]
    )
    return VerificationDelta(
        path=path,
        candidate=candidate,
        final=final,
        decision=decision,
        reason=reason,
        changed_paths=changed,
    )


def _source_metadata(
    run: CompanyResearchRun, profile: CompanyProfile | None
) -> VerificationSources:
    facts: tuple[Fact[Any], ...] = (
        run.identity.legal_name,
        run.identity.krs,
        run.identity.regon,
        run.identity.registered_city,
        run.identity.registered_address,
        run.identity.website,
        run.draft.business_description,
        run.draft.products_services,
        run.draft.industries,
        run.draft.markets,
        run.draft.employees,
        *run.draft.financials,
        *run.draft.recent_developments,
    )
    referenced = {ref.source_id for fact in facts for ref in fact.evidence}
    candidate = [
        ProfileSource(**material.source.model_dump(), kind=material.kind)
        for material in run.sources
        if material.source.source_id in referenced
        or material.source.publication_blocked_reason is not None
    ]
    return VerificationSources(candidate=candidate, final=profile.sources if profile else [])


def verify_run(
    run: CompanyResearchRun, *, input_sha256: str, input_name: str
) -> tuple[CompanyProfile | None, VerificationReport]:
    """Compare every retained research field with one deterministic gate result."""
    profile = None if run.diagnostics.status == "failed" else build_profile(run)
    deltas: list[VerificationDelta] = []
    if profile is not None:
        fields = (
            "business_description",
            "products_services",
            "industries",
            "markets",
            "employees",
        )
        for name in fields:
            candidate_fact = getattr(run.draft, name)
            final_fact = getattr(profile, name)
            deltas.append(
                _delta(
                    name,
                    _snapshot(candidate_fact),
                    _snapshot(final_fact),
                )
            )
        for index, (candidate_fact, final_fact) in enumerate(
            zip(run.draft.financials, profile.financials, strict=True)
        ):
            deltas.append(
                _delta(
                    f"financials[{index}]",
                    _snapshot(candidate_fact),
                    _snapshot(final_fact),
                )
            )
        for index, (candidate_fact, final_fact) in enumerate(
            zip(run.draft.recent_developments, profile.recent_developments, strict=True)
        ):
            deltas.append(
                _delta(
                    f"recent_developments[{index}]",
                    _snapshot(candidate_fact),
                    _snapshot(final_fact),
                )
            )
    failed = profile is None
    legal_name = run.identity.legal_name.value
    assert legal_name is not None
    report = VerificationReport(
        status="not_published" if failed else "verified",
        nip=run.identity.nip,
        legal_name=legal_name,
        input_name=input_name,
        input_sha256=input_sha256,
        generated_at=run.generated_at,
        diagnostics=run.diagnostics,
        profile_status=None if profile is None else profile.status,
        reason=(run.diagnostics.stop_reason or "Research diagnostics report a failed run.")
        if failed
        else None,
        deltas=deltas,
        sources=_source_metadata(run, profile),
        candidate_limitations=run.draft.limitations,
        final_limitations=None if profile is None else profile.limitations,
    )
    return profile, report


def _evidence_markdown(
    snapshot: FactSnapshot, source_map: dict[str, ProfileSource], *, published: bool
) -> list[str]:
    if not snapshot.evidence:
        return ["  - Evidence: none"]
    qualifier = "supporting final publication" if published else "candidate / unverified"
    lines = [f"  - Evidence ({qualifier}):"]
    for ref in snapshot.evidence:
        source = source_map.get(ref.source_id)
        label = _link(_safe(ref.source_id), str(source.url)) if source else _safe(ref.source_id)
        lines.append(f"    - {label}: {_safe(ref.excerpt)}")
    return lines


def render_verification_markdown(report: VerificationReport) -> str:
    """Render a deterministic reviewer report with untrusted text safely escaped."""
    counts: dict[str, int] = {}
    for delta in report.deltas:
        counts[delta.decision] = counts.get(delta.decision, 0) + 1
    lines = [
        f"# Offline verification — {_safe(report.legal_name)}",
        "",
        f"- Status: **{report.status}**",
        f"- NIP: {_safe(report.nip)}",
        f"- Profile status: {_safe(report.profile_status or 'none')}",
        f"- Research generated: {_safe(report.generated_at.isoformat())}",
        f"- Input: {_safe(report.input_name)} (SHA-256 `{report.input_sha256}`)",
        f"- Decisions: {', '.join(f'{key} {counts[key]}' for key in sorted(counts)) or 'none'}",
        "",
        "> This checks the supplied retained source ledger and publication gate; "
        "it does not authenticate edited input or prove publisher truth.",
        "",
        "> Candidate states are agent assertions. Only final supported facts passed this gate; "
        "preserved uncertain/unknown facts remain unverified.",
    ]
    if report.reason:
        lines.extend(["", f"**Not published:** {_safe(report.reason)}"])
    candidate_source_map = {source.source_id: source for source in report.sources.candidate}
    final_source_map = {source.source_id: source for source in report.sources.final}
    ordered = sorted(report.deltas, key=lambda item: (item.decision == "preserved", item.path))
    for delta in ordered:
        lines.extend(
            [
                "",
                f"## {_safe(delta.path)}",
                "",
                f"**Decision: {delta.decision.upper()}**",
                "",
                f"**Reason:** {_safe(delta.reason)}",
            ]
        )
        if delta.changed_paths:
            lines.append(
                "**Changed paths:** " + ", ".join(_safe(path) for path in delta.changed_paths)
            )
        for label, snapshot in (("Candidate", delta.candidate), ("Final", delta.final)):
            value_label = (
                "Value (cleared):"
                if label == "Final" and delta.candidate.value is not None and snapshot.value is None
                else "Value:"
            )
            lines.extend(["", f"**{label}:** {_safe(snapshot.state)}", "", value_label, ""])
            lines.extend(
                "    " + line
                for line in json.dumps(
                    snapshot.value, ensure_ascii=False, sort_keys=True, indent=2
                ).splitlines()
            )
            lines.append("")
            if snapshot.reason:
                lines.append(f"  - Fact reason: {_safe(snapshot.reason)}")
            if snapshot.context:
                lines.extend(["", "Context:", ""])
                lines.extend(
                    "    " + line
                    for line in json.dumps(
                        snapshot.context, ensure_ascii=False, sort_keys=True, indent=2
                    ).splitlines()
                )
                lines.append("")
            source_map = candidate_source_map if label == "Candidate" else final_source_map
            lines.extend(
                _evidence_markdown(
                    snapshot,
                    source_map,
                    published=label == "Final" and snapshot.state == "supported",
                )
            )
    for label, limitations in (
        ("Candidate limitations", report.candidate_limitations),
        ("Final limitations", report.final_limitations or []),
    ):
        lines.extend(["", f"## {_safe(label)}"])
        lines.extend([f"- {_safe(item)}" for item in limitations] or ["- None recorded."])
    lines.extend(["", "## Retained source metadata"])
    for kind, sources in (("Candidate", report.sources.candidate), ("Final", report.sources.final)):
        lines.append(f"### {kind}")
        for source in sources:
            detail = (
                f"{_link(_safe(source.source_id), str(source.url))} — {_safe(source.kind)}; "
                f"{_safe(source.title)}; retrieved {_safe(source.retrieved_at.isoformat())}"
            )
            if source.publication_blocked_reason:
                detail += f"; blocked: {_md(source.publication_blocked_reason)}"
            if source.redirect_chain:
                detail += "; redirects: " + " → ".join(
                    _link(str(url), str(url)) for url in source.redirect_chain
                )
            lines.append(f"- {detail}")
        if not sources:
            lines.append("- None.")
    lines.extend(
        [
            "",
            "Retained research diagnostics (from the input; no calls made by verification):",
            "",
            "    " + report.diagnostics.model_dump_json(indent=2).replace("\n", "\n    "),
            "",
        ]
    )
    return "\n".join(lines)


def write_verification(input_path: Path, output_dir: Path) -> VerificationReport:
    """Read, validate, verify, and write the deterministic four-file review bundle."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    data = input_path.read_bytes()
    run = CompanyResearchRun.model_validate_json(data)
    outputs = {
        name: output_dir / name
        for name in ("profile.json", "profile.md", "verification.json", "verification.md")
    }
    resolved_input = input_path.resolve()
    destinations = list(outputs.values())
    for index, path in enumerate(destinations):
        if path.resolve() == resolved_input or (
            path.exists() and input_path.exists() and path.samefile(input_path)
        ):
            raise ValueError("Verification output must not overwrite the input file")
        for other in destinations[:index]:
            if path.resolve() == other.resolve() or (
                path.exists() and other.exists() and path.samefile(other)
            ):
                raise ValueError("Verification output destinations must be distinct")
    profile, report = verify_run(
        run,
        input_sha256=hashlib.sha256(data).hexdigest(),
        input_name=input_path.name,
    )
    if profile is None and any(
        path.exists() or path.is_symlink()
        for path in (outputs["profile.json"], outputs["profile.md"])
    ):
        raise ValueError("Refusing failed-run output while profile artifacts already exist")
    payloads: dict[str, str] = {}
    if profile is not None:
        payloads["profile.json"] = render_json(profile)
        payloads["profile.md"] = render_markdown(profile)
    payloads["verification.json"] = report.model_dump_json(indent=2) + "\n"
    payloads["verification.md"] = render_verification_markdown(report)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        outputs[name].write_text(content, encoding="utf-8")
    return report
