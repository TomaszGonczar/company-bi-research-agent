"""Legacy source-lineage quarantine through validated publication."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from company_bi.evidence import build_profile
from company_bi.models import CompanyResearchRun
from company_bi.renderer import render_json, render_markdown
from company_bi.sources import SourceStore


def _ref(source_id: str, excerpt: str) -> dict[str, str]:
    return {"source_id": source_id, "excerpt": excerpt}


def _legacy_pair(run: CompanyResearchRun, *, other_domain: bool = False) -> dict[str, Any]:
    payload = run.model_dump(mode="python", exclude_none=True)
    # Simulate the historical wire shape: the field was absent on every serialized source.
    for material in payload["sources"]:
        material["source"].pop("redirect_chain", None)
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    snippet = deepcopy(page)
    snippet["kind"] = "search_snippet"
    snippet["fetch_mode"] = "tavily"
    snippet["content"] = "Legacy discovery excerpt"
    snippet["source"]["url"] = (
        "https://different.example/discovery" if other_domain else "https://page.example/discovery"
    )
    page["source"]["url"] = "https://page.example/final"
    payload["sources"].append(snippet)
    return payload


def _published(run: CompanyResearchRun) -> tuple[dict[str, Any], str, str]:
    profile = build_profile(CompanyResearchRun.model_validate_json(run.model_dump_json()))
    return (
        json.loads(render_json(profile)),
        render_json(profile),
        render_markdown(profile),
    )


def test_unchanged_asseco_legacy_fixture_publishes_registry_and_independent_research() -> None:
    path = Path(__file__).parents[2] / "examples/evals/retained/asseco-poland.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    original_sources = deepcopy(payload["sources"])
    assert not any("redirect_chain" in item["source"] for item in original_sources)
    run = CompanyResearchRun.model_validate(payload)
    profile_data, _, _ = _published(run)

    assert profile_data["identity"]["legal_name"]["state"] == "supported"
    assert profile_data["business_description"]["state"] == "uncertain"
    assert "mf-vat-5220003782-20261003T122434221952Z" in {
        source["source_id"] for source in profile_data["sources"]
    }
    assert payload["sources"] == original_sources
    assert (
        next(source for source in profile_data["sources"] if source["source_id"] == "S006")[
            "publication_blocked_reason"
        ]
        == "unproven_legacy_url_relationship"
    )


def test_legacy_mismatched_ids_are_quarantined_but_independent_identity_and_page_survive(
    make_run: Any,
) -> None:
    good_text = 'Example sp. z o.o. operates as "industrial packaging supplier".'
    product_text = 'Example sp. z o.o. offers "industrial packaging".'
    run = make_run(
        good_text,
        business_description={
            "state": "supported",
            "value": "industrial packaging supplier",
            "evidence": [_ref("page", good_text)],
        },
    )
    payload = _legacy_pair(run, other_domain=True)
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    page["content"] = product_text
    independent = deepcopy(page)
    independent["source"]["source_id"] = "independent"
    independent["source"]["url"] = "https://independent.example/company"
    independent["content"] = good_text
    payload["sources"].append(independent)
    payload["draft"]["business_description"]["evidence"] = [_ref("independent", good_text)]
    # The quarantined page has a real product assertion, but cannot authorize it.
    payload["draft"]["products_services"] = {
        "state": "supported",
        "value": ["industrial packaging"],
        "evidence": [_ref("page", product_text)],
    }
    validated = CompanyResearchRun.model_validate(payload)
    profile_data, _, _ = _published(validated)

    assert profile_data["identity"]["legal_name"]["state"] == "supported"
    assert profile_data["business_description"]["state"] == "supported"
    assert profile_data["products_services"]["state"] != "supported"
    assert "registry" in {source["source_id"] for source in profile_data["sources"]}
    assert {
        source["source_id"]: source["publication_blocked_reason"]
        for source in profile_data["sources"]
        if source["publication_blocked_reason"] is not None
    } == {"page": "unproven_legacy_url_relationship"}


def test_quarantined_employee_conflict_does_not_downgrade_independent_page_evidence(
    make_run: Any,
) -> None:
    valid = "Example sp. z o.o. employs 42 people as of 2026-01-15."
    conflicting = "Example sp. z o.o. employs 900 people as of 2026-01-15."
    run = make_run(
        valid,
        employees={
            "state": "supported",
            "value": {"kind": "exact", "count": 42},
            "as_of": "2026-01-15",
            "evidence": [_ref("page", valid)],
        },
    )
    payload = _legacy_pair(run)
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    independent = deepcopy(page)
    independent["source"]["source_id"] = "independent"
    independent["source"]["url"] = "https://independent.example/company"
    payload["sources"].append(independent)
    payload["draft"]["employees"]["evidence"] = [_ref("independent", valid)]
    page["content"] = conflicting
    snippet = next(item for item in payload["sources"] if item["kind"] == "search_snippet")
    snippet["content"] = conflicting
    result, _, _ = _published(CompanyResearchRun.model_validate(payload))
    assert result["employees"]["state"] == "supported"
    assert result["employees"]["value"]["count"] == 42


def test_quarantine_marker_survives_json_round_trip_and_is_denial_only(make_run: Any) -> None:
    quote = "Example sp. z o.o. provides industrial packaging to customers."
    run = make_run(
        quote,
        business_description={
            "state": "supported",
            "value": "provides industrial packaging to customers",
            "evidence": [_ref("page", quote)],
        },
    )
    payload = _legacy_pair(run)
    validated = CompanyResearchRun.model_validate(payload)
    first, _, _ = _published(validated)
    second = CompanyResearchRun.model_validate_json(validated.model_dump_json())
    republished, _, _ = _published(second)

    assert first == republished
    assert first["business_description"]["state"] != "supported"
    denied = [source for source in first["sources"] if source.get("publication_blocked_reason")]
    assert denied
    assert all(
        item["publication_blocked_reason"] == "unproven_legacy_url_relationship" for item in denied
    )


def test_current_verified_redirect_lineage_remains_publishable(make_run: Any) -> None:
    quote = 'Example sp. z o.o. operates as "industrial packaging supplier".'
    run = make_run(
        quote,
        business_description={
            "state": "supported",
            "value": "industrial packaging supplier",
            "evidence": [_ref("page", quote)],
        },
    )
    payload = run.model_dump(mode="python")
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    page["source"]["url"] = "https://www.page.example/final"
    page["source"]["redirect_chain"] = [
        "https://page.example/discovery",
        "https://www.page.example/final",
    ]
    discovery = deepcopy(page)
    discovery["kind"] = "search_snippet"
    discovery["fetch_mode"] = "tavily"
    discovery["content"] = "Discovery"
    discovery["source"]["url"] = "https://page.example/discovery"
    discovery["source"]["redirect_chain"] = []
    payload["sources"].append(discovery)
    result, _, _ = _published(CompanyResearchRun.model_validate(payload))
    assert result["business_description"]["state"] == "supported"


def test_explicit_empty_chain_does_not_enter_legacy_compatibility_path(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging to customers.")
    payload = _legacy_pair(run)
    for material in payload["sources"]:
        material["source"]["redirect_chain"] = []
    with pytest.raises((ValidationError, ValueError)):
        CompanyResearchRun.model_validate(payload)


@pytest.mark.parametrize(
    "chain",
    [
        pytest.param(["https://page.example/final"], id="too-short"),
        pytest.param(
            ["https://other.example/start", "https://page.example/final"],
            id="contradictory-origin",
        ),
    ],
)
def test_legacy_quarantine_does_not_accept_malformed_or_current_chains(
    make_run: Any, chain: list[str]
) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging to customers.")
    payload = _legacy_pair(run)
    page = next(item for item in payload["sources"] if item["kind"] == "full_page")
    page["source"]["redirect_chain"] = chain
    with pytest.raises((ValidationError, ValueError)):
        CompanyResearchRun.model_validate(payload)


def test_run_level_identity_inconsistency_still_rejects_publication(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging to customers.")
    payload = _legacy_pair(run)
    payload["identity"]["legal_name"]["evidence"][0]["excerpt"] = "Wrong company"
    with pytest.raises(ValueError):
        _published(CompanyResearchRun.model_validate(payload))


def test_source_store_rejects_publication_blocked_material(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging to customers.")
    registry = next(item for item in run.sources if item.kind == "registry")
    store = SourceStore(run.identity, [registry.source])
    page = next(item for item in run.sources if item.kind == "full_page")
    blocked_page = page.model_copy(
        update={
            "source": page.source.model_copy(
                update={"publication_blocked_reason": "unproven_legacy_url_relationship"}
            )
        }
    )
    with pytest.raises(ValueError, match="publication-blocked"):
        store.store_page(blocked_page)


def test_registry_address_in_comment_cannot_support_registered_address(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    payload = run.model_dump(mode="python")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = json.dumps(
        {
            "result": {
                "subject": {
                    "name": "Example sp. z o.o.",
                    "nip": "1234563218",
                }
            },
            "comment": "Registered address: 10 Main Street",
        }
    )
    payload["identity"]["registered_address"] = {
        "state": "supported",
        "value": "10 Main Street",
        "evidence": [_ref("registry", "10 Main Street")],
    }
    with pytest.raises(ValueError):
        CompanyResearchRun.model_validate(payload)


def test_duplicate_mf_identity_declarations_reject_run(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    payload = run.model_dump(mode="python")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = (
        '{"result":{"subject":{"name":"Example sp. z o.o.",'
        '"name":"Example sp. z o.o.","nip":"1234563218"}}}'
    )
    with pytest.raises(ValueError):
        CompanyResearchRun.model_validate(payload)


def test_legacy_registry_snapshot_rejects_evidence_only_address(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    payload = run.model_dump(mode="python")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = (
        "MF VAT register identity material (not a raw registry response):\n"
        "legal_name: Example sp. z o.o.\n"
        "legal_name evidence from registry: Example sp. z o.o.\n"
        "krs: unknown; Not supplied\n"
        "regon: unknown; Not supplied\n"
        "registered_city: unknown; Not supplied\n"
        "registered_address: unknown; Not supplied\n"
        "registered_address evidence from registry: 10 Main Street\n"
        "website: unknown; Not supplied\n"
        "NIP: 1234563218"
    )
    payload["identity"]["registered_address"] = {
        "state": "supported",
        "value": "10 Main Street",
        "evidence": [_ref("registry", "10 Main Street")],
    }
    with pytest.raises(ValueError):
        CompanyResearchRun.model_validate(payload)


def test_publication_blocked_registry_cannot_establish_identity(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    payload = run.model_dump(mode="python")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["source"]["publication_blocked_reason"] = "unproven_legacy_url_relationship"
    with pytest.raises(ValueError):
        CompanyResearchRun.model_validate(payload)


def test_mf_subject_nip_must_match_identity(make_run: Any) -> None:
    run = make_run("Example sp. z o.o. provides industrial packaging.")
    payload = run.model_dump(mode="python")
    registry = next(item for item in payload["sources"] if item["kind"] == "registry")
    registry["content"] = json.dumps(
        {
            "result": {
                "subject": {
                    "name": "Example sp. z o.o.",
                    "nip": "9876543210",
                }
            }
        }
    )
    with pytest.raises(ValueError):
        CompanyResearchRun.model_validate(payload)
