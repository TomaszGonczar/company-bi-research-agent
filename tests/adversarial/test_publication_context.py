"""Focused regressions for citation ownership and canonical publication context."""

from __future__ import annotations

from typing import Any

from company_bi.models import CompanyResearchRun


def product_candidate(value: list[str], evidence: list[dict[str, str]]) -> dict[str, Any]:
    return {"state": "supported", "value": value, "evidence": evidence}


def _with_pages(run: Any, pages: list[tuple[str, str]], **draft_changes: Any) -> Any:
    template = run.sources[1]
    retained = [source for source in run.sources if source.kind != "full_page"]
    for source_id, content in pages:
        source = template.model_copy(update={"content": content})
        source = source.model_copy(
            update={"source": source.source.model_copy(update={"source_id": source_id})}
        )
        retained.append(source)
    payload = run.model_dump(mode="python")
    payload["sources"] = retained
    payload["draft"].update(draft_changes)
    return CompanyResearchRun.model_validate(payload)


def _ref(source_id: str, excerpt: str) -> dict[str, str]:
    return {"source_id": source_id, "excerpt": excerpt}


def test_supported_product_drops_unrelated_exact_citation(make_run: Any, publish: Any) -> None:
    product = 'Example sp. z o.o. manufactures "industrial pumps".'
    weather = "The weather is sunny."
    result = publish(
        _with_pages(
            make_run(product),
            [("page", product), ("weather", weather)],
            products_services=product_candidate(
                ["industrial pumps"], [_ref("page", product), _ref("weather", weather)]
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["evidence"] == [_ref("page", product)]


def test_each_required_product_may_be_supported_by_a_separate_page(
    make_run: Any, publish: Any
) -> None:
    first = 'Example sp. z o.o. manufactures "industrial pumps".'
    second = 'Example sp. z o.o. manufactures "control units".'
    result = publish(
        _with_pages(
            make_run(first),
            [("page", first), ("page-2", second)],
            products_services=product_candidate(
                ["industrial pumps", "control units"],
                [_ref("page", first), _ref("page-2", second)],
            ),
        )
    )
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["evidence"] == [
        _ref("page", first),
        _ref("page-2", second),
    ]


def test_unrelated_citation_cannot_complete_a_missing_required_product(
    make_run: Any, publish: Any
) -> None:
    product = 'Example sp. z o.o. manufactures "industrial pumps".'
    weather = "The weather is sunny."
    result = publish(
        _with_pages(
            make_run(product),
            [("page", product), ("weather", weather)],
            products_services=product_candidate(
                ["industrial pumps", "turbines"],
                [_ref("page", product), _ref("weather", weather)],
            ),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_prior_condition_and_named_assertion_are_out_of_contract_true(
    make_run: Any, publish: Any
) -> None:
    quote = (
        'If market conditions improve, Example sp. z o.o. might produce "turbines". '
        'Separately, Example sp. z o.o. produces "industrial pumps".'
    )
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(["industrial pumps"], [_ref("page", quote)]),
        )
    )
    assert result["products_services"]["state"] == "uncertain"
    assert result["products_services"]["value"] is None


def test_unrelated_prior_condition_does_not_make_legacy_claim_contract_positive(
    make_run: Any, publish: Any
) -> None:
    quote = 'If visitors arrive, the café opens. Example sp. z o.o. produces "industrial pumps".'
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(["industrial pumps"], [_ref("page", quote)]),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_conditional_clause_and_anaphoric_continuation_remain_blocked(
    make_run: Any, publish: Any
) -> None:
    quote = 'If market conditions improve, Example sp. z o.o. might produce "industrial pumps".'
    result = publish(
        make_run(
            quote,
            products_services=product_candidate(["industrial pumps"], [_ref("page", quote)]),
        )
    )
    assert result["products_services"]["state"] == "uncertain"

    continuation = (
        "Example sp. z o.o. will start a project if market conditions improve. "
        'It also produces "industrial pumps" for that project.'
    )
    result = publish(
        make_run(
            continuation,
            products_services=product_candidate(["industrial pumps"], [_ref("page", continuation)]),
        )
    )
    assert result["products_services"]["state"] == "uncertain"


def test_group_financial_context_is_out_of_contract(make_run: Any, publish: Any) -> None:
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
        "evidence": [_ref("page", quote)],
    }
    unknown_result = {"metric": "net_result", "state": "unknown", "reason": "Not established"}
    result = publish(make_run(quote, financials=[fact, unknown_result]))
    assert result["financials"][0]["state"] == "uncertain"
    assert result["financials"][0]["value"] is None


def test_group_subject_does_not_make_scope_or_interval_independently_supported(
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
        "evidence": [_ref("page", quote)],
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
        "evidence": [_ref("page", scoped_quote)],
    }
    result = publish(make_run(scoped_quote, financials=[legal_entity, unknown_result]))
    assert result["financials"][0]["state"] == "uncertain"
    assert result["financials"][0]["value"] is None
