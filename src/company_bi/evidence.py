"""Deterministic publication gate for retained full-page assertions."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

from company_bi.assertions import (
    EmployeeObservation,
    EventObservation,
    FinancialObservation,
    TextObservation,
    parse_assertion,
)
from company_bi.models import (
    CompanyEvent,
    CompanyProfile,
    CompanyResearchRun,
    EvidenceRef,
    ExactEmployees,
    Fact,
    FinancialFact,
    ProfileSource,
    RetrievedSource,
    _validate_registry_identity,
    _validate_retrieval_invariants,
    profile_has_gaps,
    validate_source_lineage,
)

_BASE_UNIT_EXPONENTS = {
    "units": 0,
    "thousands": 3,
    "millions": 6,
    "billions": 9,
}


def _base_units(value: Decimal, unit: str) -> Decimal:
    """Convert a reported amount exactly, independent of Decimal context precision."""
    sign, digits, exponent = value.as_tuple()
    assert isinstance(exponent, int)
    return Decimal((sign, digits, exponent + _BASE_UNIT_EXPONENTS[unit]))


_SPACE = re.compile(r"\s+")


def _norm(value: str) -> str:
    """Apply the citation contract's NFC and whitespace normalization."""
    return _SPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def _exact_excerpt(material: RetrievedSource, excerpt: str) -> bool:
    """Check retained citation membership (publication requires whole-unit equality)."""
    return bool(_norm(excerpt)) and _norm(excerpt) in _norm(material.content)


def _unique_refs(refs: list[EvidenceRef]) -> list[EvidenceRef]:
    return [
        EvidenceRef(source_id=source_id, excerpt=excerpt)
        for source_id, excerpt in sorted({(ref.source_id, ref.excerpt) for ref in refs})
    ]


def _downgrade(
    fact: Fact[Any],
    reason: str,
    *,
    clear_value: bool = False,
    evidence: list[EvidenceRef] | None = None,
    **updates: Any,
) -> Any:
    changed: dict[str, Any] = {
        "state": "uncertain",
        "reason": reason,
        "evidence": evidence if evidence is not None else fact.evidence,
        **updates,
    }
    if clear_value:
        changed["value"] = None
    return fact.model_copy(update=changed)


def _append_reason(reason: str | None, addition: str) -> str:
    return f"{reason}; {addition}" if reason else addition


def _recent_event_window(generated: date) -> date:
    try:
        return generated.replace(year=generated.year - 1)
    except ValueError:
        return date(generated.year - 1, 2, 28)


def _financial_context_matches(financial: FinancialFact, observation: FinancialObservation) -> bool:
    return (
        financial.metric == observation.metric
        and financial.period is not None
        and financial.period.start == observation.period_start
        and financial.period.end == observation.period_end
        and financial.currency == observation.currency
        and financial.unit == observation.unit
        and financial.scope == observation.scope
        and financial.group_name is None
    )


def build_profile(run: CompanyResearchRun) -> CompanyProfile:
    """Publish only candidate facts matched by the finite whole-page grammar."""
    _validate_retrieval_invariants(run.sources)
    validate_source_lineage(run.sources)
    _validate_registry_identity(run.identity, run.sources)

    by_id: dict[str, list[RetrievedSource]] = defaultdict(list)
    for material in run.sources:
        by_id[material.source.source_id].append(material)
    blocked_ids = {
        source_id
        for source_id, materials in by_id.items()
        if any(material.source.publication_blocked_reason is not None for material in materials)
    }
    eligible_by_id = {
        source_id: materials
        for source_id, materials in by_id.items()
        if source_id not in blocked_ids
    }
    known_ids = set(by_id)

    identity_facts = (
        run.identity.legal_name,
        run.identity.krs,
        run.identity.regon,
        run.identity.registered_city,
        run.identity.registered_address,
        run.identity.website,
    )

    draft_candidates: tuple[Fact[Any], ...] = (
        run.draft.business_description,
        run.draft.products_services,
        run.draft.industries,
        run.draft.markets,
        run.draft.employees,
        *run.draft.financials,
        *run.draft.recent_developments,
    )
    for candidate in draft_candidates:
        for ref in candidate.evidence:
            if ref.source_id not in known_ids:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
    registry_ids = {item.source.source_id for item in run.sources if item.kind == "registry"}
    for fact in identity_facts:
        for ref in fact.evidence:
            if ref.source_id not in known_ids:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            if ref.source_id not in registry_ids:
                raise ValueError("identity evidence must originate from a trusted registry source")
            if not any(
                _exact_excerpt(item, ref.excerpt)
                for item in by_id[ref.source_id]
                if item.kind == "registry"
            ):
                raise ValueError("identity evidence excerpt is not an exact registry match")

    legal_name = unicodedata.normalize("NFC", str(run.identity.legal_name.value))
    generated_on = run.generated_at.date()
    # Parse each retained eligible full page exactly once. Source metadata remains paired
    # with the observation for event publication checks and deterministic evidence.
    parsed: list[tuple[RetrievedSource, Any]] = []
    for source_id in sorted(eligible_by_id):
        for material in sorted(
            (m for m in eligible_by_id[source_id] if m.kind == "full_page"),
            key=lambda m: (str(m.source.url), m.source.retrieved_at),
        ):
            observation = parse_assertion(material.content, legal_name, generated_on)
            if observation is not None:
                parsed.append((material, observation))

    def cited_observations(fact: Fact[Any]) -> list[tuple[EvidenceRef, RetrievedSource, Any]]:
        result: list[tuple[EvidenceRef, RetrievedSource, Any]] = []
        for ref in fact.evidence:
            if ref.source_id not in known_ids:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            if ref.source_id in blocked_ids:
                continue
            for material, observation in parsed:
                if material.source.source_id == ref.source_id and _norm(ref.excerpt) == _norm(
                    material.content
                ):
                    result.append((ref, material, observation))
        return result

    def text_gate(fact: Fact[Any], field: str, *, list_value: bool = False) -> Any:
        if fact.state != "supported":
            return fact
        proposal_value = fact.value
        if list_value:
            proposals = (
                [proposal for proposal in proposal_value if isinstance(proposal, str)]
                if isinstance(proposal_value, list)
                and all(isinstance(item, str) for item in proposal_value)
                else []
            )
        else:
            proposals = [proposal_value] if isinstance(proposal_value, str) else []
        if not proposals:
            return _downgrade(
                fact,
                "No complete exact-entity assertion supports every proposed value",
                clear_value=True,
            )
        matches: list[EvidenceRef] = []
        for proposal in proposals:
            for ref, _material, observation in cited_observations(fact):
                if (
                    isinstance(observation, TextObservation)
                    and observation.field == field
                    and observation.value == unicodedata.normalize("NFC", proposal)
                ):
                    matches.append(ref)
                    break
            else:
                return _downgrade(
                    fact,
                    "No complete exact-entity assertion supports every proposed value",
                    clear_value=True,
                )
        return fact.model_copy(update={"evidence": _unique_refs(matches)})

    business = text_gate(run.draft.business_description, "business_description")
    products = text_gate(run.draft.products_services, "products_services", list_value=True)
    industries = text_gate(run.draft.industries, "industries", list_value=True)
    markets = text_gate(run.draft.markets, "markets", list_value=True)

    employees = run.draft.employees
    if employees.state == "supported":
        employee_candidate = employees.value
        count = employee_candidate.count if isinstance(employee_candidate, ExactEmployees) else None
        observations = [
            (ref, mat, obs)
            for ref, mat, obs in cited_observations(employees)
            if isinstance(obs, EmployeeObservation)
        ]
        count_matches = [
            (ref, mat, obs)
            for ref, mat, obs in observations
            if count is not None and obs.count == count
        ]
        all_employee_obs = [obs for _mat, obs in parsed if isinstance(obs, EmployeeObservation)]
        conflicting = any(
            left.count != right.count
            and (left.as_of is None or right.as_of is None or left.as_of == right.as_of)
            for index, left in enumerate(all_employee_obs)
            for right in all_employee_obs[index + 1 :]
        )
        if conflicting:
            employees = _downgrade(
                employees,
                "Conflicting recognized employee observations for the same or unresolved date",
                clear_value=True,
                as_of=None,
            )
        elif not count_matches:
            employees = _downgrade(
                employees,
                "No complete employee assertion supports the proposed exact count",
                clear_value=True,
                as_of=None,
            )
        else:
            date_matches = [
                (ref, mat, obs)
                for ref, mat, obs in count_matches
                if employees.as_of is not None and obs.as_of == employees.as_of
            ]
            chosen = date_matches if date_matches else count_matches
            as_of = employees.as_of if date_matches else None
            employees = employees.model_copy(
                update={
                    "evidence": _unique_refs([ref for ref, _mat, _obs in chosen]),
                    "as_of": as_of,
                }
            )
            if employees.as_of is None and run.draft.employees.as_of is not None:
                employees = employees.model_copy(
                    update={
                        "reason": _append_reason(
                            employees.reason, "Unverified employee as-of date removed"
                        )
                    }
                )

    financials: list[FinancialFact] = []
    for financial in run.draft.financials:
        if financial.state != "supported":
            financials.append(financial)
            continue
        financial_cited = [
            (ref, mat, obs)
            for ref, mat, obs in cited_observations(financial)
            if isinstance(obs, FinancialObservation)
        ]

        candidate_key: tuple[Any, ...] | None = None
        recognized_same_key: dict[tuple[Any, ...], set[Decimal]] = defaultdict(set)
        for _mat, obs in parsed:
            if isinstance(obs, FinancialObservation):
                key = (
                    obs.metric,
                    obs.currency,
                    obs.scope,
                    obs.period_start,
                    obs.period_end,
                )
                recognized_same_key[key].add(_base_units(obs.value, obs.unit))
        if (
            financial.period is not None
            and financial.currency is not None
            and financial.unit is not None
            and financial.scope is not None
        ):
            candidate_key = (
                financial.metric,
                financial.currency,
                financial.scope,
                financial.period.start,
                financial.period.end,
            )
        financial_matches = [
            (ref, mat, obs)
            for ref, mat, obs in financial_cited
            if _financial_context_matches(financial, obs) and financial.value == obs.value
        ]
        if candidate_key is not None and len(recognized_same_key.get(candidate_key, ())) > 1:
            financials.append(
                _downgrade(
                    financial,
                    "Conflicting recognized financial observations for the same "
                    "metric and reporting context",
                    clear_value=True,
                )
            )
        elif financial_matches:
            financials.append(
                financial.model_copy(
                    update={
                        "evidence": _unique_refs([ref for ref, _mat, _obs in financial_matches])
                    }
                )
            )
        else:
            financials.append(
                _downgrade(
                    financial,
                    "No complete financial assertion supports amount and required "
                    "reporting context",
                    clear_value=True,
                )
            )

    events: list[CompanyEvent] = []
    recent_start = _recent_event_window(generated_on)
    for event in run.draft.recent_developments:
        if event.state != "supported" or event.value is None:
            events.append(event)
            continue
        event_cited = [
            (ref, mat, obs)
            for ref, mat, obs in cited_observations(event)
            if isinstance(obs, EventObservation)
        ]
        detail = event.value
        event_matches = [
            (ref, mat, obs)
            for ref, mat, obs in event_cited
            if obs.title == unicodedata.normalize("NFC", detail.title)
            and obs.summary == unicodedata.normalize("NFC", detail.summary).strip()
            and mat.source.published_on is not None
            and mat.source.published_on == detail.published_on
            and recent_start <= mat.source.published_on <= generated_on
        ]
        if not event_matches:
            events.append(
                _downgrade(
                    event,
                    "No complete event assertion and eligible publication date support the event",
                    clear_value=True,
                )
            )
            continue
        event_date_matches = [
            (ref, mat, obs)
            for ref, mat, obs in event_matches
            if detail.occurred_on is not None and obs.occurred_on == detail.occurred_on
        ]
        occurrence = detail.occurred_on if event_date_matches else None
        chosen_events = (
            event_date_matches
            if detail.occurred_on is not None and event_date_matches
            else event_matches
        )
        updated = event.model_copy(
            update={"evidence": _unique_refs([ref for ref, _mat, _obs in chosen_events])}
        )
        if detail.occurred_on is not None and occurrence is None:
            detail = detail.model_copy(update={"occurred_on": None})
            updated = updated.model_copy(
                update={
                    "value": detail,
                    "reason": _append_reason(
                        event.reason, "Unverified event occurrence date removed"
                    ),
                }
            )
        events.append(updated)

    all_facts: tuple[Fact[Any], ...] = (
        *identity_facts,
        business,
        products,
        industries,
        markets,
        employees,
        *financials,
        *events,
    )
    used_ids = {ref.source_id for fact in all_facts for ref in fact.evidence}
    used_ids.update(item.source.source_id for item in run.sources if item.kind == "registry")
    used_ids.update(blocked_ids)
    rank = {"search_snippet": 0, "full_page": 1, "registry": 2}
    sources: list[ProfileSource] = []
    for source_id in sorted(used_ids):
        materials = by_id.get(source_id)
        if not materials:
            raise ValueError(f"unknown evidence source ID: {source_id}")
        strongest = max(
            materials,
            key=lambda item: (rank[item.kind], item.source.retrieved_at, str(item.source.url)),
        )
        sources.append(ProfileSource(**strongest.source.model_dump(), kind=strongest.kind))

    identity = run.identity.model_copy(deep=True)
    limitations = list(run.draft.limitations)
    limitations.extend(
        f"Source {source_id}: publication blocked: unproven_legacy_url_relationship"
        for source_id in sorted(blocked_ids)
    )
    for label, old_text_fact, new_text_fact in (
        ("business description", run.draft.business_description, business),
        ("products/services", run.draft.products_services, products),
        ("industries", run.draft.industries, industries),
        ("markets", run.draft.markets, markets),
        ("employees", run.draft.employees, employees),
    ):
        if (
            old_text_fact.state == "supported"
            and new_text_fact.state == "uncertain"
            and new_text_fact.reason
        ):
            limitations.append(f"{label}: {new_text_fact.reason}")
    for old_financial, new_financial in zip(run.draft.financials, financials, strict=True):
        if (
            old_financial.state == "supported"
            and new_financial.state == "uncertain"
            and new_financial.reason
        ):
            limitations.append(f"{new_financial.metric}: {new_financial.reason}")
    for old_event, new_event in zip(run.draft.recent_developments, events, strict=True):
        if old_event.state == "supported" and new_event.state == "uncertain" and new_event.reason:
            limitations.append(f"Recent development: {new_event.reason}")
    if not events and not limitations:
        limitations.append("No recent developments were established from retained sources")

    facts: tuple[Fact[Any], ...] = (
        business,
        products,
        industries,
        markets,
        employees,
        *financials,
        *events,
    )
    status = (
        "partial"
        if profile_has_gaps(
            limitations=limitations,
            recent_developments=events,
            facts=facts,
            identity=identity,
            financials=financials,
        )
        else "complete"
    )
    return CompanyProfile(
        status=status,
        generated_at=run.generated_at,
        identity=identity,
        business_description=business,
        products_services=products,
        industries=industries,
        markets=markets,
        employees=employees,
        financials=financials,
        recent_developments=events,
        sources=sources,
        limitations=limitations,
    )
