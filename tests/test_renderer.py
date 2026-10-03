from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from company_bi.models import CompanyProfile
from company_bi.renderer import render_json, render_markdown

PROFILE_DIR = Path(__file__).parents[1] / "examples/profiles"


def load_profile(name: str) -> CompanyProfile:
    return CompanyProfile.model_validate_json((PROFILE_DIR / name).read_text())


def visible_markdown(markdown: str) -> str:
    """Remove renderer escape markers for assertions about displayed values."""
    return markdown.replace("\\", "").replace("**", "")


def test_renderers_are_deterministic_and_end_with_newline() -> None:
    profile = load_profile("complete.json")

    for renderer in (render_json, render_markdown):
        first = renderer(profile)
        assert first == renderer(profile)
        assert first.endswith("\n")

    assert CompanyProfile.model_validate_json(render_json(profile)) == profile


def test_financial_zero_and_negative_decimal_precision_and_period_scope_are_preserved() -> None:
    data: dict[str, Any] = json.loads((PROFILE_DIR / "complete.json").read_text())
    data["financials"][0]["value"] = "0.000"
    data["financials"][1]["value"] = "-1234567890.123456789"
    data["financials"][1]["scope"] = "group"
    data["financials"][1]["group_name"] = "Example Group"
    profile = CompanyProfile.model_validate(data)

    markdown = render_markdown(profile)
    serialized = render_json(profile)
    assert "0.000" in markdown and '"value": "0.000"' in serialized
    assert "-1234567890.123456789" in markdown
    assert '"value": "-1234567890.123456789"' in serialized
    assert "Example Group" in markdown
    assert "| group | Example Group |" in markdown
    assert "2025-01-01 to 2025-12-31" in markdown


def test_employee_range_remains_an_interval() -> None:
    markdown = render_markdown(load_profile("complete.json"))
    assert "51–200" in visible_markdown(markdown)


def test_uncertain_candidate_and_occurrence_publication_are_distinguished() -> None:
    data: dict[str, Any] = json.loads((PROFILE_DIR / "conflicting_sources.json").read_text())
    markdown = render_markdown(CompanyProfile.model_validate(data))
    plain = markdown.replace("**", "")
    assert "Published: 2026-07-15" in plain
    assert "Occurred: 2026-07-10" in plain


def test_markdown_sensitive_content_is_escaped() -> None:
    data: dict[str, Any] = json.loads((PROFILE_DIR / "complete.json").read_text())
    data["business_description"]["value"] = "A *bold* [claim](x) | # heading"
    data["business_description"]["evidence"][0]["excerpt"] = "A *bold* [claim](x) | # heading"
    data["sources"][1]["title"] = "Company [page] (synthetic)"
    data["sources"][1]["url"] = "https://company.example/path_(one)"
    markdown = render_markdown(CompanyProfile.model_validate(data))

    assert r"A \*bold\* \[claim\]\(x\) \| \# heading" in markdown
    assert r"Company \[page\] \(synthetic\)" in markdown
    assert "path_%28one%29" in markdown
