"""Normative strict-publication matrix, independent of gate outcomes."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

ENTITY = "Example sp. z o.o."
NIP = "5220003782"
GENERATED = datetime(2026, 10, 3, 12, tzinfo=UTC)
LEGAL_REF = json.dumps(ENTITY, ensure_ascii=False)
UNKNOWN = {"state": "unknown", "reason": "Not researched in this synthetic case"}


def _fact(value: Any, excerpt: str, **extra: Any) -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "evidence": [{"source_id": "page", "excerpt": excerpt}],
        **extra,
    }


def _run(
    content: str,
    field: str,
    value: Any,
    *,
    excerpt: str | None = None,
    source_date: str | None = None,
    other_pages: list[str] | None = None,
    registry: str | None = None,
    legal_excerpt: str = LEGAL_REF,
) -> dict[str, Any]:
    draft: dict[str, Any] = {
        "business_description": deepcopy(UNKNOWN),
        "products_services": deepcopy(UNKNOWN),
        "industries": deepcopy(UNKNOWN),
        "markets": deepcopy(UNKNOWN),
        "employees": deepcopy(UNKNOWN),
        "financials": [
            {**deepcopy(UNKNOWN), "metric": "revenue"},
            {**deepcopy(UNKNOWN), "metric": "net_result"},
        ],
        "recent_developments": [],
        "limitations": ["Synthetic matrix case"],
    }
    citation = content if excerpt is None else excerpt
    if field == "products_services":
        draft[field] = _fact(value if isinstance(value, list) else [value], citation)
    elif field in {"industries", "markets"}:
        draft[field] = _fact(value if isinstance(value, list) else [value], citation)
    elif field == "business_description":
        draft[field] = _fact(value, citation)
    elif field == "employees":
        employee_value = (
            value
            if value.get("kind") == "range"
            else {
                "kind": "exact",
                "count": value["count"],
            }
        )
        draft[field] = _fact(employee_value, citation, as_of=value.get("as_of"))
    elif field.startswith("financials."):
        index = int(field.rsplit(".", 1)[1])
        draft["financials"][index] = _fact(
            value["value"],
            citation,
            metric=value["metric"],
            period={"start": value["start"], "end": value["end"]},
            currency=value["currency"],
            unit=value["unit"],
            scope=value["scope"],
            group_name=value.get("group_name"),
        )
    elif field == "recent_developments":
        draft[field] = [
            {
                "state": "supported",
                "value": {
                    "title": value["title"],
                    "summary": value["summary"],
                    "published_on": value.get("published_on", "2026-09-25"),
                    "occurred_on": value.get("occurred_on"),
                },
                "evidence": [{"source_id": "page", "excerpt": citation}],
            }
        ]
    else:
        raise ValueError(field)

    registry_content = registry or json.dumps(
        {
            "result": {
                "subject": {
                    "nip": NIP,
                    "name": ENTITY,
                }
            }
        },
        ensure_ascii=False,
    )
    page = {
        "source": {
            "source_id": "page",
            "url": "https://page.example/",
            "title": "Company page",
            "retrieved_at": GENERATED.isoformat(),
            **({"published_on": source_date} if source_date else {}),
        },
        "kind": "full_page",
        "content": content,
        "fetch_mode": "static",
    }
    pages = [page]
    for index, body in enumerate(other_pages or [], start=2):
        pages.append(
            {
                "source": {
                    "source_id": f"page{index}",
                    "url": f"https://page{index}.example/",
                    "title": f"Company page {index}",
                    "retrieved_at": GENERATED.isoformat(),
                },
                "kind": "full_page",
                "content": body,
                "fetch_mode": "static",
            }
        )
    return {
        "identity": {
            "nip": NIP,
            "legal_name": {
                "state": "supported",
                "value": ENTITY,
                "evidence": [{"source_id": "registry", "excerpt": legal_excerpt}],
            },
            **{
                name: deepcopy(UNKNOWN)
                for name in ("krs", "regon", "registered_city", "registered_address", "website")
            },
            "resolved_at": GENERATED.isoformat(),
        },
        "draft": draft,
        "sources": [
            {
                "source": {
                    "source_id": "registry",
                    "url": "https://registry.example/",
                    "title": "MF registry",
                    "retrieved_at": GENERATED.isoformat(),
                },
                "kind": "registry",
                "content": registry_content,
                "fetch_mode": "registry",
            },
            *pages,
        ],
        "diagnostics": {
            "model": "offline-contract-matrix",
            "status": "completed",
            "model_requests": 0,
            "searches": 0,
            "page_reads": len(pages),
            "dynamic_reads": 0,
            "output_retries": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "duration_seconds": 0,
        },
        "generated_at": GENERATED.isoformat(),
    }


def _case(
    case_id: str,
    classification: str,
    family: str,
    shape: str,
    content: str,
    field: str,
    value: Any,
    *,
    expected: str,
    path: str | None = None,
    excerpt: str | None = None,
    source_date: str | None = None,
    other_pages: list[str] | None = None,
    registry: str | None = None,
    legal_excerpt: str = LEGAL_REF,
    run_rejected: bool = False,
    rationale: str,
) -> dict[str, Any]:
    path = path or field
    run = _run(
        content,
        field,
        value,
        excerpt=excerpt,
        source_date=source_date,
        other_pages=other_pages,
        registry=registry,
        legal_excerpt=legal_excerpt,
    )
    supported = classification == "SUPPORTED_CONTRACT_POSITIVE"
    assert expected == ("published" if supported else "rejected")
    if run_rejected:
        return {
            "case_id": case_id,
            "classification": classification,
            "family": family,
            "shape": shape,
            "path": path,
            "run": run,
            "expected": {"outcome": "rejected"},
            "rationale": rationale,
        }

    if field in {"products_services", "business_description", "industries", "markets"}:
        candidate = run["draft"][field]
        fact_expected = {"value": candidate["value"] if supported else None}
    elif field == "employees":
        candidate = run["draft"]["employees"]
        fact_expected = {
            "value": candidate["value"] if supported else None,
            "as_of": (
                None
                if case_id.startswith("emp-") and case_id.endswith("-p3")
                else candidate.get("as_of")
                if supported
                else None
            ),
        }
    elif field.startswith("financials."):
        candidate = run["draft"]["financials"][int(field.rsplit(".", 1)[1])]
        fact_expected = {
            "value": candidate.get("value") if supported else None,
            "metric": candidate["metric"],
            "period": candidate.get("period"),
            "currency": candidate.get("currency"),
            "unit": candidate.get("unit"),
            "scope": candidate.get("scope"),
            "group_name": candidate.get("group_name"),
        }
    elif field == "recent_developments":
        candidate = run["draft"]["recent_developments"][0]["value"]
        fact_expected = {"value": candidate if supported else None}
    exp: dict[str, Any] = {
        "outcome": "published",
        "state": "supported" if supported else "uncertain",
        "supported_fields" if supported else "required_fields": fact_expected,
    }
    return {
        "case_id": case_id,
        "classification": classification,
        "family": family,
        "shape": shape,
        "path": path,
        "run": run,
        "expected": exp,
        "rationale": rationale,
    }


def matrix_cases() -> list[dict[str, Any]]:
    """Build 3 positives, 3 unsafe near misses and 2 true OOC controls per shape."""
    cases: list[dict[str, Any]] = []
    products = [
        ("offers", "offers", "currently "),
        ("provides", "provides", ""),
        ("sells", "sells", "currently "),
        ("manufactures", "manufactures", ""),
        ("supplies", "supplies", "currently "),
        ("oferuje", "oferuje", "obecnie "),
        ("świadczy", "świadczy", ""),
        ("sprzedaje", "sprzedaje", "obecnie "),
        ("produkuje", "produkuje", ""),
        ("dostarcza", "dostarcza", "obecnie "),
    ]
    for idx, (predicate, pred, modifier) in enumerate(products):
        lang = (
            "pl"
            if predicate in {"oferuje", "świadczy", "sprzedaje", "produkuje", "dostarcza"}
            else "en"
        )
        shape = f"products_services.{lang}.{predicate}"
        base = f'{ENTITY} {pred} "cloud systems".'
        modified_base = (
            f'{ENTITY} {"obecnie " if lang == "pl" else "currently "}{pred} "cloud systems".'
        )
        for suffix, cls, text, val, rationale in [
            (
                "p1",
                "SUPPORTED_CONTRACT_POSITIVE",
                base,
                "cloud systems",
                "Unmodified predicate supports the exact quoted label.",
            ),
            (
                "p2",
                "SUPPORTED_CONTRACT_POSITIVE",
                modified_base.replace('"cloud systems"', '"cloud \\"systems\\""'),
                'cloud "systems"',
                "Allowed language-specific optional modifier and escaped label both match.",
            ),
            (
                "p3",
                "SUPPORTED_CONTRACT_POSITIVE",
                base.replace('"cloud systems"', '"renewable-energy systems"'),
                "renewable-energy systems",
                "Opaque punctuation-bearing label is accepted exactly.",
            ),
            (
                "n1",
                "UNSAFE_NEGATIVE",
                base,
                "cloud services",
                "Candidate names a different, unsupported service label.",
            ),
            (
                "n2",
                "UNSAFE_NEGATIVE",
                base + " Only after approval.",
                "cloud systems",
                "An added qualification invalidates the entire assertion.",
            ),
            (
                "n3",
                "UNSAFE_NEGATIVE",
                base,
                "cloud",
                "Substring candidate does not equal the decoded label.",
            ),
            (
                "o1",
                "OUT_OF_CONTRACT_TRUE",
                f"{ENTITY} {modifier}{pred} cloud systems.",
                "cloud systems",
                "True-looking unquoted phrase is outside the selected grammar.",
            ),
            (
                "o2",
                "OUT_OF_CONTRACT_TRUE",
                f'{ENTITY} {modifier}{pred} "cloud systems" for hospitals.',
                "cloud systems",
                "A sourced label with residual tail is outside contract.",
            ),
        ]:
            cases.append(
                _case(
                    f"ps-{idx:02}-{suffix}",
                    cls,
                    "products_services",
                    shape,
                    text,
                    "products_services",
                    val,
                    expected="published" if cls == "SUPPORTED_CONTRACT_POSITIVE" else "rejected",
                    rationale=rationale,
                )
            )

    qualitative = [
        ("business_description.en", "operates as", "a software company", "business_description"),
        (
            "business_description.pl",
            "działa jako",
            "spółka programistyczna",
            "business_description",
        ),
        ("industries.en", "operates in the", "software", "industries"),
        ("industries.pl", "działa w branży", "oprogramowania", "industries"),
        ("markets.en", "operates in the", "European market", "markets"),
        ("markets.pl", "działa na rynku", "europejskim", "markets"),
    ]
    for idx, (shape, predicate, label, field) in enumerate(qualitative):
        tail = (
            " industry"
            if field == "industries" and shape.endswith("en")
            else " market"
            if field == "markets" and shape.endswith("en")
            else ""
        )
        base = f'{ENTITY} {predicate} "{label}"{tail}.'
        qualified_label = label + " – B2B"
        rows = [
            (
                "p1",
                "SUPPORTED_CONTRACT_POSITIVE",
                base,
                label,
                "Exact quoted label supports scalar/list item.",
            ),
            (
                "p2",
                "SUPPORTED_CONTRACT_POSITIVE",
                base.replace(f'"{label}"', json.dumps(label + " prime", ensure_ascii=False)),
                label + " prime",
                "Complete JSON-quoted label is opaque; no vocabulary is required.",
            ),
            (
                "p3",
                "SUPPORTED_CONTRACT_POSITIVE",
                base.replace(f'"{label}"', json.dumps(qualified_label, ensure_ascii=False)),
                qualified_label,
                "A distinct punctuation-bearing opaque label is fully supported.",
            ),
            (
                "n1",
                "UNSAFE_NEGATIVE",
                base,
                [label, "unverified second item"]
                if field in {"industries", "markets"}
                else label + " extra",
                (
                    "A list with one unsupported item is not wholly supported; "
                    "scalar has an extra mismatch."
                ),
            ),
            (
                "n2",
                "UNSAFE_NEGATIVE",
                base + " After approval.",
                label,
                "Trailing source qualification invalidates assertion.",
            ),
            (
                "n3",
                "UNSAFE_NEGATIVE",
                base,
                "different label",
                "Proposed value mismatches the decoded label.",
            ),
            (
                "o1",
                "OUT_OF_CONTRACT_TRUE",
                base.replace(f'"{label}"', label),
                label,
                "Unquoted label is true-looking but outside contract.",
            ),
            (
                "o2",
                "OUT_OF_CONTRACT_TRUE",
                base[:-1] + " in Europe.",
                label,
                "Additional residual phrase is outside the one-production language.",
            ),
        ]
        for suffix, cls, text, val, rationale in rows:
            cases.append(
                _case(
                    f"ql-{idx:02}-{suffix}",
                    cls,
                    field,
                    shape,
                    text,
                    field,
                    val,
                    expected="published" if cls == "SUPPORTED_CONTRACT_POSITIVE" else "rejected",
                    rationale=rationale,
                )
            )

    emp_shapes = [
        ("employees.en", "employs", "people", "as of"),
        ("employees.pl", "zatrudnia", "pracowników", "na dzień"),
    ]
    for idx, (shape, predicate, people, date_link) in enumerate(emp_shapes):
        date_text = f" {date_link} 2026-10-01"
        base = f"{ENTITY} {predicate} 0 {people}{date_text}."
        rows = [
            (
                "p1",
                "SUPPORTED_CONTRACT_POSITIVE",
                base,
                {"count": 0, "as_of": "2026-10-01"},
                None,
                "Explicit zero and a valid observation date are preserved.",
            ),
            (
                "p2",
                "SUPPORTED_CONTRACT_POSITIVE",
                f"{ENTITY} {predicate} 42 {people}.",
                {"count": 42},
                None,
                "Missing source date supports count without inventing a date.",
            ),
            (
                "p3",
                "SUPPORTED_CONTRACT_POSITIVE",
                f"{ENTITY} {predicate} 12 {people} as of 2026-09-30."
                if idx == 0
                else f"{ENTITY} {predicate} 12 {people} na dzień 2026-09-30.",
                {"count": 12, "as_of": "2026-09-29"},
                None,
                "Wrong optional candidate date is removed while count remains supported.",
            ),
            (
                "n1",
                "UNSAFE_NEGATIVE",
                f"{ENTITY} {predicate} 01 {people}.",
                {"count": 1},
                None,
                "Leading-zero count is outside grammar.",
            ),
            (
                "n2",
                "UNSAFE_NEGATIVE",
                f"{ENTITY} {predicate} 8 {people}.",
                {"count": 9},
                None,
                "Candidate count mismatch is unsupported.",
            ),
            (
                "n3",
                "UNSAFE_NEGATIVE",
                f"{ENTITY} {predicate} 9 {people} as of 2026-10-04."
                if idx == 0
                else f"{ENTITY} {predicate} 9 {people} na dzień 2026-10-04.",
                {"count": 9},
                None,
                "Future observation invalidates the whole assertion.",
            ),
            (
                "o1",
                "OUT_OF_CONTRACT_TRUE",
                f"{ENTITY} has more than 8 people."
                if idx == 0
                else f"{ENTITY} ma ponad 8 pracowników.",
                {"kind": "range", "minimum": 9},
                None,
                "A true lower-bound workforce assertion lies outside exact-count grammar.",
            ),
            (
                "o2",
                "OUT_OF_CONTRACT_TRUE",
                f"{ENTITY} employs between 8 and 10 people."
                if idx == 0
                else f"{ENTITY} zatrudnia od 8 do 10 pracowników.",
                {"kind": "range", "minimum": 8, "maximum": 10},
                None,
                "A true employee interval is modeled as a range, outside exact-count productions.",
            ),
        ]
        for suffix, cls, text, val, _, rationale in rows:
            cases.append(
                _case(
                    f"emp-{idx:02}-{suffix}",
                    cls,
                    "employees",
                    shape,
                    text,
                    "employees",
                    val,
                    expected="published" if cls == "SUPPORTED_CONTRACT_POSITIVE" else "rejected",
                    rationale=rationale,
                )
            )

    finance_shapes = [
        (report, metric)
        for report in ("reported", "recorded")
        for metric in ("revenue", "net profit", "net loss", "net result")
    ]
    for idx, (report, metric) in enumerate(finance_shapes):
        mapped = "net_result" if metric != "revenue" else "revenue"
        signed = "12.50" if metric == "net loss" else "+12.50"
        result_value = "-12.50" if metric == "net loss" else "12.50"

        def sentence(
            amount: str = signed,
            scale: str = "thousand",
            end: str = "2025-12-31",
            currency: str = "EUR",
            report: str = report,
            metric: str = metric,
        ) -> str:
            return (
                f"{ENTITY} {report} standalone {metric} of {currency} {amount} {scale} for "
                f"2025-01-01 to {end}."
            )

        target = {
            "metric": mapped,
            "value": result_value,
            "start": "2025-01-01",
            "end": "2025-12-31",
            "currency": "EUR",
            "unit": "thousands",
            "scope": "legal_entity",
        }
        rows = [
            (
                "p1",
                "SUPPORTED_CONTRACT_POSITIVE",
                sentence(),
                target,
                None,
                "Explicit sign conventions and atomic context match.",
            ),
            (
                "p2",
                "SUPPORTED_CONTRACT_POSITIVE",
                sentence("0", "units", currency="USD"),
                {**target, "value": "0", "currency": "USD", "unit": "units"},
                None,
                "Zero, USD currency and unit scale are retained.",
            ),
            (
                "p3",
                "SUPPORTED_CONTRACT_POSITIVE",
                sentence(
                    "−123" if metric == "net result" else "123", "billion", "2025-12-30", "PLN"
                ),
                {
                    **target,
                    "value": "-123" if metric in {"net loss", "net result"} else "123",
                    "start": "2025-01-01",
                    "end": "2025-12-30",
                    "currency": "PLN",
                    "unit": "billions",
                },
                None,
                (
                    "PLN and billion map without conversion; unsigned loss and Unicode negative "
                    "sign conventions are exact."
                ),
            ),
            (
                "n1",
                "UNSAFE_NEGATIVE",
                sentence("1,25"),
                target,
                None,
                "Comma decimal is not an amount production.",
            ),
            (
                "n2",
                "UNSAFE_NEGATIVE",
                sentence() + " Preliminary.",
                target,
                None,
                "Trailing qualification invalidates the complete unit.",
            ),
            (
                "n3",
                "UNSAFE_NEGATIVE",
                sentence(
                    "-12.50"
                    if metric == "net profit"
                    else "+12.50"
                    if metric == "net loss"
                    else signed
                ),
                {**target, "value": "99"},
                None,
                "Candidate amount mismatch, and contradictory profit/loss signs, are unsupported.",
            ),
            (
                "o1",
                "OUT_OF_CONTRACT_TRUE",
                sentence().replace("standalone ", "group "),
                {**target, "scope": "group", "group_name": "Example Group"},
                None,
                "A true named-group result is outside the legal-entity contract.",
            ),
            (
                "o2",
                "OUT_OF_CONTRACT_TRUE",
                sentence(end="2026-10-03"),
                {**target, "end": "2026-10-03"},
                None,
                (
                    "True year-to-date result ends on the run date and is outside completed-period "
                    "support."
                ),
            ),
        ]
        for suffix, cls, text, val, _, rationale in rows:
            cases.append(
                _case(
                    f"fin-{idx:02}-{suffix}",
                    cls,
                    "financials",
                    f"financials.{report}.{metric}",
                    text,
                    "financials.0" if mapped == "revenue" else "financials.1",
                    val,
                    expected="published" if cls == "SUPPORTED_CONTRACT_POSITIVE" else "rejected",
                    rationale=rationale,
                )
            )

    event_shapes = [
        ("opened", "opened", "on"),
        ("launched", "launched", "on"),
        ("signed", "signed", "on"),
        ("otworzyła", "otworzyła", "w dniu"),
        ("uruchomiła", "uruchomiła", "w dniu"),
        ("podpisała", "podpisała", "w dniu"),
    ]
    for idx, (shape_name, pred, date_link) in enumerate(event_shapes):
        base = f'{ENTITY} {pred} "new laboratory" {date_link} 2026-09-20.'
        rows = [
            (
                "p1",
                "SUPPORTED_CONTRACT_POSITIVE",
                base,
                {"title": "new laboratory", "summary": base, "occurred_on": "2026-09-20"},
                "2026-09-25",
                "Exact complete event and matching publication provenance.",
            ),
            (
                "p2",
                "SUPPORTED_CONTRACT_POSITIVE",
                base,
                {"title": "new laboratory", "summary": base, "occurred_on": None},
                "2026-09-25",
                "Unverified optional occurrence date is removed, other components retained.",
            ),
            (
                "p3",
                "SUPPORTED_CONTRACT_POSITIVE",
                base.replace('"new laboratory"', '"new \\"laboratory\\""'),
                {
                    "title": 'new "laboratory"',
                    "summary": base.replace('"new laboratory"', '"new \\"laboratory\\""'),
                    "occurred_on": "2026-09-20",
                },
                "2026-09-25",
                "Escaped JSON quote is part of the decoded event label.",
            ),
            (
                "n1",
                "UNSAFE_NEGATIVE",
                base,
                {"title": "new", "summary": base, "occurred_on": "2026-09-20"},
                "2026-09-25",
                "Event title must equal the whole decoded label.",
            ),
            (
                "n2",
                "UNSAFE_NEGATIVE",
                base + " Later denied.",
                {
                    "title": "new laboratory",
                    "summary": base + " Later denied.",
                    "occurred_on": "2026-09-20",
                },
                "2026-09-25",
                "Extra source text invalidates the whole assertion.",
            ),
            (
                "n3",
                "UNSAFE_NEGATIVE",
                base,
                {"title": "new laboratory", "summary": base, "occurred_on": "2026-09-20"},
                None,
                "Missing explicit source publication date cannot be replaced by retrieval time.",
            ),
            (
                "o1",
                "OUT_OF_CONTRACT_TRUE",
                base.replace('"new laboratory"', "new laboratory"),
                {
                    "title": "new laboratory",
                    "summary": base.replace('"new laboratory"', "new laboratory"),
                    "occurred_on": "2026-09-20",
                },
                "2026-09-25",
                (
                    "Unquoted event label is a true-looking assertion outside the quote-required "
                    "grammar."
                ),
            ),
            (
                "o2",
                "OUT_OF_CONTRACT_TRUE",
                base.replace(pred, "announced"),
                {
                    "title": "new laboratory",
                    "summary": base.replace(pred, "announced"),
                    "occurred_on": "2026-09-20",
                },
                "2026-09-25",
                (
                    "True event is expressed with a predicate outside the finite completed-event "
                    "alternatives."
                ),
            ),
        ]
        for suffix, cls, text, val, pub, rationale in rows:
            cases.append(
                _case(
                    f"evt-{idx:02}-{suffix}",
                    cls,
                    "recent_developments",
                    f"events.{shape_name}",
                    text,
                    "recent_developments",
                    val,
                    path="recent_developments.0",
                    expected="published" if cls == "SUPPORTED_CONTRACT_POSITIVE" else "rejected",
                    source_date=pub,
                    rationale=rationale,
                )
            )

    # Cross-cutting source-unit, entity, multi-item and structural identity controls.
    cases.extend(
        [
            _case(
                "ctl-clipped-citation",
                "PROVENANCE_INVALID",
                "provenance",
                "full-source",
                f'{ENTITY} offers "cloud systems".',
                "products_services",
                "cloud systems",
                excerpt='offers "cloud systems"',
                expected="rejected",
                rationale="Citation omits the legal subject and full source unit.",
            ),
            _case(
                "ctl-other-company",
                "UNSAFE_NEGATIVE",
                "entity",
                "exact-subject",
                'Other sp. z o.o. offers "cloud systems".',
                "products_services",
                "cloud systems",
                expected="rejected",
                rationale="A similar neighboring company name is not the exact legal subject.",
            ),
            _case(
                "ctl-compound-finance",
                "UNSAFE_NEGATIVE",
                "financials",
                "atomic-observation",
                (
                    f"{ENTITY} reported standalone revenue of PLN 10 units for 2025-01-01 to "
                    "2025-12-31; net result was 5 EUR."
                ),
                "financials.0",
                {
                    "metric": "revenue",
                    "value": "10",
                    "start": "2025-01-01",
                    "end": "2025-12-31",
                    "currency": "PLN",
                    "unit": "units",
                    "scope": "legal_entity",
                },
                expected="rejected",
                rationale="Separate clauses cannot be assembled into one atomic observation.",
            ),
            _case(
                "ctl-mf-comment-only",
                "PROVENANCE_INVALID",
                "identity",
                "mapped-field-registry",
                f'{ENTITY} offers "cloud systems".',
                "products_services",
                "cloud systems",
                registry=json.dumps(
                    {"result": {"subject": {"nip": NIP}}, "comment": ENTITY}, ensure_ascii=False
                ),
                run_rejected=True,
                expected="rejected",
                rationale="A comment string cannot supply missing mapped legal_name.",
            ),
            _case(
                "ctl-mf-duplicate-key",
                "IDENTITY_INVALID",
                "identity",
                "duplicate-json-key",
                f'{ENTITY} offers "cloud systems".',
                "products_services",
                "cloud systems",
                registry=(
                    '{"result":{"subject":{"nip":"5220003782","name":"Example sp. z o.o.",'
                    '"name":"Example sp. z o.o."}}}'
                ),
                run_rejected=True,
                expected="rejected",
                rationale="Duplicate mapped declarations make registry JSON ambiguous.",
            ),
            _case(
                "ctl-legacy-identity",
                "SUPPORTED_CONTRACT_POSITIVE",
                "identity",
                "legacy-snapshot",
                f'{ENTITY} offers "cloud systems".',
                "products_services",
                "cloud systems",
                registry=(
                    "MF VAT register identity material (not a raw registry response):\n"
                    "legal_name: Example sp. z o.o.\n"
                    "krs: unknown; Not provided\nregon: unknown; Not provided\n"
                    "registered_city: unknown; Not provided\n"
                    "registered_address: unknown; Not provided\nwebsite: unknown; Not provided\n"
                    "NIP: 5220003782"
                ),
                legal_excerpt=ENTITY,
                expected="published",
                rationale="Exact host legacy snapshot structure maps the supported legal name.",
            ),
        ]
    )
    return cases
