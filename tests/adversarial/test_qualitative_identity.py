"""Bounded qualitative identity and current-assertion publication controls."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import HttpUrl

from company_bi.models import CompanyResearchRun


def _candidate(value: str | list[str], excerpt: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "evidence": [{"source_id": "page", "excerpt": excerpt}],
    }


@pytest.mark.parametrize(
    ("quote", "field", "value"),
    [
        (
            "Example sp. z o.o. is a leader in the production of measuring instruments "
            "and accessories for the power industry, electrical engineering, industry, "
            "and telecommunications.",
            "business_description",
            "production of measuring instruments and accessories",
        ),
        (
            "Example sp. z o.o. focuses on providing a wide range of proprietary IT "
            "solutions and services.",
            "business_description",
            "proprietary IT solutions and services",
        ),
        (
            "Example sp. z o.o. offers a wide range of products, including meters, "
            "analyzers, and thermal imaging cameras.",
            "products_services",
            ["meters", "analyzers", "thermal imaging cameras"],
        ),
        (
            "Example sp. z o.o. serves power industry, electrical engineering, "
            "industry, and telecommunications.",
            "industries",
            ["power industry", "electrical engineering", "industry", "telecommunications"],
        ),
        (
            "Example sp. z o.o. provides meters.",
            "products_services",
            ["meters"],
        ),
    ],
)
def test_former_qualitative_positives_are_out_of_contract_true(
    make_run: Any, publish: Any, quote: str, field: str, value: Any
) -> None:
    """OUT_OF_CONTRACT_TRUE: retain true research claims, but abstain outside the grammar."""
    fact = publish(make_run(quote, **{field: _candidate(value, quote)}))[field]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


@pytest.mark.parametrize(
    ("quote", "phrase"),
    [
        (
            "Example sp. z o.o. does not provide electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "Acme Ltd manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "Example sp. z o.o. manufactures electrical safety meters.",
            "gas detectors",
        ),
    ],
)
def test_wrong_entity_and_mismatched_label_remain_unsafe(
    make_run: Any, publish: Any, quote: str, phrase: str
) -> None:
    fact = publish(make_run(quote, products_services=_candidate([phrase], quote)))[
        "products_services"
    ]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


def test_extra_sentence_is_out_of_contract_true(make_run: Any, publish: Any) -> None:
    quote = "Example sp. z o.o. offers meters. Example sp. z o.o. provides analyzers."
    fact = publish(make_run(quote, products_services=_candidate(["meters"], quote)))[
        "products_services"
    ]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


def test_footer_identity_does_not_attach_first_person_testimonial(
    make_run: Any, publish: Any
) -> None:
    quote = (
        "Example sp. z o.o. NIP 1234563218. Customer testimonial: "
        "We manufacture electrical safety meters."
    )
    fact = publish(
        make_run(
            quote,
            products_services=_candidate(["electrical safety meters"], quote),
        )
    )["products_services"]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


def test_positive_owner_context_does_not_override_extra_denial(make_run: Any, publish: Any) -> None:
    """UNSAFE_NEGATIVE: an explicit denial in the full source blocks support."""
    quote = "Example sp. z o.o. does not provide meters. Example sp. z o.o. provides meters."
    fact = publish(make_run(quote, products_services=_candidate(["meters"], quote)))[
        "products_services"
    ]
    assert fact["state"] == "uncertain"


def test_candidate_cannot_combine_entity_and_claim_from_different_contexts(
    make_run: Any, publish: Any
) -> None:
    quote = (
        "Example sp. z o.o. does not provide meters. "
        "Acme Ltd sells sensors. The company provides meters."
    )
    fact = publish(make_run(quote, products_services=_candidate(["meters"], quote)))[
        "products_services"
    ]
    assert fact["state"] == "uncertain"


def test_every_catalog_item_requires_its_own_complete_quoted_assertion(
    make_run: Any, publish: Any
) -> None:
    first = 'Example sp. z o.o. offers "meters".'
    second = 'Example sp. z o.o. plans to offer "analyzers".'
    quote = f"{first} {second}"
    fact = publish(
        make_run(
            quote,
            products_services={
                "state": "supported",
                "value": ["meters", "analyzers"],
                "evidence": [{"source_id": "page", "excerpt": quote}],
            },
        )
    )["products_services"]
    assert fact["state"] == "uncertain"
    assert fact["value"] is None


def test_catalog_values_accept_distinct_exact_citations(make_run: Any, publish: Any) -> None:
    first = 'Example sp. z o.o. offers "meters".'
    second = 'Example sp. z o.o. provides "analyzers".'
    run = make_run(first)
    page = run.sources[1].model_copy(update={"content": second})
    page = page.model_copy(
        update={
            "source": page.source.model_copy(
                update={"source_id": "page-2", "url": HttpUrl("https://page-2.example/")}
            )
        }
    )
    payload = run.model_dump(mode="python")
    payload["sources"].append(page.model_dump(mode="python"))
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["meters", "analyzers"],
        "evidence": [
            {"source_id": "page", "excerpt": first},
            {"source_id": "page-2", "excerpt": second},
        ],
    }
    run = CompanyResearchRun.model_validate(payload)
    fact = publish(run)["products_services"]
    assert fact["state"] == "supported"
    assert fact["value"] == ["meters", "analyzers"]
    assert {ref["source_id"] for ref in fact["evidence"]} == {"page", "page-2"}


def test_quoted_business_label_matches_complete_production(make_run: Any, publish: Any) -> None:
    quote = 'Example sp. z o.o. operates as "a manufacturer of instruments".'
    fact = publish(
        make_run(
            quote,
            business_description=_candidate("a manufacturer of instruments", quote),
        )
    )["business_description"]
    assert fact["state"] == "supported"
    assert fact["value"] == "a manufacturer of instruments"
