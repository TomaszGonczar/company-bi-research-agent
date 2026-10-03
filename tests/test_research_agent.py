from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.models.test import TestModel as PydanticTestModel

from company_bi.agent import research_company
from company_bi.models import (
    CompanyIdentity,
    CompanyResearchDraft,
    CompanyResearchRun,
    RetrievedSource,
    Source,
)
from company_bi.sources import ResearchBudget


@pytest.fixture
def identity() -> CompanyIdentity:
    evidence = [{"source_id": "identity-record", "excerpt": "Verified registry identity"}]
    return CompanyIdentity.model_validate(
        {
            "nip": "1234567890",
            "legal_name": {
                "state": "supported",
                "value": "Example sp. z o.o.",
                "evidence": evidence,
            },
            "krs": {"state": "unknown", "reason": "Not provided"},
            "regon": {"state": "unknown", "reason": "Not provided"},
            "registered_city": {"state": "unknown", "reason": "Not provided"},
            "registered_address": {"state": "unknown", "reason": "Not provided"},
            "website": {"state": "unknown", "reason": "Not provided"},
            "resolved_at": datetime.now(UTC),
        }
    )


def registry_source() -> Source:
    return Source(
        source_id="identity-record",
        url="https://registry.example/",
        title="Registry record",
        retrieved_at=datetime.now(UTC),
    )


def unknown_output() -> dict[str, Any]:
    unknown = {"state": "unknown", "reason": "No source established this fact"}
    return {
        "business_description": unknown,
        "products_services": unknown,
        "industries": unknown,
        "markets": unknown,
        "employees": unknown,
        "financials": [
            {**unknown, "metric": "revenue"},
            {**unknown, "metric": "net_result"},
        ],
        "recent_developments": [],
        "limitations": ["No source established this fact"],
    }


def saved_candidate_output() -> dict[str, Any]:
    result = unknown_output()
    result["business_description"] = {
        "state": "supported",
        "value": "A saved candidate finding",
        "evidence": [{"source_id": "identity-record", "excerpt": "Verified registry evidence"}],
    }
    return result


async def run_research(identity: CompanyIdentity, output: Any) -> CompanyResearchRun:
    return await research_company(
        identity,
        [registry_source()],
        model=PydanticTestModel(call_tools=[], custom_output_args=output),
        max_seconds=10,
    )


@pytest.mark.asyncio
async def test_typed_output_keeps_host_identity_and_unknown_financial_slots(
    identity: CompanyIdentity,
) -> None:
    run = await run_research(identity, unknown_output())

    assert run.identity.model_dump() == identity.model_dump()
    assert {fact.metric for fact in run.draft.financials} == {"revenue", "net_result"}
    assert all(fact.state == "unknown" for fact in run.draft.financials)
    assert run.diagnostics.status == "completed"
    assert run.diagnostics.model_requests == 1
    assert run.diagnostics.input_tokens > 0
    assert run.diagnostics.output_tokens > 0


@pytest.mark.asyncio
async def test_model_identity_fields_never_replace_host_identity(identity: CompanyIdentity) -> None:
    invalid = {**unknown_output(), "identity": identity.model_dump(mode="json")}
    run = await run_research(identity, invalid)

    assert run.identity.model_dump() == identity.model_dump()
    assert "identity" not in run.draft.model_dump()
    assert run.diagnostics.output_retries == 1
    assert run.diagnostics.model_requests == 2
    assert run.diagnostics.status == "failed"


@pytest.mark.asyncio
async def test_invented_evidence_id_is_rejected(identity: CompanyIdentity) -> None:
    invalid = unknown_output()
    invalid["business_description"] = {
        "state": "supported",
        "value": "An invented assertion",
        "evidence": [{"source_id": "invented-source", "excerpt": "No host source"}],
    }
    run = await run_research(identity, invalid)

    assert run.draft.business_description.state == "unknown"
    assert run.diagnostics.output_retries == 1
    assert run.diagnostics.status == "failed"
    assert run.diagnostics.model_requests == 2
    assert run.diagnostics.stop_reason is not None


def test_employee_range_and_duplicate_financial_periods_use_canonical_constraints() -> None:
    payload = unknown_output()
    payload["employees"] = {
        "state": "supported",
        "value": {"kind": "range", "minimum": 20, "maximum": 35},
        "evidence": [{"source_id": "S001", "excerpt": "20–35 employees"}],
    }
    draft = CompanyResearchDraft.model_validate(payload)
    assert draft.employees.value is not None
    assert draft.employees.value.kind == "range"
    assert draft.employees.value.minimum == 20
    assert draft.employees.value.maximum == 35

    duplicate = unknown_output()
    period = {"start": "2025-01-01", "end": "2025-12-31"}
    duplicate["financials"] = [
        {**unknown_output()["financials"][0], "period": period},
        {**unknown_output()["financials"][1], "period": period},
        {**unknown_output()["financials"][0], "period": period},
    ]
    with pytest.raises(ValidationError):
        CompanyResearchDraft.model_validate(duplicate)

    conflicting_observations = {
        **unknown_output(),
        "financials": [
            {
                "state": "uncertain",
                "reason": "Sources report conflicting revenue amounts",
                "evidence": [{"source_id": "S001", "excerpt": "Conflicting revenue figures"}],
                "metric": "revenue",
                "period": period,
            },
            unknown_output()["financials"][1],
        ],
    }
    uncertain_draft = CompanyResearchDraft.model_validate(conflicting_observations)
    assert uncertain_draft.financials[0].state == "uncertain"


def test_unknown_financials_are_valid_when_both_metrics_are_attempted() -> None:
    draft = CompanyResearchDraft.model_validate(unknown_output())
    assert [(fact.metric, fact.value) for fact in draft.financials] == [
        ("revenue", None),
        ("net_result", None),
    ]


@pytest.mark.asyncio
async def test_search_budget_exhaustion_is_visible_without_a_provider_call(
    identity: CompanyIdentity, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ExhaustedBudget(ResearchBudget):
        def __init__(self, max_seconds: float = 180) -> None:
            super().__init__(max_seconds=max_seconds, max_searches=0)

    monkeypatch.setattr("company_bi.agent.ResearchBudget", ExhaustedBudget)
    run = await research_company(
        identity,
        [registry_source()],
        model=PydanticTestModel(call_tools=["search_web"], custom_output_args=unknown_output()),
        max_seconds=10,
    )

    assert run.diagnostics.status == "completed"
    assert run.diagnostics.searches == 0
    assert run.diagnostics.stop_reason is not None
    assert all(fact.state == "unknown" for fact in run.draft.financials)


@pytest.mark.asyncio
async def test_saved_partial_progress_survives_later_provider_failure(
    identity: CompanyIdentity,
) -> None:
    calls = 0

    def save_then_fail(_messages: Any, _info: Any) -> ModelResponse:
        nonlocal calls
        calls += 1
        if calls == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "save_progress",
                        {"draft": saved_candidate_output()},
                        tool_call_id="save-progress-1",
                    )
                ]
            )
        raise RuntimeError("provider unavailable")

    run = await research_company(
        identity,
        [registry_source()],
        model=FunctionModel(save_then_fail),
        max_seconds=10,
    )

    assert run.diagnostics.status == "partial"
    assert run.diagnostics.stop_reason is not None
    assert run.draft.business_description.state == "supported"
    assert run.draft.business_description.value == "A saved candidate finding"
    assert run.draft.business_description.evidence[0].source_id == "identity-record"
    assert run.diagnostics.model_requests == 2
    assert run.diagnostics.input_tokens > 0
    assert run.diagnostics.output_tokens > 0


@pytest.mark.asyncio
async def test_provider_failure_without_progress_returns_explicit_unknowns(
    identity: CompanyIdentity,
) -> None:
    def fail_model(_messages: Any, _info: Any) -> Any:
        raise RuntimeError("provider unavailable")

    run = await research_company(
        identity, [registry_source()], model=FunctionModel(fail_model), max_seconds=10
    )

    assert run.diagnostics.status == "failed"
    assert run.diagnostics.model_requests == 1
    assert run.diagnostics.stop_reason is not None
    assert all(fact.state == "unknown" for fact in run.draft.financials)


@pytest.mark.asyncio
async def test_deadline_failure_reports_interruption(identity: CompanyIdentity) -> None:
    run = await research_company(
        identity,
        [registry_source()],
        model=PydanticTestModel(call_tools=[], custom_output_args=unknown_output()),
        max_seconds=0,
    )

    assert run.diagnostics.status == "failed"
    assert run.diagnostics.model_requests == 0
    assert run.diagnostics.stop_reason is not None


@pytest.mark.asyncio
async def test_run_orphan_references_fail_but_retained_material_versions_are_valid(
    identity: CompanyIdentity,
) -> None:
    run = await run_research(identity, saved_candidate_output())

    orphan_identity = run.model_dump(mode="json")
    orphan_identity["identity"]["legal_name"]["evidence"][0]["source_id"] = "missing-identity"
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(orphan_identity)

    orphan_draft = run.model_dump(mode="json")
    orphan_draft["draft"]["business_description"]["evidence"][0]["source_id"] = "missing-finding"
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate(orphan_draft)

    retained = run.model_dump(mode="json")
    source = run.sources[0].source
    retained["sources"].extend(
        [
            RetrievedSource(
                source=source,
                kind="search_snippet",
                content="Discovery snippet",
                fetch_mode="tavily",
            ).model_dump(mode="json"),
            RetrievedSource(
                source=source,
                kind="full_page",
                content="Retrieved full page",
                fetch_mode="static",
            ).model_dump(mode="json"),
        ]
    )
    accepted = CompanyResearchRun.model_validate(retained)
    assert {(material.source.source_id, material.kind) for material in accepted.sources} == {
        (source.source_id, "registry"),
        (source.source_id, "search_snippet"),
        (source.source_id, "full_page"),
    }


@pytest.mark.asyncio
async def test_persisted_zero_financial_candidate_requires_full_page_material(
    identity: CompanyIdentity,
) -> None:
    run = await run_research(identity, unknown_output())
    payload = run.model_dump(mode="json")
    source = Source(
        source_id="financial-source",
        url="https://issuer.example/results",
        title="Financial results",
        retrieved_at=run.generated_at,
    )
    excerpt = "Legal entity revenue: PLN 0 units, 2025-01-01 through 2025-12-31."
    payload["draft"]["financials"][0] = {
        "state": "uncertain",
        "metric": "revenue",
        "value": "0",
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "units",
        "scope": "legal_entity",
        "evidence": [{"source_id": source.source_id, "excerpt": excerpt}],
        "reason": "Candidate needs semantic verification",
    }
    snippet = RetrievedSource(
        source=source, kind="search_snippet", content=excerpt, fetch_mode="tavily"
    )
    payload["sources"].append(snippet.model_dump(mode="json"))
    with pytest.raises(ValidationError):
        CompanyResearchRun.model_validate_json(json.dumps(payload))

    page = RetrievedSource(source=source, kind="full_page", content=excerpt, fetch_mode="static")
    payload["sources"].append(page.model_dump(mode="json"))
    accepted = CompanyResearchRun.model_validate_json(json.dumps(payload))
    assert accepted.draft.financials[0].value == 0
    assert accepted.draft.financials[0].state == "uncertain"


@pytest.mark.asyncio
async def test_model_cannot_replace_identity_in_draft_output(
    identity: CompanyIdentity,
) -> None:
    injected = {
        **unknown_output(),
        "identity": {"nip": "5831014898", "legal_name": "Another company"},
    }
    result = await run_research(identity, injected)
    assert result.identity == identity
    assert result.diagnostics.status == "failed"
    assert result.diagnostics.output_retries == 1
    assert result.draft.business_description.state == "unknown"


@pytest.mark.parametrize(
    ("state", "amount"),
    [("supported", "1703.4"), ("uncertain", "1703.4"), ("uncertain", "0")],
)
@pytest.mark.asyncio
async def test_pdf_discovery_snippet_cannot_supply_a_financial_amount(
    identity: CompanyIdentity, monkeypatch: pytest.MonkeyPatch, state: str, amount: str
) -> None:
    excerpt = "Revenue PLN 1703.4 million for January 1 to December 31, 2025, legal entity."

    async def controlled_search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "results": [
                {
                    "title": "Annual report",
                    "url": "https://example.com/report.pdf",
                    "content": excerpt,
                }
            ]
        }

    monkeypatch.setattr("tavily.AsyncTavilyClient.search", controlled_search)
    output = unknown_output()
    output["financials"][0] = {
        "state": state,
        "metric": "revenue",
        "value": amount,
        "period": {"start": "2025-01-01", "end": "2025-12-31"},
        "currency": "PLN",
        "unit": "millions",
        "scope": "legal_entity",
        "evidence": [{"source_id": "S001", "excerpt": excerpt}],
    }
    if state == "uncertain":
        output["financials"][0]["reason"] = "The PDF was discovered but not retrieved"
    requests = 0

    async def respond(messages: Any, info: Any) -> ModelResponse:
        nonlocal requests
        requests += 1
        if requests == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart("search_web", {"query": "Company annual results"}, "search"),
                ]
            )
        return ModelResponse(
            parts=[
                ToolCallPart(info.output_tools[0].name, output, "output"),
            ]
        )

    run = await research_company(
        identity, [registry_source()], model=FunctionModel(respond), max_seconds=10
    )
    assert run.diagnostics.status == "failed"
    assert run.diagnostics.output_retries == 1
    assert run.draft.financials[0].value is None
    assert next(item for item in run.sources if item.source.source_id == "S001").kind == (
        "search_snippet"
    )
