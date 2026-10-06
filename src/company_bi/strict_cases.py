"""Strict authoring schemas and supported fact-path resolution for holdout cases."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


Classification = Literal[
    "SUPPORTED_CONTRACT_POSITIVE",
    "OUT_OF_CONTRACT_TRUE",
    "UNSAFE_NEGATIVE",
    "IDENTITY_INVALID",
    "PROVENANCE_INVALID",
]
ExpectedAction = Literal["publish", "abstain", "reject"]
FieldPath = Literal[
    "draft.business_description",
    "draft.products_services",
    "draft.industries",
    "draft.markets",
    "draft.employees",
    "draft.financials.revenue",
    "draft.financials.net_result",
    "draft.recent_developments",
]


class SourceAssertionSpec(StrictModel):
    text: str
    published_on: str | None = None


class ReportingPeriodSpec(StrictModel):
    start: str = Field(strict=True)
    end: str = Field(strict=True)


class FinancialContext(StrictModel):
    period: ReportingPeriodSpec | None = None
    currency: Any = None
    unit: Any = None
    scope: Any = None
    group_name: Any = None


class CandidateFactSpec(StrictModel):
    field_path: FieldPath
    value: Any = None
    state: Literal["supported", "uncertain", "unknown"] = "supported"
    context: str | None = None
    reason: str | None = None
    as_of: str | None = None
    context_fields: FinancialContext | None = None

    @model_validator(mode="after")
    def check_placement_and_financial_precision(self) -> CandidateFactSpec:
        if "as_of" in self.model_fields_set and self.field_path != "draft.employees":
            raise ValueError("candidate_fact.as_of is only valid for employees")
        if "context_fields" in self.model_fields_set and not self.field_path.startswith(
            "draft.financials."
        ):
            raise ValueError("candidate_fact.context_fields is only valid for financials")
        if self.field_path.startswith("draft.financials.") and self.value is not None:
            if not isinstance(self.value, str):
                raise ValueError("non-null financial values must be decimal strings")
            try:
                amount = Decimal(self.value)
            except (InvalidOperation, ValueError) as error:
                raise ValueError("non-null financial values must be decimal strings") from error
            if not amount.is_finite():
                raise ValueError("non-null financial values must be finite decimal strings")
        if isinstance(self.value, dict):
            if self.field_path == "draft.employees":
                allowed = (
                    {"kind", "count"}
                    if self.value.get("kind") == "exact"
                    else {"kind", "minimum", "maximum"}
                )
            elif self.field_path == "draft.recent_developments":
                allowed = {"title", "summary", "published_on", "occurred_on"}
            else:
                allowed = set()
            unknown = self.value.keys() - allowed
            if unknown:
                raise ValueError(
                    f"unknown candidate_fact.value fields: {', '.join(sorted(unknown))}"
                )
        if self.state == "unknown" and self.value is not None:
            raise ValueError("unknown candidate facts must use a null value")
        return self


class PublicationMetadataSpec(StrictModel):
    url: str | None = None
    title: str | None = None
    published_on: str | None = None
    kind: str | None = None
    fetch_mode: str | None = None


class IdentityPatch(StrictModel):
    nip: Any = None
    legal_name: Any = None
    krs: Any = None
    regon: Any = None
    registered_city: Any = None
    registered_address: Any = None
    website: Any = None
    resolved_at: Any = None

    @model_validator(mode="before")
    @classmethod
    def validate_nested_fact_keys(cls, value: Any) -> Any:
        fact_fields = {"state", "value", "evidence", "reason"}
        evidence_fields = {"source_id", "excerpt"}
        if isinstance(value, dict):
            for name in {
                "legal_name",
                "krs",
                "regon",
                "registered_city",
                "registered_address",
                "website",
            }:
                fact = value.get(name)
                if isinstance(fact, dict):
                    unknown = fact.keys() - fact_fields
                    if unknown:
                        raise ValueError(
                            f"unknown identity fact fields: {', '.join(sorted(unknown))}"
                        )
                    evidence = fact.get("evidence")
                    if isinstance(evidence, list):
                        for ref in evidence:
                            if isinstance(ref, dict):
                                unknown = ref.keys() - evidence_fields
                                if unknown:
                                    raise ValueError(
                                        "unknown identity evidence fields: "
                                        f"{', '.join(sorted(unknown))}"
                                    )
        return value


class SourceMetadataPatch(StrictModel):
    source_id: Any = None
    url: Any = None
    title: Any = None
    retrieved_at: Any = None
    published_on: Any = None
    redirect_chain: Any = None
    publication_blocked_reason: Any = None


class SourcePatch(StrictModel):
    kind: Any = None
    fetch_mode: Any = None
    content: Any = None
    source: Any = None

    @model_validator(mode="after")
    def validate_nested_source_patch(self) -> SourcePatch:
        if isinstance(self.source, dict):
            SourceMetadataPatch.model_validate(self.source)
        return self


class IndexedSourceMutation(StrictModel):
    index: Any
    changes: SourcePatch


class EnvelopeSpec(StrictModel):
    identity: IdentityPatch | None = None
    sources: list[IndexedSourceMutation] = Field(default_factory=list)


class AuthorSpec(StrictModel):
    case_id: str
    classification: Classification
    source_assertion: SourceAssertionSpec
    candidate_fact: CandidateFactSpec
    expected_action: ExpectedAction
    publication_metadata: PublicationMetadataSpec | None = None
    envelope: EnvelopeSpec | None = None

    @model_validator(mode="after")
    def check_author_requirements(self) -> AuthorSpec:
        if not self.case_id.strip():
            raise ValueError("case_id must be nonempty")
        if not self.source_assertion.text.strip():
            raise ValueError("source_assertion.text is required")
        if self.envelope and self.classification not in {"IDENTITY_INVALID", "PROVENANCE_INVALID"}:
            raise ValueError(
                "envelope mutations are reserved for identity/provenance boundary controls"
            )
        return self


def resolve_fact_path(document: dict[str, Any], path: str) -> dict[str, Any]:
    """Resolve one documented fact path in a raw run or serialized profile."""
    if not isinstance(document, dict) or not isinstance(path, str):
        raise ValueError("document and fact path must be objects and strings")
    root: Any = document.get("draft", document)
    if not isinstance(root, dict):
        raise ValueError(f"unsupported fact path: {path}")
    if path.startswith("identity."):
        identity = document.get("identity")
        name = path.removeprefix("identity.")
        allowed = {"legal_name", "krs", "regon", "registered_city", "registered_address", "website"}
        fact = identity.get(name) if name in allowed and isinstance(identity, dict) else None
        if isinstance(fact, dict):
            return fact
        raise ValueError(f"unsupported or missing fact path: {path}")
    if path in {"business_description", "products_services", "industries", "markets", "employees"}:
        fact = root.get(path)
    else:
        match = re.fullmatch(r"(financials|recent_developments)\.(0|[1-9][0-9]*)", path)
        if not match:
            raise ValueError(f"unsupported fact path: {path}")
        collection, index_text = match.groups()
        values = root.get(collection)
        index = int(index_text)
        if not isinstance(values, list) or index >= len(values):
            raise ValueError(f"unsupported or missing fact path: {path}")
        fact = values[index]
    if isinstance(fact, dict):
        return fact
    raise ValueError(f"unsupported or missing fact path: {path}")
