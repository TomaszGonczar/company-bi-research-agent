"""Source URL identity regressions for IPv4, DNS, and IPv6 authorities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import HttpUrl, ValidationError

from company_bi.evidence import build_profile
from company_bi.models import CompanyResearchRun, RetrievedSource
from company_bi.sources import SourceStore

STAMP = datetime(2026, 10, 3, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    ("first", "equivalent"),
    [
        ("https://example.test/story", "https://EXAMPLE.test:443/story#top"),
        ("http://192.0.2.1/story", "http://192.0.2.1:80/story"),
        ("https://[2001:db8::1]/story", "https://[2001:DB8::1]:443/story#top"),
    ],
    ids=["dns", "ipv4", "ipv6"],
)
def test_source_store_reuses_ids_for_same_normalized_owner(
    make_run: Any, first: str, equivalent: str
) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    one = store.add_search(
        title="First", url=HttpUrl(first), content="first", score=None, retrieved_at=STAMP
    )
    two = store.add_search(
        title="Equivalent",
        url=HttpUrl(equivalent),
        content="second",
        score=None,
        retrieved_at=STAMP,
    )
    assert one.source_id == two.source_id


def test_source_store_keeps_ipv6_host_port_collision_pair_distinct(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    registry = next(item.source for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry])
    first = store.add_search(
        title="Port 8080",
        url=HttpUrl("https://[2001:db8::1]:8080/"),
        content="first",
        score=None,
        retrieved_at=STAMP,
    )
    second = store.add_search(
        title="Different IPv6 host",
        url=HttpUrl("https://[2001:db8::1:8080]/"),
        content="second",
        score=None,
        retrieved_at=STAMP,
    )
    third = store.add_search(
        title="Another IPv6 host",
        url=HttpUrl("https://[2001:db8::2]:8080/"),
        content="third",
        score=None,
        retrieved_at=STAMP,
    )
    assert len({first.source_id, second.source_id, third.source_id}) == 3


@pytest.mark.parametrize(
    ("discovered", "final", "chain"),
    [
        pytest.param(
            "https://[2001:db8::1:8080]/",
            "https://[2001:db8::2]:8080/final",
            ["https://[2001:db8::1]:8080/", "https://[2001:db8::2]:8080/final"],
            id="ipv6-origin-collision",
        ),
        pytest.param(
            "https://[2001:db8::1]/start",
            "https://[2001:db8::3]/forged",
            ["https://[2001:db8::1]/start", "https://[2001:db8::2]/final"],
            id="ipv6-wrong-final",
        ),
        pytest.param(
            "https://192.0.2.1/start",
            "https://192.0.2.2/final",
            ["https://192.0.2.9/start", "https://192.0.2.2/final"],
            id="ipv4-wrong-origin",
        ),
    ],
)
def test_redirect_lineage_origin_and_final_urls_reject_at_both_boundaries(
    make_run: Any, discovered: str, final: str, chain: list[str]
) -> None:
    run = make_run('Example sp. z o.o. provides "industrial packaging".')
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    discovery = {
        **page,
        "source": {**page["source"], "url": discovered},
        "kind": "search_snippet",
        "fetch_mode": "tavily",
        "content": "Retained discovery",
    }
    payload["sources"].append(discovery)
    page["source"]["url"] = final
    page["source"]["redirect_chain"] = chain

    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(payload)

    materials = [RetrievedSource.model_validate(item) for item in payload["sources"]]
    unchecked = run.model_copy(update={"sources": materials})
    with pytest.raises(ValueError):
        build_profile(unchecked)
