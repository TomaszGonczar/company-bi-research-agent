"""Public-web page retrieval with static-first parsing and bounded dynamic fallback."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Literal
from urllib.parse import urljoin, urlsplit

from pydantic import HttpUrl
from scrapling.fetchers import AsyncFetcher, DynamicFetcher

from company_bi.models import OperationalFailure, PageReadResult, RetrievedSource
from company_bi.sources import ResearchBudget, SourceStore

if TYPE_CHECKING:
    from playwright.async_api import Page, Route

_MAX_REDIRECTS = 5
_DNS_TIMEOUT = 3.0


class _UnsafeTarget(ValueError):
    pass


class _UnsupportedContent(ValueError):
    pass


@dataclass(frozen=True)
class _PageArtifact:
    text: str
    url: str
    published_on: date | None
    title: str | None


async def _validate_public_url(value: str, timeout: float = _DNS_TIMEOUT) -> str:
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise _UnsafeTarget("Only public HTTP(S) URLs are allowed")
        if parts.username is not None or parts.password is not None:
            raise _UnsafeTarget("Credential-bearing URLs are not allowed")
        port = parts.port
        if port is not None and not 1 <= port <= 65535:
            raise _UnsafeTarget("Invalid URL port")
        hostname = parts.hostname.rstrip(".").lower()
        try:
            literal = ipaddress.ip_address(hostname)
        except ValueError:
            literal = None
        if literal is not None:
            addresses = [literal]
        else:
            if (
                "." not in hostname
                or hostname == "localhost"
                or hostname.endswith((".localhost", ".local", ".localdomain", ".internal", ".lan"))
                or hostname == "home.arpa"
                or hostname.endswith(".home.arpa")
            ):
                raise _UnsafeTarget("Local or internal URL hosts are not allowed")
            resolved = await asyncio.wait_for(
                asyncio.to_thread(
                    socket.getaddrinfo,
                    hostname,
                    port or (443 if parts.scheme.lower() == "https" else 80),
                    type=socket.SOCK_STREAM,
                ),
                timeout=max(0.001, min(timeout, _DNS_TIMEOUT)),
            )
            addresses = [
                ipaddress.ip_address(str(entry[4][0]).split("%", 1)[0]) for entry in resolved
            ]
        if not addresses or any(not address.is_global for address in addresses):
            raise _UnsafeTarget("URL resolves to a non-public address")
        return value
    except _UnsafeTarget:
        raise
    except (OSError, ValueError, TimeoutError) as error:
        raise _UnsafeTarget("URL host could not be safely resolved") from error


def _header(headers: object, key: str) -> str | None:
    if not isinstance(headers, dict):
        return None
    value = headers.get(key) or headers.get(key.title())
    return (
        value.decode("latin-1")
        if isinstance(value, bytes)
        else value
        if isinstance(value, str)
        else None
    )


def _body_bytes(response: object) -> bytes:
    body = getattr(response, "body", b"")
    return body if isinstance(body, bytes) else b""


def _content_type(response: object) -> str | None:
    value = _header(getattr(response, "headers", {}), "content-type")
    return value.split(";", 1)[0].strip().lower() if value else None


def _require_page_content(response: object) -> bool:
    """Refuse binary/document/XML payloads; return True for text/csv decoding."""
    content_type = _content_type(response)
    body = _body_bytes(response)
    lowered = body[:16].lstrip().lower()
    if lowered.startswith(
        (
            b"%pdf-",
            b"pk\x03\x04",
            b"pk\x05\x06",
            b"pk\x07\x08",
            b"\x89png",
            b"\xff\xd8\xff",
            b"gif8",
            b"bm",
            b"ii*\x00",
            b"mm\x00*",
            b"<svg",
            b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
            b"<?xml",
        )
    ) or (body[:4] == b"RIFF" and body[8:12] == b"WEBP"):
        raise _UnsupportedContent("Unsupported non-page document content")
    if content_type is None:
        return False
    if (
        content_type
        in {
            "application/pdf",
            "application/zip",
            "application/x-zip-compressed",
            "application/xml",
            "text/xml",
            "application/octet-stream",
            "application/msword",
            "application/rtf",
            "text/rtf",
        }
        or content_type.startswith(("image/", "application/vnd."))
        or content_type.endswith(("+xml", "+zip"))
    ):
        raise _UnsupportedContent("Unsupported non-page document content")
    if content_type in {"text/plain", "text/csv", "application/csv"}:
        return True
    if content_type == "text/html":
        return False
    raise _UnsupportedContent("Unsupported page content type")


def _normalized_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _page_text(response: object) -> str:
    if _require_page_content(response):
        encoding = getattr(response, "encoding", None) or "utf-8"
        return _normalized_text(_body_bytes(response).decode(encoding, errors="replace"))
    get_all_text = getattr(response, "get_all_text", None)
    if not callable(get_all_text):
        return ""
    text = get_all_text(
        strip=True,
        ignore_tags=("script", "style", "noscript", "svg", "iframe", "template"),
    )
    return _normalized_text(str(text))


def _publication_date(response: object) -> date | None:
    css = getattr(response, "css", None)
    if not callable(css):
        return None
    for selector, attribute in (
        ('meta[property="article:published_time"]', "content"),
        ('time[itemprop="datePublished"][datetime]', "datetime"),
        ("time[pubdate][datetime]", "datetime"),
    ):
        try:
            element = css(selector).first
            value = element.attrib.get(attribute) if element is not None else None
            if value:
                parsed = date.fromisoformat(str(value)[:10])
                return parsed
        except (AttributeError, TypeError, ValueError):
            continue
    return None


def _page_title(response: object) -> str | None:
    css = getattr(response, "css", None)
    if not callable(css):
        return None
    for selector, attribute in (
        ("title", None),
        ('meta[property="og:title"]', "content"),
    ):
        try:
            element = css(selector).first
            if element is None:
                continue
            value = element.attrib.get(attribute) if attribute else element.get_all_text(strip=True)
            title = " ".join(str(value or "").split())
            if title:
                return title
        except (AttributeError, TypeError):
            continue
    return None


def _meaningful(text: str) -> bool:
    folded = " ".join(text.casefold().split())
    if not folded:
        return False
    shell_markers = (
        "enable javascript",
        "javascript is required",
        "javascript must be enabled",
        "requires javascript",
        "javascript to run this app",
        "checking your browser",
        "verify you are human",
    )
    if any(marker in folded for marker in shell_markers) or folded in {
        "loading...",
        "please wait",
        "just a moment...",
    }:
        return False
    return any(char.isalnum() for char in folded)


def _full_page(
    store: SourceStore, source_id: str, artifact: _PageArtifact, mode: str
) -> RetrievedSource:
    known = store.get(source_id)
    if known is None:
        raise ValueError("Unknown search source")
    material = RetrievedSource(
        source=known.source.model_copy(
            update={
                "url": HttpUrl(artifact.url),
                "title": artifact.title or known.source.title,
                "retrieved_at": datetime.now(UTC),
                "published_on": artifact.published_on,
            }
        ),
        kind="full_page",
        content=artifact.text,
        fetch_mode=mode,
    )
    store.store_page(material)
    return material


def _record_fetch_failure(
    budget: ResearchBudget,
    *,
    source_id: str | None,
    stage: Literal[
        "static_fetch", "dynamic_fetch", "url_validation", "source_reference_validation"
    ],
    reason: str,
    error: BaseException | None = None,
    attempt: int | None = None,
    field_path: str | None = None,
) -> OperationalFailure:
    failure = OperationalFailure(
        code="FETCH_FAILURE",
        stage=stage,
        reason=reason,
        error_type=type(error).__name__ if error is not None else None,
        source_id=source_id,
        attempt=attempt,
        field_path=field_path,
    )
    budget.record_failure(failure)
    return failure


async def _static_read(url: str, timeout: float) -> _PageArtifact:
    current = url
    for redirect_count in range(_MAX_REDIRECTS + 1):
        await _validate_public_url(current, timeout)
        response = await AsyncFetcher.get(
            current,
            timeout=timeout,
            retries=0,
            follow_redirects=False,
            max_redirects=0,
        )
        status = getattr(response, "status", 200)
        headers = getattr(response, "headers", {}) or {}
        if status in {301, 302, 303, 307, 308}:
            location = _header(headers, "location")
            if not location or redirect_count >= _MAX_REDIRECTS:
                raise _UnsafeTarget("Unsafe or excessive redirect")
            current = urljoin(current, location)
            await _validate_public_url(current, timeout)
            continue
        if status < 200 or status >= 300:
            raise RuntimeError("Static page request failed")
        response_url = getattr(response, "url", current) or current
        await _validate_public_url(str(response_url), timeout)
        text = _page_text(response)
        return _PageArtifact(
            text, str(response_url), _publication_date(response), _page_title(response)
        )
    raise _UnsafeTarget("Excessive redirect")


async def _page_setup(page: Page) -> None:
    async def guard(route: Route) -> None:
        try:
            await _validate_public_url(route.request.url)
            # Playwright routes only the first hop of a redirect chain. Fetch without
            # following redirects and block them before the browser sees Location.
            response = await route.fetch(max_redirects=0, max_retries=0, timeout=15_000)
            if 300 <= response.status < 400:
                await route.abort()
            else:
                await route.fulfill(response=response)
        except Exception:
            await route.abort()

    await page.route("**/*", guard)


async def read_page(
    source_id: str, *, store: SourceStore, budget: ResearchBudget
) -> PageReadResult:
    if source_id not in store.known_ids():
        failure = _record_fetch_failure(
            budget,
            source_id=None,
            stage="source_reference_validation",
            reason="Page read source reference is not known to this run",
            field_path="source_id",
        )
        return PageReadResult(error=failure.reason, failure=failure)
    existing = store.get(source_id)
    if existing is not None and existing.kind == "full_page":
        return PageReadResult(material=existing)
    if existing is None or existing.fetch_mode != "tavily":
        failure = _record_fetch_failure(
            budget,
            source_id=None,
            stage="source_reference_validation",
            reason="Only discovered Tavily sources can be read",
            field_path="source_id",
        )
        return PageReadResult(error=failure.reason, failure=failure)
    if not budget.consume("page"):
        return PageReadResult(
            error="Page-read budget or deadline exhausted", failure=budget.failures[-1]
        )
    try:
        target = await _validate_public_url(str(existing.source.url), budget.remaining())
    except _UnsafeTarget as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="url_validation",
            reason="Page URL failed public-target validation",
            error=error,
            attempt=1,
        )
        return PageReadResult(error=failure.reason, failure=failure)

    try:
        timeout = budget.remaining()
        if timeout <= 0:
            raise TimeoutError
        async with asyncio.timeout(timeout):
            artifact = await _static_read(target, timeout)
        if _meaningful(artifact.text):
            return PageReadResult(material=_full_page(store, source_id, artifact, "static"))
        target = artifact.url
        _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="static_fetch",
            reason="Static fetch returned no meaningful page text",
            attempt=1,
        )
    except _UnsafeTarget as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="url_validation",
            reason="Static redirect failed public-target validation",
            error=error,
            attempt=1,
        )
        return PageReadResult(error=failure.reason, failure=failure)
    except _UnsupportedContent as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="static_fetch",
            reason="Static fetch returned unsupported page content",
            error=error,
            attempt=1,
        )
        return PageReadResult(error=failure.reason, failure=failure)
    except Exception as error:
        _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="static_fetch",
            reason="Static page fetch failed",
            error=error,
            attempt=1,
        )

    if not budget.consume("dynamic"):
        failure = budget.failures[-1]
        return PageReadResult(error=failure.reason, failure=failure)
    timeout = budget.remaining()
    if timeout <= 0:
        budget.record_failure(
            OperationalFailure(
                code="RESOURCE_LIMIT",
                stage="resource_limit",
                reason="Research deadline reached",
                source_id=source_id,
            )
        )
        failure = budget.failures[-1]
        return PageReadResult(error=failure.reason, failure=failure)
    try:
        await _validate_public_url(target, timeout)
        async with asyncio.timeout(timeout):
            response = await DynamicFetcher.async_fetch(
                target,
                timeout=max(1, int(timeout * 1000)),
                retries=1,  # Scrapling browser mode counts total attempts, not extra retries.
                page_setup=_page_setup,
                disable_resources=True,
                additional_args={"service_workers": "block", "accept_downloads": False},
                max_pages=1,
            )
        status = getattr(response, "status", 200)
        if status < 200 or status >= 300:
            raise RuntimeError("Dynamic page request failed")
        final_url = str(getattr(response, "url", target) or target)
        await _validate_public_url(final_url, timeout)
        artifact = _PageArtifact(
            _page_text(response), final_url, _publication_date(response), _page_title(response)
        )
        if not _meaningful(artifact.text):
            raise ValueError("Dynamic fetch returned no meaningful page text")
        return PageReadResult(material=_full_page(store, source_id, artifact, "dynamic"))
    except _UnsafeTarget as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="url_validation",
            reason="Dynamic page target failed public-target validation",
            error=error,
            attempt=2,
        )
        return PageReadResult(error=failure.reason, failure=failure)
    except _UnsupportedContent as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="dynamic_fetch",
            reason="Dynamic fetch returned unsupported page content",
            error=error,
            attempt=2,
        )
        return PageReadResult(error=failure.reason, failure=failure)
    except Exception as error:
        failure = _record_fetch_failure(
            budget,
            source_id=source_id,
            stage="dynamic_fetch",
            reason="Dynamic page fetch failed",
            error=error,
            attempt=2,
        )
        return PageReadResult(error=failure.reason, failure=failure)
