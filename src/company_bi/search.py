"""Bounded Tavily discovery that records host-owned source material."""

from __future__ import annotations

import asyncio
import math
from datetime import UTC, datetime
from typing import Any

from pydantic import HttpUrl
from tavily import AsyncTavilyClient  # type: ignore[import-untyped]

from company_bi.models import SearchResults
from company_bi.sources import ResearchBudget, SourceStore


def _provider_error(error: BaseException) -> str:
    # Exception strings may contain request headers or credentials; retain only the class.
    return f"Tavily search failed ({type(error).__name__})"


async def search_web(
    query: str, *, client: AsyncTavilyClient, store: SourceStore, budget: ResearchBudget
) -> SearchResults:
    if not budget.consume("search"):
        return SearchResults(query=query, results=[], error="Search budget or deadline exhausted")
    timeout = budget.remaining()
    if timeout <= 0:
        return SearchResults(query=query, results=[], error="Research deadline reached")
    try:
        async with asyncio.timeout(timeout):
            response: Any = await client.search(
                query,
                search_depth="basic",
                max_results=5,
                include_answer=False,
                include_raw_content=False,
                timeout=timeout,
            )
        if not isinstance(response, dict) or not isinstance(response.get("results"), list):
            raise ValueError("Malformed Tavily response")
        parsed = []
        for item in response["results"][:5]:
            if not isinstance(item, dict):
                raise ValueError("Malformed Tavily result")
            raw_url = item.get("url")
            content = item.get("content")
            title = item.get("title")
            score = item.get("score")
            if not isinstance(raw_url, str) or not raw_url.strip() or not isinstance(content, str):
                raise ValueError("Malformed Tavily result fields")
            url = HttpUrl(raw_url)
            if title is None or (isinstance(title, str) and not title.strip()):
                title = str(url)
            if not isinstance(title, str):
                raise ValueError("Malformed Tavily result title")
            numeric_score = float(score) if score is not None else None
            if numeric_score is not None and (
                not math.isfinite(numeric_score) or not 0 <= numeric_score <= 1
            ):
                raise ValueError("Malformed Tavily result score")
            parsed.append((title, url, content, numeric_score))
        retrieved_at = datetime.now(UTC)
        hits = [
            store.add_search(
                title=title, url=url, content=content, score=score, retrieved_at=retrieved_at
            )
            for title, url, content, score in parsed
        ]
        return SearchResults(query=query, results=hits)
    except TimeoutError:
        message = "Tavily search timed out"
    except Exception as error:
        message = _provider_error(error)
    budget.note(message)
    return SearchResults(query=query, results=[], error=message)
