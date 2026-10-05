"""Bounded qualitative identity and current-assertion publication controls."""

from __future__ import annotations

from typing import Any

import pytest


def _candidate(value: str | list[str], excerpt: str) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "evidence": [{"source_id": "page", "excerpt": excerpt}],
    }


@pytest.mark.parametrize(
    ("identity", "quote", "field", "value"),
    [
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. is a leader in the production of measuring instruments "
            "and accessories for the power industry, electrical engineering, "
            "industry, and telecommunications.",
            "business_description",
            "production of measuring instruments and accessories",
        ),
        (
            '"ASSECO POLAND" SPÓŁKA AKCYJNA',
            "The activities of the Asseco Poland S.A focus on "
            "providing a wide range of proprietary IT solutions and services.",
            "business_description",
            "The activities of the Asseco Poland S.A focus on "
            "providing a wide range of proprietary IT solutions and services.",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. is a leader in the production of measuring instruments "
            "and accessories for the power industry, electrical engineering, "
            "industry, and telecommunications. The company offers a wide range "
            "of products, including meters, analyzers, and thermal imaging cameras.",
            "products_services",
            ["meters", "analyzers", "thermal imaging cameras"],
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. is a leader in the production of measuring instruments "
            "and accessories for the power industry, electrical engineering, "
            "industry, and telecommunications.",
            "industries",
            [
                "power industry",
                "electrical engineering",
                "industry",
                "telecommunications",
            ],
        ),
        (
            "Example spółka komandytowa",
            "Example sp.k. provides meters.",
            "products_services",
            ["meters"],
        ),
    ],
)
def test_legal_form_equivalent_bounded_current_assertions_publish(
    make_run: Any,
    publish: Any,
    identity: str,
    quote: str,
    field: str,
    value: Any,
) -> None:
    fact = publish(
        make_run(
            quote,
            identity_name=identity,
            **{field: _candidate(value, quote)},
        )
    )[field]
    assert fact["state"] == "supported"
    assert fact["value"] == value


def test_production_wording_does_not_publish_leadership_claim(make_run: Any, publish: Any) -> None:
    quote = (
        "Sonel S.A. is a leader in the production of measuring instruments "
        "and accessories for the power industry, electrical engineering, "
        "industry, and telecommunications."
    )
    production = publish(
        make_run(
            quote,
            identity_name="SONEL SPÓŁKA AKCYJNA",
            business_description=_candidate(
                "production of measuring instruments and accessories", quote
            ),
        )
    )["business_description"]
    leadership = publish(
        make_run(
            quote,
            identity_name="SONEL SPÓŁKA AKCYJNA",
            business_description=_candidate(
                "leader in the production of measuring instruments and accessories",
                quote,
            ),
        )
    )["business_description"]
    assert production["state"] == "supported"
    assert production["value"] == ("production of measuring instruments and accessories")
    assert leadership["state"] == "uncertain"


@pytest.mark.parametrize(
    ("identity", "quote", "phrase"),
    [
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel sp. z o.o. manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "Example spółka komandytowa",
            "Example sp. k.a. provides meters.",
            "meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonex S.A. manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. NIP 1111111111 manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "The competitor Sonel S.A. manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "The Sonel Group manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. has never offered electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. no longer manufactures electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. plans to manufacture electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. formerly manufactured electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A.'s strategy is to provide electrical safety meters.",
            "electrical safety meters",
        ),
        (
            "SONEL SPÓŁKA AKCYJNA",
            "Sonel S.A. welcomes visitors. Acme Ltd manufactures electrical safety meters.",
            "electrical safety meters",
        ),
    ],
)
def test_ambiguous_or_noncurrent_company_claims_do_not_publish(
    make_run: Any, publish: Any, identity: str, quote: str, phrase: str
) -> None:
    fact = publish(
        make_run(
            quote,
            identity_name=identity,
            products_services=_candidate([phrase], quote),
        )
    )["products_services"]
    assert fact["state"] == "uncertain"


def test_footer_identity_does_not_attach_first_person_testimonial(
    make_run: Any, publish: Any
) -> None:
    quote = (
        "SONEL S.A. NIP 1234563218. Customer testimonial: We manufacture electrical safety meters."
    )
    fact = publish(
        make_run(
            quote,
            identity_name="SONEL SPÓŁKA AKCYJNA",
            products_services=_candidate(["electrical safety meters"], quote),
        )
    )["products_services"]
    assert fact["state"] == "uncertain"


def test_repeated_quote_uses_matching_positive_owner_context(make_run: Any, publish: Any) -> None:
    quote = "Example sp. z o.o. does not provide meters. Example sp. z o.o. provides meters."
    fact = publish(
        make_run(
            quote,
            products_services=_candidate(["meters"], "meters"),
        )
    )["products_services"]
    assert fact["state"] == "supported"


def test_repeated_quote_cannot_combine_entity_and_claim_from_different_contexts(
    make_run: Any, publish: Any
) -> None:
    quote = (
        "Example sp. z o.o. does not provide meters. "
        "Acme Ltd sells sensors. The company provides meters."
    )
    fact = publish(
        make_run(
            quote,
            products_services=_candidate(["meters"], "meters"),
        )
    )["products_services"]
    assert fact["state"] == "uncertain"


def test_each_catalog_value_requires_its_own_exact_quote(make_run: Any, publish: Any) -> None:
    quote = "Sonel S.A. offers meters. The company plans to offer analyzers."
    fact = publish(
        make_run(
            quote,
            identity_name="SONEL SPÓŁKA AKCYJNA",
            products_services=_candidate(
                ["meters", "analyzers"],
                "Sonel S.A. offers meters.",
            ),
        )
    )["products_services"]
    assert fact["state"] == "uncertain"


def test_atomic_catalog_values_accept_distinct_exact_citations(make_run: Any, publish: Any) -> None:
    first = "Example sp. z o.o. offers meters."
    second = "The company provides analyzers."
    fact = publish(
        make_run(
            f"{first} {second}",
            products_services={
                "state": "supported",
                "value": ["meters", "analyzers"],
                "evidence": [
                    {"source_id": "page", "excerpt": first},
                    {"source_id": "page", "excerpt": second},
                ],
            },
        )
    )["products_services"]
    assert fact["state"] == "supported"
    assert fact["value"] == ["meters", "analyzers"]
