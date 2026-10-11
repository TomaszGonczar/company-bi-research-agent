"""Offline dossier: presentation of an already publication-approved profile only."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from importlib.resources import as_file, files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from xml.sax.saxutils import escape, quoteattr

# ReportLab has no py.typed marker. Keep its untyped boundary confined to layout.
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle  # type: ignore[import-untyped]
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.pdfbase import pdfmetrics  # type: ignore[import-untyped]
from reportlab.pdfbase.ttfonts import TTFont  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
)

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


def _preview(text: str, limit: int = 180) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "… [skrót; pełna treść w aneksie]"


def _safe_link(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return (
            parts.scheme in {"http", "https"}
            and bool(parts.hostname)
            and parts.username is None
            and parts.password is None
            and not any(char.isspace() or ord(char) < 32 for char in url)
            and (parts.port is None or 0 < parts.port < 65536)
        )
    except ValueError:
        return False


def render_dossier_pdf(view: DossierView, output_path: Path) -> None:
    """Render faithful text with bounded main previews and complete flowing appendix."""
    for name, filename in (("Dossier", "DejaVuSans.ttf"), ("Dossier-Bold", "DejaVuSans-Bold.ttf")):
        if name not in pdfmetrics.getRegisteredFontNames():
            with as_file(files("company_bi").joinpath("assets", "fonts", filename)) as font:
                pdfmetrics.registerFont(TTFont(name, str(font)))
    pdfmetrics.registerFontFamily(
        "Dossier",
        normal="Dossier",
        bold="Dossier-Bold",
        italic="Dossier",
        boldItalic="Dossier-Bold",
    )
    slate = colors.HexColor("#24364B")
    blue = colors.HexColor("#215F87")
    body = ParagraphStyle(
        "body",
        fontName="Dossier",
        fontSize=10.5,
        leading=14,
        textColor=slate,
        spaceAfter=6,
        splitLongWords=True,
    )
    heading = ParagraphStyle(
        "heading",
        parent=body,
        fontName="Dossier-Bold",
        fontSize=12,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
        textColor=blue,
        keepWithNext=True,
    )
    title = ParagraphStyle("title", parent=heading, fontSize=17, leading=22, spaceBefore=0)
    banner = ParagraphStyle(
        "banner",
        parent=body,
        fontName="Dossier-Bold",
        backColor=colors.HexColor("#E8F0F6"),
        borderPadding=5,
        spaceBefore=6,
        spaceAfter=12,
    )

    def p(text: str, style: Any = body) -> Any:
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    def link(url: str) -> Any:
        text = escape(url)
        if _safe_link(url):
            text = f'<link href={quoteattr(url)} color="#215F87">{text}</link>'
        return Paragraph(text, body)

    def refs(fact: FactBlock, *, compact: bool) -> str:
        numbers = tuple(dict.fromkeys(ref.number for ref in fact.citations))
        shown = numbers[:3] if compact else numbers
        label = ", ".join(str(number) for number in shown)
        if len(shown) < len(numbers):
            label += "; pozostałe w aneksie"
        return f" [{label}]"

    main: list[Any] = []
    if view.synthetic:
        main.append(p("DANE SYNTETYCZNE - demonstracja układu", banner))
    main.extend(
        [
            p(_preview(view.legal_name, 160), title),
            p(
                f"NIP {view.nip} • "
                + ("Dane częściowe" if view.status == "partial" else "Kompletne pokrycie profilu")
            ),
            p(f"Data raportu / researchu: {view.generated_at}"),
            p("Tożsamość z rejestru", heading),
        ]
    )
    for fact in view.facts:
        if fact.section == "identity" and fact.path != "identity.legal_name":
            main.append(
                p(f"{fact.label}: {_preview(fact.values[0], 120)}{refs(fact, compact=True)}")
            )
    legal = next(f for f in view.facts if f.path == "identity.legal_name")
    main.append(p(f"Nazwa prawna{refs(legal, compact=True)} • identyfikacja: {view.resolved_at}"))
    main.append(p("Co ustalono w researchu", heading))
    if view.research_support_count == 0:
        main.append(p("Nie ustalono faktów z researchu spełniających kontrakt publikacji"))
    else:
        main.append(
            p(
                f"Poparte pola / obserwacje z researchu: {view.research_support_count}. "
                "Poparte przytoczonym źródłem — nie jest to miara dokładności."
            )
        )
    for section, label in (
        ("business", None),
        ("scale", "Skala i finanse"),
        ("events", "Zdarzenia"),
    ):
        section_facts = [fact for fact in view.facts if fact.section == section]
        if label:
            main.append(p(label, heading))
        for fact in section_facts:
            # Keep all financial context together; only text/list previews are shortened.
            value = "; ".join(fact.values[:3])
            if section == "events":
                value = _preview(fact.values[0], 100) + "; " + fact.values[-1]
            elif section != "scale":
                value = _preview(value)
            if len(fact.values) > 3:
                value += f" [podgląd listy: {len(fact.values)} elementów; pełna lista w aneksie]"
            main.append(p(f"{fact.label}: {value}{refs(fact, compact=True)}"))
        if not section_facts and section == "events":
            main.append(p("Nie ustalono zdarzeń spełniających kryteria."))
        elif not section_facts and section == "scale":
            states = sorted(
                {
                    STATE_LABELS[g.state]
                    for g in view.gaps
                    if g.path == "employees" or g.path.startswith("financials[")
                }
            )
            main.append(p(" / ".join(states) + " — szczegóły stanów i przyczyn w aneksie."))
    main.append(p("Najważniejsze braki", heading))
    research_gaps = [g for g in view.gaps if not g.path.startswith("identity.")]
    prioritized = research_gaps + [g for g in view.gaps if g.path.startswith("identity.")]
    for gap in prioritized[:3]:
        main.append(p(f"{gap.label}: {STATE_LABELS[gap.state]}. {_preview(gap.reason, 90)}"))
    if not view.gaps and not view.limitations:
        main.append(p("Nie wykazano braków pokrycia w przekazanym profilu."))
    if len(view.gaps) > 3 or view.limitations:
        main.append(
            p(
                "Pozostałe stany, przyczyny i ograniczenia: aneks. "
                "Nie ustalono nie oznacza braku w rzeczywistości."
            )
        )
    if view.questions:
        main.append(p("Pytania do potwierdzenia", heading))
        main.extend(p(question) for question in view.questions)
    main.append(
        p(
            "Treść faktów wynika z zachowanego materiału i bieżącego kontraktu publikacji. "
            "Daty nie oznaczają odświeżenia danych. Pełne fakty, cytaty i źródła: aneks."
        )
    )

    width, height = A4
    margin = 16 * mm
    frame_width, frame_height = width - 2 * margin, height - 2 * margin - 12
    # Exact paragraph measurements; never shrink text. Overflow remains in the appendix.
    pages: list[list[Any]] = [[]]
    used = 0.0
    overflow: list[Any] = []
    reserve = 52.0  # Room for a labelled continuation, even with an oversized field.
    for index, paragraph in enumerate(main):
        _, paragraph_height = paragraph.wrap(frame_width, frame_height)
        needed = paragraph_height + paragraph.getSpaceBefore() + paragraph.getSpaceAfter()
        with_next = 0.0
        if paragraph.getKeepWithNext() and index + 1 < len(main):
            following = main[index + 1]
            _, next_height = following.wrap(frame_width, frame_height)
            with_next = next_height + following.getSpaceBefore() + following.getSpaceAfter()
        if used + needed + with_next > frame_height - reserve:
            if len(pages) == 1:
                pages.append([])
                used = 0
            else:
                overflow.append(paragraph)
                continue
        if needed > frame_height - reserve:
            overflow.append(paragraph)
        else:
            pages[-1].append(paragraph)
            used += needed
    if overflow:
        pages[-1].append(p("Dalsza część przeglądu i pytania: początek aneksu.", banner))
    main_count = len(pages)

    def footer(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Dossier", 9)
        canvas.setFillColor(slate)
        label = "Dossier" if doc.page <= main_count else "Aneks — źródła i szczegóły"
        canvas.drawString(margin, 9 * mm, f"{label} • strona {doc.page}")
        canvas.drawRightString(width - margin, 9 * mm, f"NIP {view.nip}")
        canvas.restoreState()

    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"Dossier NIP {view.nip}",
        author="Company BI",
        pageCompression=1,
    )
    frame = Frame(
        margin,
        margin + 12,
        frame_width,
        frame_height,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="main", frames=[frame], onPage=footer),
            PageTemplate(id="appendix", frames=[frame], onPage=footer),
        ]
    )
    story: list[Any] = []
    for index, page in enumerate(pages):
        if index:
            story.append(PageBreak())
        story.extend(page)
    story.extend(
        [NextPageTemplate("appendix"), PageBreak(), p("Źródła i szczegóły — aneks", title)]
    )
    if view.synthetic:
        story.append(p("DANE SYNTETYCZNE - demonstracja układu", banner))
    if overflow:
        story.append(p("Kontynuacja przeglądu", heading))
        story.extend(overflow)
    story.append(p("Pełne poparte fakty i cytaty", heading))
    story.append(
        p(
            "Poparte przytoczonym źródłem. Cytaty poniżej dotyczą wyłącznie popartych "
            "faktów; samo pobranie źródła nie dowodzi jego treści."
        )
    )
    for fact in view.facts:
        story.append(p(f"{fact.label} • {fact.path}{refs(fact, compact=True)}", heading))
        story.extend(p(value) for value in fact.values)
        if fact.reason:
            story.append(p(f"Przyczyna / uwaga: {fact.reason}"))
        for citation in fact.citations:
            story.append(p(f"Cytat [{citation.number}] • {citation.source_id} • {fact.path}"))
            story.append(p(citation.excerpt))
    story.append(p("Stany, braki i ograniczenia", heading))
    for gap in view.gaps:
        references = ", ".join(f"[{n}]" for n in gap.references) or "bez odwołań"
        story.append(
            p(
                f"{gap.label} • {gap.path}: {STATE_LABELS[gap.state]} ({gap.state}); {references}",
                heading,
            )
        )
        story.append(p(gap.reason))
    story.extend(p(f"Ograniczenie: {text}") for text in view.limitations)
    story.append(p("Rejestr źródeł", heading))
    story.append(
        p(
            "Wszystkie źródła końcowego profilu. Materiały niepotwierdzone, niecytowane "
            "i objęte kwarantanną nie są popartymi faktami."
        )
    )
    for source in view.sources:
        story.append(p(f"[{source.number}] {source.source_id} • {source.kind}", heading))
        story.append(p(source.title))
        story.append(link(source.url))
        story.append(p(" • ".join(source.usage)))
        metadata = (
            f"Pobrano: {source.retrieved_at}; "
            f"opublikowano: {source.published_on or 'nie ustalono'}\n"
            "Powód blokady publikacji: "
            + (source.publication_blocked_reason or "nie zapisano blokady")
        )
        if source.redirect_chain:
            story.append(p(metadata + "\nŁańcuch przekierowań (w oryginalnej kolejności):"))
            story.extend(link(url) for url in source.redirect_chain)
        else:
            story.append(p(metadata + "\nŁańcuch przekierowań: nie zapisano."))

    def invariant_canvas(*args: Any, **kwargs: Any) -> Any:
        kwargs["invariant"] = 1
        return Canvas(*args, **kwargs)

    doc.build(story, canvasmaker=invariant_canvas)
