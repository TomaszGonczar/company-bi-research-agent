"""Compact, raw-input regressions for the v0.1.1 release blockers.

``blocker_cases`` is deliberately independent of pytest fixtures so the same
full JSON cases can be consumed by the offline CLI audit harness.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from company_bi.models import CompanyResearchRun
from company_bi.verification import verify_run

ROOT = Path(__file__).resolve().parents[2]
CONTROLLED = ROOT / "examples/verification/controlled-current-service.json"
ASSECO = ROOT / "examples/utility_v011/runs/baseline/asseco-poland.json"
GENERATED_AT = "2026-10-03T12:00:00Z"


def _base() -> dict[str, Any]:
    run = json.loads(CONTROLLED.read_text(encoding="utf-8"))
    registry = next(
        source for source in run["sources"] if source["source"]["source_id"] == "registry"
    )
    registry["content"] = 'NIP: 1234563218; "Example sp. z o.o."'
    # Preserve the template's exact name citation alongside explicit registry NIP.
    run["identity"]["legal_name"]["evidence"][0]["excerpt"] = '"Example sp. z o.o."'
    run["identity"]["legal_name"]["value"] = "Example sp. z o.o."
    run["identity"]["nip"] = "1234563218"
    unknown = {"state": "unknown", "reason": "Not established in this blocker case"}
    draft = run["draft"]
    for name in ("business_description", "products_services", "industries", "markets", "employees"):
        draft[name] = copy.deepcopy(unknown)
    draft["financials"] = [
        {**copy.deepcopy(unknown), "metric": "revenue"},
        {**copy.deepcopy(unknown), "metric": "net_result"},
    ]
    draft["recent_developments"] = []
    run["generated_at"] = GENERATED_AT
    run["identity"]["resolved_at"] = GENERATED_AT
    for source in run["sources"]:
        source["source"]["retrieved_at"] = GENERATED_AT
    return run


def _set_content(run: dict[str, Any], content: str) -> None:
    next(source for source in run["sources"] if source["source"]["source_id"] == "page")[
        "content"
    ] = content


def _fact(value: Any, excerpt: str, *, source_id: str = "page") -> dict[str, Any]:
    return {
        "state": "supported",
        "value": value,
        "evidence": [{"source_id": source_id, "excerpt": excerpt}],
    }


def _case(
    case_id: str,
    pair_id: str,
    role: str,
    family: str,
    focus: str,
    why: str,
    run: dict[str, Any],
    kind: str,
    *,
    target_path: str = "products_services",
    removed_paths: list[str] | None = None,
    preserve_supported: list[str] | None = None,
    origin: str = "runbook",
) -> dict[str, Any]:
    return {
        "id": case_id,
        "pair_id": pair_id,
        "role": role,
        "family": family,
        "focus": focus,
        "why": why,
        "target_path": target_path,
        "run": run,
        "expect": {
            "kind": kind,
            **({"removed_paths": removed_paths} if removed_paths else {}),
            **({"preserve_supported": preserve_supported} if preserve_supported else {}),
        },
        "origin": origin,
    }


def blocker_cases() -> list[dict[str, Any]]:
    """Return complete deterministic raw cases, before Pydantic validation."""
    cases: list[dict[str, Any]] = []

    def product_case(
        case_id: str,
        pair_id: str,
        role: str,
        text: str,
        *,
        value: str = "cloud services",
        origin: str = "runbook",
    ) -> None:
        run = _base()
        _set_content(run, text)
        run["draft"]["products_services"] = _fact([value], text)
        cases.append(
            _case(
                case_id,
                pair_id,
                role,
                "current_future_conditional",
                "products_services",
                (
                    "A supported current-service candidate must be affirmatively current, "
                    "not prospective, expired, or conditional."
                ),
                run,
                "supported" if role == "positive" else "blocked",
                target_path="products_services",
                origin=origin,
            )
        )

    # A — future, expired and conditional claims versus real current controls.
    product_case(
        "a-future-en",
        "a-past-control",
        "negative",
        "Example sp. z o.o. offers cloud services starting in January 2028.",
    )
    product_case(
        "a-future-pl",
        "a-polish-current-control",
        "negative",
        "Example sp. z o.o. oferuje usługi chmurowe od stycznia 2028 roku.",
        value="usługi chmurowe",
    )
    product_case(
        "a-expired",
        "a-past-control",
        "negative",
        "Example sp. z o.o. offers cloud services only until 2024-12-31.",
    )
    product_case(
        "a-subject-to",
        "a-licensed-control",
        "negative",
        "Example sp. z o.o. offers cloud services subject to obtaining a licence.",
    )
    product_case(
        "a-once",
        "a-licensed-control",
        "negative",
        "Example sp. z o.o. offers cloud services once its licence application is approved.",
    )
    product_case(
        "a-provided-that",
        "a-licensed-control",
        "negative",
        "Example sp. z o.o. offers cloud services, provided that regulators approve.",
    )
    product_case(
        "a-question-denial",
        "a-current-control",
        "negative",
        "Example sp. z o.o. offers cloud services?",
    )
    product_case(
        "a-postposed-denial",
        "a-current-control",
        "negative",
        "Example sp. z o.o. offers cloud services, a claim later denied by the board.",
    )
    product_case(
        "a-past-positive",
        "a-past-control",
        "positive",
        "Example sp. z o.o. offers cloud services from January 2020.",
    )
    product_case(
        "a-current-positive",
        "a-current-control",
        "positive",
        "Example sp. z o.o. currently offers cloud services.",
    )
    product_case(
        "a-polish-current-positive",
        "a-polish-current-control",
        "positive",
        "Example sp. z o.o. obecnie oferuje usługi chmurowe.",
        value="usługi chmurowe",
    )
    product_case(
        "a-licence-positive",
        "a-licensed-control",
        "positive",
        "Example sp. z o.o. offers cloud services under its existing licence.",
    )

    def financial_case(
        case_id: str, pair_id: str, role: str, text: str, amount: str, *, origin: str = "runbook"
    ) -> None:
        run = _base()
        idx = 1
        _set_content(run, text)
        run["draft"]["financials"][idx] = {
            **_fact(amount, text),
            "metric": "net_result",
            "period": {"start": "2025-01-01", "end": "2025-12-31"},
            "currency": "PLN",
            "unit": "millions",
            "scope": "legal_entity",
        }
        cases.append(
            _case(
                case_id,
                pair_id,
                role,
                "financial_sign",
                "financials[1]",
                (
                    "The sign must follow the selected net-result assertion, "
                    "not a nearby operating-profit mention or punctuation loss."
                ),
                run,
                "supported" if role == "positive" else "blocked",
                target_path="financials[1]",
                origin=origin,
            )
        )

    # B — net loss, Unicode/accounting/Polish negatives and explicit controls.
    financial_case(
        "b-mixed-loss-profit",
        "b-loss-control",
        "negative",
        (
            "Example sp. z o.o. reported a standalone net loss of PLN 12.5 million for 2025-01-01 "
            "to 2025-12-31, despite an operating profit."
        ),
        "12.5",
    )
    financial_case(
        "b-unicode-minus",
        "b-unicode-minus-control",
        "negative",
        (
            "Example sp. z o.o. standalone net result was PLN −12.5 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "12.5",
    )
    financial_case(
        "b-accounting-negative",
        "b-accounting-control",
        "negative",
        (
            "Example sp. z o.o. standalone net result was PLN (12.5) million for "
            "2025-01-01 to 2025-12-31."
        ),
        "12.5",
    )
    financial_case(
        "b-polish-minus",
        "b-polish-minus-control",
        "negative",
        (
            "Example sp. z o.o. wykazała jednostkowy wynik netto minus 12,5 mln PLN za okres "
            "2025-01-01 do 2025-12-31."
        ),
        "12.5",
    )
    financial_case(
        "b-loss-positive",
        "b-loss-control",
        "positive",
        (
            "Example sp. z o.o. standalone net loss was PLN 12.5 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "-12.5",
    )
    financial_case(
        "b-plus-positive",
        "b-plus-control",
        "positive",
        (
            "Example sp. z o.o. standalone net result was PLN +12.5 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "12.5",
    )
    financial_case(
        "b-minus-positive",
        "b-minus-control",
        "positive",
        (
            "Example sp. z o.o. standalone net result was PLN -12.5 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "-12.5",
    )
    financial_case(
        "b-unicode-minus-positive",
        "b-unicode-minus-control",
        "positive",
        (
            "Example sp. z o.o. standalone net result was PLN −12.5 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "-12.5",
    )
    financial_case(
        "b-accounting-positive",
        "b-accounting-control",
        "positive",
        (
            "Example sp. z o.o. standalone net result was PLN (12.5) million for "
            "2025-01-01 to 2025-12-31."
        ),
        "-12.5",
    )
    financial_case(
        "b-polish-minus-positive",
        "b-polish-minus-control",
        "positive",
        (
            "Example sp. z o.o. wykazała jednostkowy wynik netto minus 12,5 mln PLN za okres "
            "2025-01-01 do 2025-12-31."
        ),
        "-12.5",
    )
    financial_case(
        "b-zero-positive",
        "b-zero-control",
        "positive",
        "Example sp. z o.o. standalone net result was PLN 0 million for 2025-01-01 to 2025-12-31.",
        "0",
    )

    def revenue_case(
        case_id: str,
        pair_id: str,
        role: str,
        text: str,
        value: str,
        period: tuple[str, str],
        *,
        cue: str | None = None,
    ) -> None:
        run = _base()
        _set_content(run, text)
        run["draft"]["financials"][0] = {
            **_fact(value, text),
            "metric": "revenue",
            "period": {"start": period[0], "end": period[1]},
            "currency": "PLN",
            "unit": "millions",
            "scope": "legal_entity",
        }
        cases.append(
            _case(
                case_id,
                pair_id,
                role,
                "financial_amount_period_actuality",
                "financials[0]",
                cue
                or (
                    "Revenue amount, period and actuality must belong to the same reported "
                    "observation."
                ),
                run,
                "supported" if role == "positive" else "blocked",
                target_path="financials[0]",
            )
        )

    # C — delta versus level, adjacent period amounts, nonactual language and incomplete period.
    delta_source = (
        "Example sp. z o.o. reported standalone revenue up by PLN 20 million to PLN 140 million "
        "for 2025-01-01 to 2025-12-31."
    )
    revenue_case(
        "c-delta-not-level",
        "c-delta-control",
        "negative",
        delta_source,
        "20",
        ("2025-01-01", "2025-12-31"),
    )
    revenue_case(
        "c-delta-positive",
        "c-delta-control",
        "positive",
        delta_source,
        "140",
        ("2025-01-01", "2025-12-31"),
    )
    comparison = (
        "Example sp. z o.o. reported standalone revenue of PLN 140 million for 2025-01-01 "
        "to 2025-12-31 compared with PLN 120 million for 2024-01-01 to 2024-12-31."
    )
    revenue_case(
        "c-own-2025-vs-2024",
        "c-period-control",
        "negative",
        comparison,
        "140",
        ("2024-01-01", "2024-12-31"),
    )
    revenue_case(
        "c-period-positive",
        "c-period-control",
        "positive",
        comparison,
        "120",
        ("2024-01-01", "2024-12-31"),
    )
    for key in ("guidance", "forecast", "target", "outlook"):
        revenue_case(
            f"c-{key}",
            "c-reported-actual",
            "negative",
            f"Example sp. z o.o. reported standalone revenue {key} of PLN 140 million for "
            "2025-01-01 to 2025-12-31.",
            "140",
            ("2025-01-01", "2025-12-31"),
        )
    revenue_case(
        "c-open-annual-period",
        "c-reported-actual",
        "negative",
        (
            "Example sp. z o.o. reported annual standalone revenue of PLN 140 million for "
            "2026-01-01 to 2026-12-31."
        ),
        "140",
        ("2026-01-01", "2026-12-31"),
    )
    revenue_case(
        "c-reported-actual",
        "c-reported-actual",
        "positive",
        (
            "Example sp. z o.o. reported standalone revenue of PLN 140 million for "
            "2025-01-01 to 2025-12-31."
        ),
        "140",
        ("2025-01-01", "2025-12-31"),
    )

    def employee_case(
        case_id: str,
        pair_id: str,
        role: str,
        text: str,
        count: int,
        *,
        identity_name: str = "Example sp. z o.o.",
        as_of: str | None = None,
    ) -> None:
        run = _base()
        if identity_name != "Example sp. z o.o.":
            registry = next(
                source for source in run["sources"] if source["source"]["source_id"] == "registry"
            )
            registry["content"] = f'NIP: 1234563218; "{identity_name}"'
            run["identity"]["legal_name"]["value"] = identity_name
            run["identity"]["legal_name"]["evidence"][0]["excerpt"] = f'"{identity_name}"'
        _set_content(run, text)
        run["draft"]["employees"] = {
            **_fact({"kind": "exact", "count": count}, text),
            "as_of": as_of,
        }
        cases.append(
            _case(
                case_id,
                pair_id,
                role,
                "employee_entity_attribution",
                "employees",
                (
                    "People counts require employment semantics and direct attribution "
                    "to the exact target legal entity."
                ),
                run,
                "supported" if role == "positive" else "blocked",
                target_path="employees",
            )
        )

    # D — distinguish service recipients, partners/suppliers and longer legal names.
    employee_case(
        "d-serves-people",
        "d-serves-control",
        "negative",
        "Example sp. z o.o. serves 12,000 people.",
        12000,
    )
    employee_case(
        "d-serves-control",
        "d-serves-control",
        "positive",
        "Example sp. z o.o. employs 12,000 people as of 2025-12-31.",
        12000,
        as_of="2025-12-31",
    )
    employee_case(
        "d-trained-people",
        "d-trained-control",
        "negative",
        "Example sp. z o.o. has trained 3,000 people.",
        3000,
    )
    employee_case(
        "d-trained-control",
        "d-trained-control",
        "positive",
        "Example sp. z o.o. employs 3,000 people as of 2025-12-31.",
        3000,
        as_of="2025-12-31",
    )
    employee_case(
        "d-possessive-partner",
        "d-target-employees",
        "negative",
        "Example sp. z o.o.'s partner employs 64 people.",
        64,
    )
    employee_case(
        "d-polish-supplier",
        "d-target-employees",
        "negative",
        "Dostawca Example sp. z o.o. zatrudnia 64 pracowników.",
        64,
    )
    employee_case(
        "d-polish-partner",
        "d-target-employees",
        "negative",
        "Partner spółki Example sp. z o.o. zatrudnia 64 pracowników.",
        64,
    )
    employee_case(
        "d-longer-name",
        "d-nova-target-employees",
        "negative",
        "Nova Tech Services S.A. employs 64 people.",
        64,
        identity_name="Nova Tech S.A.",
    )
    employee_case(
        "d-target-employees",
        "d-target-employees",
        "positive",
        "Example sp. z o.o. employs 64 people as of 2025-12-31.",
        64,
        as_of="2025-12-31",
    )
    employee_case(
        "d-nova-target-employees",
        "d-nova-target-employees",
        "positive",
        "Nova Tech S.A. employs 64 people as of 2025-12-31.",
        64,
        identity_name="Nova Tech S.A.",
        as_of="2025-12-31",
    )

    def event_case(
        case_id: str,
        pair_id: str,
        role: str,
        full: str,
        excerpt: str,
        *,
        title: str = "opened a robotics laboratory",
        summary: str | None = None,
        occurred_on: str | None = "2026-09-10",
        expected: str = "supported",
    ) -> None:
        run = _base()
        _set_content(run, full)
        page = next(source for source in run["sources"] if source["source"]["source_id"] == "page")
        page["source"]["published_on"] = "2026-09-20"
        run["draft"]["recent_developments"] = [
            {
                **_fact(
                    {
                        "title": title,
                        "summary": summary or title,
                        "published_on": "2026-09-20",
                        "occurred_on": occurred_on,
                    },
                    excerpt,
                ),
            }
        ]
        cases.append(
            _case(
                case_id,
                pair_id,
                role,
                "event_context_date_ownership",
                "recent_developments[0]",
                (
                    "Retained full-page context controls denial and the occurrence date "
                    "must attach to this event, not its neighbor."
                ),
                run,
                expected,
                target_path="recent_developments[0]",
                removed_paths=["value.occurred_on"] if expected == "removed" else None,
                preserve_supported=["recent_developments[0]"] if expected == "removed" else None,
            )
        )

    # E — clipped excerpts cannot erase denial/untruth in retained page context.
    denial_full = (
        "The board denied the rumour that Example sp. z o.o. opened a robotics laboratory."
    )
    event_case(
        "e-denied-rumour",
        "e-affirmative-event",
        "negative",
        denial_full,
        "Example sp. z o.o. opened a robotics laboratory",
        occurred_on=None,
        expected="blocked",
    )
    untrue_full = "It is untrue that Example sp. z o.o. opened a robotics laboratory."
    event_case(
        "e-untrue-claim",
        "e-affirmative-event",
        "negative",
        untrue_full,
        "Example sp. z o.o. opened a robotics laboratory",
        occurred_on=None,
        expected="blocked",
    )
    postposed = "Example sp. z o.o. opened a robotics laboratory, a claim the board denied."
    event_case(
        "e-postposed-board-denial",
        "e-affirmative-event",
        "negative",
        postposed,
        "Example sp. z o.o. opened a robotics laboratory",
        occurred_on=None,
        expected="blocked",
    )
    affirmative = "Example sp. z o.o. opened a robotics laboratory on 2026-09-10."
    event_case(
        "e-affirmative-event",
        "e-affirmative-event",
        "positive",
        affirmative,
        affirmative,
        occurred_on=None,
    )

    # F — neighboring occurrences use the reported event/date order and preserve content.
    neighbors = (
        "Example sp. z o.o. operates a robotics laboratory opened on 2026-09-10 and a warehouse "
        "opened on 2026-08-01."
    )

    event_case(
        "f-wrong-neighbor-date",
        "f-correct-event-date",
        "negative",
        neighbors,
        neighbors,
        title="robotics laboratory",
        summary="operates a robotics laboratory",
        occurred_on="2026-08-01",
        expected="removed",
    )
    event_case(
        "f-right-event-date",
        "f-correct-event-date",
        "positive",
        neighbors,
        neighbors,
        title="robotics laboratory",
        summary="operates a robotics laboratory",
        occurred_on="2026-09-10",
    )
    simple_event = "Example sp. z o.o. opened a robotics laboratory on 2026-09-10."
    event_case(
        "f-straightforward-date",
        "f-correct-event-date",
        "positive",
        simple_event,
        simple_event,
        title="opened a robotics laboratory",
        occurred_on="2026-09-10",
    )

    # G — mutations remain raw until test execution; real registry NIP/name stay exact.
    for origin, template, altered_nip in (
        ("synthetic", _base(), "5220003782"),
        ("retained_asseco", json.loads(ASSECO.read_text(encoding="utf-8")), "1234563218"),
    ):
        # Retained Asseco timestamps and all other retained input fields stay untouched.
        cases.append(
            _case(
                f"g-{origin}-identity-control",
                f"g-{origin}-identity",
                "positive",
                "identity_binding",
                "identity",
                "The unchanged retained registry identity and NIP are the positive control.",
                copy.deepcopy(template),
                "identity_consistent",
                target_path="identity",
                origin=origin,
            )
        )
        bad_nip = copy.deepcopy(template)
        bad_nip["identity"]["nip"] = altered_nip
        cases.append(
            _case(
                f"g-{origin}-altered-nip",
                f"g-{origin}-identity",
                "negative",
                "identity_binding",
                "identity",
                (
                    "A candidate NIP inconsistent with the retained registry material "
                    "must be rejected."
                ),
                bad_nip,
                "reject_run",
                target_path="identity",
                origin=origin,
            )
        )
        bad_name = copy.deepcopy(template)
        bad_name["identity"]["legal_name"]["value"] = "Altered Example Legal Name S.A."
        cases.append(
            _case(
                f"g-{origin}-altered-name",
                f"g-{origin}-identity",
                "negative",
                "identity_binding",
                "identity",
                (
                    "A candidate legal name inconsistent with its unchanged registry evidence "
                    "must be rejected."
                ),
                bad_name,
                "reject_run",
                target_path="identity",
                origin=origin,
            )
        )

    return cases


def _value_at(profile: Any, path: str) -> Any:
    if path == "products_services":
        return profile.products_services
    if path == "employees":
        return profile.employees
    if path.startswith("financials["):
        return profile.financials[int(path[len("financials[") : -1])]
    if path.startswith("recent_developments["):
        return profile.recent_developments[int(path[len("recent_developments[") : -1])]
    raise AssertionError(f"unexpected target path: {path}")


@pytest.mark.parametrize("case", blocker_cases(), ids=lambda case: case["id"])
def test_blocker_raw_case(case: dict[str, Any]) -> None:
    expected = case["expect"]["kind"]
    try:
        run = CompanyResearchRun.model_validate(case["run"])
    except (ValidationError, ValueError):
        assert expected == "reject_run"
        return
    if expected == "reject_run":
        with pytest.raises((ValidationError, ValueError)):
            verify_run(run, input_sha256="0" * 64, input_name=case["id"])
        return

    profile, report = verify_run(run, input_sha256="0" * 64, input_name=case["id"])
    assert profile is not None
    assert report.status == "verified"
    if expected == "identity_consistent":
        assert profile.identity.nip == run.identity.nip
        assert profile.identity.legal_name.value == run.identity.legal_name.value
        registry_text = " ".join(
            source.content for source in run.sources if source.kind == "registry"
        )
        assert run.identity.nip in registry_text
        assert run.identity.legal_name.value in registry_text
        return
    candidate = _value_at(run.draft, case["target_path"])
    actual = _value_at(profile, case["target_path"])
    if expected == "supported":
        assert actual.state == "supported", case["why"]
        assert actual.value == candidate.value, case["why"]
        if case["target_path"] == "employees":
            assert actual.as_of == candidate.as_of
        if case["target_path"].startswith("financials["):
            assert actual.period == candidate.period
            assert actual.currency == candidate.currency
            assert actual.unit == candidate.unit
            assert actual.scope == candidate.scope
            assert actual.group_name == candidate.group_name
    elif expected in {"blocked", "removed"}:
        if case["target_path"] == "recent_developments[0]":
            if expected == "blocked":
                assert actual.state != "supported", case["why"]
            else:
                assert actual.state == "supported", case["why"]
                assert actual.value is not None
                assert actual.value.occurred_on is None, case["why"]
                assert actual.value.title == candidate.value.title
                assert actual.value.summary == candidate.value.summary
                assert actual.value.published_on == candidate.value.published_on
        else:
            assert actual.state != "supported", case["why"]
    else:
        raise AssertionError(f"unknown expected kind {expected}")


@pytest.mark.parametrize("field", ("nip", "legal_name"))
def test_identity_publication_rejects_unchecked_model_copy(field: str) -> None:
    control = next(case for case in blocker_cases() if case["id"] == "g-synthetic-identity-control")
    run = CompanyResearchRun.model_validate(control["run"])
    if field == "nip":
        altered_identity = run.identity.model_copy(update={"nip": "5220003782"})
    else:
        altered_name = run.identity.legal_name.model_copy(
            update={"value": "Altered Example Legal Name S.A."}
        )
        altered_identity = run.identity.model_copy(update={"legal_name": altered_name})
    unchecked = run.model_copy(update={"identity": altered_identity})
    with pytest.raises((ValidationError, ValueError)):
        verify_run(unchecked, input_sha256="0" * 64, input_name=f"unchecked-{field}")
