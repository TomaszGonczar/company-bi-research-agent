from pathlib import Path

import pytest
from pypdf import PdfReader

from company_bi.dossier import build_dossier_view, render_dossier_pdf
from company_bi.models import CompanyResearchRun
from company_bi.verification import verify_run


def render(path, output):
    run = CompanyResearchRun.model_validate_json(Path(path).read_bytes())
    profile, _ = verify_run(run, input_sha256="test", input_name=Path(path).name)
    assert profile is not None
    view = build_dossier_view(profile, synthetic=True)
    render_dossier_pdf(view, output)
    return view, PdfReader(output)


def compact(text):
    return "".join(text.split())


def body_text(pdf):
    pieces = []

    def visit(text, cm, tm, font, size):
        # Remove page furniture geometrically, including between split paragraphs.
        y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
        if y > 35:
            pieces.append(text)

    for page in pdf.pages:
        page.extract_text(visitor_text=visit)
    return "".join(pieces)


@pytest.mark.parametrize("case", ["rich", "zero-finance", "stress"])
def test_pdf_preserves_supported_values_context_and_sources(tmp_path, case):
    view, pdf = render(f"examples/dossier/{case}.json", tmp_path / "dossier.pdf")
    text = body_text(pdf)
    assert 1 <= sum("Dossier • strona" in p.extract_text() for p in pdf.pages) <= 2
    assert "DANE SYNTETYCZNE - demonstracja układu" in text
    assert compact(view.legal_name) in compact(text)
    for fact in view.facts:
        for value in fact.values:
            assert compact(value) in compact(text)
        for citation in fact.citations:
            assert compact(citation.excerpt) in compact(text)
    for source in view.sources:
        assert compact(source.url) in compact(text)
        assert compact(source.title) in compact(text)
        assert source.retrieved_at in text
    for gap in view.gaps:
        assert compact(gap.reason) in compact(text)
    urls = {
        str(annotation.get_object()["/A"]["/URI"])
        for page in pdf.pages
        for annotation in page.get("/Annots", [])
        if "/A" in annotation.get_object()
    }
    assert {s.url for s in view.sources} <= urls
    embedded = {
        str(font.get_object()["/BaseFont"])
        for page in pdf.pages
        for font in page["/Resources"]["/Font"].values()
        if "/FontDescriptor" in font.get_object()
        and "/FontFile2" in font.get_object()["/FontDescriptor"]
    }
    assert any("DejaVuSans" in name for name in embedded)
    assert any("DejaVuSans-Bold" in name for name in embedded)
    if case == "stress":
        assert '<pomiar> "precyzyjny"' in text  # Not parsed as Paragraph markup.


def test_same_locked_environment_produces_identical_pdf(tmp_path):
    view, _ = render("examples/dossier/rich.json", tmp_path / "first.pdf")
    render_dossier_pdf(view, tmp_path / "second.pdf")
    assert (tmp_path / "first.pdf").read_bytes() == (tmp_path / "second.pdf").read_bytes()


@pytest.mark.parametrize("case", ["out_of_contract", "unsafe"])
def test_abstention_pdf_has_no_candidate_value_or_excerpt(tmp_path, case):
    view, pdf = render(f"examples/strict_contract/{case}.json", tmp_path / "dossier.pdf")
    text = "\n".join(p.extract_text() for p in pdf.pages)
    run = CompanyResearchRun.model_validate_json(
        Path(f"examples/strict_contract/{case}.json").read_bytes()
    )
    assert view.research_support_count == 0
    for value in run.draft.products_services.value:
        assert value not in text
    for ref in run.draft.products_services.evidence:
        assert ref.excerpt not in text
    assert "Niepotwierdzone" in text
    assert "Nie ustalono faktów z researchu" in text
