from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from company_bi.evidence import build_profile
from company_bi.models import (
    CompanyIdentity,
    CompanyResearchDraft,
    CompanyResearchRun,
    EvidenceRef,
    ResearchDiagnostics,
    RetrievedSource,
    Source,
)

_NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)
_NIP = "1234567890"


def _source(source_id: str, title: str) -> Source:
    return Source(
        source_id=source_id,
        url=f"https://{source_id}.example/",
        title=title,
        retrieved_at=datetime(2026, 10, 2, 12, tzinfo=UTC),
    )


def _run(
    content: str,
    *,
    employee: dict | None = None,
    financials: list[dict] | None = None,
) -> CompanyResearchRun:
    registry = RetrievedSource(
        source=_source("registry", "Official register"),
        kind="registry",
        content='Registry identity: "Example sp. z o.o."',
        fetch_mode="registry",
    )
    page = RetrievedSource(
        source=_source("page", "Company page"),
        kind="full_page",
        content=content,
        fetch_mode="static",
    )
    identity = CompanyIdentity.model_validate(
        {
            "nip": _NIP,
            "legal_name": {
                "state": "supported",
                "value": "Example sp. z o.o.",
                "evidence": [{"source_id": "registry", "excerpt": '"Example sp. z o.o."'}],
            },
            "krs": {"state": "unknown", "reason": "Not provided by register"},
            "regon": {"state": "unknown", "reason": "Not provided by register"},
            "registered_city": {"state": "unknown", "reason": "Not separately provided"},
            "registered_address": {
                "state": "unknown",
                "reason": "No address evidence in test register",
            },
            "website": {"state": "unknown", "reason": "Not provided by register"},
            "resolved_at": datetime(2026, 10, 2, 12, tzinfo=UTC),
        }
    )
    unknown = {"state": "unknown", "reason": "No researched evidence"}
    draft = CompanyResearchDraft.model_validate(
        {
            "business_description": unknown,
            "products_services": unknown,
            "industries": unknown,
            "markets": unknown,
            "employees": employee or unknown,
            "financials": financials
            or [{**unknown, "metric": "revenue"}, {**unknown, "metric": "net_result"}],
            "recent_developments": [],
            "limitations": ["Other requested facts were not established"],
        }
    )
    return CompanyResearchRun(
        identity=identity,
        draft=draft,
        sources=[registry, page],
        diagnostics=ResearchDiagnostics(
            model="offline-test",
            status="completed",
            model_requests=0,
            searches=0,
            page_reads=1,
            dynamic_reads=0,
            output_retries=0,
            input_tokens=0,
            output_tokens=0,
            duration_seconds=0,
        ),
        generated_at=_NOW,
    )


def _draft_with(run: CompanyResearchRun, **updates: object) -> CompanyResearchDraft:
    payload = run.draft.model_dump(mode="python")
    payload.update(updates)
    return CompanyResearchDraft.model_validate(payload)


def test_exact_employee_observation_and_optional_identifiers() -> None:
    quote = "Example sp. z o.o. employs 120 employees as of 2026-09-01."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "as_of": "2026-09-01",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run)
    assert result.employees.state == "supported" and result.employees.value.count == 120
    assert result.identity.krs.state == "unknown"
    assert result.identity.model_dump() == run.identity.model_dump()


def test_employee_as_of_does_not_inherit_source_publication_date() -> None:
    quote = "Example sp. z o.o. employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "as_of": "2026-10-01",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    page = run.sources[1]
    dated_page = page.model_copy(
        update={"source": page.source.model_copy(update={"published_on": date(2026, 10, 1)})}
    )
    result = build_profile(run.model_copy(update={"sources": [run.sources[0], dated_page]}))
    assert result.employees.state == "supported"
    assert result.employees.value.count == 120 and result.employees.as_of is None


def test_employee_as_of_survives_explicitly_dated_employee_sentence() -> None:
    quote = "As of 2026-10-01, Example sp. z o.o. employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "as_of": "2026-10-01",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run)
    assert result.employees.state == "supported"
    assert result.employees.as_of == date(2026, 10, 1)


def test_uncertain_employee_also_drops_unverified_as_of_date() -> None:
    quote = "Example sp. z o.o. employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "uncertain",
            "value": {"kind": "exact", "count": 120},
            "as_of": "2026-10-01",
            "evidence": [{"source_id": "page", "excerpt": quote}],
            "reason": "Candidate count needs review",
        },
    )
    page = run.sources[1]
    dated_page = page.model_copy(
        update={"source": page.source.model_copy(update={"published_on": date(2026, 10, 1)})}
    )
    result = build_profile(run.model_copy(update={"sources": [run.sources[0], dated_page]}))
    assert result.employees.state == "uncertain"
    assert result.employees.value.count == 120 and result.employees.as_of is None


@pytest.mark.parametrize(
    "excerpt",
    [
        "Example sp. z o.o. employs … employees.",
        "Example sp. z o.o. employees 120.",
    ],
)
def test_model_ellipsis_and_altered_quote_structure_are_not_repaired(excerpt: str) -> None:
    quote = "Example sp. z o.o. employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": excerpt}],
        },
    )
    assert build_profile(run).employees.state == "uncertain"


def test_employee_quantity_and_range_bounds_must_match() -> None:
    quote = "Example sp. z o.o. employs 51 to 200 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "range", "minimum": 51, "maximum": 201},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    assert build_profile(run).employees.state == "uncertain"


@pytest.mark.parametrize(
    ("phrase", "minimum", "maximum", "supported"),
    [
        ("at least 100", 100, None, True),
        ("over 100", 101, None, True),
        ("at most 100", None, 100, True),
        ("fewer than 100", None, 99, True),
        ("up to 100", None, 100, True),
        ("at most 100", 100, None, False),
        ("at least 100", None, 100, False),
        ("about 100", 100, None, False),
        ("exactly 100", 100, None, False),
    ],
)
def test_employee_qualified_bounds_preserve_direction(
    phrase: str, minimum: int | None, maximum: int | None, supported: bool
) -> None:
    quote = f"Example sp. z o.o. employs {phrase} employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "range", "minimum": minimum, "maximum": maximum},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    fact = build_profile(run).employees
    assert fact.state == ("supported" if supported else "uncertain")


def test_conflicting_employee_observations_are_retained_without_selection() -> None:
    first, second = (
        "Example sp. z o.o. employs 120 employees.",
        "Example sp. z o.o. employs 240 employees.",
    )
    run = _run(
        first + " " + second,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [
                {"source_id": "page", "excerpt": first},
                {"source_id": "page", "excerpt": second},
            ],
        },
    )
    fact = build_profile(run).employees
    assert fact.state == "uncertain" and fact.value is None and len(fact.evidence) >= 2


def test_uncited_conflicting_employee_observation_is_retained_as_evidence() -> None:
    cited = "Example sp. z o.o. employs 120 employees."
    alternative = "Example sp. z o.o. employs 240 employees."
    run = _run(cited + " " + alternative)
    draft = _draft_with(
        run,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": cited}],
        },
    )
    fact = build_profile(run.model_copy(update={"draft": draft})).employees
    assert fact.state == "uncertain" and fact.value is None
    assert any(ref.excerpt == alternative for ref in fact.evidence)


def test_snippet_only_claim_is_downgraded() -> None:
    quote = "Example sp. z o.o. employs 120 employees."
    run = _run(quote)
    snippet = RetrievedSource(
        source=_source("snippet", "Search result"),
        kind="search_snippet",
        content=quote,
        fetch_mode="tavily",
    )
    draft = _draft_with(
        run,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "snippet", "excerpt": quote}],
        },
    )
    run = run.model_copy(update={"draft": draft, "sources": [*run.sources, snippet]})
    assert build_profile(run).employees.state == "uncertain"


def test_unknown_source_id_fails_explicitly() -> None:
    quote = "Example sp. z o.o. employs 120 employees."
    run = _run(quote)
    draft = _draft_with(
        run,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "missing", "excerpt": quote}],
        },
    )
    with pytest.raises(ValueError):
        build_profile(run.model_copy(update={"draft": draft}))


def test_qualitative_claim_requires_its_own_lexical_support() -> None:
    quote = "Example sp. z o.o. provides cloud accounting software to customers."
    run = _run(quote)
    draft = _draft_with(
        run,
        business_description={
            "state": "supported",
            "value": "Example manufactures electric aircraft",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    fact = build_profile(run.model_copy(update={"draft": draft})).business_description
    assert fact.state == "uncertain"


def test_nonregistry_identity_evidence_is_rejected() -> None:
    run = _run("Example sp. z o.o. employs 120 employees.")
    legal_name = run.identity.legal_name.model_copy(
        update={"evidence": [EvidenceRef(source_id="page", excerpt="Example sp. z o.o.")]}
    )
    identity = run.identity.model_copy(update={"legal_name": legal_name})
    with pytest.raises(ValueError):
        build_profile(run.model_copy(update={"identity": identity}))


def test_financial_context_and_amount_are_verified_with_zero_preserved() -> None:
    quote = (
        "Example sp. z o.o. reported standalone net result of PLN 0 units for "
        "2025-01-01 to 2025-12-31."
    )
    rows = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        {
            "state": "supported",
            "value": "0",
            "metric": "net_result",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "currency": "PLN",
            "unit": "units",
            "scope": "legal_entity",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    ]
    assert build_profile(_run(quote, financials=rows)).financials[1].state == "supported"
    wrong = [rows[0], dict(rows[1], value="9")]
    result = build_profile(_run(quote, financials=wrong)).financials[1]
    assert result.state == "uncertain" and result.value is None


def test_wrong_financial_metric_scope_or_reporting_interval_is_downgraded() -> None:
    quote = (
        "Example sp. z o.o. reported standalone revenue of PLN 12 thousand for "
        "2025-01-01 to 2025-12-31."
    )
    base = {
        "state": "supported",
        "value": "12",
        "metric": "revenue",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "thousands",
        "scope": "legal_entity",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }
    unknown_revenue = {"state": "unknown", "reason": "No revenue", "metric": "revenue"}
    unknown_net = {"state": "unknown", "reason": "No net result", "metric": "net_result"}
    cases = [
        ([unknown_revenue, dict(base, metric="net_result")], 1),
        ([dict(base, scope="group", group_name="Example Group"), unknown_net], 0),
        ([dict(base, period={"start": "2024-01-01", "end": "2024-12-31"}), unknown_net], 0),
    ]
    for rows, index in cases:
        assert build_profile(_run(quote, financials=rows)).financials[index].state == "uncertain"
    no_dates = "Example sp. z o.o. reported standalone revenue of PLN 12 thousand."
    assert (
        build_profile(_run(no_dates, financials=[base, unknown_net])).financials[0].state
        == "uncertain"
    )


def test_page_entity_must_match_registry_identity() -> None:
    quote = "Other Company employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    assert build_profile(run).employees.state == "uncertain"


def test_article_about_another_company_is_not_supported_by_footer_identity() -> None:
    quote = "Other Company employs 100 employees. Example sp. z o.o. is listed in the page footer."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 100},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run).employees
    assert result.state == "uncertain" and result.value is None


def test_nearby_resolved_company_heading_can_anchor_pronoun_employee_count() -> None:
    quote = (
        "Example sp. z o.o. is a software company. The company employs 2,465 people "
        "as of 2026-09-01."
    )
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 2465},
            "as_of": "2026-09-01",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    assert build_profile(run).employees.state == "supported"


def test_registry_only_material_cannot_support_researched_employee_claim() -> None:
    run = _run(
        "Example sp. z o.o. employs 120 employees.",
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "registry", "excerpt": '"Example sp. z o.o."'}],
        },
    )
    assert build_profile(run).employees.state == "uncertain"


def test_nfc_and_collapsed_whitespace_are_only_quote_normalization() -> None:
    content, excerpt = (
        "Example sp. z o.o. employs 120 employees in Łódź.",
        "Example sp. z o.o.\nemploys 120 employees in Ło\u0301dz\u0301.",
    )
    run = _run(
        content,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": excerpt}],
        },
    )
    assert build_profile(run).employees.state == "supported"


def test_news_publication_metadata_and_occurrence_date_are_separate() -> None:
    quote = "Example sp. z o.o. opened a new factory on 2026-09-10."
    event = {
        "state": "supported",
        "value": {
            "title": "Example opened a new factory",
            "summary": "Example opened a new factory",
            "published_on": "2026-09-20",
            "occurred_on": "2026-09-10",
        },
        "evidence": [{"source_id": "news", "excerpt": quote}],
    }
    run = _run(quote)
    news_source = Source(
        source_id="news",
        url="https://news.example/",
        title="News report",
        retrieved_at=datetime(2026, 10, 2, 12, tzinfo=UTC),
        published_on=date(2026, 9, 20),
    )
    news = RetrievedSource(source=news_source, kind="full_page", content=quote, fetch_mode="static")
    draft = _draft_with(run, recent_developments=[event])
    run = run.model_copy(update={"draft": draft, "sources": [*run.sources, news]})
    assert build_profile(run).recent_developments[0].state == "supported"


def test_news_without_separately_supported_publication_date_is_downgraded() -> None:
    quote = "Example sp. z o.o. opened a new factory on 2026-09-10."
    event = {
        "state": "supported",
        "value": {
            "title": "Example opened a new factory",
            "summary": "Example opened a new factory",
            "published_on": "2026-09-20",
            "occurred_on": "2026-09-10",
        },
        "evidence": [{"source_id": "news", "excerpt": quote}],
    }
    run = _run(quote)
    news = RetrievedSource(
        source=_source("news", "News report"), kind="full_page", content=quote, fetch_mode="static"
    )
    draft = _draft_with(run, recent_developments=[event])
    result = build_profile(
        run.model_copy(
            update={
                "draft": draft,
                "sources": [*run.sources, news],
            }
        )
    ).recent_developments[0]
    assert result.state == "uncertain" and result.value is None


def test_country_in_legal_name_does_not_support_a_market_claim() -> None:
    quote = "Example Poland S.A. serves customers in Germany."
    run = _run(quote)
    registry = run.sources[0].model_copy(
        update={"content": "Registry identity: Example Poland S.A."}
    )
    legal_name = run.identity.legal_name.model_copy(
        update={
            "value": "Example Poland S.A.",
            "evidence": [EvidenceRef(source_id="registry", excerpt="Example Poland S.A.")],
        }
    )
    identity = run.identity.model_copy(update={"legal_name": legal_name})
    draft = _draft_with(
        run,
        markets={
            "state": "supported",
            "value": ["Poland"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(
        run.model_copy(
            update={
                "identity": identity,
                "draft": draft,
                "sources": [registry, run.sources[1]],
            }
        )
    )
    assert result.markets.state == "uncertain"


def test_negated_product_statement_does_not_support_positive_catalog_item() -> None:
    quote = "Example sp. z o.o. does not sell pumps."
    run = _run(quote)
    draft = _draft_with(
        run,
        products_services={
            "state": "supported",
            "value": ["pumps"],
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run.model_copy(update={"draft": draft}))
    assert result.products_services.state == "uncertain"


def test_registry_identity_conflict_remains_visible_and_immutable() -> None:
    run = _run("Example sp. z o.o. employs 120 employees.")
    conflict = run.identity.krs.model_copy(
        update={
            "state": "uncertain",
            "evidence": [EvidenceRef(source_id="registry", excerpt='"Example sp. z o.o."')],
            "reason": "Conflicting KRS references",
        }
    )
    identity = run.identity.model_copy(update={"krs": conflict})
    result = build_profile(run.model_copy(update={"identity": identity}))
    assert result.identity.krs.state == "uncertain"
    assert result.identity.krs.evidence == conflict.evidence


def test_og152_asseco_style_search_snippet_is_provenance_not_support() -> None:
    quote = "ASSECO POLAND S.A. employs 2,465 employees."
    run = _run(quote)
    registry = run.sources[0].model_copy(
        update={"content": "Registry identity: ASSECO POLAND S.A."}
    )
    legal_name = run.identity.legal_name.model_copy(
        update={
            "value": "ASSECO POLAND S.A.",
            "evidence": [EvidenceRef(source_id="registry", excerpt="ASSECO POLAND S.A.")],
        }
    )
    identity = run.identity.model_copy(update={"legal_name": legal_name})
    snippet = run.sources[1].model_copy(update={"kind": "search_snippet"})
    draft = _draft_with(
        run,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 2465},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(
        run.model_copy(
            update={
                "identity": identity,
                "draft": draft,
                "sources": [registry, snippet],
            }
        )
    )
    assert result.employees.state == "uncertain"
    assert (
        next(source for source in result.sources if source.source_id == "page").kind
        == "search_snippet"
    )


def test_over_100_employees_is_not_an_exact_count_of_100() -> None:
    quote = "Example sp. z o.o. employs over 100 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 100},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run).employees
    assert result.state == "uncertain" and result.value is None


def test_operating_profit_is_not_net_result() -> None:
    quote = (
        "Example sp. z o.o. reported standalone operating profit of PLN 12 thousand "
        "for 2025-01-01 to 2025-12-31."
    )
    rows = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        {
            "state": "supported",
            "value": "12",
            "metric": "net_result",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "currency": "PLN",
            "unit": "thousands",
            "scope": "legal_entity",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    ]
    result = build_profile(_run(quote, financials=rows)).financials[1]
    assert result.state == "uncertain" and result.value is None


def test_revenue_amount_cannot_be_reused_as_net_result_amount() -> None:
    quote = (
        "Example sp. z o.o. reported standalone revenue of PLN 12 thousand "
        "and net result of PLN 20 thousand for 2025-01-01 to 2025-12-31."
    )
    rows = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        {
            "state": "supported",
            "value": "12",
            "metric": "net_result",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "currency": "PLN",
            "unit": "thousands",
            "scope": "legal_entity",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    ]
    result = build_profile(_run(quote, financials=rows)).financials[1]
    assert result.state == "uncertain" and result.value is None


def test_date_digits_cannot_substitute_for_a_missing_financial_amount() -> None:
    quote = (
        "Example sp. z o.o. reported standalone net result in PLN millions "
        "for 2025-01-01 to 2025-12-31 with no figure disclosed."
    )
    rows = [
        {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
        {
            "state": "supported",
            "value": "12",
            "metric": "net_result",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "currency": "PLN",
            "unit": "millions",
            "scope": "legal_entity",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    ]
    result = build_profile(_run(quote, financials=rows)).financials[1]
    assert result.state == "uncertain" and result.value is None


def test_same_metric_financial_conflict_retains_both_citations_without_selection() -> None:
    first = (
        "Example sp. z o.o. reported standalone revenue of PLN 12 thousand for "
        "2025-01-01 to 2025-12-31."
    )
    second = (
        "Example sp. z o.o. reported standalone revenue of PLN 20 thousand for "
        "2025-01-01 to 2025-12-31."
    )
    run = _run(first + " " + second)
    draft = _draft_with(
        run,
        financials=[
            {
                "state": "supported",
                "value": "12",
                "metric": "revenue",
                "period": {"start": "2025-01-01", "end": "2025-12-31"},
                "currency": "PLN",
                "unit": "thousands",
                "scope": "legal_entity",
                "evidence": [
                    {"source_id": "page", "excerpt": first},
                    {"source_id": "page", "excerpt": second},
                ],
            },
            {"state": "unknown", "reason": "No net result", "metric": "net_result"},
        ],
    )
    result = build_profile(run.model_copy(update={"draft": draft})).financials[0]
    assert result.state == "uncertain" and result.value is None
    assert len(result.evidence) == 2


def test_different_explicit_nip_blocks_claim_attribution() -> None:
    quote = "Example sp. z o.o. (NIP 9999999999) employs 120 employees."
    run = _run(
        quote,
        employee={
            "state": "supported",
            "value": {"kind": "exact", "count": 120},
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run).employees
    assert result.state == "uncertain" and result.value is None


def test_occurrence_date_alone_does_not_establish_news_publication_date() -> None:
    quote = "Example sp. z o.o. opened a factory on 2026-09-20."
    event = {
        "state": "supported",
        "value": {
            "title": "Example opened a factory",
            "summary": "Example opened a factory",
            "published_on": "2026-09-20",
            "occurred_on": "2026-09-20",
        },
        "evidence": [{"source_id": "news", "excerpt": quote}],
    }
    run = _run(quote)
    draft = _draft_with(run, recent_developments=[event])
    news = RetrievedSource(
        source=_source("news", "News report"),
        kind="full_page",
        content=quote,
        fetch_mode="static",
    )
    result = build_profile(
        run.model_copy(update={"draft": draft, "sources": [*run.sources, news]})
    ).recent_developments[0]
    assert result.state == "uncertain" and result.value is None


def test_month_only_event_occurrence_does_not_become_first_of_month() -> None:
    quote = "In July this year Example sp. z o.o. launched a new distribution centre."
    run = _run(quote)
    page = RetrievedSource(
        source=_source("news", "News report").model_copy(
            update={"published_on": date(2026, 8, 15)}
        ),
        kind="full_page",
        content=quote,
        fetch_mode="static",
    )
    draft = _draft_with(
        run,
        recent_developments=[
            {
                "state": "supported",
                "value": {
                    "title": "Example launched a new distribution centre",
                    "summary": "Example launched a new distribution centre",
                    "published_on": "2026-08-15",
                    "occurred_on": "2026-07-01",
                },
                "evidence": [{"source_id": "news", "excerpt": quote}],
            }
        ],
    )
    result = build_profile(
        run.model_copy(update={"draft": draft, "sources": [*run.sources, page]})
    ).recent_developments[0]
    assert result.state == "supported"
    assert result.value.occurred_on is None


def test_publication_date_does_not_become_event_occurrence_date() -> None:
    quote = "Published on 2026-07-01: Example sp. z o.o. launched a new distribution centre."
    run = _run(quote)
    page = RetrievedSource(
        source=_source("news", "News report").model_copy(update={"published_on": date(2026, 7, 1)}),
        kind="full_page",
        content=quote,
        fetch_mode="static",
    )
    draft = _draft_with(
        run,
        recent_developments=[
            {
                "state": "supported",
                "value": {
                    "title": "Example launched a new distribution centre",
                    "summary": "Example launched a new distribution centre",
                    "published_on": "2026-07-01",
                    "occurred_on": "2026-07-01",
                },
                "evidence": [{"source_id": "news", "excerpt": quote}],
            }
        ],
    )
    result = build_profile(
        run.model_copy(update={"draft": draft, "sources": [*run.sources, page]})
    ).recent_developments[0]
    assert result.state == "supported"
    assert result.value.occurred_on is None


def test_uncertain_event_drops_unverified_publication_and_occurrence_dates() -> None:
    quote = "In July this year Example sp. z o.o. launched a new distribution centre."
    run = _run(quote)
    page = RetrievedSource(
        source=_source("news", "News report"),
        kind="full_page",
        content=quote,
        fetch_mode="static",
    )
    draft = _draft_with(
        run,
        recent_developments=[
            {
                "state": "uncertain",
                "value": {
                    "title": "Example launched a new distribution centre",
                    "summary": "Example launched a new distribution centre",
                    "published_on": "2026-08-15",
                    "occurred_on": "2026-07-01",
                },
                "evidence": [{"source_id": "news", "excerpt": quote}],
                "reason": "Candidate event needs review",
            }
        ],
    )
    result = build_profile(
        run.model_copy(update={"draft": draft, "sources": [*run.sources, page]})
    ).recent_developments[0]
    assert result.state == "uncertain" and result.value is None


def test_reordered_relation_does_not_support_qualitative_claim() -> None:
    quote = "Example sp. z o.o. transferred assets from Bob to Alice."
    run = _run(quote)
    draft = _draft_with(
        run,
        business_description={
            "state": "supported",
            "value": "Example transferred assets from Alice to Bob",
            "evidence": [{"source_id": "page", "excerpt": quote}],
        },
    )
    result = build_profile(run.model_copy(update={"draft": draft})).business_description
    assert result.state == "uncertain"


def test_financial_heading_and_amount_can_be_separate_exact_companion_citations() -> None:
    heading = "Example sp. z o.o. standalone revenue PLN thousand for 2025-01-01 to 2025-12-31."
    run = _run(heading + " 12")
    draft = _draft_with(
        run,
        financials=[
            {
                "state": "supported",
                "value": "12",
                "metric": "revenue",
                "period": {"start": "2025-01-01", "end": "2025-12-31"},
                "currency": "PLN",
                "unit": "thousands",
                "scope": "legal_entity",
                "evidence": [
                    {"source_id": "page", "excerpt": heading},
                    {"source_id": "page", "excerpt": "12"},
                ],
            },
            {"state": "unknown", "reason": "No net result", "metric": "net_result"},
        ],
    )
    result = build_profile(run.model_copy(update={"draft": draft})).financials[0]
    assert result.state == "supported" and result.value == Decimal("12")
