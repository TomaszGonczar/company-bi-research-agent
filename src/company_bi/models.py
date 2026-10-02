"""Publication schemas, not an identity resolver or an evidence-verification engine."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    model_validator,
)

Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
NIP = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9]{10}$")]
KRS = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9]{10}$")]
REGON = Annotated[str, StringConstraints(strict=True, pattern=r"^(?:[0-9]{9}|[0-9]{14})$")]
Currency = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{3}$")]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
PositiveInt = Annotated[int, Field(strict=True, gt=0)]
Money = Annotated[Decimal, Field(allow_inf_nan=False)]
TextList = Annotated[list[Text], Field(min_length=1)]
EvidenceState = Literal["supported", "uncertain", "unknown"]
EntityScope = Literal["legal_entity", "group"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_default=True)


class InputRow(Model):
    """Normalized row shape; checksum validation belongs to deterministic ingest."""

    row_number: PositiveInt
    nip: NIP


class Source(Model):
    """Metadata for a successful retrieval, created only by the retriever."""

    source_id: Text
    url: HttpUrl
    title: Text
    retrieved_at: AwareDatetime
    published_on: date | None = None


class EvidenceRef(Model):
    source_id: Text
    excerpt: Text


class Fact[T](Model):
    state: EvidenceState
    value: T | None = None
    evidence: list[EvidenceRef] = Field(default_factory=list)
    reason: Text | None = None

    @model_validator(mode="after")
    def check_evidence_state(self) -> Self:
        if self.state == "unknown":
            if self.value is not None or self.evidence:
                raise ValueError("unknown cannot assert a value or supporting evidence")
            if self.reason is None:
                raise ValueError("unknown requires a missing-data reason")
        elif self.state == "supported":
            if self.value is None or not self.evidence:
                raise ValueError("supported requires a value and evidence")
        elif not self.evidence or self.reason is None:
            raise ValueError("uncertain requires candidate evidence and a reason")
        return self


class CompanyIdentity(Model):
    """Resolved NIP anchor; legal identity is established before LLM research."""

    nip: NIP
    legal_name: Fact[Text]
    krs: Fact[KRS]
    regon: Fact[REGON]
    registered_city: Fact[Text]
    registered_address: Fact[Text]
    website: Fact[HttpUrl]
    resolved_at: AwareDatetime

    @model_validator(mode="after")
    def require_resolved_identity(self) -> Self:
        if self.legal_name.state != "supported":
            raise ValueError("a profile requires a deterministically resolved legal name")
        return self


class ExactEmployees(Model):
    kind: Literal["exact"]
    count: NonNegativeInt


class EmployeeRange(Model):
    kind: Literal["range"]
    minimum: NonNegativeInt | None = None
    maximum: NonNegativeInt | None = None

    @model_validator(mode="after")
    def check_bounds(self) -> Self:
        if self.minimum is None and self.maximum is None:
            raise ValueError("an employee range requires at least one bound")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("employee range minimum exceeds maximum")
        return self


EmployeeValue = Annotated[ExactEmployees | EmployeeRange, Field(discriminator="kind")]


class EmployeeFact(Fact[EmployeeValue]):
    as_of: date | None = None


class ReportingPeriod(Model):
    start: date
    end: date

    @model_validator(mode="after")
    def check_order(self) -> Self:
        if self.start > self.end:
            raise ValueError("reporting period start exceeds end")
        return self


class FinancialFact(Fact[Money]):
    """Value is the reported decimal amount in the explicitly stated unit."""

    metric: Literal["revenue", "net_result"]
    period: ReportingPeriod | None = None
    currency: Currency | None = None
    unit: Literal["units", "thousands", "millions", "billions"] | None = None
    scope: EntityScope | None = None
    group_name: Text | None = None

    @model_validator(mode="after")
    def require_amount_context(self) -> Self:
        if self.value is not None:
            if any(item is None for item in (self.period, self.currency, self.unit, self.scope)):
                raise ValueError("a financial amount requires period, currency, unit and scope")
            if self.scope == "group" and self.group_name is None:
                raise ValueError("a group financial amount requires the reported group name")
        if self.group_name is not None and self.scope != "group":
            raise ValueError("group_name is only valid for group scope")
        return self


class EventDetails(Model):
    title: Text
    summary: Text
    published_on: date
    occurred_on: date | None = None


class CompanyEvent(Fact[EventDetails]):
    """A dated development with its own publication state and evidence."""


class CompanyProfile(Model):
    schema_version: Literal["0.1"] = "0.1"
    status: Literal["complete", "partial"]
    generated_at: AwareDatetime
    identity: CompanyIdentity
    business_description: Fact[Text]
    products_services: Fact[TextList]
    industries: Fact[TextList]
    markets: Fact[TextList]
    employees: EmployeeFact
    financials: list[FinancialFact] = Field(min_length=2, max_length=6)
    recent_developments: list[CompanyEvent] = Field(max_length=3)
    sources: list[Source] = Field(min_length=1)
    limitations: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_profile_contract(self) -> Self:
        source_ids = {source.source_id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("source IDs must be unique within a profile")
        if any(source.retrieved_at > self.generated_at for source in self.sources):
            raise ValueError("a source cannot be retrieved after profile generation")
        if self.identity.resolved_at > self.generated_at:
            raise ValueError("identity cannot be resolved after profile generation")

        facts: tuple[Fact[Any], ...] = (
            self.identity.legal_name,
            self.identity.krs,
            self.identity.regon,
            self.identity.website,
            self.business_description,
            self.products_services,
            self.industries,
            self.markets,
            self.employees,
            *self.financials,
            *self.recent_developments,
        )
        location_facts = (self.identity.registered_city, self.identity.registered_address)
        for fact in (*facts, *location_facts):
            if any(ref.source_id not in source_ids for ref in fact.evidence):
                raise ValueError("evidence must reference a source in the retrieved-source ledger")

        if {fact.metric for fact in self.financials} != {"revenue", "net_result"}:
            raise ValueError("both financial metrics must be represented, even when unknown")
        periods = {
            (fact.period.start, fact.period.end)
            for fact in self.financials
            if fact.period is not None
        }
        if len(periods) > 3:
            raise ValueError("financials may cover at most three reporting periods")
        financial_keys = [
            (
                fact.metric,
                fact.period.start if fact.period else None,
                fact.period.end if fact.period else None,
            )
            for fact in self.financials
        ]
        if len(set(financial_keys)) != len(financial_keys):
            raise ValueError("conflicting metric/period observations belong in one uncertain fact")

        today = self.generated_at.date()
        try:
            recent_start = today.replace(year=today.year - 1)
        except ValueError:  # Leap-day reports use February 28 in the preceding year.
            recent_start = date(today.year - 1, 2, 28)
        for event in self.recent_developments:
            if event.value is not None and not recent_start <= event.value.published_on <= today:
                raise ValueError("recent developments must be published within the last 12 months")

        has_gaps = (
            bool(self.limitations)
            or not self.recent_developments
            or any(fact.state != "supported" for fact in facts)
            or not any(fact.state == "supported" for fact in location_facts)
            or any(fact.state == "uncertain" for fact in location_facts)
        )
        if self.status == "complete" and has_gaps:
            raise ValueError("complete requires supported coverage in every requested section")
        if self.status == "partial" and not has_gaps:
            raise ValueError("partial requires an uncertain/unknown fact or an explicit limitation")
        if not self.recent_developments and not self.limitations:
            raise ValueError("no retrieved recent developments requires an explicit limitation")
        return self


class BatchResult(Model):
    """One input row's identity-stage or final-report outcome."""

    row_number: PositiveInt
    input_nip: Annotated[str, StringConstraints(strict=True)]
    nip: NIP | None = None
    status: Literal["resolved", "complete", "partial", "invalid_input", "unresolved", "failed"]
    identity: CompanyIdentity | None = None
    sources: list[Source] = Field(default_factory=list)
    error_code: Text | None = None
    json_path: Text | None = None
    markdown_path: Text | None = None
    reason: Text | None = None
    completed_at: AwareDatetime

    @model_validator(mode="after")
    def check_outcome(self) -> Self:
        if self.status == "invalid_input":
            if self.nip is not None or self.identity is not None or self.sources:
                raise ValueError("invalid input cannot carry a validated NIP or registry result")
        elif self.nip is None:
            raise ValueError("a post-validation outcome requires a normalized NIP")
        if self.status == "resolved":
            if self.identity is None or not self.sources:
                raise ValueError("resolved requires an identity and its retrieved sources")
            if self.identity.nip != self.nip:
                raise ValueError("resolved identity must match the validated input NIP")
            if self.error_code is not None:
                raise ValueError("a resolved identity cannot carry a failure code")
        elif self.identity is not None:
            raise ValueError("only an identity-stage resolved row contains an identity")
        if self.status in {"complete", "partial"}:
            if self.json_path is None or self.markdown_path is None:
                raise ValueError("a published result requires both report paths")
        elif self.json_path is not None or self.markdown_path is not None:
            raise ValueError("an identity-only or unsuccessful row cannot claim BI report paths")
        if self.status not in {"complete", "resolved"} and self.reason is None:
            raise ValueError("a non-complete/non-resolved row requires a reason")
        source_ids = {source.source_id for source in self.sources}
        if len(source_ids) != len(self.sources):
            raise ValueError("source IDs must be unique within a row result")
        if any(source.retrieved_at > self.completed_at for source in self.sources):
            raise ValueError("a source cannot be retrieved after row completion")
        if self.identity is not None:
            if self.identity.resolved_at > self.completed_at:
                raise ValueError("identity cannot be resolved after row completion")
            for fact in (
                self.identity.legal_name,
                self.identity.krs,
                self.identity.regon,
                self.identity.registered_city,
                self.identity.registered_address,
                self.identity.website,
            ):
                if any(ref.source_id not in source_ids for ref in fact.evidence):
                    raise ValueError("identity evidence must reference the row source ledger")
        return self
