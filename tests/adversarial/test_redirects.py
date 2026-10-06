"""Offline redirect provenance regressions across retrieval and publication."""

from __future__ import annotations

import socket
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import HttpUrl, ValidationError
from scrapling.engines.toolbelt.custom import Response

from company_bi.fetch import read_page
from company_bi.models import CompanyResearchRun
from company_bi.sources import ResearchBudget, SourceStore


def response(
    url: str,
    *,
    status: int = 200,
    headers: dict[str, str] | None = None,
    content: str | bytes = (
        '<html><body><article>Example sp. z o.o. provides "industrial packaging".'
        "</article></body></html>"
    ),
) -> Response:
    return Response(
        url=url,
        content=content,
        status=status,
        reason="OK",
        cookies={},
        headers=headers or {"content-type": "text/html; charset=utf-8"},
        request_headers={},
    )


def public_dns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )


def page_store(make_run: Any, url: str) -> tuple[SourceStore, str]:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    hit = store.add_search(
        title="Example company",
        url=HttpUrl(url),
        content='Example sp. z o.o. provides "industrial packaging".',
        score=None,
        retrieved_at=datetime(2026, 10, 3, 12, tzinfo=UTC),
    )
    return store, hit.source_id


def validated_run(make_run: Any, store: SourceStore, source_id: str) -> CompanyResearchRun:
    materials = store.snapshots()
    page = next(item for item in materials if item.kind == "full_page")
    run = make_run(page.content)
    payload = run.model_dump(mode="python")
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["industrial packaging"],
        "evidence": [
            {
                "source_id": source_id,
                "excerpt": 'Example sp. z o.o. provides "industrial packaging".',
            }
        ],
    }
    payload["sources"] = [item.model_dump(mode="python") for item in materials]
    payload["generated_at"] = max(
        [run.generated_at, *(item.source.retrieved_at for item in materials)]
    )
    return CompanyResearchRun.model_validate(payload)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("redirects", "final_url", "expected_chain"),
    [
        pytest.param(
            [("https://example.com/start", "https://example.com/final")],
            "https://example.com/final",
            ["https://example.com/start", "https://example.com/final"],
            id="positive_same_host_redirect",
        ),
        pytest.param(
            [("https://example.com/start", "https://www.example.com/final")],
            "https://www.example.com/final",
            ["https://example.com/start", "https://www.example.com/final"],
            id="positive_apex_to_www_redirect",
        ),
        pytest.param(
            [
                ("https://example.com/start", "https://example.com/middle"),
                ("https://example.com/middle", "https://www.example.com/final"),
            ],
            "https://www.example.com/final",
            [
                "https://example.com/start",
                "https://example.com/middle",
                "https://www.example.com/final",
            ],
            id="positive_two_hop_redirect",
        ),
    ],
)
async def test_redirect_chain_is_retained_through_validated_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    make_run: Any,
    publish: Any,
    redirects: list[tuple[str, str]],
    final_url: str,
    expected_chain: list[str],
) -> None:
    public_dns(monkeypatch)
    store, source_id = page_store(make_run, redirects[0][0])
    redirect_map = dict(redirects)
    requests: list[str] = []

    async def get(url: str, **kwargs: Any) -> Response:
        requests.append(url)
        if url in redirect_map:
            return response(url, status=302, headers={"location": redirect_map[url]}, content=b"")
        return response(url)

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", get)
    monkeypatch.setattr(
        "company_bi.fetch.DynamicFetcher.async_fetch",
        lambda *args, **kwargs: pytest.fail("unexpected dynamic fallback"),
    )
    result = await read_page(source_id, store=store, budget=ResearchBudget())
    assert result.material is not None
    assert result.material.source.url == HttpUrl(final_url)
    assert requests == [hop[0] for hop in redirects] + [final_url]

    run = validated_run(make_run, store, source_id)
    output = publish(run)
    assert output["products_services"]["state"] == "supported"
    published = next(source for source in output["sources"] if source["source_id"] == source_id)
    assert published["url"] == final_url
    assert published["redirect_chain"] == expected_chain
    markdown = tmp_path.joinpath("profile.md").read_text(encoding="utf-8")
    assert "Example sp. z o.o." in markdown
    assert all(url in markdown for url in expected_chain)


@pytest.mark.asyncio
async def test_self_redirect_is_retained_and_survives_json_publication(
    monkeypatch: pytest.MonkeyPatch,
    make_run: Any,
    publish: Any,
) -> None:
    public_dns(monkeypatch)
    url = "https://example.com/self"
    store, source_id = page_store(make_run, url)
    requests: list[str] = []

    async def get(request_url: str, **kwargs: Any) -> Response:
        requests.append(request_url)
        if len(requests) == 1:
            return response(request_url, status=302, headers={"location": url}, content=b"")
        return response(request_url)

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", get)
    monkeypatch.setattr(
        "company_bi.fetch.DynamicFetcher.async_fetch",
        lambda *args, **kwargs: pytest.fail("unexpected dynamic fallback"),
    )
    result = await read_page(source_id, store=store, budget=ResearchBudget())
    assert result.material is not None
    run = validated_run(make_run, store, source_id)
    output = publish(run)
    published = next(source for source in output["sources"] if source["source_id"] == source_id)
    assert published["redirect_chain"] == [url, url]
    assert output["products_services"]["state"] == "supported"
    assert requests == [url, url]


@pytest.mark.asyncio
async def test_static_thin_shell_dynamic_fallback_retains_redirect_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    make_run: Any,
    publish: Any,
) -> None:
    public_dns(monkeypatch)
    discovered = "https://example.com/start"
    final_url = "https://www.example.com/final"
    store, source_id = page_store(make_run, discovered)

    async def static_get(url: str, **kwargs: Any) -> Response:
        if url == discovered:
            return response(url, status=302, headers={"location": final_url}, content=b"")
        return response(
            url,
            content="<html><body>Enable JavaScript to continue</body></html>",
        )

    async def dynamic_fetch(url: str, **kwargs: Any) -> Response:
        return response(final_url)

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", static_get)
    monkeypatch.setattr("company_bi.fetch.DynamicFetcher.async_fetch", dynamic_fetch)
    result = await read_page(source_id, store=store, budget=ResearchBudget())
    assert result.material is not None and result.material.fetch_mode == "dynamic"
    run = validated_run(make_run, store, source_id)
    output = publish(run)
    published = next(source for source in output["sources"] if source["source_id"] == source_id)
    assert published["url"] == final_url
    assert published["redirect_chain"] == [discovered, final_url]
    assert tmp_path.joinpath("profile.md").exists()
    markdown = tmp_path.joinpath("profile.md").read_text(encoding="utf-8")
    assert all(url in markdown for url in (discovered, final_url))


@pytest.mark.asyncio
async def test_redirect_to_private_target_is_rejected_before_transport_contact(
    monkeypatch: pytest.MonkeyPatch, make_run: Any
) -> None:
    public_dns(monkeypatch)
    store, source_id = page_store(make_run, "https://example.com/start")
    contacted: list[str] = []

    async def get(url: str, **kwargs: Any) -> Response:
        contacted.append(url)
        return response(
            url, status=302, headers={"location": "http://127.0.0.1/private"}, content=b""
        )

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", get)
    result = await read_page(source_id, store=store, budget=ResearchBudget())
    assert result.material is None
    assert result.failure is not None and result.failure.stage == "url_validation"
    assert contacted == ["https://example.com/start"]


def test_unrecorded_same_host_path_change_is_rejected(
    make_run: Any,
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["source"]["source_id"] == "page")
    discovery = {
        **page,
        "source": {**page["source"]},
        "kind": "search_snippet",
        "fetch_mode": "tavily",
        "content": "Original discovery URL",
    }
    payload["sources"].append(discovery)
    page["source"]["url"] = "https://page.example/unexplained"
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(payload)


def test_same_id_unrelated_host_substitution_cannot_be_published(
    make_run: Any, publish: Any
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    payload = run.model_dump(mode="python")
    original_page = next(
        item for item in payload["sources"] if item["source"]["source_id"] == "page"
    )
    discovery = {
        **original_page,
        "source": {**original_page["source"]},
        "kind": "search_snippet",
        "fetch_mode": "tavily",
        "content": "Original discovery came from page.example",
    }
    payload["sources"].append(discovery)
    original_page["source"]["url"] = "https://unrelated.example/forged"
    with pytest.raises(ValueError):
        forged = CompanyResearchRun.model_validate(payload)
        publish(forged)


@pytest.mark.parametrize(
    "chain",
    [
        pytest.param(
            ["https://other.example/start", "https://www.example.com/final"],
            id="negative_wrong_origin",
        ),
        pytest.param(
            ["https://example.com/start", "https://elsewhere.example/final"],
            id="negative_wrong_end",
        ),
    ],
)
def test_redirect_lineage_must_match_discovered_and_final_urls(
    make_run: Any, chain: list[str]
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["source"]["source_id"] == "page")
    discovered = {
        **page,
        "source": {**page["source"], "url": "https://example.com/start"},
        "kind": "search_snippet",
        "fetch_mode": "tavily",
        "content": "Example sp. z o.o. discovery snippet",
    }
    payload["sources"].append(discovered)
    page["source"]["url"] = "https://www.example.com/final"
    page["source"]["redirect_chain"] = chain
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(payload)


@pytest.mark.parametrize("kind", ["registry", "search_snippet"])
def test_non_page_material_cannot_masquerade_as_redirect_provenance(
    make_run: Any, kind: str
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    payload = run.model_dump(mode="python")
    if kind == "registry":
        material = next(item for item in payload["sources"] if item["kind"] == kind)
    else:
        page = next(item for item in payload["sources"] if item["kind"] == "full_page")
        material = {
            **page,
            "source": {**page["source"], "source_id": "snippet"},
            "kind": "search_snippet",
            "fetch_mode": "tavily",
        }
        payload["sources"].append(material)
    material["source"]["redirect_chain"] = [
        "https://example.com/start",
        "https://www.example.com/final",
    ]
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(payload)
