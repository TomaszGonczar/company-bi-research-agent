"""Adversarial checks for the finite assertion language used at publication."""

from __future__ import annotations

from typing import Any

import pytest

UNKNOWN_REVENUE = {"state": "unknown", "reason": "No revenue observation", "metric": "revenue"}
UNKNOWN_RESULT = {"state": "unknown", "reason": "No net-result observation", "metric": "net_result"}
PERIOD = {"start": "2025-01-01", "end": "2025-12-31"}


def product_candidate(label: str, quote: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": [label],
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }


def test_quoted_opaque_product_label_is_supported(make_run: Any, publish: Any) -> None:
    quote = 'Example sp. z o.o. provides "cloud services".'
    result = publish(make_run(quote, products_services=product_candidate("cloud services", quote)))
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["value"] == ["cloud services"]


@pytest.mark.parametrize(
    "quote",
    [
        "Example sp. z o.o. provides cloud services.",
        'Example sp. z o.o. provides "cloud services" after approval.',
        'Example sp. z o.o. provides "cloud services". Extra source sentence.',
    ],
    ids=["true-unquoted-is-out-of-contract", "qualified-tail", "second-sentence"],
)
def test_product_assertion_must_match_one_complete_production(
    make_run: Any, publish: Any, quote: str
) -> None:
    result = publish(make_run(quote, products_services=product_candidate("cloud services", quote)))
    assert result["products_services"]["state"] == "uncertain"
    assert result["products_services"]["value"] is None


def test_product_candidate_must_equal_the_whole_quoted_label(make_run: Any, publish: Any) -> None:
    quote = 'Example sp. z o.o. provides "cloud services".'
    result = publish(make_run(quote, products_services=product_candidate("cloud", quote)))
    assert result["products_services"]["state"] == "uncertain"
    assert result["products_services"]["value"] is None


def test_exact_employee_assertion_and_optional_date(make_run: Any, publish: Any) -> None:
    quote = "Example sp. z o.o. employs 40 people as of 2026-09-30."
    run = make_run(
        quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 40},
            "as_of": "2026-09-30",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    fact = publish(run)["employees"]
    assert fact["state"] == "supported"
    assert fact["value"] == {"kind": "exact", "count": 40}
    assert fact["as_of"] == "2026-09-30"


def financial_candidate(metric: str, value: str, quote: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "metric": metric,
        "period": PERIOD,
        "currency": "PLN",
        "unit": "millions",
        "scope": "legal_entity",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }


def financial_run(make_run: Any, quote: str, value: str) -> Any:
    rows = [dict(UNKNOWN_REVENUE), dict(UNKNOWN_RESULT)]
    rows[0] = financial_candidate("revenue", value, quote)
    return make_run(quote, financials=rows)


def test_atomic_financial_assertion_is_supported(make_run: Any, publish: Any) -> None:
    quote = (
        "Example sp. z o.o. reported standalone revenue of PLN 12 million "
        "for 2025-01-01 to 2025-12-31."
    )
    fact = publish(financial_run(make_run, quote, "12"))["financials"][0]
    assert fact["state"] == "supported"
    assert fact["value"] == "12"
    assert fact["period"] == PERIOD


def test_post_amount_target_tail_blocks_financial_publication(make_run: Any, publish: Any) -> None:
    quote = (
        "Example sp. z o.o. reported standalone revenue of PLN 10 thousand "
        "for 2025-01-01 to 2025-12-31, but this was only a target."
    )
    fact = publish(financial_run(make_run, quote, "10"))["financials"][0]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


def test_completed_event_label_summary_and_optional_occurrence_date(
    make_run: Any, publish: Any
) -> None:
    quote = 'Example sp. z o.o. launched "a distribution centre" on 2026-09-10.'
    run = make_run(
        quote,
        recent_developments=[
            {
                "state": "supported",
                "value": {
                    "title": "a distribution centre",
                    "summary": quote,
                    "published_on": "2026-09-20",
                    "occurred_on": "2026-09-10",
                },
                "evidence": [{"source_id": "page", "excerpt": quote}],
            }
        ],
    )
    payload = run.model_dump(mode="json")
    payload["sources"][1]["source"]["published_on"] = "2026-09-20"
    fact = publish(type(run).model_validate(payload))["recent_developments"][0]
    assert fact["state"] == "supported"
    assert fact["value"]["title"] == "a distribution centre"
    assert fact["value"]["summary"] == quote
    assert fact["value"]["occurred_on"] == "2026-09-10"
