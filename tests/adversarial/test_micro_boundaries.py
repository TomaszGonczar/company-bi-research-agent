"""Micro-corrections for registry text fidelity and discovery ownership."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import HttpUrl, ValidationError

from company_bi.evidence import build_profile
from company_bi.models import CompanyIdentity, CompanyResearchRun, RetrievedSource, Source
from company_bi.sources import SourceStore

STAMP = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _ref(source_id: str, excerpt: str) -> dict[str, str]:
    return {"source_id": source_id, "excerpt": excerpt}


def _registry_payload(make_run: Any) -> dict[str, Any]:
    return make_run("Example sp. z o.o. provides industrial packaging.").model_dump(mode="python")


def _mapped_identity_case(make_run: Any, *, strip_quotes: bool = False) -> dict[str, Any]:
    payload = _registry_payload(make_run)
    name = '"Example sp. z o.o."'
    address = '"ul. Główna 1, Warszawa"'
    subject = {"name": name, "nip": "1234563218", "workingAddress": address}
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = json.dumps({"result": {"subject": subject}}, ensure_ascii=False)
    payload["identity"]["legal_name"] = {
        "state": "supported",
        "value": name[1:-1] if strip_quotes else name,
        "evidence": [_ref("registry", json.dumps(name, ensure_ascii=False))],
    }
    payload["identity"]["registered_address"] = {
        "state": "supported",
        "value": address[1:-1] if strip_quotes else address,
        "evidence": [_ref("registry", json.dumps(address, ensure_ascii=False))],
    }
    return payload


@pytest.mark.parametrize("field", ["legal_name", "registered_address"])
def test_quoted_raw_registry_candidates_and_encoded_citations_pass(
    make_run: Any, publish: Any, field: str
) -> None:
    run = CompanyResearchRun.model_validate(_mapped_identity_case(make_run))
    profile = publish(run)
    assert profile["identity"][field]["state"] == "supported"
    assert profile["identity"][field]["value"] == (
        '"Example sp. z o.o."' if field == "legal_name" else '"ul. Główna 1, Warszawa"'
    )


@pytest.mark.parametrize("field", ["legal_name", "registered_address"])
def test_stripping_quotes_from_raw_registry_candidate_rejects_both_boundaries(
    make_run: Any, field: str
) -> None:
    validated = CompanyResearchRun.model_validate(_mapped_identity_case(make_run))
    with pytest.raises((ValidationError, ValueError)):
        CompanyResearchRun.model_validate(_mapped_identity_case(make_run, strip_quotes=True))
    candidate = validated.identity.model_dump(mode="python")[field]
    candidate["value"] = candidate["value"][1:-1]
    identity = CompanyIdentity.model_validate(
        {**validated.identity.model_dump(mode="python"), field: candidate}
    )
    unchecked = validated.model_copy(update={"identity": identity})
    with pytest.raises(ValueError):
        build_profile(unchecked)


@pytest.mark.parametrize(
    "json_encoded", [False, True], ids=["plain-citation", "json-string-citation"]
)
def test_normalized_registry_citations_accept_plain_or_json_string_excerpt(
    make_run: Any, json_encoded: bool
) -> None:
    payload = _registry_payload(make_run)
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = json.dumps(
        {"result": {"subject": {"name": "Café  spółka", "nip": "1234563218"}}},
        ensure_ascii=False,
    )
    excerpt = "Cafe\u0301   spółka"
    payload["identity"]["legal_name"] = {
        "state": "supported",
        "value": "Cafe\u0301 spółka",
        "evidence": [
            _ref("registry", json.dumps(excerpt, ensure_ascii=False) if json_encoded else excerpt)
        ],
    }
    run = CompanyResearchRun.model_validate(payload)
    assert run.identity.legal_name.state == "supported"


def _store_with_searches(make_run: Any, urls: list[str]) -> tuple[SourceStore, list[str]]:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    ids = [
        store.add_search(
            title=f"Discovery {index}",
            url=HttpUrl(url),
            content="Example sp. z o.o. discovery",
            score=None,
            retrieved_at=STAMP,
        ).source_id
        for index, url in enumerate(urls)
    ]
    return store, ids


@pytest.mark.parametrize("identical_content", [False, True], ids=["conflicting", "identical"])
@pytest.mark.parametrize(
    "equivalent_urls",
    [
        ("https://example.test/story#top", "https://EXAMPLE.test:443/story"),
    ],
)
def test_duplicate_normalized_discovery_owner_with_distinct_ids_rejects_both_boundaries(
    make_run: Any, identical_content: bool, equivalent_urls: tuple[str, str]
) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    owner_urls = list(equivalent_urls)
    first = store.add_search(
        title="First discovery",
        url=HttpUrl(owner_urls[0]),
        content="first",
        score=None,
        retrieved_at=STAMP,
    )
    base = store.snapshots()
    first_snippet = next(item for item in base if item.kind == "search_snippet")
    second = store.add_search(
        title="Second discovery",
        url=HttpUrl("https://second.example/original"),
        content="same" if identical_content else "different",
        score=None,
        retrieved_at=STAMP,
    )
    second_snippet_original = next(
        item
        for item in store.snapshots()
        if item.kind == "search_snippet" and item.source.source_id == second.source_id
    )
    second_snippet = second_snippet_original.model_copy(
        update={
            "source": second_snippet_original.source.model_copy(
                update={"url": HttpUrl(owner_urls[1])}
            )
        }
    )
    first_page = RetrievedSource(
        source=Source(
            source_id=first.source_id,
            url=first_snippet.source.url,
            title=first_snippet.source.title,
            retrieved_at=STAMP,
        ),
        kind="full_page",
        fetch_mode="static",
        content="same page" if identical_content else "first page",
    )
    second_page = RetrievedSource(
        source=Source(
            source_id=second.source_id,
            url=HttpUrl("https://second.example/original"),
            title=second_snippet.source.title,
            retrieved_at=STAMP,
        ),
        kind="full_page",
        fetch_mode="static",
        content="same page" if identical_content else "second page",
    )
    store.store_page(first_page)
    store.store_page(second_page)
    second_page = second_page.model_copy(
        update={"source": second_page.source.model_copy(update={"url": HttpUrl(owner_urls[1])})}
    )
    payload = _registry_payload(make_run)
    payload["sources"] = [
        item.model_dump(mode="python") for item in [*base, second_snippet, first_page, second_page]
    ]
    with pytest.raises((ValidationError, ValueError)):
        CompanyResearchRun.model_validate(payload)
    unchecked = run.model_copy(update={"sources": [*base, second_snippet, first_page, second_page]})
    with pytest.raises(ValueError):
        build_profile(unchecked)


def test_one_discovery_with_repeated_snippets_and_one_page_passes(
    make_run: Any, publish: Any
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    url = HttpUrl("https://example.test/story")
    hit = store.add_search(
        title="Story",
        url=url,
        content='Example sp. z o.o. provides "industrial packaging".',
        score=None,
        retrieved_at=STAMP,
    )
    store.add_search(
        title="Story duplicate snippet",
        url=url,
        content='Example sp. z o.o. provides "industrial packaging".',
        score=None,
        retrieved_at=STAMP,
    )
    store.store_page(
        RetrievedSource(
            source=Source(source_id=hit.source_id, url=url, title="Story", retrieved_at=STAMP),
            kind="full_page",
            fetch_mode="static",
            content='Example sp. z o.o. provides "industrial packaging".',
        )
    )
    payload = run.model_dump(mode="python")
    payload["sources"] = [item.model_dump(mode="python") for item in store.snapshots()]
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["industrial packaging"],
        "evidence": [_ref(hit.source_id, 'Example sp. z o.o. provides "industrial packaging".')],
    }
    validated = CompanyResearchRun.model_validate(payload)
    assert publish(validated)["products_services"]["state"] == "supported"


@pytest.mark.parametrize(
    "urls",
    [
        ("https://a.example/start", "https://b.example/other"),
        ("https://a.example/story?x=1", "https://a.example/story?x=2"),
    ],
)
def test_distinct_discovery_path_or_query_is_not_duplicate_owner(
    make_run: Any, publish: Any, urls: tuple[str, str]
) -> None:
    quote = 'Example sp. z o.o. provides "industrial packaging".'
    run = make_run(quote)
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    ids = []
    for index, url in enumerate(urls):
        hit = store.add_search(
            title=f"Discovery {index}",
            url=HttpUrl(url),
            content=quote,
            score=None,
            retrieved_at=STAMP,
        )
        ids.append(hit.source_id)
        store.store_page(
            RetrievedSource(
                source=Source(
                    source_id=hit.source_id,
                    url=hit.url,
                    title=hit.title,
                    retrieved_at=STAMP,
                ),
                kind="full_page",
                fetch_mode="static",
                content=quote,
            )
        )
    payload = run.model_dump(mode="python")
    materials = store.snapshots()
    payload["sources"] = [item.model_dump(mode="python") for item in materials]
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["industrial packaging"],
        "evidence": [_ref(ids[0], quote)],
    }
    validated = CompanyResearchRun.model_validate(payload)
    assert publish(validated)["products_services"]["state"] == "supported"


def test_independent_convergent_and_direct_final_discoveries_pass(
    make_run: Any, publish: Any
) -> None:
    """Converging final URLs are legal when discovery owners differ."""
    quote = 'Example sp. z o.o. provides "industrial packaging".'
    run = make_run(quote)
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    sources = [registry]
    for source_id, start, chain in (
        ("a", "https://a.example/start", ["https://a.example/start", "https://final.example/page"]),
        (
            "self",
            "https://self.example/self",
            ["https://self.example/self", "https://self.example/self"],
        ),
        ("b", "https://b.example/other", ["https://b.example/other", "https://final.example/page"]),
        ("direct", "https://final.example/page", []),
    ):
        full = deepcopy(page)
        full["source"].update(source_id=source_id, url=chain[-1] if chain else start)
        if chain:
            full["source"]["redirect_chain"] = chain
        else:
            full["source"].pop("redirect_chain", None)
        full["content"] = quote
        sources.append(full)
        if chain:
            snippet = deepcopy(full)
            snippet["kind"] = "search_snippet"
            snippet["fetch_mode"] = "tavily"
            snippet["content"] = quote
            snippet["source"]["url"] = start
            snippet["source"]["redirect_chain"] = []
            sources.append(snippet)
    payload["sources"] = sources
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["industrial packaging"],
        "evidence": [_ref("a", quote)],
    }
    validated = CompanyResearchRun.model_validate(payload)
    assert publish(validated)["products_services"]["state"] == "supported"


def test_quarantined_employee_conflict_does_not_veto_trusted_page(
    make_run: Any, publish: Any
) -> None:
    employee_quote = "Example sp. z o.o. employs 42 people as of 2026-01-15."
    conflicting_quote = "Example sp. z o.o. employs 9 people as of 2026-01-15."
    run = make_run(
        employee_quote,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 42},
            "as_of": "2026-01-15",
            "evidence": [_ref("page", employee_quote)],
        },
    )
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    page["source"]["source_id"] = "quarantined"
    page["source"]["url"] = "https://page.example/final"
    page["source"]["publication_blocked_reason"] = "unproven_legacy_url_relationship"
    page["content"] = conflicting_quote
    snippet = deepcopy(page)
    snippet["kind"] = "search_snippet"
    snippet["fetch_mode"] = "tavily"
    snippet["source"]["url"] = "https://page.example/discovery"
    snippet["content"] = conflicting_quote
    trusted = deepcopy(page)
    trusted["source"].update(
        source_id="trusted", url="https://page.example/discovery", publication_blocked_reason=None
    )
    trusted["content"] = employee_quote
    payload["sources"].extend([snippet, trusted])
    payload["draft"]["employees"]["evidence"] = [_ref("trusted", employee_quote)]
    result = publish(CompanyResearchRun.model_validate(payload))["employees"]
    assert result["state"] == "supported"
    assert result["value"]["count"] == 42
