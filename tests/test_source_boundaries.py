import json
from datetime import UTC, datetime
from itertools import product

import pytest
from pydantic import HttpUrl, ValidationError

from company_bi.models import (
    CompanyIdentity,
    CompanyResearchRun,
    RetrievedSource,
    Source,
)
from company_bi.sources import SourceStore

STAMP = datetime(2026, 10, 3, 12, tzinfo=UTC)


def _source(source_id: str, url: str = "https://example.test/") -> Source:
    return Source(
        source_id=source_id,
        url=HttpUrl(url),
        title="Example",
        retrieved_at=STAMP,
    )


def _material(source_id: str, kind: str, mode: str, content: str = "material") -> RetrievedSource:
    return RetrievedSource(source=_source(source_id), kind=kind, fetch_mode=mode, content=content)


@pytest.mark.parametrize(
    ("kind", "mode"),
    [
        (kind, mode)
        for kind, mode in product(
            ("registry", "search_snippet", "full_page"),
            ("registry", "tavily", "static", "dynamic"),
        )
        if (kind, mode)
        not in {
            ("registry", "registry"),
            ("search_snippet", "tavily"),
            ("full_page", "static"),
            ("full_page", "dynamic"),
        }
    ],
)
def test_retrieved_source_rejects_inadmissible_kind_mode_pairs(kind: str, mode: str) -> None:
    with pytest.raises(ValidationError):
        _material("source", kind, mode)


def _identity(
    legal_name: str,
    *,
    name_excerpt: str | None = None,
    krs: str | None = None,
    krs_excerpt: str | None = None,
    source_id: str = "registry",
) -> CompanyIdentity:
    unknown = {"state": "unknown", "reason": "Not supplied"}
    data = {
        "nip": "1234567890",
        "legal_name": {
            "state": "supported",
            "value": legal_name,
            "evidence": [{"source_id": source_id, "excerpt": name_excerpt or legal_name}],
        },
        **{
            field: unknown
            for field in ("regon", "registered_city", "registered_address", "website")
        },
        "krs": (
            {
                "state": "supported",
                "value": krs,
                "evidence": [{"source_id": source_id, "excerpt": krs_excerpt or krs}],
            }
            if krs is not None
            else unknown
        ),
        "resolved_at": STAMP,
    }
    return CompanyIdentity.model_validate(data)


def test_registry_citation_uses_nfc_and_whitespace_normalization() -> None:
    name = "Café  spółka"
    content = json.dumps(
        {
            "result": {
                "subject": {"name": "Cafe\u0301   spółka", "nip": "1234567890", "krs": "0000123456"}
            }
        },
        ensure_ascii=False,
    )
    identity = _identity(
        name, name_excerpt="Cafe\u0301   spółka", krs="0000123456", krs_excerpt="0000123456"
    )
    _validate_registry_run(identity, content)


def test_registry_citation_cannot_substitute_other_mapped_field() -> None:
    content = json.dumps(
        {
            "result": {
                "subject": {"name": "Example sp. z o.o.", "nip": "1234567890", "krs": "0000123456"}
            }
        }
    )
    identity = _identity("Example sp. z o.o.", krs="0000123456", krs_excerpt="Example sp. z o.o.")
    with pytest.raises(ValidationError, match="does not match mapped registry data"):
        _validate_registry_run(identity, content)


def test_registry_citation_must_belong_to_referenced_registry_source() -> None:
    record = {"result": {"subject": {"name": "Café spółka", "nip": "1234567890"}}}
    payload = _run_payload([])
    payload["identity"] = _identity("Café spółka", source_id="other-registry").model_dump(
        mode="json"
    )
    payload["sources"] = [
        _material(
            "registry", "registry", "registry", json.dumps(record, ensure_ascii=False)
        ).model_dump(mode="json"),
        _material(
            "other-registry", "registry", "registry", json.dumps(record, ensure_ascii=True)
        ).model_dump(mode="json"),
    ]
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(payload)


def test_decoded_unicode_citation_absent_from_escaped_registry_text_is_rejected() -> None:
    content = json.dumps(
        {"result": {"subject": {"name": "Cafe\u0301   spółka", "nip": "1234567890"}}}
    )
    identity = _identity("Café  spółka", name_excerpt="Cafe\u0301   spółka")
    with pytest.raises(ValidationError, match="lacks retained registry evidence"):
        _validate_registry_run(identity, content)


def _run_payload(
    pages: list[tuple[str, str, str]], snippets: list[tuple[str, str, str]] | None = None
) -> dict:
    name = "Example sp. z o.o."
    unknown = {"state": "unknown", "reason": "Not established"}
    timestamp = STAMP.isoformat()
    registry_content = json.dumps({"result": {"subject": {"name": name, "nip": "1234567890"}}})
    materials = [
        {
            "source": {
                "source_id": "registry",
                "url": "https://registry.test/",
                "title": "Registry",
                "retrieved_at": timestamp,
            },
            "kind": "registry",
            "content": registry_content,
            "fetch_mode": "registry",
        }
    ]
    for index, (kind, mode, content) in enumerate([*(snippets or []), *pages]):
        source_id = "page" if kind != "registry" else f"source-{index}"
        materials.append(
            {
                "source": {
                    "source_id": source_id,
                    "url": "https://page.test/",
                    "title": "Page",
                    "retrieved_at": timestamp,
                },
                "kind": kind,
                "content": content,
                "fetch_mode": mode,
            }
        )
    return {
        "identity": {
            "nip": "1234567890",
            "legal_name": {
                "state": "supported",
                "value": name,
                "evidence": [{"source_id": "registry", "excerpt": name}],
            },
            **{
                field: unknown
                for field in ("krs", "regon", "registered_city", "registered_address", "website")
            },
            "resolved_at": timestamp,
        },
        "draft": {
            **{
                field: unknown
                for field in (
                    "business_description",
                    "products_services",
                    "industries",
                    "markets",
                    "employees",
                )
            },
            "financials": [{**unknown, "metric": "revenue"}, {**unknown, "metric": "net_result"}],
            "recent_developments": [],
            "limitations": ["Synthetic boundary test"],
        },
        "sources": materials,
        "diagnostics": {
            "model": "test",
            "status": "completed",
            "model_requests": 0,
            "searches": 0,
            "page_reads": 0,
            "dynamic_reads": 0,
            "output_retries": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "duration_seconds": 0,
        },
        "generated_at": timestamp,
    }


def _validate_registry_run(identity: CompanyIdentity, content: str) -> None:
    from company_bi.models import CompanyResearchRun

    payload = _run_payload([], [])
    payload["identity"] = identity.model_dump(mode="python")
    payload["sources"][0]["content"] = content
    CompanyResearchRun.model_validate(payload)


def _service_run(
    pages: list[tuple[str, str, str]],
    snippets: list[tuple[str, str, str]] | None = None,
) -> CompanyResearchRun:

    excerpt = (pages or snippets or [])[0][2]
    payload = _run_payload(pages, snippets)
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["cloud services"],
        "evidence": [{"source_id": "page", "excerpt": excerpt}],
    }
    return CompanyResearchRun.model_validate(payload)


def test_duplicate_full_pages_reject_same_url_affirmation_and_retraction() -> None:
    from company_bi.evidence import build_profile

    pages = [
        ("full_page", "static", "The company affirmed a launch."),
        ("full_page", "dynamic", "The company retracted the launch."),
    ]
    with pytest.raises(ValidationError, match="duplicate full-page"):
        CompanyResearchRun.model_validate(_run_payload(pages))

    valid = _service_run([("full_page", "static", 'Example sp. z o.o. provides "cloud services".')])
    page = next(material for material in valid.sources if material.kind == "full_page")
    duplicate = page.model_copy(
        update={
            "fetch_mode": "dynamic",
            "content": 'Example sp. z o.o. does not provide "cloud services".',
        }
    )
    unchecked = valid.model_copy(update={"sources": [*valid.sources, duplicate]})
    with pytest.raises(ValueError, match="duplicate full-page"):
        build_profile(unchecked)


def test_search_discovery_snippet_does_not_publish_proposed_service() -> None:
    from company_bi.evidence import build_profile

    excerpt = 'Example sp. z o.o. provides "cloud services".'
    run = _service_run([], [("search_snippet", "tavily", excerpt)])
    assert (
        next(source for source in run.sources if source.source.source_id == "page").kind
        == "search_snippet"
    )
    result = build_profile(run)
    assert result.products_services.state == "uncertain"
    assert result.products_services.value is None


@pytest.mark.parametrize("mode", ["static", "dynamic"])
def test_static_and_dynamic_full_pages_publish_proposed_service(mode: str) -> None:
    from company_bi.evidence import build_profile

    excerpt = 'Example sp. z o.o. provides "cloud services".'
    run = _service_run([("full_page", mode, excerpt)])
    result = build_profile(run)
    assert result.products_services.state == "supported"
    assert result.products_services.value == ["cloud services"]


def test_snippets_plus_one_full_page_publish_only_page_verified_service() -> None:
    from company_bi.evidence import build_profile

    excerpt = 'Example sp. z o.o. provides "cloud services".'
    run = _service_run(
        [("full_page", "static", excerpt)],
        [("search_snippet", "tavily", excerpt)],
    )
    result = build_profile(run)
    assert result.products_services.state == "supported"
    assert result.products_services.value == ["cloud services"]


def test_source_store_snippet_kind_tamper_cannot_promote_search_to_page() -> None:
    from company_bi.evidence import build_profile

    identity = _identity("Example sp. z o.o.")
    store = SourceStore(identity, [_source("registry")])
    excerpt = 'Example sp. z o.o. offers "cloud services".'
    page_text = 'Example sp. z o.o. does not offer "cloud services".'
    hit = store.add_search(
        title="Page",
        url=HttpUrl("https://page.test/"),
        content=excerpt,
        score=None,
        retrieved_at=STAMP,
    )
    store.store_page(
        RetrievedSource(
            source=Source(
                source_id=hit.source_id, url=hit.url, title=hit.title, retrieved_at=STAMP
            ),
            kind="full_page",
            fetch_mode="static",
            content=page_text,
        )
    )
    snapshots = store.snapshots()
    payload = _run_payload([], [])
    payload["sources"] = snapshots
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["cloud services"],
        "evidence": [{"source_id": hit.source_id, "excerpt": excerpt}],
    }
    run = CompanyResearchRun.model_validate(payload)
    published = build_profile(run)
    assert published.products_services.state != "supported"

    tampered_sources = list(snapshots)
    tampered_sources[1] = tampered_sources[1].model_copy(update={"kind": "full_page"})
    tampered_payload = {**payload, "sources": tampered_sources}
    with pytest.raises(ValidationError, match="cannot use fetch mode"):
        CompanyResearchRun.model_validate(tampered_payload)
    unchecked_run = run.model_copy(update={"sources": tampered_sources})
    with pytest.raises(ValueError, match="cannot use fetch mode"):
        build_profile(unchecked_run)
