"""Finite, whole-unit source grammar for deterministic publication support."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True, slots=True)
class TextObservation:
    field: str
    value: str


@dataclass(frozen=True, slots=True)
class EmployeeObservation:
    count: int
    as_of: date | None


@dataclass(frozen=True, slots=True)
class FinancialObservation:
    entity: str
    actuality: str
    sign: str
    metric: str
    value: Decimal
    currency: str
    unit: str
    scope: str
    period_start: date
    period_end: date


@dataclass(frozen=True, slots=True)
class EventObservation:
    title: str
    summary: str
    occurred_on: date | None


_LABEL = r'("(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*")'
_EMPLOYEE = re.compile(
    r"^(?P<predicate>employs|zatrudnia) (?P<count>0|[1-9][0-9]{0,11}) "
    r"(?P<noun>people|pracowników)(?: (?P<datepart>as of|na dzień) "
    r"(?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2}))?\.$"
)
_FINANCIAL = re.compile(
    r"^(?P<actuality>reported|recorded) standalone "
    r"(?P<metric>revenue|net profit|net loss|net result) of "
    r"(?P<currency>PLN|EUR|USD) (?P<amount>[+\-−]?(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,6})?) "
    r"(?P<scale>units|thousand|million|billion) for "
    r"(?P<start>[0-9]{4}-[0-9]{2}-[0-9]{2}) to "
    r"(?P<end>[0-9]{4}-[0-9]{2}-[0-9]{2})\.$"
)
_EVENT = re.compile(
    rf"^(?P<predicate>opened|launched|signed|otworzyła|uruchomiła|podpisała) "
    rf"{_LABEL}(?: (?P<datepart>on|w dniu) (?P<date>[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}))?\.$",
    re.DOTALL,
)
_QUALITATIVE = (
    (
        "products_services",
        re.compile(
            rf"^(?:currently )?(?:offers|provides|sells|manufactures|supplies) {_LABEL}\.$",
            re.DOTALL,
        ),
    ),
    (
        "products_services",
        re.compile(
            rf"^(?:obecnie )?(?:oferuje|świadczy|sprzedaje|produkuje|dostarcza) {_LABEL}\.$",
            re.DOTALL,
        ),
    ),
    ("business_description", re.compile(rf"^(?:operates as|działa jako) {_LABEL}\.$", re.DOTALL)),
    ("industries", re.compile(rf"^operates in the {_LABEL} industry\.$", re.DOTALL)),
    ("industries", re.compile(rf"^(?:działa w branży) {_LABEL}\.$", re.DOTALL)),
    ("markets", re.compile(rf"^operates in the {_LABEL} market\.$", re.DOTALL)),
    ("markets", re.compile(rf"^(?:działa na rynku) {_LABEL}\.$", re.DOTALL)),
)


def _label(value: str) -> str | None:
    try:
        decoded = json.loads(value)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(decoded, str) or not 1 <= len(decoded) <= 256:
        return None
    if decoded != decoded.strip() or any(
        unicodedata.category(char).startswith("C") for char in decoded
    ):
        return None
    return unicodedata.normalize("NFC", decoded)


def _date(value: str) -> date | None:
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def parse_assertion(
    content: str, legal_name: str, generated_on: date
) -> TextObservation | EmployeeObservation | FinancialObservation | EventObservation | None:
    """Parse exactly one complete retained assertion, without selecting a substring."""
    if not isinstance(content, str):
        return None
    text = unicodedata.normalize("NFC", content).strip()
    if len(text) > 4096:
        return None
    entity = " ".join(unicodedata.normalize("NFC", legal_name).split())
    if not entity:
        return None
    if not text.startswith(entity + " "):
        return None
    body = text[len(entity) + 1 :]

    for field, pattern in _QUALITATIVE:
        match = pattern.fullmatch(body)
        if match:
            value = _label(match.group(1))
            if value is not None:
                return TextObservation(field=field, value=value)

    match = _EMPLOYEE.fullmatch(body)
    if match:
        expected = "employs" if match.group("predicate") == "employs" else "zatrudnia"
        if match.group("noun") != ("people" if expected == "employs" else "pracowników"):
            return None
        if match.group("datepart") and match.group("datepart") != (
            "as of" if expected == "employs" else "na dzień"
        ):
            return None
        observation_date = _date(match.group("date")) if match.group("date") else None
        if match.group("date") and (observation_date is None or observation_date > generated_on):
            return None
        return EmployeeObservation(count=int(match.group("count")), as_of=observation_date)

    match = _FINANCIAL.fullmatch(body)
    if match:
        start, end = _date(match.group("start")), _date(match.group("end"))
        if start is None or end is None or start > end or end >= generated_on:
            return None
        raw_amount = match.group("amount")
        sign = raw_amount[0] if raw_amount[:1] in ("+", "-", "−") else ""
        magnitude = raw_amount[1:] if sign else raw_amount
        try:
            amount = Decimal(magnitude)
        except InvalidOperation:
            return None
        metric = match.group("metric")
        if metric == "net profit":
            if sign in ("-", "−"):
                return None
        elif metric == "net loss":
            if sign:
                return None
            amount = -amount
        elif sign in ("-", "−"):
            amount = -amount
        units = {
            "units": "units",
            "thousand": "thousands",
            "million": "millions",
            "billion": "billions",
        }
        return FinancialObservation(
            entity=entity,
            actuality=match.group("actuality"),
            sign=sign,
            metric="revenue" if metric == "revenue" else "net_result",
            value=amount,
            currency=match.group("currency"),
            unit=units[match.group("scale")],
            scope="legal_entity",
            period_start=start,
            period_end=end,
        )

    match = _EVENT.fullmatch(body)
    if match:
        occurrence = _date(match.group("date")) if match.group("date") else None
        if match.group("date") and (occurrence is None or occurrence > generated_on):
            return None
        title = _label(match.group(2))
        if title is not None:
            return EventObservation(title=title, summary=text, occurred_on=occurrence)
    return None
