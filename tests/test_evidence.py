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

NOW = datetime(2026, 10, 3, 12, tzinfo=UTC)
LEGAL_NAME = "Example sp. z o.o."


def _source(source_id: str, *, published_on: date | None = None) -> Source:
    return Source(
        source_id=source_id,
        url=f"https://{source_id}.example/",
        title=source_id,
        retrieved_at=datetime(2026, 10, 2, 12, tzinfo=UTC),
        published_on=published_on,
    )


def _run(
    content: str,
    *,
    draft_changes: dict | None = None,
    legal_name: str = LEGAL_NAME,
    source_kind: str = "full_page",
    source_id: str = "page",
    published_on: date | None = None,
) -> CompanyResearchRun:
    registry_content = '{"result":{"subject":{"name":"' + legal_name + '","nip":"1234567890"}}}'
    registry = RetrievedSource(
        source=_source("registry"),
        kind="registry",
        content=registry_content,
        fetch_mode="registry",
    )
    assertion_source = RetrievedSource(
        source=_source(source_id, published_on=published_on),
        kind=source_kind,
        content=content,
        fetch_mode="static" if source_kind == "full_page" else "tavily",
    )
    identity = CompanyIdentity.model_validate(
        {
            "nip": "1234567890",
            "legal_name": {
                "state": "supported",
                "value": legal_name,
                "evidence": [{"source_id": "registry", "excerpt": legal_name}],
            },
            **{
                field: {"state": "unknown", "reason": "Not in test registry"}
                for field in (
                    "krs",
                    "regon",
                    "registered_city",
                    "registered_address",
                    "website",
                )
            },
            "resolved_at": NOW,
        }
    )
    unknown = {"state": "unknown", "reason": "No researched evidence"}
    draft = {
        "business_description": unknown,
        "products_services": unknown,
        "industries": unknown,
        "markets": unknown,
        "employees": unknown,
        "financials": [
            {**unknown, "metric": "revenue"},
            {**unknown, "metric": "net_result"},
        ],
        "recent_developments": [],
        "limitations": ["Other requested facts were not established"],
        **(draft_changes or {}),
    }
    return CompanyResearchRun(
        identity=identity,
        draft=CompanyResearchDraft.model_validate(draft),
        sources=[registry, assertion_source],
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
        generated_at=NOW,
    )


def _employee(count: int, excerpt: str, *, as_of: str | None = None) -> dict:
    return {
        "state": "supported",
        "value": {"kind": "exact", "count": count},
        "as_of": as_of,
        "evidence": [{"source_id": "page", "excerpt": excerpt}],
    }


def test_exact_employee_observation_keeps_explicit_date_and_registry_identity() -> None:
    quote = f"{LEGAL_NAME} employs 120 people as of 2026-09-01."
    result = build_profile(
        _run(quote, draft_changes={"employees": _employee(120, quote, as_of="2026-09-01")})
    )
    assert result.employees.state == "supported"
    assert result.employees.value.count == 120
    assert result.employees.as_of == date(2026, 9, 1)
    assert result.identity.legal_name.value == LEGAL_NAME


def test_employee_date_is_not_inherited_from_publication_metadata() -> None:
    quote = f"{LEGAL_NAME} employs 120 people."
    run = _run(
        quote,
        draft_changes={"employees": _employee(120, quote, as_of="2026-10-01")},
    )
    page = run.sources[1]
    dated_page = page.model_copy(
        update={"source": page.source.model_copy(update={"published_on": date(2026, 10, 1)})}
    )
    result = build_profile(run.model_copy(update={"sources": [run.sources[0], dated_page]}))
    assert result.employees.state == "supported"
    assert result.employees.value.count == 120
    assert result.employees.as_of is None


def test_employee_optional_candidate_date_is_removed_without_losing_count() -> None:
    quote = f"{LEGAL_NAME} employs 120 people as of 2026-09-01."
    result = build_profile(
        _run(quote, draft_changes={"employees": _employee(120, quote, as_of="2026-09-02")})
    )
    assert result.employees.state == "supported"
    assert result.employees.value.count == 120
    assert result.employees.as_of is None


def test_true_but_unquoted_product_label_is_out_of_contract() -> None:
    quote = f"{LEGAL_NAME} provides cloud services."
    result = build_profile(
        _run(
            quote,
            draft_changes={
                "products_services": {
                    "state": "supported",
                    "value": ["cloud services"],
                    "evidence": [{"source_id": "page", "excerpt": quote}],
                }
            },
        )
    )
    assert result.products_services.state == "uncertain"
    assert result.products_services.value is None


def test_quoted_product_label_is_opaque_and_must_match_exactly() -> None:
    quote = f'{LEGAL_NAME} provides "cloud services".'
    mismatch = build_profile(
        _run(
            quote,
            draft_changes={
                "products_services": {
                    "state": "supported",
                    "value": ["cloud"],
                    "evidence": [{"source_id": "page", "excerpt": quote}],
                }
            },
        )
    )
    assert mismatch.products_services.state == "uncertain"
    assert mismatch.products_services.value is None
    accepted = build_profile(
        _run(
            quote,
            draft_changes={
                "products_services": {
                    "state": "supported",
                    "value": ["cloud services"],
                    "evidence": [{"source_id": "page", "excerpt": quote}],
                }
            },
        )
    )
    assert accepted.products_services.state == "supported"


@pytest.mark.parametrize(
    "tail",
    [" after approval", ". Additional source sentence"],
    ids=["qualification-tail", "second-sentence"],
)
def test_product_assertion_requires_complete_source_unit(tail: str) -> None:
    quote = f'{LEGAL_NAME} provides "cloud services"{tail}.'
    result = build_profile(
        _run(
            quote,
            draft_changes={
                "products_services": {
                    "state": "supported",
                    "value": ["cloud services"],
                    "evidence": [
                        {
                            "source_id": "page",
                            "excerpt": f'{LEGAL_NAME} provides "cloud services". ',
                        }
                    ],
                }
            },
        )
    )
    assert result.products_services.state == "uncertain"
    assert result.products_services.value is None


def test_financial_assertion_is_atomic_and_preserves_explicit_zero() -> None:
    quote = (
        f"{LEGAL_NAME} reported standalone net result of PLN 0 units for 2025-01-01 to 2025-12-31."
    )
    row = {
        "state": "supported",
        "value": "0",
        "metric": "net_result",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "units",
        "scope": "legal_entity",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }
    result = build_profile(
        _run(
            quote,
            draft_changes={
                "financials": [
                    {"state": "unknown", "reason": "No revenue", "metric": "revenue"},
                    row,
                ]
            },
        )
    )
    assert result.financials[1].state == "supported"
    assert result.financials[1].value == Decimal("0")


def test_post_amount_target_tail_rejects_financial_observation() -> None:
    quote = (
        f"{LEGAL_NAME} reported standalone revenue of PLN 10 thousand "
        "for 2025-01-01 to 2025-12-31, but this was only a target."
    )
    row = {
        "state": "supported",
        "value": "10",
        "metric": "revenue",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "thousands",
        "scope": "legal_entity",
        "evidence": [{"source_id": "page", "excerpt": quote}],
    }
    result = build_profile(
        _run(
            quote,
            draft_changes={
                "financials": [
                    row,
                    {"state": "unknown", "reason": "No result", "metric": "net_result"},
                ]
            },
        )
    )
    assert result.financials[0].state == "uncertain"
    assert result.financials[0].value is None


def test_foreign_company_date_cannot_support_target_employee_fact() -> None:
    quote = "Other Company employs 84 people as of 2026-10-02."
    result = build_profile(
        _run(quote, draft_changes={"employees": _employee(84, quote, as_of="2026-10-02")})
    )
    assert result.employees.state == "uncertain"
    assert result.employees.value is None
    assert result.employees.as_of is None


def test_search_snippet_is_provenance_not_full_page_support() -> None:
    quote = f"{LEGAL_NAME} employs 84 people as of 2026-09-30."
    result = build_profile(
        _run(
            quote,
            draft_changes={"employees": _employee(84, quote, as_of="2026-09-30")},
            source_kind="search_snippet",
        )
    )
    assert result.employees.state == "uncertain"
    assert result.employees.value is None


def test_unknown_source_id_fails_explicitly() -> None:
    quote = f"{LEGAL_NAME} employs 120 people."
    run = _run(quote, draft_changes={"employees": _employee(120, quote)})
    draft = run.draft.model_copy(
        update={
            "employees": run.draft.employees.model_copy(
                update={"evidence": [EvidenceRef(source_id="missing", excerpt=quote)]}
            )
        }
    )
    with pytest.raises(ValueError):
        build_profile(run.model_copy(update={"draft": draft}))
