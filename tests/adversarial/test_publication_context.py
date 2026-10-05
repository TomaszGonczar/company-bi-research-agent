"""Focused regressions for citation ownership and canonical publication context."""

from __future__ import annotations

from typing import Any


def product_candidate(value: list[str], evidence: list[dict[str, str]]) -> dict[str, Any]:
    return {"state": "supported", "value": value, "evidence": evidence}


def test_supported_product_drops_unrelated_exact_citation(make_run: Any, publish: Any) -> None:
    product = "Example sp. z o.o. produces industrial pumps."
    weather = "The weather is sunny."
    source = f"{product} {weather}"
    result = publish(
        make_run(
            source,
            products_services=product_candidate(
                ["industrial pumps"],
                [
                    {"source_id": "page", "excerpt": product},
                    {"source_id": "page", "excerpt": weather},
                ],
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["evidence"] == [{"source_id": "page", "excerpt": product}]
    assert {source["source_id"] for source in result["sources"]} == {"page", "registry"}


def test_each_required_product_may_be_supported_by_a_separate_citation(
    make_run: Any, publish: Any
) -> None:
    first = "Example sp. z o.o. produces industrial pumps."
    second = "Example sp. z o.o. manufactures control units."
    irrelevant = "The weather is sunny."
    result = publish(
        make_run(
            f"{first} {second} {irrelevant}",
            products_services=product_candidate(
                ["industrial pumps", "control units"],
                [
                    {"source_id": "page", "excerpt": first},
                    {"source_id": "page", "excerpt": second},
                    {"source_id": "page", "excerpt": irrelevant},
                ],
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["evidence"] == [
        {"source_id": "page", "excerpt": first},
        {"source_id": "page", "excerpt": second},
    ]


def test_unrelated_citation_cannot_complete_a_missing_required_product(
    make_run: Any, publish: Any
) -> None:
    product = "Example sp. z o.o. produces industrial pumps."
    weather = "The weather is sunny."
    result = publish(
        make_run(
            f"{product} {weather}",
            products_services=product_candidate(
                ["industrial pumps", "turbines"],
                [
                    {"source_id": "page", "excerpt": product},
                    {"source_id": "page", "excerpt": weather},
                ],
            ),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_complete_prior_condition_does_not_spill_into_named_assertion(
    make_run: Any, publish: Any
) -> None:
    quote = (
        "If market conditions improve, Example sp. z o.o. might produce turbines. "
        "Separately, Example sp. z o.o. produces industrial pumps."
    )
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(
                ["industrial pumps"], [{"source_id": "page", "excerpt": quote}]
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["value"] == ["industrial pumps"]


def test_unrelated_prior_condition_does_not_block_named_company_assertion(
    make_run: Any, publish: Any
) -> None:
    quote = "If visitors arrive, the café opens. Example sp. z o.o. produces industrial pumps."
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(
                ["industrial pumps"], [{"source_id": "page", "excerpt": quote}]
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"


def test_conditional_clause_still_blocks_same_sentence_assertion(
    make_run: Any, publish: Any
) -> None:
    quote = "If market conditions improve, Example sp. z o.o. might produce industrial pumps."
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(
                ["industrial pumps"], [{"source_id": "page", "excerpt": quote}]
            ),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_conditional_anaphoric_continuation_remains_blocked(make_run: Any, publish: Any) -> None:
    quote = (
        "Example sp. z o.o. will start a project if market conditions improve. "
        "It also produces industrial pumps for that project."
    )
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(
                ["industrial pumps"], [{"source_id": "page", "excerpt": quote}]
            ),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_explicit_group_of_entity_revenue_is_supported(make_run: Any, publish: Any) -> None:
    quote = (
        "The Example Group of Example sp. z o.o. reported revenue of 500 thousand PLN "
        "for 2025-01-01 to 2025-12-31."
    )
    fact = {
        "state": "supported",
        "value": "500",
        "metric": "revenue",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "thousands",
        "scope": "group",
        "group_name": "Example Group",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }
    unknown_result = {"metric": "net_result", "state": "unknown", "reason": "Not established"}
    result = publish(make_run(quote, financials=[fact, unknown_result]))
    assert result["financials"][0]["state"] == "supported"
    assert result["financials"][0]["value"] == "500"


def test_group_subject_does_not_relax_explicit_scope_or_interval(
    make_run: Any, publish: Any
) -> None:
    quote = "The Example Group of Example sp. z o.o. reported revenue of 500 thousand PLN."
    base = {
        "state": "supported",
        "value": "500",
        "metric": "revenue",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "thousands",
        "scope": "group",
        "group_name": "Example Group",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }
    unknown_result = {"metric": "net_result", "state": "unknown", "reason": "Not established"}
    result = publish(make_run(quote, financials=[base, unknown_result]))
    assert result["financials"][0]["state"] == "uncertain"
    assert result["financials"][0]["value"] is None

    scoped_quote = quote.rstrip(".") + " for 2025-01-01 to 2025-12-31."
    legal_entity = {
        **base,
        "scope": "legal_entity",
        "group_name": None,
        "evidence": [{"source_id": "page", "excerpt": scoped_quote}],
    }
    result = publish(make_run(scoped_quote, financials=[legal_entity, unknown_result]))
    assert result["financials"][0]["state"] == "uncertain"
    assert result["financials"][0]["value"] is None
