"""Validation-only schema for a future component-level holdout oracle."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any, Literal

from pydantic import Field, StringConstraints, model_validator

from company_bi.models import Model
from company_bi.strict_cases import Classification

CaseId = Annotated[str, StringConstraints(strict=True, min_length=1)]
FactPath = Annotated[str, StringConstraints(strict=True, min_length=1)]

_PATH = re.compile(
    r"(?:business_description|products_services|industries|markets|employees|"
    r"financials\.(?:0|[1-9][0-9]*)|recent_developments\.(?:0|[1-9][0-9]*)|"
    r"identity\.(?:legal_name|krs|regon|registered_city|registered_address|website))"
)


class ProfileExpectation(Model):
    """Expected profile components; omitted checks are unassessed, null checks clear."""

    kind: Literal["profile"]
    state: Literal["supported", "uncertain", "unknown"]
    value: Any
    reason_nonempty: bool | None = None
    evidence_source_ids: list[str] | None = None
    period: dict[str, Any] | None = None
    currency: str | None = None
    unit: Literal["units", "thousands", "millions", "billions"] | None = None
    scope: Literal["legal_entity", "group"] | None = None
    group_name: str | None = None
    as_of: str | None = None
    published_on: str | None = None
    occurred_on: str | None = None

    @model_validator(mode="after")
    def unique_evidence_ids(self) -> ProfileExpectation:
        if "evidence_source_ids" in self.model_fields_set and self.evidence_source_ids is None:
            raise ValueError("evidence_source_ids must be omitted or a list, not null")
        if self.evidence_source_ids is not None:
            if len(self.evidence_source_ids) != len(set(self.evidence_source_ids)):
                raise ValueError("evidence_source_ids must not contain duplicates")
            if any(not item for item in self.evidence_source_ids):
                raise ValueError("evidence_source_ids must contain non-empty strings")
        return self


class RejectionExpectation(Model):
    """Expected explicit rejection at a named boundary."""

    kind: Literal["reject"]
    stage: Literal["model", "run"]


Expectation = Annotated[ProfileExpectation | RejectionExpectation, Field(discriminator="kind")]


class HoldoutCase(Model):
    case_id: CaseId
    classification: Classification
    target: FactPath
    expected: Expectation

    @model_validator(mode="after")
    def check_case_contract(self) -> HoldoutCase:
        if not self.case_id.strip():
            raise ValueError("case_id must not be blank")
        if not _PATH.fullmatch(self.target):
            raise ValueError("unsupported or noncanonical target fact path")
        boundary = self.classification in {"IDENTITY_INVALID", "PROVENANCE_INVALID"}
        if not boundary and self.expected.kind == "reject" and self.expected.stage != "run":
            raise ValueError("semantic rejection expectations must use run stage")
        if self.expected.kind == "profile":
            family = self.target.split(".", 1)[0]
            supplied = set(self.expected.model_fields_set)
            applicable = {
                "financials": {"period", "currency", "unit", "scope", "group_name"},
                "employees": {"as_of"},
                "recent_developments": {"published_on", "occurred_on"},
            }.get(family, set())
            component_fields = {
                "period",
                "currency",
                "unit",
                "scope",
                "group_name",
                "as_of",
                "published_on",
                "occurred_on",
            }
            invalid = (supplied & component_fields) - applicable
            if invalid:
                raise ValueError(f"components {sorted(invalid)} do not apply to {self.target}")
            for date_field in ("as_of", "published_on", "occurred_on"):
                value = getattr(self.expected, date_field)
                if date_field in supplied and value is not None:
                    try:
                        parsed = date.fromisoformat(value)
                    except ValueError as error:
                        raise ValueError(f"{date_field} must be an ISO date") from error
                    if parsed.isoformat() != value:
                        raise ValueError(f"{date_field} must be a canonical ISO date")
            if "period" in supplied and self.expected.period is not None:
                period = self.expected.period
                if set(period) != {"start", "end"} or any(
                    not isinstance(period[key], str) for key in ("start", "end")
                ):
                    raise ValueError("period must contain exactly string start and end dates")
                for endpoint in ("start", "end"):
                    try:
                        parsed = date.fromisoformat(period[endpoint])
                    except ValueError as error:
                        raise ValueError("period endpoints must be ISO dates") from error
                    if parsed.isoformat() != period[endpoint]:
                        raise ValueError("period endpoints must be canonical ISO dates")
            if family == "financials":
                if not isinstance(self.expected.value, (str, type(None))):
                    raise ValueError("expected financial value must be a decimal string or null")
                if isinstance(self.expected.value, str):
                    try:
                        amount = Decimal(self.expected.value)
                    except InvalidOperation as error:
                        raise ValueError(
                            "expected financial value must be a decimal string"
                        ) from error
                    if not amount.is_finite():
                        raise ValueError("expected financial value must be finite")
        return self


class HoldoutOracle(Model):
    """Unique, machine-readable expected component results."""

    cases: list[HoldoutCase] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_case_ids(self) -> HoldoutOracle:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("case_id values must be unique")
        return self
