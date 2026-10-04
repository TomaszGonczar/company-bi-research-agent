"""Adversarial publication checks for assertion meaning and financial polarity."""

from __future__ import annotations

from typing import Any

import pytest

UNKNOWN_REVENUE = {"state": "unknown", "reason": "No revenue observation", "metric": "revenue"}
UNKNOWN_RESULT = {"state": "unknown", "reason": "No net-result observation", "metric": "net_result"}
PERIOD = {"start": "2025-01-01", "end": "2025-12-31"}


def product_candidate(phrase: str, quote: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": [phrase],
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }


@pytest.mark.parametrize(
    ("quote", "phrase"),
    [
        pytest.param(
            "Example sp. z o.o. has never offered industrial pumps to customers.",
            "industrial pumps",
            id="negative_long_negation",
        ),
        pytest.param(
            "Example sp. z o.o. plans to launch cloud accounting software next year.",
            "cloud accounting software",
            id="negative_planned_service",
        ),
        pytest.param(
            "Example sp. z o.o. discontinued its solar panel installation service in 2024.",
            "solar panel installation service",
            id="negative_discontinued_service",
        ),
        pytest.param(
            "Example sp. z o.o. nigdy nie oferowała usług księgowości w chmurze.",
            "usług księgowości w chmurze",
            id="negative_polish_long_negation",
        ),
        pytest.param(
            "Example sp. z o.o. planuje uruchomić serwis rowerowy w przyszłym roku.",
            "serwis rowerowy",
            id="negative_polish_planned_service",
        ),
        pytest.param(
            "Example sp. z o.o. offered cloud services in 2024.",
            "cloud services",
            id="negative_past_offering_without_current_assertion",
        ),
        pytest.param(
            "Example sp. z o.o. is considering cloud services.",
            "cloud services",
            id="negative_embedded_consideration",
        ),
        pytest.param(
            "Example sp. z o.o. does not currently sell or provide cloud services.",
            "cloud services",
            id="negative_original_crosscheck_cloud_services",
        ),
    ],
)
def test_negative_or_planned_catalog_assertions_are_not_published(
    make_run: Any, publish: Any, quote: str, phrase: str
) -> None:
    result = publish(make_run(quote, products_services=product_candidate(phrase, quote)))
    assert result["products_services"]["state"] == "uncertain"
    assert result["products_services"]["value"] is None


def test_clipped_quote_cannot_omit_a_source_conditional(make_run: Any, publish: Any) -> None:
    excerpt = "Example sp. z o.o. offers cloud services"
    content = f"If {excerpt}, the company may launch a new division."
    run = make_run(
        content,
        products_services=product_candidate("cloud services", excerpt),
    )
    result = publish(run)
    assert result["products_services"]["state"] == "uncertain"
    assert result["products_services"]["value"] is None


@pytest.mark.parametrize(
    ("quote", "phrase", "state"),
    [
        pytest.param(
            "Example sp. z o.o. sells machinery to retailers of cloud services.",
            "cloud services",
            "uncertain",
            id="negative_customer-activity-complement",
        ),
        pytest.param(
            "Example sp. z o.o. sells machinery to retailers of cloud services.",
            "machinery",
            "supported",
            id="positive_direct-object-before-customer-complement",
        ),
        pytest.param(
            "Example sp. z o.o. sells machinery to retailers who provide cloud services.",
            "cloud services",
            "uncertain",
            id="negative_embedded-customer-subject",
        ),
        pytest.param(
            "Retailers of cloud services are provided by Example sp. z o.o.",
            "cloud services",
            "uncertain",
            id="negative-passive-complement",
        ),
        pytest.param(
            "Machines for cloud services are sold by Example sp. z o.o.",
            "Machines",
            "supported",
            id="positive-passive-subject-head-before-purpose-complement",
        ),
        pytest.param(
            "Machines for cloud services are sold by Example sp. z o.o.",
            "cloud services",
            "uncertain",
            id="negative-passive-purpose-complement",
        ),
    ],
)
def test_customer_activity_complements_do_not_attach_to_company(
    make_run: Any, publish: Any, quote: str, phrase: str, state: str
) -> None:
    result = publish(make_run(quote, products_services=product_candidate(phrase, quote)))
    assert result["products_services"]["state"] == state
    assert result["products_services"]["value"] == ([phrase] if state == "supported" else None)


def test_current_passive_offering_remains_publishable(make_run: Any, publish: Any) -> None:
    quote = "Cloud services are currently provided by Example sp. z o.o."
    result = publish(make_run(quote, products_services=product_candidate("cloud services", quote)))
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["value"] == ["cloud services"]


@pytest.mark.parametrize(
    ("quote", "phrase"),
    [
        pytest.param(
            "Example sp. z o.o. currently provides payroll outsourcing to Polish companies.",
            "payroll outsourcing",
            id="positive_current_offering",
        ),
        pytest.param(
            "Example sp. z o.o. provides payroll outsourcing. It has never offered factoring.",
            "payroll outsourcing",
            id="positive_nearby_unrelated_negative_clause",
        ),
        pytest.param(
            "Example sp. z o.o. świadczy usługi transportu drogowego.",
            "usługi transportu drogowego",
            id="positive_polish_current_offering",
        ),
        pytest.param(
            "Example sp. z o.o. plans to offer hosting but currently provides cloud services.",
            "cloud services",
            id="positive_current_assertion_after_planned_contrast",
        ),
    ],
)
def test_affirmative_current_catalog_claims_remain_publishable(
    make_run: Any, publish: Any, quote: str, phrase: str
) -> None:
    result = publish(make_run(quote, products_services=product_candidate(phrase, quote)))
    assert result["products_services"]["state"] == "supported"
    assert result["products_services"]["value"] == [phrase]


def test_direct_current_design_predicate_supports_business_description(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. designs modular water pumps for municipal utilities."
    candidate = "Designs modular water pumps for municipal utilities."
    run = make_run(
        quote,
        business_description={
            "state": "supported",
            "value": candidate,
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    fact = publish(run)["business_description"]
    assert fact["state"] == "supported"
    assert fact["value"] == candidate


def test_possessive_product_copula_supports_each_explicit_list_item(
    make_run: Any, publish: Any
) -> None:
    quote = "Its products are industrial water pumps and control units."
    content = "Example sp. z o.o. is a pump manufacturer. " + quote
    run = make_run(
        content,
        products_services={
            "state": "supported",
            "value": ["Industrial water pumps", "Control units"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    fact = publish(run)["products_services"]
    assert fact["state"] == "supported"
    assert fact["value"] == ["Industrial water pumps", "Control units"]


def test_future_hiring_plan_does_not_establish_current_headcount(
    make_run: Any, publish: Any
) -> None:
    quote = "Example sp. z o.o. plans to hire 40 employees next year."
    run = make_run(
        quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 40},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = publish(run)
    assert result["employees"]["state"] == "uncertain"
    assert result["employees"]["value"] is None


@pytest.mark.parametrize(
    ("quote", "count"),
    [
        pytest.param(
            "Example sp. z o.o. employs 40 people today.", 40, id="positive_current_headcount"
        ),
        pytest.param(
            "Example sp. z o.o. zatrudnia 40 pracowników.", 40, id="positive_polish_headcount"
        ),
    ],
)
def test_affirmative_current_headcount_remains_publishable(
    make_run: Any, publish: Any, quote: str, count: int
) -> None:
    run = make_run(
        quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": count},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    assert publish(run)["employees"]["state"] == "supported"


def financial_candidate(metric: str, value: str, quote: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "metric": metric,
        "period": PERIOD,
        "currency": "PLN",
        "unit": "thousands",
        "scope": "legal_entity",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }


def financial_run(make_run: Any, quote: str, *, metric: str, value: str) -> Any:
    rows = [dict(UNKNOWN_REVENUE), dict(UNKNOWN_RESULT)]
    index = 0 if metric == "revenue" else 1
    rows[index] = financial_candidate(metric, value, quote)
    return make_run(quote, financials=rows)


@pytest.mark.parametrize(
    ("quote", "candidate", "state", "value"),
    [
        pytest.param(
            "Example sp. z o.o. reported a standalone net loss of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "10",
            "uncertain",
            None,
            id="negative_loss_wrong_positive_sign",
        ),
        pytest.param(
            "Example sp. z o.o. reported a standalone net loss of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "-10",
            "supported",
            "-10",
            id="positive_loss_negative_sign",
        ),
        pytest.param(
            "Example sp. z o.o. standalone net loss was PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "10",
            "uncertain",
            None,
            id="negative_original_crosscheck_loss_wrong_sign",
        ),
        pytest.param(
            "Example sp. z o.o. standalone net loss was PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "-10",
            "supported",
            "-10",
            id="positive_original_crosscheck_loss_sign",
        ),
    ],
)
def test_net_loss_preserves_observed_sign_without_repair(
    make_run: Any,
    publish: Any,
    quote: str,
    candidate: str,
    state: str,
    value: str | None,
) -> None:
    result = publish(financial_run(make_run, quote, metric="net_result", value=candidate))
    fact = result["financials"][1]
    assert fact["state"] == state
    assert fact["value"] == value


def test_financial_quote_cannot_omit_a_source_conditional(make_run: Any, publish: Any) -> None:
    excerpt = (
        "Example sp. z o.o. reported standalone revenue of PLN 10 thousand "
        "for 2025-01-01 to 2025-12-31"
    )
    rows = [dict(UNKNOWN_REVENUE), dict(UNKNOWN_RESULT)]
    rows[0] = financial_candidate("revenue", "10", excerpt)
    run = make_run(f"If {excerpt}, it would exceed the forecast.", financials=rows)
    fact = publish(run)["financials"][0]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


@pytest.mark.parametrize(
    ("quote", "metric", "candidate"),
    [
        pytest.param(
            "Example sp. z o.o. targets standalone revenue of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_target_is_not_realized_revenue",
        ),
        pytest.param(
            "Example sp. z o.o. forecasts standalone revenue of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_forecast_is_not_realized_revenue",
        ),
        pytest.param(
            "Example sp. z o.o. reported no standalone revenue of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_denied_revenue",
        ),
        pytest.param(
            "Example sp. z o.o. standalone revenue was not PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_original_crosscheck_denied_revenue",
        ),
        pytest.param(
            "Example sp. z o.o. standalone revenue target was PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_original_crosscheck_target_noun",
        ),
        pytest.param(
            "Example sp. z o.o. reported standalone revenue of PLN 10 thousand, "
            "but this was only a target for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_post_amount_target_qualification",
        ),
        pytest.param(
            "Example sp. z o.o. hopes its standalone revenue was PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            id="negative_embedded_revenue_aspiration",
        ),
    ],
)
def test_nonrealized_or_denied_revenue_is_not_published_as_actual(
    make_run: Any, publish: Any, quote: str, metric: str, candidate: str
) -> None:
    result = publish(financial_run(make_run, quote, metric=metric, value=candidate))
    assert result["financials"][0]["state"] == "uncertain"
    assert result["financials"][0]["value"] is None


@pytest.mark.parametrize(
    ("quote", "metric", "candidate", "index"),
    [
        pytest.param(
            "Example sp. z o.o. reported standalone revenue of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "revenue",
            "10",
            0,
            id="positive_actual_revenue",
        ),
        pytest.param(
            "Example sp. z o.o. reported standalone net profit of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "net_result",
            "10",
            1,
            id="positive_net_profit",
        ),
        pytest.param(
            "Example sp. z o.o. reported standalone net result of PLN 0 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "net_result",
            "0",
            1,
            id="positive_explicit_zero_net_result",
        ),
        pytest.param(
            "Example sp. z o.o. reported standalone net result of PLN -10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "net_result",
            "-10",
            1,
            id="positive_explicit_negative_net_result",
        ),
        pytest.param(
            "Example sp. z o.o. reported standalone net profit/(loss) of PLN 10 thousand "
            "for 2025-01-01 to 2025-12-31.",
            "net_result",
            "10",
            1,
            id="positive_unsigned_combined_profit_loss_header",
        ),
    ],
)
def test_actual_financial_controls_preserve_metric_and_metadata(
    make_run: Any,
    publish: Any,
    quote: str,
    metric: str,
    candidate: str,
    index: int,
) -> None:
    result = publish(financial_run(make_run, quote, metric=metric, value=candidate))
    fact = result["financials"][index]
    assert fact["state"] == "supported"
    assert fact["value"] == candidate
    assert fact["metric"] == metric
    assert fact["period"] == PERIOD
    assert fact["currency"] == "PLN"
    assert fact["unit"] == "thousands"
    assert fact["scope"] == "legal_entity"
    assert fact["evidence"] == [{"source_id": "page", "excerpt": quote}]
