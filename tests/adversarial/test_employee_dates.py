"""Adversarial employee observations: observation dates are not publication dates."""

from __future__ import annotations

from datetime import date
from typing import Any

from company_bi.models import CompanyResearchRun


def employee_candidate(quote: str, count: int, as_of: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": {"kind": "exact", "count": count},
        "as_of": as_of,
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }


def make_employee_run(make_run: Any, content: str, quote: str, count: int, as_of: str) -> Any:
    run = make_run(content, employees=employee_candidate(quote, count, as_of))
    payload = run.model_dump(mode="python")
    # Publication metadata belongs to the retained source, not the employee observation.
    payload["sources"][1]["source"]["published_on"] = date(2026, 10, 2)
    return CompanyResearchRun.model_validate(payload)


def test_different_employee_counts_on_distinct_dates_are_not_automatic_conflicts(
    make_run: Any, publish: Any
) -> None:
    quote = "As of 2026-06-30, Example sp. z o.o. employs 120 employees."
    content = "As of 2025-12-31, Example sp. z o.o. employed 100 employees. " + quote
    result = publish(make_employee_run(make_run, content, quote, 120, "2026-06-30"))
    employees = result["employees"]
    assert employees["state"] == "supported"
    assert employees["value"] == {"kind": "exact", "count": 120}
    assert employees["as_of"] == "2026-06-30"
    page = next(source for source in result["sources"] if source["source_id"] == "page")
    assert page["published_on"] == "2026-10-02"
    assert employees["evidence"] == [{"source_id": "page", "excerpt": quote}]


def test_differing_employee_counts_for_same_date_remain_uncertain(
    make_run: Any, publish: Any
) -> None:
    quote = "As of 2026-06-30, Example sp. z o.o. employs 120 employees."
    content = quote + " As of 2026-06-30, Example sp. z o.o. employs 100 employees."
    result = publish(make_employee_run(make_run, content, quote, 120, "2026-06-30"))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None
    assert len(result["employees"]["evidence"]) >= 2


def test_undated_alternative_does_not_authorize_newest_count_selection(
    make_run: Any, publish: Any
) -> None:
    quote = "As of 2026-06-30, Example sp. z o.o. employs 120 employees."
    content = quote + " Example sp. z o.o. employs 100 employees."
    result = publish(make_employee_run(make_run, content, quote, 120, "2026-06-30"))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None


def test_missing_candidate_date_with_multiple_dated_pages_stays_uncertain(
    make_run: Any, publish: Any
) -> None:
    quote = "As of 2026-09-01, Example sp. z o.o. employs 120 employees."
    older_quote = "As of 2025-09-01, Example sp. z o.o. employed 100 employees."
    run = make_run(
        quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    payload = run.model_dump(mode="python")
    payload["sources"][1]["source"]["published_on"] = date(2025, 10, 1)
    payload["sources"].append(
        {
            "source": {
                "source_id": "older-page",
                "url": "https://older-page.example/",
                "title": "Older synthetic company page",
                "retrieved_at": run.generated_at,
                "published_on": date(2026, 10, 1),
            },
            "kind": "full_page",
            "content": older_quote,
            "fetch_mode": "static",
        }
    )
    result = publish(CompanyResearchRun.model_validate(payload))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None
    assert result["employees"]["as_of"] is None


def test_explicitly_dated_past_tense_headcount_can_remain_supported(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. employed 100 employees as of 2025-09-01."
    result = publish(make_employee_run(make_run, quote, quote, 100, "2025-09-01"))
    assert result["employees"]["state"] == "supported"
    assert result["employees"]["value"] == {"kind": "exact", "count": 100}
    assert result["employees"]["as_of"] == "2025-09-01"


def test_explicit_group_and_other_entity_counts_are_not_company_alternatives(
    make_run: Any, publish: Any
) -> None:
    quote = "As of 2026-06-30, Example sp. z o.o. employs 120 employees."
    content = (
        quote
        + " The Example Group employs 900 employees. "
        + "Other Company employs 400 employees."
    )
    result = publish(make_employee_run(make_run, content, quote, 120, "2026-06-30"))
    employees = result["employees"]
    assert employees["state"] == "supported"
    assert employees["value"] == {"kind": "exact", "count": 120}
    assert employees["as_of"] == "2026-06-30"
