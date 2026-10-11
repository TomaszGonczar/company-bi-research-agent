"""Offline dossier: presentation of an already publication-approved profile only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from company_bi.models import CompanyProfile, Fact

TEMPLATE_VERSION = "0.2.0"
STATE_LABELS = {
    "supported": "Poparte przytoczonym źródłem",
    "uncertain": "Niepotwierdzone",
    "unknown": "Nie ustalono",
}


@dataclass(frozen=True)
class Citation:
    number: int
    source_id: str
    excerpt: str


@dataclass(frozen=True)
class FactBlock:
    path: str
    label: str
    section: str
    values: tuple[str, ...]
    citations: tuple[Citation, ...]
    reason: str | None


@dataclass(frozen=True)
class GapBlock:
    path: str
    label: str
    state: str
    reason: str
    references: tuple[int, ...]


@dataclass(frozen=True)
class SourceBlock:
    number: int
    source_id: str
    kind: str
    title: str
    url: str
    retrieved_at: str
    published_on: str | None
    redirect_chain: tuple[str, ...]
    publication_blocked_reason: str | None
    usage: tuple[str, ...]


@dataclass(frozen=True)
class DossierView:
    nip: str
    legal_name: str
    status: str
    generated_at: str
    resolved_at: str
    synthetic: bool
    facts: tuple[FactBlock, ...]
    gaps: tuple[GapBlock, ...]
    questions: tuple[str, ...]
    sources: tuple[SourceBlock, ...]
    limitations: tuple[str, ...]
    research_support_count: int


def build_dossier_view(profile: CompanyProfile, *, synthetic: bool = False) -> DossierView:
    """Project final states; non-supported values/context/excerpts never enter the view."""
    numbers = {
        source.source_id: number
        for number, source in enumerate(sorted(profile.sources, key=lambda s: s.source_id), 1)
    }
    facts: list[FactBlock] = []
    gaps: list[GapBlock] = []

    def add(path: str, label: str, section: str, fact: Fact[Any], values: tuple[str, ...]) -> None:
        if fact.state == "supported":
            facts.append(
                FactBlock(
                    path,
                    label,
                    section,
                    values,
                    tuple(
                        Citation(numbers[r.source_id], r.source_id, r.excerpt)
                        for r in fact.evidence
                    ),
                    fact.reason,
                )
            )
        else:
            gaps.append(
                GapBlock(
                    path,
                    label,
                    fact.state,
                    fact.reason or "Nie ustalono przyczyny.",
                    tuple(dict.fromkeys(numbers[r.source_id] for r in fact.evidence)),
                )
            )

    identity_fields = (
        ("legal_name", "Nazwa prawna"),
        ("registered_address", "Adres rejestrowy"),
        ("registered_city", "Miasto"),
        ("krs", "KRS"),
        ("regon", "REGON"),
        ("website", "Witryna"),
    )
    for name, label in identity_fields:
        fact = getattr(profile.identity, name)
        add(
            f"identity.{name}",
            label,
            "identity",
            fact,
            (str(fact.value),) if fact.state == "supported" else (),
        )
    for name, label in (
        ("business_description", "Działalność"),
        ("products_services", "Produkty i usługi"),
        ("industries", "Branże"),
        ("markets", "Rynki"),
    ):
        fact = getattr(profile, name)
        values: tuple[str, ...] = ()
        if fact.state == "supported":
            values = tuple(fact.value) if isinstance(fact.value, list) else (str(fact.value),)
        add(name, label, "business", fact, values)

    employee = profile.employees
    employee_values: tuple[str, ...] = ()
    if employee.state == "supported" and employee.value is not None:
        value = employee.value
        if value.kind == "exact":
            quantity = str(value.count)
        else:
            # The current strict gate abstains on ranges. Do not invent a midpoint.
            quantity = f"zakres: {value.minimum if value.minimum is not None else '?'}–"
            quantity += str(value.maximum) if value.maximum is not None else "?"
        employee_values = (f"{quantity}; data obserwacji: {employee.as_of or 'nieokreślona'}",)
    add("employees", "Pracownicy", "scale", employee, employee_values)

    for index, financial in sorted(
        enumerate(profile.financials),
        key=lambda pair: (
            pair[1].period.start if pair[1].period else date.max,
            pair[1].period.end if pair[1].period else date.max,
            pair[1].metric,
        ),
    ):
        values = ()
        if financial.state == "supported":
            assert financial.value is not None and financial.period is not None
            unit = {
                "units": "jednostki",
                "thousands": "tysiące",
                "millions": "miliony",
                "billions": "miliardy",
            }[str(financial.unit)]
            scope = "jednostka prawna" if financial.scope == "legal_entity" else "grupa"
            group = f" ({financial.group_name})" if financial.group_name else ""
            values = (
                f"{format(financial.value, 'f')} {financial.currency}; skala: {unit} "
                f"({financial.unit}); okres: {financial.period.start} – {financial.period.end}; "
                f"zakres: {scope} ({financial.scope}){group}",
            )
        add(
            f"financials[{index}]",
            "Przychody" if financial.metric == "revenue" else "Wynik netto",
            "scale",
            financial,
            values,
        )
    for index, event in enumerate(profile.recent_developments):
        values = ()
        if event.state == "supported" and event.value is not None:
            detail = event.value
            values = (
                detail.title,
                detail.summary,
                f"Publikacja: {detail.published_on}; "
                f"zdarzenie: {detail.occurred_on or 'data nieokreślona'}",
            )
        add(f"recent_developments[{index}]", "Zdarzenie", "events", event, values)
    if not profile.recent_developments:
        gaps.append(
            GapBlock(
                "recent_developments",
                "Zdarzenia",
                "unknown",
                "Nie ustalono zdarzeń spełniających kryteria.",
                (),
            )
        )

    periods = {
        metric: {
            (f.period.start, f.period.end)
            for f in profile.financials
            if f.state == "supported" and f.metric == metric and f.period is not None
        }
        for metric in ("revenue", "net_result")
    }
    questions = tuple(
        question
        for missing, question in (
            (
                profile.business_description.state != "supported"
                or profile.products_services.state != "supported",
                "Jakie produkty i usługi firma obecnie oferuje?",
            ),
            (employee.state != "supported", "Jaka jest aktualna liczba pracowników?"),
            (
                not (periods["revenue"] & periods["net_result"]),
                "Czy dostępne są jednostkowe wyniki finansowe za ostatni zamknięty okres?",
            ),
            (profile.markets.state != "supported", "Na jakich rynkach firma obecnie działa?"),
            (
                not any(e.state == "supported" for e in profile.recent_developments),
                "Jakie istotne zmiany zaszły w firmie w ostatnich 12 miesiącach?",
            ),
        )
        if missing
    )[:3]
    supported_ids = {ref.source_id for fact in facts for ref in fact.citations}
    uncertain_numbers = {n for gap in gaps for n in gap.references}
    sources: list[SourceBlock] = []
    for source in sorted(profile.sources, key=lambda s: s.source_id):
        usage = []
        if source.source_id in supported_ids:
            usage.append("Cytowane dla popartych faktów")
        if numbers[source.source_id] in uncertain_numbers:
            usage.append("Odwołanie niepotwierdzone — nie stanowi poparcia faktu")
        if not usage:
            usage.append("Niewykorzystane w faktach — samo pobranie nie potwierdza treści")
        if source.publication_blocked_reason:
            usage.append("Kwarantanna publikacyjna")
        sources.append(
            SourceBlock(
                numbers[source.source_id],
                source.source_id,
                source.kind,
                source.title,
                str(source.url),
                source.retrieved_at.isoformat(),
                source.published_on.isoformat() if source.published_on else None,
                tuple(str(url) for url in source.redirect_chain),
                source.publication_blocked_reason,
                tuple(usage),
            )
        )
    assert profile.identity.legal_name.value is not None
    return DossierView(
        profile.identity.nip,
        profile.identity.legal_name.value,
        profile.status,
        profile.generated_at.isoformat(),
        profile.identity.resolved_at.isoformat(),
        synthetic,
        tuple(facts),
        tuple(gaps),
        questions,
        tuple(sources),
        tuple(profile.limitations),
        sum(fact.section != "identity" for fact in facts),
    )
