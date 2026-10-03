from __future__ import annotations

import socket
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import HttpUrl
from scrapling.engines.toolbelt.custom import Response

from company_bi.fetch import read_page
from company_bi.models import CompanyIdentity, EvidenceRef, Fact, RetrievedSource, Source
from company_bi.search import search_web
from company_bi.sources import ResearchBudget, SourceStore


def identity() -> CompanyIdentity:
    source_id = "mf-source"
    ref = [EvidenceRef(source_id=source_id, excerpt='"Example Sp. z o.o."')]
    return CompanyIdentity(
        nip="5220003782",
        legal_name=Fact[str](state="supported", value="Example Sp. z o.o.", evidence=ref),
        krs=Fact[str](state="unknown", reason="not supplied"),
        regon=Fact[str](state="unknown", reason="not supplied"),
        registered_city=Fact[str](state="unknown", reason="not supplied"),
        registered_address=Fact[str](state="unknown", reason="not supplied"),
        website=Fact[HttpUrl](state="unknown", reason="not supplied"),
        resolved_at=datetime.now(UTC),
    )


def registry_source() -> Source:
    return Source(
        source_id="mf-source",
        url="https://www.gov.pl/",
        title="MF registry",
        retrieved_at=datetime.now(UTC),
    )


def response(html: str, url: str = "https://example.com/page") -> Response:
    return Response(
        url=url, content=html, status=200, reason="OK", cookies={}, headers={}, request_headers={}
    )


class ControlledTavily:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def search(self, query: str, **kwargs: Any) -> Any:
        self.calls.append((query, kwargs))
        if self.error:
            raise self.error
        return self.result


def test_source_store_keeps_registry_repeated_snippets_and_full_page() -> None:
    store = SourceStore(identity(), [registry_source()])
    first = store.add_search(
        title="Company",
        url=HttpUrl("https://Example.com/story#top"),
        content="First snippet",
        score=0.7,
        retrieved_at=datetime.now(UTC),
    )
    second = store.add_search(
        title="Updated title",
        url=HttpUrl("https://example.com/story"),
        content="Second snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    assert first.source_id == second.source_id == "S001"
    assert store.get("S001").content == "Second snippet"
    page = store.get("S001").model_copy(
        update={"kind": "full_page", "content": "Full text " * 100, "fetch_mode": "static"}
    )
    store.store_page(page)
    assert store.get("S001").content == "Full text " * 100
    snapshots = store.snapshots()
    assert [item.kind for item in snapshots] == [
        "registry",
        "search_snippet",
        "search_snippet",
        "full_page",
    ]
    assert snapshots[1].source.title == "Company"
    assert snapshots[2].source.title == "Updated title"
    assert "Example Sp. z o.o." in snapshots[0].content
    assert store.known_ids() == {"mf-source", "S001"}


def test_source_store_rejects_unknown_page() -> None:
    store = SourceStore(identity(), [])
    material = RetrievedSource(
        source=Source(
            source_id="missing",
            url="https://example.com/",
            title="Unknown",
            retrieved_at=datetime.now(UTC),
        ),
        kind="full_page",
        content="content",
        fetch_mode="static",
    )
    with pytest.raises(ValueError):
        store.store_page(material)


@pytest.mark.asyncio
async def test_search_web_limits_results_and_uses_host_ids() -> None:
    client = ControlledTavily(
        {
            "answer": "ignored",
            "results": [
                {
                    "title": "",
                    "url": f"https://example.com/{i}",
                    "content": f"snippet {i}",
                    "score": 0.5,
                }
                for i in range(7)
            ],
        }
    )
    store = SourceStore(identity(), [])
    result = await search_web("example", client=client, store=store, budget=ResearchBudget())
    assert len(result.results) == 5
    assert [hit.source_id for hit in result.results] == [f"S{i:03d}" for i in range(1, 6)]
    assert result.results[0].title == "https://example.com/0"
    assert store.get("S001").content == "snippet 0"


@pytest.mark.asyncio
async def test_search_without_provider_score_preserves_missing_ranking() -> None:
    store = SourceStore(identity(), [])
    result = await search_web(
        "company",
        client=ControlledTavily(
            {
                "results": [
                    {
                        "title": "Company",
                        "url": "https://example.com/company",
                        "content": "Company activity",
                        "source_id": "provider-invented",
                    }
                ]
            }
        ),
        store=store,
        budget=ResearchBudget(),
    )
    assert result.error is None
    hit = result.results[0]
    assert hit.score is None
    assert hit.source_id == "S001"
    assert store.get(hit.source_id).content == "Company activity"


@pytest.mark.asyncio
async def test_empty_search_results_are_not_a_provider_failure() -> None:
    store = SourceStore(identity(), [])
    result = await search_web(
        "no matches",
        client=ControlledTavily({"results": []}),
        store=store,
        budget=ResearchBudget(),
    )
    assert result.results == []
    assert result.error is None
    assert store.snapshots() == []


@pytest.mark.asyncio
async def test_search_web_errors_and_budget_are_structured() -> None:
    store = SourceStore(identity(), [])
    budget = ResearchBudget(max_searches=1)
    failed_client = ControlledTavily(error=RuntimeError("token=secret"))
    error = await search_web("bad", client=failed_client, store=store, budget=budget)
    assert error.error
    assert "secret" not in error.error
    assert budget.searches == 1
    limited = await search_web(
        "again", client=ControlledTavily({"results": []}), store=store, budget=budget
    )
    assert limited.error
    assert budget.searches == 1
    expired_client = ControlledTavily({"results": []})
    expired = await search_web(
        "expired", client=expired_client, store=store, budget=ResearchBudget(max_seconds=0)
    )
    assert expired.error
    assert expired_client.calls == []


@pytest.mark.asyncio
async def test_search_web_rejects_malformed_provider_data_atomically() -> None:
    store = SourceStore(identity(), [])
    result = await search_web(
        "broken",
        client=ControlledTavily(
            {
                "results": [
                    {"url": "https://example.com/valid", "title": "Valid", "content": "snippet"},
                    {"url": "https://example.com/bad", "title": "Bad"},
                ]
            }
        ),
        store=store,
        budget=ResearchBudget(),
    )
    assert result.results == []
    assert result.error
    assert store.known_ids() == set()


@pytest.mark.asyncio
async def test_read_page_static_html_caches_page_and_keeps_short_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SourceStore(identity(), [])
    hit = store.add_search(
        title="Story",
        url=HttpUrl("https://example.com/page"),
        content="snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )
    calls = 0

    async def static_get(url: str, **kwargs: Any) -> Response:
        nonlocal calls
        calls += 1
        return response(
            "<html><head><title>Page title</title><meta property='article:published_time' "
            "content='2025-02-03T10:00:00Z'></head>"
            "<body><article>Short but meaningful</article>"
            "<template>hidden template</template><script>hidden script</script></body></html>",
            url,
        )

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", static_get)
    monkeypatch.setattr(
        "company_bi.fetch.DynamicFetcher.async_fetch",
        lambda *args, **kwargs: pytest.fail("unexpected dynamic fallback"),
    )
    budget = ResearchBudget()
    result = await read_page(hit.source_id, store=store, budget=budget)
    assert result.material is not None
    assert result.material.kind == "full_page"
    assert result.material.fetch_mode == "static"
    assert "Short but meaningful" in result.material.content
    assert "hidden" not in result.material.content
    assert result.material.source.published_on.isoformat() == "2025-02-03"
    assert result.material.source.title == "Page title"
    cached = await read_page(hit.source_id, store=store, budget=budget)
    assert cached.material == result.material
    assert calls == 1
    assert budget.page_reads == 1


@pytest.mark.asyncio
async def test_static_redirect_retains_final_url_and_text_csv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SourceStore(identity(), [])
    hit = store.add_search(
        title="Story",
        url=HttpUrl("https://example.com/page"),
        content="snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )
    requests: list[str] = []

    async def static_get(url: str, **kwargs: Any) -> Response:
        requests.append(url)
        if url.endswith("/page"):
            result = response("", url)
            result.status = 302
            result.headers = {"location": "/final"}
            return result
        result = response(
            "<html><head><meta property='article:published_time' "
            "content='2025-04-05'></head><body>Reported fact</body></html>",
            url,
        )
        result.headers = {"content-type": "text/html; charset=utf-8"}
        return result

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", static_get)
    result = await read_page(hit.source_id, store=store, budget=ResearchBudget())
    assert result.material is not None
    assert [url.rsplit("/", 1)[-1] for url in requests] == ["page", "final"]
    assert str(result.material.source.url) == "https://example.com/final"
    assert result.material.source.published_on.isoformat() == "2025-04-05"

    csv_store = SourceStore(identity(), [])
    csv_hit = csv_store.add_search(
        title="CSV",
        url=HttpUrl("https://example.com/report.csv"),
        content="csv result",
        score=None,
        retrieved_at=datetime.now(UTC),
    )

    async def csv_get(url: str, **kwargs: Any) -> Response:
        result = Response(
            url=url,
            content=b"metric,value\nrevenue,12\n",
            status=200,
            reason="OK",
            cookies={},
            headers={"content-type": "text/csv; charset=utf-8"},
            request_headers={},
        )
        return result

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", csv_get)
    csv_result = await read_page(csv_hit.source_id, store=csv_store, budget=ResearchBudget())
    assert csv_result.material is not None
    assert csv_result.material.content == "metric,value\nrevenue,12"

    text_store = SourceStore(identity(), [])
    text_hit = text_store.add_search(
        title="Text",
        url=HttpUrl("https://example.com/summary.txt"),
        content="text result",
        score=None,
        retrieved_at=datetime.now(UTC),
    )

    async def plain_text_get(url: str, **kwargs: Any) -> Response:
        return Response(
            url=url,
            content=b"Plain text content without HTML parsing.",
            status=200,
            reason="OK",
            cookies={},
            headers={"content-type": "text/plain; charset=utf-8"},
            request_headers={},
        )

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", plain_text_get)
    text_result = await read_page(text_hit.source_id, store=text_store, budget=ResearchBudget())
    assert text_result.material is not None
    assert text_result.material.content == "Plain text content without HTML parsing."


@pytest.mark.parametrize(
    ("content_type", "body"),
    [
        ("application/pdf", b"%PDF-1.7"),
        ("application/zip", b"PK\\x03\\x04"),
        ("text/xml", b"<?xml version='1.0'?>"),
        ("application/msword", b"\\xd0\\xcf\\x11\\xe0\\xa1\\xb1\\x1a\\xe1"),
        ("image/png", b"\\x89PNG\\r\\n\\x1a\\n"),
        (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            b"PK\\x03\\x04",
        ),
    ],
)
@pytest.mark.asyncio
async def test_non_page_content_is_not_stored_as_full_page(
    monkeypatch: pytest.MonkeyPatch, content_type: str, body: bytes
) -> None:
    store = SourceStore(identity(), [])
    hit = store.add_search(
        title="Document",
        url=HttpUrl("https://example.com/report"),
        content="search snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )

    async def document_get(url: str, **kwargs: Any) -> Response:
        return Response(
            url=url,
            content=body,
            status=200,
            reason="OK",
            cookies={},
            headers={"content-type": content_type},
            request_headers={},
        )

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", document_get)
    monkeypatch.setattr(
        "company_bi.fetch.DynamicFetcher.async_fetch",
        lambda *args, **kwargs: pytest.fail("unsupported documents must not use dynamic fallback"),
    )
    budget = ResearchBudget()
    result = await read_page(hit.source_id, store=store, budget=budget)
    assert result.material is None and result.error
    assert budget.dynamic_reads == 0


@pytest.mark.asyncio
async def test_read_page_dynamic_fallback_is_bounded_and_stored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SourceStore(identity(), [])
    hit = store.add_search(
        title="Story",
        url=HttpUrl("https://example.com/page"),
        content="snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )

    async def static_shell(url: str, **kwargs: Any) -> Response:
        return response(
            "<html><body><div id='app'>Enable JavaScript to run this app</div>"
            "<script src='/app.js'></script></body></html>",
            url,
        )

    async def dynamic(url: str, **kwargs: Any) -> Response:
        class FakePage:
            async def route(self, pattern: str, handler: Any) -> None:
                self.handler = handler

        class FakeRoute:
            def __init__(self, url: str) -> None:
                self.request = type("Request", (), {"url": url})()
                self.aborted = False

            async def abort(self) -> None:
                self.aborted = True

            async def continue_(self) -> None:
                raise AssertionError("non-HTTP request must be blocked")

        page = FakePage()
        await kwargs["page_setup"](page)
        routes = [
            FakeRoute("file:///etc/passwd"),
            FakeRoute("http://127.0.0.1/private"),
        ]
        for route in routes:
            await page.handler(route)
        assert all(route.aborted for route in routes)
        return response("<main>Rendered useful content</main>", url)

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", static_shell)
    monkeypatch.setattr("company_bi.fetch.DynamicFetcher.async_fetch", dynamic)
    budget = ResearchBudget()
    result = await read_page(hit.source_id, store=store, budget=budget)
    assert result.material is not None and result.material.fetch_mode == "dynamic"
    assert result.material.content == "Rendered useful content"
    assert budget.page_reads == budget.dynamic_reads == 1


@pytest.mark.asyncio
async def test_read_page_rejects_unknown_and_private_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SourceStore(identity(), [registry_source()])
    budget = ResearchBudget()
    unknown = await read_page("not-a-source", store=store, budget=budget)
    assert unknown.material is None and unknown.error
    hit = store.add_search(
        title="Story",
        url=HttpUrl("https://example.com/page"),
        content="snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )

    def resolve(host: str, *args: Any, **kwargs: Any) -> list[tuple[Any, ...]]:
        ip = "127.0.0.1" if host == "127.0.0.1" else "93.184.216.34"
        return [(None, None, None, None, (ip, 0))]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)

    requested_urls: list[str] = []

    async def redirect(url: str, **kwargs: Any) -> Response:
        requested_urls.append(url)
        result = response("", url)
        result.status = 302
        result.headers = {"location": "http://127.0.0.1/private"}
        return result

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", redirect)
    result = await read_page(hit.source_id, store=store, budget=budget)
    assert result.material is None and result.error
    assert requested_urls == ["https://example.com/page"]
    assert budget.page_reads == 1
    assert budget.dynamic_reads == 0


@pytest.mark.asyncio
async def test_read_page_budget_exhaustion_and_failed_fetch_are_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = SourceStore(identity(), [])
    hit = store.add_search(
        title="Story",
        url=HttpUrl("https://example.com/page"),
        content="snippet",
        score=None,
        retrieved_at=datetime.now(UTC),
    )
    exhausted = ResearchBudget(max_page_reads=0)
    blocked = await read_page(hit.source_id, store=store, budget=exhausted)
    assert blocked.error

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )

    async def failed(*args: Any, **kwargs: Any) -> Response:
        raise OSError("offline")

    monkeypatch.setattr("company_bi.fetch.AsyncFetcher.get", failed)
    monkeypatch.setattr("company_bi.fetch.DynamicFetcher.async_fetch", failed)
    limited_dynamic = ResearchBudget(max_dynamic_reads=0)
    result = await read_page(hit.source_id, store=store, budget=limited_dynamic)
    assert result.material is None and result.error
    assert limited_dynamic.page_reads == 1 and limited_dynamic.dynamic_reads == 0


@pytest.mark.asyncio
async def test_browser_redirect_is_blocked_before_an_unrouted_private_hop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from company_bi.fetch import _page_setup

    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, ("93.184.216.34", 0))],
    )

    class BrowserPage:
        async def route(self, pattern: str, handler: Any) -> None:
            self.handler = handler

    class RedirectRoute:
        request = type("Request", (), {"url": "https://example.com/redirect"})()

        def __init__(self) -> None:
            self.aborted = False
            self.private_hop_contacted = False

        async def continue_(self) -> None:
            # Playwright does not route later hops in this HTTP redirect chain.
            self.private_hop_contacted = True

        async def fetch(self, **kwargs: Any) -> Any:
            return type(
                "RedirectResponse",
                (),
                {
                    "status": 302,
                    "headers": {"location": "http://127.0.0.1/private"},
                },
            )()

        async def abort(self) -> None:
            self.aborted = True

        async def fulfill(self, **kwargs: Any) -> None:
            self.private_hop_contacted = True

    page = BrowserPage()
    route = RedirectRoute()
    await _page_setup(page)
    await page.handler(route)
    assert route.aborted
    assert not route.private_hop_contacted
