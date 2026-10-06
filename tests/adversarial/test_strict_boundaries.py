import json
from datetime import date
from decimal import Decimal, localcontext

import pytest
from pydantic import HttpUrl

PERIOD_START = "2025-01-01"
PERIOD_END = "2025-12-31"
PUBLISHED = date(2026, 9, 1)


def _financial_row(metric: str, amount: str, unit: str, source_id: str, excerpt: str) -> dict:
    return {
        "state": "supported",
        "value": amount,
        "metric": metric,
        "period": {"start": PERIOD_START, "end": PERIOD_END},
        "currency": "PLN",
        "unit": unit,
        "scope": "legal_entity",
        "evidence": [{"source_id": source_id, "excerpt": excerpt}],
    }


def _with_pages(run, pages):
    sources = list(run.sources)
    for source_id, content in pages:
        page = run.sources[1]
        sources.append(
            page.model_copy(
                update={
                    "source": page.source.model_copy(
                        update={
                            "source_id": source_id,
                            "url": HttpUrl(f"https://{source_id}.example/"),
                        }
                    ),
                    "content": content,
                }
            )
        )
    return run.model_copy(update={"sources": sources})


def _assert_financial_publishes(make_run, publish, quote, metric, amount, unit, equivalent_quote):
    row = _financial_row(metric, amount, unit, "page", quote)
    financials = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        {"state": "unknown", "reason": "No result", "metric": "net_result"},
    ]
    financials[0 if metric == "revenue" else 1] = row
    run = _with_pages(make_run(quote, financials=financials), [("equivalent", equivalent_quote)])
    item = publish(run)["financials"][0 if metric == "revenue" else 1]
    assert item["state"] == "supported"
    assert Decimal(item["value"]) == Decimal(amount)
    assert item["unit"] == unit


@pytest.mark.parametrize(
    ("amount", "source_scale", "unit", "equivalent_amount", "equivalent_scale"),
    [
        ("10", "million", "millions", "10000", "thousand"),
        ("1", "billion", "billions", "1000", "million"),
        ("1000000", "units", "units", "1", "million"),
    ],
)
def test_equivalent_scales_do_not_create_financial_conflicts(
    make_run, publish, amount, source_scale, unit, equivalent_amount, equivalent_scale
):
    quote = (
        f"Example sp. z o.o. reported standalone revenue of PLN {amount} {source_scale} "
        f"for {PERIOD_START} to {PERIOD_END}."
    )
    equivalent_quote = (
        f"Example sp. z o.o. reported standalone revenue of PLN {equivalent_amount} "
        f"{equivalent_scale} for {PERIOD_START} to {PERIOD_END}."
    )
    _assert_financial_publishes(make_run, publish, quote, "revenue", amount, unit, equivalent_quote)


def test_financial_conflict_across_scales_abstains(make_run, publish):
    first = (
        f"Example sp. z o.o. reported standalone revenue of PLN 120 million for "
        f"{PERIOD_START} to {PERIOD_END}."
    )
    second = (
        f"Example sp. z o.o. reported standalone revenue of PLN 140000 thousand for "
        f"{PERIOD_START} to {PERIOD_END}."
    )
    run = make_run(
        first,
        financials=[
            _financial_row("revenue", "120", "millions", "page", first),
            {"state": "unknown", "reason": "No result", "metric": "net_result"},
        ],
    )
    run = _with_pages(run, [("other", second)])
    item = publish(run)["financials"][0]
    assert item["state"] == "uncertain"
    assert item["value"] is None


def test_financial_sign_conflict_across_scales_abstains(make_run, publish):
    loss = (
        f"Example sp. z o.o. reported standalone net loss of PLN 10 million for "
        f"{PERIOD_START} to {PERIOD_END}."
    )
    profit = (
        f"Example sp. z o.o. reported standalone net profit of PLN 10000 thousand for "
        f"{PERIOD_START} to {PERIOD_END}."
    )
    financials = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        _financial_row("net_result", "-10", "millions", "page", loss),
    ]
    run = _with_pages(make_run(loss, financials=financials), [("other", profit)])
    item = publish(run)["financials"][1]
    assert item["state"] == "uncertain"
    assert item["value"] is None


def test_publication_compares_high_precision_amounts_exactly(make_run, publish):
    first = (
        f"Example sp. z o.o. reported standalone revenue of PLN "
        f"123456789012345.123456 billion for {PERIOD_START} to {PERIOD_END}."
    )
    equivalent = (
        f"Example sp. z o.o. reported standalone revenue of PLN "
        f"123456789012345123.456 million for {PERIOD_START} to {PERIOD_END}."
    )
    financials = [
        _financial_row("revenue", "123456789012345.123456", "billions", "page", first),
        {"state": "unknown", "reason": "No result", "metric": "net_result"},
    ]
    run = _with_pages(make_run(first, financials=financials), [("other", equivalent)])
    with localcontext() as context:
        context.prec = 2
        item = publish(run)["financials"][0]
    assert item["state"] == "supported"
    assert item["unit"] == "billions"


@pytest.mark.parametrize(
    "assertion",
    [
        'Example sp. z o.o. opened "a" on 2026-08-01.',
        'Example sp. z o.o. launched "a" on 2026-08-01.',
        'Example sp. z o.o. signed "a" on 2026-08-01.',
        'Example sp. z o.o. otworzyła "a" w dniu 2026-08-01.',
        'Example sp. z o.o. uruchomiła "a" w dniu 2026-08-01.',
        'Example sp. z o.o. podpisała "a" w dniu 2026-08-01.',
    ],
)
def test_event_date_markers_match_predicate_language(make_run, publish, assertion):
    result = _publish_event(make_run, publish, assertion)
    event = result["recent_developments"][0]
    assert event["state"] == "supported"
    assert event["value"]["occurred_on"] == "2026-08-01"


def test_event_predicates_without_dates_remain_supported(make_run, publish):
    for assertion in (
        'Example sp. z o.o. opened "a".',
        'Example sp. z o.o. otworzyła "a".',
    ):
        event = _publish_event(make_run, publish, assertion)["recent_developments"][0]
        assert event["state"] == "supported"
        assert event["value"]["occurred_on"] is None


@pytest.mark.parametrize(
    "assertion",
    [
        'Example sp. z o.o. opened "a" w dniu 2026-08-01.',
        'Example sp. z o.o. otworzyła "a" on 2026-08-01.',
    ],
)
def test_cross_language_event_date_markers_abstain(make_run, publish, assertion):
    event = _publish_event(make_run, publish, assertion)["recent_developments"][0]
    assert event["state"] == "uncertain"
    assert event["value"] is None


def _publish_event(make_run, publish, assertion, *, summary=None, title=None):
    label_start = assertion.index('"')
    decoded_title, _ = json.JSONDecoder().raw_decode(assertion[label_start:])
    detail_summary = assertion if summary is None else summary
    event = {
        "state": "supported",
        "value": {
            "title": decoded_title if title is None else title,
            "summary": detail_summary,
            "published_on": PUBLISHED.isoformat(),
            "occurred_on": "2026-08-01",
        },
        "evidence": [{"source_id": "page", "excerpt": assertion}],
    }
    run = make_run(assertion, recent_developments=[event])
    page = run.sources[1]
    dated_page = page.model_copy(
        update={"source": page.source.model_copy(update={"published_on": PUBLISHED})}
    )
    return publish(run.model_copy(update={"sources": [run.sources[0], dated_page]}))


def test_event_summary_preserves_internal_spaces_and_nbsp(make_run, publish):
    assertion = 'Example sp. z o.o. opened "A  B" on 2026-08-01.'
    accepted = _publish_event(make_run, publish, assertion)["recent_developments"][0]
    assert accepted["state"] == "supported"

    rejected = _publish_event(
        make_run, publish, assertion, summary=assertion.replace("A  B", "A B")
    )["recent_developments"][0]
    assert rejected["state"] == "uncertain"
    assert rejected["value"] is None

    nbsp_assertion = 'Example sp. z o.o. opened "A\u00a0B" on 2026-08-01.'
    nbsp_accepted = _publish_event(make_run, publish, nbsp_assertion)["recent_developments"][0]
    assert nbsp_accepted["state"] == "supported"

    nbsp_mismatch = _publish_event(
        make_run, publish, nbsp_assertion, summary=nbsp_assertion.replace("\u00a0", " ")
    )["recent_developments"][0]
    assert nbsp_mismatch["state"] == "uncertain"
    assert nbsp_mismatch["value"] is None


def test_reverse_internal_whitespace_change_is_rejected(make_run, publish):
    assertion = 'Example sp. z o.o. opened "A B" on 2026-08-01.'
    event = _publish_event(make_run, publish, assertion, summary=assertion.replace("A B", "A  B"))[
        "recent_developments"
    ][0]
    assert event["state"] == "uncertain"
    assert event["value"] is None


def test_event_escaped_json_label_keeps_decoded_title_exact(make_run, publish):
    assertion = r'Example sp. z o.o. opened "A\u0020B" on 2026-08-01.'
    accepted = _publish_event(make_run, publish, assertion)["recent_developments"][0]
    assert accepted["state"] == "supported"
    assert accepted["value"]["title"] == "A B"

    wrong_title = _publish_event(make_run, publish, assertion, title=r"A\u0020B")[
        "recent_developments"
    ][0]
    assert wrong_title["state"] == "uncertain"


def test_event_escaped_quote_and_backslash_label(make_run, publish):
    assertion = r'Example sp. z o.o. opened "A\"B\\C" on 2026-08-01.'
    event = _publish_event(make_run, publish, assertion)["recent_developments"][0]
    assert event["state"] == "supported"
    assert event["value"]["title"] == r'A"B\C'
