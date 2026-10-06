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


def add_employee_page(payload: dict[str, Any], run: Any, source_id: str, content: str) -> None:
    payload["sources"].append(
        {
            "source": {
                "source_id": source_id,
                "url": f"https://{source_id}.example/",
                "title": source_id,
                "retrieved_at": run.generated_at,
                "published_on": date(2026, 10, 2),
            },
            "kind": "full_page",
            "content": content,
            "fetch_mode": "static",
        }
    )


def test_different_employee_counts_on_distinct_dates_are_not_automatic_conflicts(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. employs 120 people as of 2026-06-30."
    run = make_employee_run(make_run, quote, quote, 120, "2026-06-30")
    payload = run.model_dump(mode="python")
    add_employee_page(
        payload, run, "older-page", "Example sp. z o.o. employs 100 people as of 2025-12-31."
    )
    result = publish(CompanyResearchRun.model_validate(payload))
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
    quote = "Example sp. z o.o. employs 120 people as of 2026-06-30."
    run = make_employee_run(make_run, quote, quote, 120, "2026-06-30")
    payload = run.model_dump(mode="python")
    add_employee_page(
        payload, run, "conflicting-page", "Example sp. z o.o. employs 100 people as of 2026-06-30."
    )
    result = publish(CompanyResearchRun.model_validate(payload))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None


def test_undated_alternative_does_not_authorize_newest_count_selection(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. employs 120 people as of 2026-06-30."
    run = make_employee_run(make_run, quote, quote, 120, "2026-06-30")
    payload = run.model_dump(mode="python")
    add_employee_page(payload, run, "undated-page", "Example sp. z o.o. employs 100 people.")
    result = publish(CompanyResearchRun.model_validate(payload))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None


def test_missing_candidate_date_is_not_filled_from_dated_pages(make_run: Any, publish: Any) -> None:
    quote = "Example sp. z o.o. employs 120 people as of 2026-09-01."
    older_quote = "Example sp. z o.o. employs 100 people as of 2025-09-01."
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
    assert result["employees"]["state"] == "supported"
    assert result["employees"]["value"] == {"kind": "exact", "count": 120}
    assert result["employees"]["as_of"] is None


def test_past_tense_headcount_is_true_out_of_contract(make_run: Any, publish: Any) -> None:
    quote = "Example sp. z o.o. employed 100 people as of 2025-09-01."
    result = publish(make_employee_run(make_run, quote, quote, 100, "2025-09-01"))
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None
    assert result["employees"]["as_of"] is None


def test_explicit_group_and_other_entity_counts_are_not_company_alternatives(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. employs 120 people as of 2026-06-30."
    run = make_employee_run(make_run, quote, quote, 120, "2026-06-30")
    payload = run.model_dump(mode="python")
    for source_id, content in (
        ("group-page", "The Example Group employs 900 people."),
        ("other-page", "Other Company employs 400 people."),
    ):
        payload["sources"].append(
            {
                "source": {
                    "source_id": source_id,
                    "url": f"https://{source_id}.example/",
                    "title": source_id,
                    "retrieved_at": run.generated_at,
                    "published_on": date(2026, 10, 2),
                },
                "kind": "full_page",
                "content": content,
                "fetch_mode": "static",
            }
        )
    result = publish(CompanyResearchRun.model_validate(payload))
    employees = result["employees"]
    assert employees["state"] == "supported"
    assert employees["value"] == {"kind": "exact", "count": 120}
    assert employees["as_of"] == "2026-06-30"
