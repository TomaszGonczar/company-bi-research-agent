"""Publication schemas, not an identity resolver or an evidence-verification engine."""

import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal, Self
from urllib.parse import urlsplit, urlunsplit

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
FailureCode = Literal[
    "SEARCH_FAILURE",
    "FETCH_FAILURE",
    "MODEL_FAILURE",
    "MODEL_OUTPUT_INVALID",
    "RESOURCE_LIMIT",
    "EVIDENCE_VALIDATION_FAILURE",
    "CONFIG_ERROR",
]


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
    redirect_chain: list[HttpUrl] = Field(default_factory=list, max_length=6)
    publication_blocked_reason: Literal["unproven_legacy_url_relationship"] | None = None

    @model_validator(mode="after")
    def check_redirect_chain(self) -> Self:
        if self.redirect_chain and len(self.redirect_chain) < 2:
            raise ValueError("redirect lineage must contain a start and final HTTP URL")
        return self


class ProfileSource(Source):
    """Published provenance with the strongest retained material kind."""

    kind: Literal["registry", "search_snippet", "full_page"]


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


def profile_has_gaps(
    *,
    limitations: list[str],
    recent_developments: list[CompanyEvent],
    facts: tuple[Fact[Any], ...],
    identity: CompanyIdentity,
    financials: list[FinancialFact],
) -> bool:
    """Canonical coverage calculation shared by the evidence gate and schema."""
    if identity.legal_name.state != "supported":
        return True
    optional_identifiers = (identity.krs, identity.regon, identity.website)
    required_facts = tuple(
        fact for fact in facts if all(fact is not optional for optional in optional_identifiers)
    )
    if (
        limitations
        or not recent_developments
        or any(fact.state != "supported" for fact in required_facts)
    ):
        return True
    if any(fact.state == "uncertain" for fact in optional_identifiers):
        return True
    if (
        identity.registered_city.state != "supported"
        and identity.registered_address.state != "supported"
    ):
        return True
    if any(
        fact.state == "uncertain"
        for fact in (identity.registered_city, identity.registered_address)
    ):
        return True
    revenue_periods = {
        (fact.period.start, fact.period.end)
        for fact in financials
        if fact.state == "supported" and fact.metric == "revenue" and fact.period is not None
    }
    net_result_periods = {
        (fact.period.start, fact.period.end)
        for fact in financials
        if fact.state == "supported" and fact.metric == "net_result" and fact.period is not None
    }
    return not bool(revenue_periods & net_result_periods)


def _check_financial_coverage(financials: list[FinancialFact]) -> None:
    if {fact.metric for fact in financials} != {"revenue", "net_result"}:
        raise ValueError("both financial metrics must be represented, even when unknown")
    periods = {
        (fact.period.start, fact.period.end) for fact in financials if fact.period is not None
    }
    if len(periods) > 3:
        raise ValueError("financials may cover at most three reporting periods")
    keys = [
        (
            fact.metric,
            fact.period.start if fact.period else None,
            fact.period.end if fact.period else None,
        )
        for fact in financials
    ]
    if len(set(keys)) != len(keys):
        raise ValueError("conflicting metric/period observations belong in one uncertain fact")


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
    sources: list[ProfileSource] = Field(min_length=1)
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

        _check_financial_coverage(self.financials)

        today = self.generated_at.date()
        try:
            recent_start = today.replace(year=today.year - 1)
        except ValueError:  # Leap-day reports use February 28 in the preceding year.
            recent_start = date(today.year - 1, 2, 28)
        for event in self.recent_developments:
            if event.value is not None and not recent_start <= event.value.published_on <= today:
                raise ValueError("recent developments must be published within the last 12 months")

        has_gaps = profile_has_gaps(
            limitations=self.limitations,
            recent_developments=self.recent_developments,
            facts=facts,
            identity=self.identity,
            financials=self.financials,
        )
        if self.status == "complete" and has_gaps:
            raise ValueError("complete requires supported coverage in every requested section")
        if self.status == "partial" and not has_gaps:
            raise ValueError("partial requires an uncertain/unknown fact or an explicit limitation")
        if not self.recent_developments and not self.limitations:
            raise ValueError("no retrieved recent developments requires an explicit limitation")
        return self


class OperationalFailure(Model):
    code: FailureCode
    stage: Literal[
        "search",
        "static_fetch",
        "dynamic_fetch",
        "url_validation",
        "model",
        "structured_output_validation",
        "source_reference_validation",
        "evidence_validation",
        "progress_validation",
        "resource_limit",
        "cleanup",
        "publication",
    ]
    reason: Text = Field(max_length=500)
    error_type: Text | None = None
    field_path: Text | None = None
    attempt: PositiveInt | None = None
    source_id: Text | None = None
    validated_progress_available: bool = False


class ResearchDiagnostics(Model):
    model: Text
    status: Literal["completed", "partial", "failed"]
    stop_reason: Text | None = None
    failure_code: FailureCode | None = None
    failures: list[OperationalFailure] = Field(default_factory=list)
    validated_progress_retained: bool = False
    model_requests: NonNegativeInt
    searches: NonNegativeInt
    page_reads: NonNegativeInt
    dynamic_reads: NonNegativeInt
    output_retries: NonNegativeInt
    input_tokens: NonNegativeInt
    output_tokens: NonNegativeInt
    duration_seconds: Annotated[float, Field(ge=0)]
    cost_usd: Money | None = None


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
    diagnostics: ResearchDiagnostics | None = None
    research_path: Text | None = None

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


class CompanyResearchDraft(Model):
    """Candidate findings, not a published profile or model-owned legal identity."""

    business_description: Fact[Text]
    products_services: Fact[TextList]
    industries: Fact[TextList]
    markets: Fact[TextList]
    employees: EmployeeFact
    financials: list[FinancialFact] = Field(min_length=2, max_length=6)
    recent_developments: list[CompanyEvent] = Field(max_length=3)
    limitations: list[Text] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_financial_attempts(self) -> Self:
        _check_financial_coverage(self.financials)
        return self


class SearchHit(Model):
    source_id: Text
    title: Text
    url: HttpUrl
    content: str
    score: Annotated[float, Field(ge=0, le=1)] | None = None


class SearchResults(Model):
    query: Text
    results: list[SearchHit] = Field(default_factory=list)
    error: Text | None = None
    failure: OperationalFailure | None = None


_RETRIEVAL_MODES = {
    "registry": frozenset({"registry"}),
    "search_snippet": frozenset({"tavily"}),
    "full_page": frozenset({"static", "dynamic"}),
}


class RetrievedSource(Model):
    """Host-owned material; search discovery is not a full-page retrieval."""

    source: Source
    kind: Literal["registry", "search_snippet", "full_page"]
    content: str
    fetch_mode: Literal["registry", "tavily", "static", "dynamic"]

    @model_validator(mode="after")
    def check_kind_and_fetch_mode(self) -> Self:
        if self.fetch_mode not in _RETRIEVAL_MODES[self.kind]:
            raise ValueError(
                f"retrieved source kind {self.kind} cannot use fetch mode {self.fetch_mode}"
            )
        return self


def _validate_retrieval_invariants(materials: list[RetrievedSource]) -> None:
    """Recheck source invariants at trust boundaries, including unchecked model copies."""
    full_page_ids: set[str] = set()
    for material in materials:
        if material.fetch_mode not in _RETRIEVAL_MODES.get(material.kind, ()):
            raise ValueError(
                f"retrieved source kind {material.kind} cannot use fetch mode {material.fetch_mode}"
            )
        if material.kind == "full_page" and material.source.publication_blocked_reason is None:
            source_id = material.source.source_id
            if source_id in full_page_ids:
                raise ValueError(f"source ID {source_id} has duplicate full-page material")
            full_page_ids.add(source_id)


def _normalized_source_url(url: HttpUrl | str) -> str:
    """Canonical URL key shared by source discovery and lineage validation."""
    parts = urlsplit(str(url))
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    authority_host = f"[{host}]" if ":" in host else host
    netloc = (
        authority_host
        if port is None or (scheme, port) in {("http", 80), ("https", 443)}
        else f"{authority_host}:{port}"
    )
    if parts.username or parts.password:
        netloc = f"{parts.username or ''}:{parts.password or ''}@{netloc}"
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


def _source_origin(url: HttpUrl) -> tuple[str, str, int | None]:
    parts = urlsplit(str(url))
    scheme = parts.scheme.lower()
    port = parts.port
    if port is None:
        port = 443 if scheme == "https" else 80
    return scheme, (parts.hostname or "").lower(), port


def validate_source_lineage(materials: list[RetrievedSource]) -> None:
    """Reject unexplained same-ID URL changes while allowing retained redirect chains."""
    by_id: dict[str, list[RetrievedSource]] = defaultdict(list)
    for material in materials:
        by_id[material.source.source_id].append(material)

    for source_id, retained in by_id.items():
        blocked = [
            material
            for material in retained
            if material.source.publication_blocked_reason is not None
        ]
        if blocked:
            if (
                len(blocked) != len(retained)
                or any(material.kind == "registry" for material in retained)
                or any(material.source.redirect_chain for material in retained)
            ):
                raise ValueError(
                    f"blocked source ID {source_id} has trusted or contradictory lineage"
                )
            continue

        chained = [material for material in retained if material.source.redirect_chain]
        if any(material.kind != "full_page" for material in chained):
            raise ValueError(
                f"redirect lineage for source ID {source_id} is not full-page provenance"
            )

        if not chained:
            origins = {_source_origin(material.source.url) for material in retained}
            if len(origins) > 1:
                raise ValueError(f"source ID {source_id} has conflicting host metadata")
            urls = {_normalized_source_url(material.source.url) for material in retained}
            if len(urls) > 1:
                raise ValueError(f"source ID {source_id} has unexplained URL changes")
            continue

        chains = {
            tuple(_normalized_source_url(url) for url in material.source.redirect_chain)
            for material in chained
        }
        if len(chains) != 1:
            raise ValueError(f"source ID {source_id} has conflicting redirect lineages")
        chain = chained[0].source.redirect_chain
        start_url = _normalized_source_url(chain[0])
        end_url = _normalized_source_url(chain[-1])
        start_origin = _source_origin(chain[0])
        end_origin = _source_origin(chain[-1])
        discoveries = [material for material in retained if material.kind == "search_snippet"]
        pages = [material for material in retained if material.kind == "full_page"]
        if not discoveries or not pages:
            raise ValueError(f"redirect lineage for source ID {source_id} lacks retained discovery")
        if any(
            _source_origin(item.source.url) != start_origin
            or _normalized_source_url(item.source.url) != start_url
            for item in discoveries
        ):
            raise ValueError(f"redirect lineage for source ID {source_id} has the wrong origin")
        if any(
            not item.source.redirect_chain
            or _source_origin(item.source.url) != end_origin
            or _normalized_source_url(item.source.url) != end_url
            for item in pages
        ):
            raise ValueError(f"redirect lineage for source ID {source_id} has the wrong final URL")
        if any(item.kind not in {"search_snippet", "full_page"} for item in retained):
            raise ValueError(
                f"redirect lineage for source ID {source_id} is attached to non-web material"
            )

    owner_ids: dict[str, str] = {}
    for material in materials:
        if (
            material.kind not in {"search_snippet", "full_page"}
            or material.source.publication_blocked_reason is not None
        ):
            continue
        owner_url = (
            material.source.redirect_chain[0]
            if material.kind == "full_page" and material.source.redirect_chain
            else material.source.url
        )
        owner = _normalized_source_url(owner_url)
        source_id = material.source.source_id
        previous_id = owner_ids.setdefault(owner, source_id)
        if previous_id != source_id:
            raise ValueError("discovery URL is assigned to multiple source IDs")


def _identity_text(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value))
    return " ".join(text.split())


def _registry_citation_matches(mapped_value: str, excerpt: str) -> bool:
    """Match a mapped registry value against a raw or JSON-string citation excerpt."""
    if _identity_text(mapped_value) == _identity_text(excerpt):
        return True
    try:
        decoded = json.loads(excerpt)
    except (json.JSONDecodeError, TypeError):
        return False
    return isinstance(decoded, str) and _identity_text(mapped_value) == _identity_text(decoded)


_LEGACY_REGISTRY_HEADER = "MF VAT register identity material (not a raw registry response):"
_LEGACY_FIELDS = (
    "legal_name",
    "krs",
    "regon",
    "registered_city",
    "registered_address",
    "website",
)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("registry JSON contains duplicate object keys")
        result[key] = value
    return result


def _legacy_registry_record(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    if len(lines) < 8 or lines[0] != _LEGACY_REGISTRY_HEADER:
        raise ValueError("unsupported registry material format")
    if re.fullmatch(r"NIP: [0-9]{10}", lines[-1]) is None:
        raise ValueError("legacy registry snapshot requires a final canonical NIP")
    nip = lines[-1][5:]
    declarations: dict[str, str] = {}
    for line in lines[1:-1]:
        evidence = re.fullmatch(
            r"(legal_name|krs|regon|registered_city|registered_address|website) "
            r"evidence from ([^:\s]+): (.+)",
            line,
        )
        if evidence is not None:
            continue
        declaration = re.fullmatch(
            r"(legal_name|krs|regon|registered_city|registered_address|website): (.+)",
            line,
        )
        if declaration is None:
            raise ValueError("legacy registry snapshot contains an unknown or ambiguous line")
        field_name, value = declaration.groups()
        if field_name in declarations:
            raise ValueError("legacy registry snapshot contains duplicate declarations")
        if value.startswith(("unknown; ", "uncertain; ")):
            continue
        declarations[field_name] = value
    if not any(line.startswith("legal_name: ") for line in lines[1:-1]):
        raise ValueError("legacy registry snapshot is missing legal_name")
    # The declaration count is structural, including explicitly unknown fields.
    declared = [
        re.match(r"(legal_name|krs|regon|registered_city|registered_address|website):", line)
        for line in lines[1:-1]
    ]
    names = [match.group(1) for match in declared if match is not None]
    if len(names) != len(_LEGACY_FIELDS) or set(names) != set(_LEGACY_FIELDS):
        raise ValueError("legacy registry snapshot requires each identity declaration once")
    return declarations, nip


def _registry_record(content: str) -> tuple[dict[str, str], str]:
    try:
        root = json.loads(content, object_pairs_hook=_unique_json_object)
    except json.JSONDecodeError:
        return _legacy_registry_record(content)
    if not isinstance(root, dict):
        raise ValueError("unsupported registry material format")
    result = root.get("result")
    subject = result.get("subject") if isinstance(result, dict) else None
    if not isinstance(subject, dict):
        raise ValueError("MF registry JSON requires result.subject")
    nip, legal_name = subject.get("nip"), subject.get("name")
    if not isinstance(nip, str) or re.fullmatch(r"[0-9]{10}", nip) is None:
        raise ValueError("MF registry JSON requires a canonical subject NIP")
    if not isinstance(legal_name, str) or not legal_name:
        raise ValueError("MF registry JSON requires a subject legal name")
    mapped: dict[str, str] = {"legal_name": legal_name}
    for field_name in ("krs", "regon"):
        value = subject.get(field_name)
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"MF registry {field_name} must be a string")
            mapped[field_name] = value
    working = subject.get("workingAddress")
    residence = subject.get("residenceAddress")
    if working is not None and not isinstance(working, str):
        raise ValueError("MF registry workingAddress must be a string")
    if residence is not None and not isinstance(residence, str):
        raise ValueError("MF registry residenceAddress must be a string")
    address = working if isinstance(working, str) and working else residence
    if address:
        mapped["registered_address"] = address
    return mapped, nip


def _validate_registry_identity(
    identity: CompanyIdentity, materials: list[RetrievedSource]
) -> None:
    """Require every retained registry record and supported identity value to agree."""
    registry_materials = [material for material in materials if material.kind == "registry"]
    if not registry_materials:
        raise ValueError("resolved identity requires recognized registry material")
    records: list[tuple[RetrievedSource, dict[str, str]]] = []
    target_name = _identity_text(identity.legal_name.value)
    for material in registry_materials:
        if material.source.publication_blocked_reason is not None:
            raise ValueError("publication-blocked registry material cannot establish identity")
        fields, nip = _registry_record(material.content)
        if nip != identity.nip:
            raise ValueError("retained registry material contains a conflicting NIP")
        if "legal_name" not in fields or _identity_text(fields["legal_name"]) != target_name:
            raise ValueError("retained registry material contains a conflicting legal_name")
        records.append((material, fields))

    for field_name in _LEGACY_FIELDS:
        fact = getattr(identity, field_name)
        value = fact.value
        if fact.state != "supported":
            continue
        cited = False
        for ref in fact.evidence:
            matching = [
                (material, fields)
                for material, fields in records
                if material.source.source_id == ref.source_id
            ]
            retained = [
                (material, fields)
                for material, fields in matching
                if _identity_text(ref.excerpt) in _identity_text(material.content)
            ]
            if not retained:
                raise ValueError(
                    f"supported identity field {field_name} lacks retained registry evidence"
                )
            if not any(
                field_name in fields
                and _identity_text(value) == _identity_text(fields[field_name])
                and _registry_citation_matches(fields[field_name], ref.excerpt)
                for _, fields in retained
            ):
                raise ValueError(
                    f"supported identity field {field_name} does not match mapped registry data"
                )
            cited = True
        if not cited:
            raise ValueError(f"supported identity field {field_name} requires registry evidence")
        for _, fields in records:
            if field_name in fields and _identity_text(value) != _identity_text(fields[field_name]):
                raise ValueError(f"retained registry material declares a conflicting {field_name}")


class PageReadResult(Model):
    material: RetrievedSource | None = None
    error: Text | None = None
    failure: OperationalFailure | None = None


class CompanyResearchRun(Model):
    """One draft and its trusted retrieval artifacts; never a final BI report."""

    identity: CompanyIdentity
    draft: CompanyResearchDraft
    sources: list[RetrievedSource]
    diagnostics: ResearchDiagnostics
    generated_at: AwareDatetime

    @model_validator(mode="before")
    @classmethod
    def mark_unproven_legacy_source_groups(cls, value: Any) -> Any:
        """Quarantine old serialized groups only when lineage is absent and URLs differ."""
        if not isinstance(value, dict) or not isinstance(value.get("sources"), list):
            return value
        groups: dict[str, list[tuple[int, dict[str, Any], dict[str, Any]]]] = defaultdict(list)
        non_dict_source_ids: set[str] = set()
        for index, material in enumerate(value["sources"]):
            if not isinstance(material, dict) or not isinstance(material.get("source"), dict):
                source = getattr(material, "source", None)
                source_id = getattr(source, "source_id", None)
                if isinstance(source_id, str):
                    non_dict_source_ids.add(source_id)
                continue
            source = material["source"]
            source_id = source.get("source_id")
            if isinstance(source_id, str):
                groups[source_id].append((index, material, source))
        blocked_ids: set[str] = set()
        for source_id, group in groups.items():
            if source_id in non_dict_source_ids:
                continue
            if len(group) < 2 or any(
                material.get("kind") not in {"search_snippet", "full_page"}
                or "redirect_chain" in source
                or "url" not in source
                for _, material, source in group
            ):
                continue
            urls = {_normalized_source_url(source["url"]) for _, _, source in group}
            if len(urls) > 1:
                blocked_ids.add(source_id)

        if not blocked_ids:
            return value
        copied = dict(value)
        sources = list(value["sources"])
        for index, material in enumerate(sources):
            if (
                isinstance(material, dict)
                and isinstance(material.get("source"), dict)
                and material["source"].get("source_id") in blocked_ids
            ):
                copied_material = dict(material)
                copied_source = dict(material["source"])
                copied_source["publication_blocked_reason"] = "unproven_legacy_url_relationship"
                copied_material["source"] = copied_source
                sources[index] = copied_material
        copied["sources"] = sources
        return copied

    @model_validator(mode="after")
    def check_retrieval_references(self) -> Self:
        _validate_retrieval_invariants(self.sources)
        validate_source_lineage(self.sources)
        # One source ID may have multiple retained snippets and a full-page snapshot.
        source_ids = {material.source.source_id for material in self.sources}
        if any(material.source.retrieved_at > self.generated_at for material in self.sources):
            raise ValueError("a source cannot be retrieved after draft generation")
        if self.identity.resolved_at > self.generated_at:
            raise ValueError("identity cannot be resolved after draft generation")
        facts: tuple[Fact[Any], ...] = (
            self.identity.legal_name,
            self.identity.krs,
            self.identity.regon,
            self.identity.registered_city,
            self.identity.registered_address,
            self.identity.website,
            self.draft.business_description,
            self.draft.products_services,
            self.draft.industries,
            self.draft.markets,
            self.draft.employees,
            *self.draft.financials,
            *self.draft.recent_developments,
        )
        if any(ref.source_id not in source_ids for fact in facts for ref in fact.evidence):
            raise ValueError("research evidence must reference retained host source material")
        full_page_ids = {
            material.source.source_id for material in self.sources if material.kind == "full_page"
        }
        for financial in self.draft.financials:
            if financial.value is not None and (
                not financial.evidence
                or any(ref.source_id not in full_page_ids for ref in financial.evidence)
            ):
                raise ValueError("financial amounts require retained full-page evidence")
        _validate_registry_identity(self.identity, self.sources)
        return self
