"""Deterministic human- and machine-readable renderers for validated profiles."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from company_bi.models import CompanyProfile, Fact


def render_json(profile: CompanyProfile) -> str:
    """Serialize a validated profile without changing its data or field order."""
    return profile.model_dump_json(indent=2) + "\n"


def _md(value: object) -> str:
    """Escape inline Markdown metacharacters while retaining readable text."""
    text = str(value)
    return "".join("\\" + char if char in r"\\`*_{}[]<>()#+!|" else char for char in text)


def _state(fact: Fact[Any]) -> str:
    labels = {
        "supported": "Supported",
        "uncertain": "Uncertain — candidate / unverified",
        "unknown": "Unknown",
    }
    return labels[fact.state]


def _evidence_label(fact: Fact[Any], source: Any) -> str:
    if fact.state != "supported" or source.kind == "search_snippet":
        return "Candidate excerpt (unverified)"
    return "Excerpt"


def _fact_lines(label: str, fact: Fact[Any], sources: dict[str, Any]) -> list[str]:
    lines = [f"- **{_md(label)}** — {_state(fact)}"]
    if fact.value is not None:
        value = (
            "; ".join(_md(item) for item in fact.value)
            if isinstance(fact.value, list)
            else _md(fact.value)
        )
        lines.append(f"  - Value: {value}")
    else:
        lines.append("  - Value: Unknown (null)")
    if fact.reason is not None:
        lines.append(f"  - Reason: {_md(fact.reason)}")
    if fact.evidence:
        lines.append("  - Evidence:")
        for ref in fact.evidence:
            source = sources.get(ref.source_id)
            source_link = _source_link(ref.source_id, source) if source else _md(ref.source_id)
            qualifier = (
                _evidence_label(fact, source) if source else "Candidate excerpt (unverified)"
            )
            lines.append(f"    - {source_link} — {qualifier}: {_md(ref.excerpt)}")
    else:
        lines.append("  - Evidence: none")
    return lines


def _link(label: object, url: str) -> str:
    safe_url = quote(url, safe=":/?#@&=+$,;%~.*!-_")
    return f"[{_md(label)}]({safe_url})"


def _source_link(source_id: str, source: Any) -> str:
    return _link(source_id, str(source.url))


def _quantity(fact: Fact[Any]) -> str:
    value = fact.value
    if value is None:
        return "Unknown (null)"
    if hasattr(value, "kind"):
        if value.kind == "exact":
            return str(value.count)
        low = "unknown" if value.minimum is None else str(value.minimum)
        high = "unknown" if value.maximum is None else str(value.maximum)
        return f"{low}–{high} (range)"
    return str(value)


def render_markdown(profile: CompanyProfile) -> str:
    """Render every profile section, state, reason, citation, and source provenance."""
    sources = {source.source_id: source for source in profile.sources}
    lines = [
        f"# {_md(profile.identity.legal_name.value)}",
        "",
        f"- **Publication status:** {_md(profile.status)}",
        f"- **NIP:** {_md(profile.identity.nip)}",
        f"- **Generated:** {_md(profile.generated_at.isoformat())}",
        "",
        "## Identity",
    ]
    identity_facts = (
        ("Legal name", profile.identity.legal_name),
        ("KRS", profile.identity.krs),
        ("REGON", profile.identity.regon),
        ("Registered city", profile.identity.registered_city),
        ("Registered address", profile.identity.registered_address),
        ("Website", profile.identity.website),
    )
    for label, identity_fact in identity_facts:
        lines.extend(_fact_lines(label, identity_fact, sources))
    lines.extend(["", "## Business profile"])
    for label, list_fact in (
        ("Business description", profile.business_description),
        ("Products and services", profile.products_services),
        ("Industries", profile.industries),
        ("Markets", profile.markets),
    ):
        lines.extend(_fact_lines(label, list_fact, sources))
    lines.extend(
        [
            "",
            "## Employees",
            f"- **State:** {_state(profile.employees)}",
            f"- **Quantity:** {_md(_quantity(profile.employees))}",
        ]
    )
    as_of = (
        profile.employees.as_of.isoformat()
        if profile.employees.as_of is not None
        else "Unknown / not stated"
    )
    lines.append(f"- **As of:** {as_of}")
    if profile.employees.reason is not None:
        lines.append(f"- **Reason:** {_md(profile.employees.reason)}")
    if profile.employees.evidence:
        lines.append("- **Evidence:**")
        for ref in profile.employees.evidence:
            source = sources[ref.source_id]
            lines.append(
                f"  - {_source_link(ref.source_id, source)} — "
                f"{_evidence_label(profile.employees, source)}: {_md(ref.excerpt)}"
            )
    else:
        lines.append("- **Evidence:** none")
    lines.extend(
        [
            "",
            "## Financials",
            "",
            "| Metric | Amount | Period | Currency | Unit | Scope | Group | State |",
            "| --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    financial_details: list[str] = []
    for number, financial_fact in enumerate(profile.financials, 1):
        amount = _md(financial_fact.value) if financial_fact.value is not None else "Unknown (null)"
        period = (
            "Unknown"
            if financial_fact.period is None
            else (
                f"{financial_fact.period.start.isoformat()} to "
                f"{financial_fact.period.end.isoformat()}"
            )
        )
        cells = (
            _md(financial_fact.metric),
            amount,
            _md(period),
            _md(financial_fact.currency) if financial_fact.currency is not None else "Unknown",
            _md(financial_fact.unit) if financial_fact.unit is not None else "Unknown",
            _md(financial_fact.scope) if financial_fact.scope is not None else "Unknown",
            _md(financial_fact.group_name) if financial_fact.group_name is not None else "Unknown",
            _state(financial_fact),
        )
        lines.append("| " + " | ".join(cells) + " |")
        if financial_fact.reason is not None or financial_fact.evidence:
            financial_details.extend(
                ["", f"- **Observation {number} ({_md(financial_fact.metric)}, {_md(period)}):**"]
            )
            if financial_fact.reason is not None:
                financial_details.append(f"  - **Reason:** {_md(financial_fact.reason)}")
            if financial_fact.evidence:
                financial_details.append("  - **Evidence:**")
                for ref in financial_fact.evidence:
                    source = sources[ref.source_id]
                    financial_details.append(
                        f"    - {_source_link(ref.source_id, source)} — "
                        f"{_evidence_label(financial_fact, source)}: {_md(ref.excerpt)}"
                    )
    if financial_details:
        lines.extend(["", "### Financial evidence and reasons", *financial_details])
    lines.extend(["", "## Recent developments"])
    if not profile.recent_developments:
        lines.append("- None reported (not a claim that no events occurred).")
    for number, event in enumerate(profile.recent_developments, 1):
        lines.extend(["", f"### Development {number}", f"- **State:** {_state(event)}"])
        if event.value is None:
            lines.append("- **Details:** Unknown (null)")
        else:
            occurred = (
                event.value.occurred_on.isoformat()
                if event.value.occurred_on
                else "Unknown / not stated"
            )
            lines.extend(
                [
                    f"- **Title:** {_md(event.value.title)}",
                    f"- **Summary:** {_md(event.value.summary)}",
                    f"- **Published:** {event.value.published_on.isoformat()}",
                    f"- **Occurred:** {occurred}",
                ]
            )
        if event.reason is not None:
            lines.append(f"- **Reason:** {_md(event.reason)}")
        if event.evidence:
            lines.append("- **Evidence:**")
            for ref in event.evidence:
                source = sources[ref.source_id]
                lines.append(
                    f"  - {_source_link(ref.source_id, source)} — "
                    f"{_evidence_label(event, source)}: {_md(ref.excerpt)}"
                )
        else:
            lines.append("- **Evidence:** none")
    lines.extend(["", "## Limitations"])
    if profile.limitations:
        lines.extend(f"- {_md(item)}" for item in profile.limitations)
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Sources"])
    for source in profile.sources:
        lines.extend(
            [
                f"- **{_md(source.source_id)}** — {_md(source.kind)}; "
                f"{_link(source.title, str(source.url))}",
                f"  - Retrieved: {source.retrieved_at.isoformat()}",
                f"  - Published: "
                f"{source.published_on.isoformat() if source.published_on else 'Unknown'}",
            ]
        )
        if source.publication_blocked_reason is not None:
            lines.append(f"  - Publication blocked: {_md(source.publication_blocked_reason)}")
        if source.redirect_chain:
            lines.append(
                "  - Validated redirect chain: "
                + " → ".join(_link(url, str(url)) for url in source.redirect_chain)
            )
    return "\n".join(lines) + "\n"
