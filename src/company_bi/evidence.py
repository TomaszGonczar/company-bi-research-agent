"""Deterministic evidence gate from research drafts to publishable profiles."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

from company_bi.models import (
    CompanyEvent,
    CompanyProfile,
    CompanyResearchRun,
    EmployeeFact,
    EmployeeRange,
    EventDetails,
    EvidenceRef,
    ExactEmployees,
    Fact,
    FinancialFact,
    ProfileSource,
    RetrievedSource,
    profile_has_gaps,
)

_SPACE = re.compile(r"\s+")
_WORD = re.compile(r"[\w]+", re.UNICODE)
_EMPLOYEE_WORDS = {
    "employee",
    "employees",
    "employed",
    "staff",
    "personnel",
    "person",
    "people",
    "pracownik",
    "pracowników",
    "zatrudnia",
    "zatrudnienie",
}
_OTHER_ENTITY_MARKERS = {
    "competitor",
    "competitors",
    "rival",
    "rivals",
    "subsidiary",
    "subsidiaries",
    "affiliate",
    "affiliates",
}
_METRIC_PHRASES = {
    "revenue": (
        ("revenue",),
        ("revenues",),
        ("sales",),
        ("sales", "revenue"),
        ("turnover",),
        ("przychody",),
        ("sprzedaż",),
    ),
    "net_result": (
        ("net", "result"),
        ("net", "profit"),
        ("net", "loss"),
        ("net", "income"),
        ("net", "earnings"),
        ("wynik", "netto"),
        ("wynik", "finansowy", "netto"),
        ("zysk", "netto"),
        ("strata", "netto"),
    ),
}
_METRICS = {
    metric: {word for phrase in phrases for word in phrase}
    for metric, phrases in _METRIC_PHRASES.items()
}
_CURRENCY = {
    "PLN": {"pln", "zł", "złoty", "złotych", "polish zloty"},
    "EUR": {"eur", "€", "euro"},
    "USD": {"usd", "$", "dollar", "dollars"},
    "GBP": {"gbp", "£", "pound", "pounds"},
}
_UNIT_WORDS = {
    "units": {"units", "unit", "jednostek"},
    "thousands": {"thousand", "thousands", "tys", "tysięcy"},
    "millions": {"million", "millions", "mln", "milionów"},
    "billions": {"billion", "billions", "mld", "miliardów"},
}


def _norm(value: str) -> str:
    """NFC normalize, then collapse every Unicode whitespace run to one space."""
    return _SPACE.sub(" ", unicodedata.normalize("NFC", value)).strip()


def _tokens(value: str) -> set[str]:
    return {token.casefold() for token in _WORD.findall(_norm(value))}


def _exact_excerpt(material: RetrievedSource, excerpt: str) -> bool:
    return bool(_norm(excerpt)) and _norm(excerpt) in _norm(material.content)


def _sentences(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"(?<=[!?])\s+|(?<=\.)\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9])|\n+|;", _norm(text))
        if part.strip()
    ]


def _company_name_tokens(run: CompanyResearchRun) -> list[str]:
    return [
        token.casefold() for token in _WORD.findall(_norm(str(run.identity.legal_name.value or "")))
    ]


_SOURCE_SENTENCE_BREAK = re.compile(r"(?<=[!?])\s+|(?<=\.)\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ0-9])|;")


def _bounded_source_contexts(content: str, excerpt: str) -> list[str]:
    """Return retained contiguous spans: two sentences before each exact quote occurrence."""
    normalized = _norm(content)
    quote = _norm(excerpt)
    if not quote:
        return []
    sentence_starts = [0]
    sentence_starts.extend(match.end() for match in _SOURCE_SENTENCE_BREAK.finditer(normalized))
    contexts: list[str] = []
    offset = 0
    while (offset := normalized.find(quote, offset)) >= 0:
        sentence_index = max(
            index for index, start in enumerate(sentence_starts) if start <= offset
        )
        start = sentence_starts[max(0, sentence_index - 2)]
        contexts.append(normalized[start : offset + len(quote)])
        offset += 1
    return contexts


_LEGAL_FORM_SUFFIXES = (
    ("spółka", "z", "ograniczoną", "odpowiedzialnością"),
    ("spółka", "komandytowo", "akcyjna"),
    ("spółka", "komandytowa"),
    ("spółka", "partnerska"),
    ("spółka", "akcyjna"),
    ("spółka", "jawna"),
    ("sp", "z", "o", "o"),
    ("sp", "k", "a"),
    ("sp", "k"),
    ("sp", "j"),
    ("sp", "p"),
    ("s", "a"),
    ("sa",),
)
_EMPLOYEE_SCOPE_BLOCKERS = {"group", "groups", "grupa", "segment", "segments", "consolidated"}
_EMPLOYEE_RELATION_BLOCKERS = {
    "customer",
    "customers",
    "client",
    "clients",
    "supplier",
    "suppliers",
    "vendor",
    "vendors",
}
_SENTENCE_INITIAL_NON_NAMES = {
    "a",
    "an",
    "as",
    "at",
    "for",
    "from",
    "in",
    "on",
    "the",
    "this",
}


def _legal_name_core_tokens(run: CompanyResearchRun) -> list[str]:
    tokens = _company_name_tokens(run)
    for suffix in _LEGAL_FORM_SUFFIXES:
        if len(tokens) > len(suffix) and tokens[-len(suffix) :] == list(suffix):
            return tokens[: -len(suffix)]
    return tokens


def _has_company_antecedent(context: str, run: CompanyResearchRun) -> bool:
    sentences = _sentences(context)
    name = _company_name_tokens(run)
    if not name or len(sentences) < 2:
        return False
    for index in range(len(sentences) - 2, -1, -1):
        words = _WORD.findall(sentences[index])
        tokens = [word.casefold() for word in words]
        subject = tokens[1:] if tokens[:1] == ["the"] else tokens
        if subject[: len(name)] != name:
            continue
        if any(word[:1].isupper() and word.casefold() not in set(name) for word in words):
            return False
        for sentence in sentences[index + 1 :]:
            following = [word.casefold() for word in _WORD.findall(sentence)]
            if following[:1] not in (["it"], ["its"]) and following[:2] not in (
                ["the", "company"],
                ["this", "company"],
            ):
                return False
        return True
    return False


def _issuer_nip_matches(text: str, identity_nip: str) -> bool:
    for sentence in _sentences(text):
        match = re.match(
            r"(?:the\s+)?issuer\s+NIP\s*[:#]?\s*"
            r"(\d{10}|\d{3}[- ]\d{3}[- ]\d{2}[- ]\d{2})\b",
            sentence,
            re.I,
        )
        if match is not None and re.sub(r"\D", "", match.group(1)) == identity_nip:
            return True
    return False


def _employee_entity_attached(context: str, run: CompanyResearchRun) -> bool:
    sentences = _sentences(context)
    if not sentences:
        return False
    claim = sentences[-1]
    claim_tokens = [token.casefold() for token in _WORD.findall(claim)]
    if (
        _tokens(claim) & (_EMPLOYEE_SCOPE_BLOCKERS | _EMPLOYEE_RELATION_BLOCKERS)
        or _conflicting_nip(context, run.identity.nip)
        or _nearby_negation(claim, _EMPLOYEE_WORDS)
    ):
        return False
    if _entity_attached(claim, _EMPLOYEE_WORDS, run):
        return True
    first = claim_tokens[0] if claim_tokens else ""
    if (
        first in {"the", "company", "it", "its", "this", "these"}
        and _has_company_antecedent(context, run)
        and _entity_attached(context, _EMPLOYEE_WORDS, run)
    ):
        return True

    core = _legal_name_core_tokens(run)
    full_core_match = _contains_sequence(claim_tokens, core)
    suffix_match = len(core) >= 2 and any(
        _contains_sequence(claim_tokens, core[-size:]) for size in range(2, len(core))
    )
    if not core or not (full_core_match or suffix_match):
        return False
    local_sentences = sentences[-3:]
    local_context = " ".join(local_sentences)
    if not _issuer_nip_matches(local_context, run.identity.nip):
        return False
    foreign_names = {
        word.casefold()
        for local_sentence in local_sentences
        for index, word in enumerate(_WORD.findall(local_sentence))
        if word[:1].isupper()
        and word.casefold() not in core
        and word.casefold() != "nip"
        and not (index == 0 and word.casefold() in _SENTENCE_INITIAL_NON_NAMES)
        and word.casefold() != "issuer"
    }
    return not foreign_names


def _conflicting_nip(text: str, identity_nip: str) -> bool:
    values = re.findall(
        r"\bNIP\s*[:#]?\s*(\d{10}|\d{3}[- ]\d{3}[- ]\d{2}[- ]\d{2})\b",
        text,
        re.I,
    )
    return any(re.sub(r"\D", "", value) != identity_nip for value in values)


def _entity_attached(text: str, anchors: set[str], run: CompanyResearchRun) -> bool:
    if _conflicting_nip(text, run.identity.nip):
        return False
    name_tokens = set(_company_name_tokens(run))
    if not name_tokens or _tokens(text) & _OTHER_ENTITY_MARKERS:
        return False
    sentences = _sentences(text)
    token_lists = [
        [token.casefold() for token in _WORD.findall(sentence)] for sentence in sentences
    ]
    for tokens in token_lists:
        if name_tokens.issubset(set(tokens)):
            entities = [index for index, token in enumerate(tokens) if token in name_tokens]
            claims = [index for index, token in enumerate(tokens) if token in anchors]
            if claims and min(abs(entity - claim) for entity in entities for claim in claims) <= 8:
                return True
    if len(sentences) < 2 or len(sentences) > 3:
        return False
    for entity_index, tokens in enumerate(token_lists):
        if not name_tokens.issubset(set(tokens)):
            continue
        entity_positions = [
            index + sum(len(item) for item in token_lists[:entity_index])
            for index, token in enumerate(tokens)
            if token in name_tokens
        ]
        for claim_index, claim_tokens in enumerate(token_lists):
            if abs(claim_index - entity_index) > 2 or not any(
                token in anchors for token in claim_tokens
            ):
                continue
            first = claim_tokens[0] if claim_tokens else ""
            if (
                first
                not in anchors
                | {
                    "the",
                    "company",
                    "it",
                    "its",
                    "this",
                    "these",
                    "standalone",
                    "individual",
                    "jednostkowo",
                }
                and not first.isdigit()
            ):
                continue
            words = _WORD.findall(sentences[claim_index])
            foreign_names = {
                word.casefold()
                for word in words[1:]
                if word[:1].isupper() and not word.isupper() and word.casefold() not in name_tokens
            }
            if foreign_names:
                continue
            claim_offset = sum(len(item) for item in token_lists[:claim_index])
            claim_positions = [
                index + claim_offset for index, token in enumerate(claim_tokens) if token in anchors
            ]
            if (
                entity_positions
                and claim_positions
                and min(
                    abs(entity - claim) for entity in entity_positions for claim in claim_positions
                )
                <= 24
            ):
                return True
    return False


def _source_entity_attached(text: str, anchors: set[str], run: CompanyResearchRun) -> bool:
    if _tokens(text) & {"group"}:
        return False
    sentences = _sentences(text)
    if not sentences:
        return False
    if _entity_attached(sentences[-1], anchors, run):
        return True
    return _has_company_antecedent(text, run) and _entity_attached(text, anchors, run)


def _nearby_negation(text: str, anchors: set[str]) -> bool:
    tokens = [token.casefold() for token in _WORD.findall(_norm(text))]
    negatives = {"not", "never", "no", "without", "neither", "nie", "nigdy", "żaden"}
    return any(
        token in anchors
        and any(previous in negatives for previous in tokens[max(0, index - 4) : index])
        for index, token in enumerate(tokens)
    )


def _context_windows(text: str) -> list[str]:
    sentences = _sentences(text)
    windows = list(sentences)
    windows.extend(f"{left} {right}" for left, right in zip(sentences, sentences[1:], strict=False))
    windows.extend(
        f"{first} {middle} {last}"
        for first, middle, last in zip(sentences, sentences[1:], sentences[2:], strict=False)
    )
    return windows


def _candidate_terms(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _contains_sequence(tokens: list[str], phrase: list[str]) -> bool:
    return bool(phrase) and any(
        tokens[start : start + len(phrase)] == phrase
        for start in range(len(tokens) - len(phrase) + 1)
    )


def _phrase_outside_company_name(phrase: list[str], text: str, run: CompanyResearchRun) -> bool:
    tokens = [token.casefold() for token in _WORD.findall(_norm(text))]
    name = _company_name_tokens(run)
    excluded: set[int] = set()
    for start in range(max(0, len(tokens) - len(name) + 1)):
        if tokens[start : start + len(name)] == name:
            excluded.update(range(start, start + len(name)))
    return any(
        tokens[start : start + len(phrase)] == phrase
        and not any(index in excluded for index in range(start, start + len(phrase)))
        for start in range(len(tokens) - len(phrase) + 1)
    )


def _ordered_phrase_supported(
    phrase: str,
    excerpt: str,
    run: CompanyResearchRun,
    source_content: str | None = None,
) -> bool:
    phrase_tokens = [token.casefold() for token in _WORD.findall(_norm(phrase))]
    if not phrase_tokens:
        return False
    company_tokens = set(_company_name_tokens(run))
    claim_tokens = [token for token in phrase_tokens if token not in company_tokens]
    anchors = set(claim_tokens or phrase_tokens)
    negative_markers = {"not", "never", "no", "without", "neither", "nie", "nigdy"}
    phrase_is_negative = bool(set(phrase_tokens) & negative_markers)
    for sentence in _sentences(excerpt):
        sentence_tokens = [token.casefold() for token in _WORD.findall(sentence)]
        exact_claim = (
            _contains_sequence(sentence_tokens, claim_tokens)
            if claim_tokens
            else _phrase_outside_company_name(phrase_tokens, sentence, run)
        )
        contexts = (
            _bounded_source_contexts(source_content, sentence)
            if source_content is not None
            else [sentence]
        )
        attachment = _source_entity_attached if source_content is not None else _entity_attached
        if (
            exact_claim
            and any(attachment(context, anchors, run) for context in contexts)
            and (phrase_is_negative or not _nearby_negation(sentence, anchors))
        ):
            return True
    return False


def _lexical_support(
    fact: Fact[Any], excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    phrases = _candidate_terms(fact.value)
    return bool(phrases) and all(
        _ordered_phrase_supported(phrase, excerpt, run, material.content) for phrase in phrases
    )


_DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}|\d{2}/\d{2}/\d{4})\b")
_AMOUNT_PATTERN = re.compile(r"(?<![\w])[+-]?\d+(?:[ ,.]\d{3})*(?:[.,]\d+)?(?![\w])")


def _phrase_spans(tokens: list[str], phrases: set[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for phrase in phrases:
        phrase_tokens = [token.casefold() for token in _WORD.findall(phrase)]
        if not phrase_tokens:
            continue
        spans.extend(
            (start, start + len(phrase_tokens))
            for start in range(len(tokens) - len(phrase_tokens) + 1)
            if tokens[start : start + len(phrase_tokens)] == phrase_tokens
        )
    return spans


def _metric_spans(tokens: list[str], metric: str) -> list[tuple[int, int]]:
    return [
        span
        for phrase in _METRIC_PHRASES[metric]
        for span in _phrase_spans(tokens, {" ".join(phrase)})
    ]


def _currency_spans(tokens: list[str], currency: str) -> list[tuple[int, int]]:
    return _phrase_spans(tokens, _CURRENCY.get(currency, {currency.casefold()}))


def _unit_spans(tokens: list[str], unit: str) -> list[tuple[int, int]]:
    return _phrase_spans(tokens, _UNIT_WORDS[unit])


def _numeric_values(raw: str) -> set[Decimal]:
    compact = raw.replace(" ", "").replace("'", "")
    values: set[Decimal] = set()
    try:
        if "," in compact and "." in compact:
            decimal_sep = "," if compact.rfind(",") > compact.rfind(".") else "."
            grouping_sep = "." if decimal_sep == "," else ","
            values.add(Decimal(compact.replace(grouping_sep, "").replace(decimal_sep, ".")))
        elif "," in compact:
            values.add(Decimal(compact.replace(",", ".")))
            if len(compact.rsplit(",", 1)[1]) == 3:
                values.add(Decimal(compact.replace(",", "")))
        elif "." in compact:
            values.add(Decimal(compact))
            if len(compact.rsplit(".", 1)[1]) == 3:
                values.add(Decimal(compact.replace(".", "")))
        else:
            values.add(Decimal(compact))
    except Exception:
        return set()
    return values


def _same_precision_amount(raw: str, value: Decimal) -> bool:
    return any(
        number == value and number.as_tuple().exponent == value.as_tuple().exponent
        for number in _numeric_values(raw)
    )


def _observed_metric_amount(text: str, fact: FinancialFact) -> str | None:
    without_dates = _DATE_PATTERN.sub(" ", text)
    tokens = [token.casefold() for token in _WORD.findall(without_dates)]
    metrics = _metric_spans(tokens, fact.metric)
    currencies = _currency_spans(tokens, fact.currency or "")
    units = _unit_spans(tokens, fact.unit or "")
    if not metrics or not currencies or not units:
        return None

    amounts: list[tuple[int, str]] = []
    for match in _AMOUNT_PATTERN.finditer(without_dates):
        token_index = len(_WORD.findall(without_dates[: match.start()]))
        near_currency = any(
            abs(token_index - min(max(token_index, start), end - 1)) <= 12
            for start, end in currencies
        )
        near_unit = any(
            abs(token_index - min(max(token_index, start), end - 1)) <= 12 for start, end in units
        )
        if near_currency and near_unit:
            amounts.append((token_index, match.group()))
    if not amounts:
        return None

    nearest_amounts: list[str] = []
    for start, end in metrics:
        distances = [
            (start - position, 1) if position < start else (position - (end - 1), 0)
            for position, _ in amounts
        ]
        nearest = min(distances)
        if nearest[0] <= 14:
            nearest_amounts.extend(
                amounts[index][1] for index, distance in enumerate(distances) if distance == nearest
            )
    if not nearest_amounts:
        return None
    parsed = [number for amount in nearest_amounts for number in _numeric_values(amount)]
    if not parsed or len({(number, number.as_tuple().exponent) for number in parsed}) != 1:
        return None
    return nearest_amounts[0]


def _date_present(text: str, value: date) -> bool:
    normalized = _norm(text)
    return (
        value.isoformat() in normalized
        or value.strftime("%d.%m.%Y") in normalized
        or value.strftime("%d/%m/%Y") in normalized
    )


def _financial_observation(
    fact: FinancialFact, excerpt: str, run: CompanyResearchRun
) -> str | None:
    if fact.period is None or fact.currency is None or fact.unit is None:
        return None
    metric_words = _METRICS[fact.metric]
    for window in _context_windows(excerpt):
        tokens = _tokens(window)
        if not _date_present(window, fact.period.start) or not _date_present(
            window, fact.period.end
        ):
            continue
        if fact.scope == "group":
            if not fact.group_name or not _tokens(fact.group_name).issubset(tokens):
                continue
            if not (tokens & {"group", "consolidated", "grupa", "skonsolidowany"}):
                continue
        elif fact.scope == "legal_entity":
            if not (
                tokens
                & {
                    "standalone",
                    "non-consolidated",
                    "individual",
                    "jednostkowy",
                    "jednostkowe",
                    "jednostkowo",
                }
            ):
                continue
        else:
            continue
        if not _entity_attached(
            window,
            metric_words
            | {
                "standalone",
                "non-consolidated",
                "individual",
                "jednostkowy",
                "jednostkowe",
                "jednostkowo",
            },
            run,
        ):
            continue
        observed = _observed_metric_amount(window, fact)
        if observed is not None:
            return observed
    return None


def _employee_supported(
    fact: EmployeeFact, excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    value = fact.value
    if isinstance(value, ExactEmployees):
        expected = (value.count,)
        for sentence in _sentences(excerpt):
            contexts = _bounded_source_contexts(material.content, sentence)
            if (
                _employee_observation(sentence) == expected
                and not _employee_qualifier(sentence)
                and _tokens(sentence) & _EMPLOYEE_WORDS
                and any(_employee_entity_attached(context, run) for context in contexts)
            ):
                return True
    if isinstance(value, EmployeeRange):
        expected_bounds = (value.minimum, value.maximum)
        for sentence in _sentences(excerpt):
            contexts = _bounded_source_contexts(material.content, sentence)
            if (
                _employee_range_observation(sentence) == expected_bounds
                and _tokens(sentence) & _EMPLOYEE_WORDS
                and any(_employee_entity_attached(context, run) for context in contexts)
            ):
                return True
    return False


def _employee_as_of_supported(
    fact: EmployeeFact,
    run: CompanyResearchRun,
    by_id: dict[str, list[RetrievedSource]],
) -> bool:
    if fact.as_of is None:
        return True
    for ref in fact.evidence:
        for material in by_id.get(ref.source_id, []):
            if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                continue
            for sentence in _sentences(ref.excerpt):
                contexts = _bounded_source_contexts(material.content, sentence)
                if (
                    _employee_range_observation(sentence) is not None
                    and _tokens(sentence) & _EMPLOYEE_WORDS
                    and any(_employee_entity_attached(context, run) for context in contexts)
                    and _date_present(sentence, fact.as_of)
                    and not _publication_date_present(sentence, fact.as_of)
                ):
                    return True
    return False


def _publication_date_present(text: str, value: date) -> bool:
    normalized = _norm(text)
    date_spellings = (
        value.isoformat(),
        value.strftime("%d.%m.%Y"),
        value.strftime("%d/%m/%Y"),
    )
    labels = (
        r"(?:published(?:\s+on)?|publication(?:\s+date)?|date\s+published|"
        r"opublikowano|publikacja|data\s+publikacji)"
    )
    for spelling in date_spellings:
        for match in re.finditer(re.escape(spelling), normalized, re.I):
            before = normalized[max(0, match.start() - 48) : match.start()].casefold()
            after = normalized[match.end() : match.end() + 32].casefold()
            if re.search(labels + r"[\s:,-]{0,24}$", before) or re.match(
                r"[\s:,-]{0,16}" + labels, after
            ):
                return True
    return False


def _event_contexts(event: CompanyEvent, excerpt: str, run: CompanyResearchRun) -> list[str]:
    value = event.value
    if value is None:
        return []
    phrases = [phrase for phrase in (value.title, value.summary) if phrase]
    return [
        window
        for window in _context_windows(excerpt)
        if all(_ordered_phrase_supported(phrase, window, run) for phrase in phrases)
    ]


def _event_publication_supported(
    event: CompanyEvent, excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    value = event.value
    contexts = _event_contexts(event, excerpt, run)
    if value is None or not contexts:
        return False
    if material.source.published_on is not None:
        return material.source.published_on == value.published_on
    return any(_publication_date_present(window, value.published_on) for window in contexts)


def _event_occurrence_supported(event: CompanyEvent, excerpt: str, run: CompanyResearchRun) -> bool:
    value = event.value
    if value is None or value.occurred_on is None:
        return value is not None
    phrases = [phrase for phrase in (value.title, value.summary) if phrase]
    return any(
        _date_present(sentence, value.occurred_on)
        and not _publication_date_present(sentence, value.occurred_on)
        and any(_ordered_phrase_supported(phrase, sentence, run) for phrase in phrases)
        for sentence in _sentences(excerpt)
    )


def _event_supported(
    event: CompanyEvent, excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    return _event_publication_supported(event, excerpt, run, material)


def _employee_observation(text: str) -> tuple[int, ...]:
    """Extract only quantities directly attached to employee terminology."""
    pattern = re.compile(
        r"(?:(\d[\d ,.]*)(?:\s*(?:to|[-–—])\s*(\d[\d ,.]*))?\s+"
        r"(?:employees?|staff|personnel|people|persons?|pracowników|pracownicy|zatrudnionych|zatrudnia))",
        re.I,
    )
    found: list[int] = []
    for match in pattern.finditer(_norm(text)):
        for raw in match.groups():
            if raw:
                digits = re.sub(r"\D", "", raw)
                if digits:
                    found.append(int(digits))
    return tuple(found)


def _employee_range_observation(text: str) -> tuple[int | None, int | None] | None:
    normalized = _norm(text)
    pattern = re.compile(
        r"(?:(\d[\d ,.]*)(?:\s*(?:to|[-–—])\s*(\d[\d ,.]*))?\s+"
        r"(?:employees?|staff|personnel|people|persons?|pracowników|pracownicy|zatrudnionych|zatrudnia))",
        re.I,
    )
    lower_prefixes = {
        ("at", "least"): False,
        ("no", "fewer", "than"): False,
        ("minimum",): False,
        ("minimum", "of"): False,
        ("over",): True,
        ("above",): True,
        ("more", "than"): True,
        ("greater", "than"): True,
        ("co", "najmniej"): False,
        ("ponad",): True,
        ("powyżej",): True,
    }
    upper_prefixes = {
        ("at", "most"): False,
        ("no", "more", "than"): False,
        ("up", "to"): False,
        ("maximum",): False,
        ("maximum", "of"): False,
        ("less", "than"): True,
        ("fewer", "than"): True,
        ("below",): True,
        ("nie", "więcej", "niż"): False,
    }
    approximate_prefixes = (
        ("approximately",),
        ("about",),
        ("around",),
        ("roughly",),
        ("nearly",),
        ("circa",),
        ("około",),
    )
    found: tuple[int | None, int | None] | None = None
    for match in pattern.finditer(normalized):
        first = int(re.sub(r"\D", "", match.group(1)))
        second = int(re.sub(r"\D", "", match.group(2))) if match.group(2) else None
        if second is not None:
            found = (first, second)
            continue
        preceding = tuple(
            token.casefold() for token in _WORD.findall(normalized[: match.start(1)])[-4:]
        )
        following = tuple(
            token.casefold() for token in _WORD.findall(normalized[match.end() :])[:3]
        )
        if any(preceding[-len(item) :] == item for item in approximate_prefixes):
            return None
        for prefix, strict in lower_prefixes.items():
            if preceding[-len(prefix) :] == prefix:
                found = (first + int(strict), None)
                break
        else:
            for prefix, strict in upper_prefixes.items():
                if preceding[-len(prefix) :] == prefix:
                    found = (None, first - int(strict))
                    break
            else:
                if following[:2] in {("or", "more"), ("or", "over")} or following[:1] == ("plus",):
                    found = (first, None)
                elif following[:2] in {("or", "less"), ("or", "fewer")}:
                    found = (None, first)
                elif following[:2] in {("and", "above"), ("and", "over")}:
                    found = (first, None)
                elif following[:1] == ("minimum",):
                    found = (first, None)
                elif following[:1] == ("maximum",):
                    found = (None, first)
                elif _employee_qualifier(normalized):
                    return None
                else:
                    found = (first, first)
    return found


def _employee_qualifier(text: str) -> bool:
    normalized = _norm(text)
    quantity = re.compile(
        r"(?:(\d[\d ,.]*)(?:\s*(?:to|[-–—])\s*(\d[\d ,.]*))?\s+"
        r"(?:employees?|staff|personnel|people|persons?|pracowników|pracownicy|zatrudnionych|zatrudnia))",
        re.I,
    )
    qualifiers = (
        ("over",),
        ("above",),
        ("more", "than"),
        ("greater", "than"),
        ("less", "than"),
        ("fewer", "than"),
        ("at", "least"),
        ("at", "most"),
        ("up", "to"),
        ("no", "more", "than"),
        ("no", "fewer", "than"),
        ("below",),
        ("minimum",),
        ("maximum",),
        ("approximately",),
        ("about",),
        ("around",),
        ("roughly",),
        ("nearly",),
        ("circa",),
        ("ponad",),
        ("powyżej",),
        ("około",),
        ("co", "najmniej"),
        ("więcej", "niż"),
        ("nie", "więcej", "niż"),
    )
    suffix_qualifiers = (
        ("or", "more"),
        ("or", "over"),
        ("or", "less"),
        ("or", "fewer"),
        ("and", "less"),
        ("and", "fewer"),
        ("plus",),
        ("and", "above"),
        ("and", "over"),
        ("minimum",),
        ("at", "least"),
    )
    for match in quantity.finditer(normalized):
        preceding = [token.casefold() for token in _WORD.findall(normalized[: match.start(1)])]
        following = [token.casefold() for token in _WORD.findall(normalized[match.end() :])[:3]]
        if any(preceding[-len(item) :] == list(item) for item in qualifiers):
            return True
        if any(following[: len(item)] == list(item) for item in suffix_qualifiers):
            return True
    return False


def _downgrade[FactT: Fact[Any]](
    fact: FactT,
    reason: str,
    *,
    clear_value: bool = False,
    evidence: list[EvidenceRef] | None = None,
) -> FactT:
    updates: dict[str, Any] = {
        "state": "uncertain",
        "reason": reason,
        "evidence": evidence if evidence is not None else fact.evidence,
    }
    if clear_value:
        updates["value"] = None
    return fact.model_copy(update=updates)


def _append_rejection_reason(reason: str | None, rejection: str) -> str:
    return f"{reason}; {rejection}" if reason else rejection


def build_profile(run: CompanyResearchRun) -> CompanyProfile:
    """Build a final profile only from exact, eligible, context-bearing retained citations."""
    by_id: dict[str, list[RetrievedSource]] = defaultdict(list)
    for material in run.sources:
        by_id[material.source.source_id].append(material)
    for source_id, materials in by_id.items():
        hosts = {urlsplit(str(material.source.url)).hostname for material in materials}
        if len(hosts) > 1:
            raise ValueError(f"source ID {source_id} has conflicting host metadata")
    known_ids = set(by_id)

    identity_facts = (
        run.identity.legal_name,
        run.identity.krs,
        run.identity.regon,
        run.identity.registered_city,
        run.identity.registered_address,
        run.identity.website,
    )
    registry_ids = {item.source.source_id for item in run.sources if item.kind == "registry"}
    for fact in identity_facts:
        for ref in fact.evidence:
            if ref.source_id not in known_ids:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            if ref.source_id not in registry_ids:
                raise ValueError("identity evidence must originate from a trusted registry source")
            if any(_conflicting_nip(ref.excerpt, run.identity.nip) for ref in fact.evidence):
                raise ValueError("identity evidence contains a conflicting explicit NIP")
            if not any(
                _exact_excerpt(item, ref.excerpt)
                for item in by_id[ref.source_id]
                if item.kind == "registry"
            ):
                raise ValueError("identity evidence excerpt is not an exact registry match")

    def gate[FactT: Fact[Any]](fact: FactT, kind: str) -> FactT:
        if fact.state != "supported":
            return fact
        refs = fact.evidence
        eligible: list[tuple[EvidenceRef, RetrievedSource]] = []
        exact_refs: list[EvidenceRef] = []
        for ref in refs:
            materials_for_ref = by_id.get(ref.source_id)
            if not materials_for_ref:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            matches = [
                material
                for material in materials_for_ref
                if material.kind == "full_page" and _exact_excerpt(material, ref.excerpt)
            ]
            if matches:
                exact_refs.append(ref)
                eligible.extend((ref, material) for material in matches)
        if kind == "employees" and isinstance(fact, EmployeeFact):
            valid_pairs = [
                (ref, material)
                for ref, material in eligible
                if _employee_supported(fact, ref.excerpt, run, material)
            ]
        else:
            valid_pairs = [
                (ref, material)
                for ref, material in eligible
                if _lexical_support(fact, ref.excerpt, run, material)
            ]
        if kind == "employees" and isinstance(fact, EmployeeFact) and valid_pairs:
            expected: tuple[int | None, int | None]
            candidate = fact.value
            if isinstance(candidate, ExactEmployees):
                expected = (candidate.count, candidate.count)
            else:
                assert isinstance(candidate, EmployeeRange)
                expected = (candidate.minimum, candidate.maximum)
            observations = {
                observed
                for ref, material in eligible
                if (observed := _employee_range_observation(ref.excerpt)) is not None
            }
            alternative_refs: list[EvidenceRef] = []
            for material in run.sources:
                if material.kind != "full_page":
                    continue
                for sentence in _sentences(material.content):
                    observed = _employee_range_observation(sentence)
                    contexts = _bounded_source_contexts(material.content, sentence)
                    if (
                        observed is not None
                        and _tokens(sentence) & _EMPLOYEE_WORDS
                        and any(_employee_entity_attached(context, run) for context in contexts)
                    ):
                        observations.add(observed)
                        if observed != expected:
                            alternative_refs.append(
                                EvidenceRef(source_id=material.source.source_id, excerpt=sentence)
                            )
            if any(observed != expected for observed in observations):
                unique_refs = {
                    (ref.source_id, ref.excerpt): ref for ref in [*fact.evidence, *alternative_refs]
                }
                return _downgrade(
                    fact,
                    "Conflicting employee observations are retained without selecting one",
                    clear_value=True,
                    evidence=list(unique_refs.values()),
                )
        if any(_conflicting_nip(ref.excerpt, run.identity.nip) for ref in exact_refs):
            return _downgrade(
                fact,
                "Cited full-page text contains a conflicting explicit NIP for the resolved entity",
                clear_value=kind == "employees",
            )
        if valid_pairs:
            return fact
        reason = (
            "No exact full-page citation verifies the candidate value, entity, and required context"
        )
        if not exact_refs:
            reason = (
                "Evidence is absent, snippet-only, or not an exact "
                "NFC/whitespace-normalized excerpt from a retained full page"
            )
        return _downgrade(fact, reason, clear_value=kind == "employees")

    business = gate(run.draft.business_description, "text")
    products = gate(run.draft.products_services, "text")
    industries = gate(run.draft.industries, "text")
    markets = gate(run.draft.markets, "text")
    employees = gate(run.draft.employees, "employees")
    if employees.as_of is not None and not _employee_as_of_supported(employees, run, by_id):
        employees = employees.model_copy(
            update={
                "as_of": None,
                "reason": _append_rejection_reason(
                    employees.reason, "Unverified employee as-of date removed"
                ),
            }
        )

    financials: list[FinancialFact] = []
    for financial in run.draft.financials:
        if financial.state != "supported":
            financials.append(financial)
            continue
        verified_amount = False
        conflicting_amount = False
        nip_conflict = False
        for ref in financial.evidence:
            if not by_id.get(ref.source_id):
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            if any(
                material.kind == "full_page"
                and _exact_excerpt(material, ref.excerpt)
                and _conflicting_nip(ref.excerpt, run.identity.nip)
                for material in by_id[ref.source_id]
            ):
                nip_conflict = True
        for source_id, source_materials in by_id.items():
            for material in source_materials:
                if material.kind != "full_page":
                    continue
                cited = [
                    ref
                    for ref in financial.evidence
                    if ref.source_id == source_id and _exact_excerpt(material, ref.excerpt)
                ]
                if not cited:
                    continue
                observations = [
                    observed
                    for ref in cited
                    if (observed := _financial_observation(financial, ref.excerpt, run)) is not None
                ]
                normalized_content = _norm(material.content)
                ordered_quotes = sorted(
                    {ref.excerpt for ref in cited},
                    key=lambda excerpt: (
                        normalized_content.find(_norm(excerpt)),
                        len(_norm(excerpt)),
                        _norm(excerpt),
                    ),
                )
                if len(ordered_quotes) > 1:
                    combined = " ; ".join(ordered_quotes)
                    combined_observation = _financial_observation(financial, combined, run)
                    if combined_observation is not None:
                        observations.append(combined_observation)
                for observed in observations:
                    if financial.value is not None and _same_precision_amount(
                        observed, financial.value
                    ):
                        verified_amount = True
                    else:
                        conflicting_amount = True
        if nip_conflict:
            financials.append(
                _downgrade(
                    financial,
                    "Cited full-page text contains a conflicting explicit NIP "
                    "for the resolved entity",
                    clear_value=True,
                )
            )
        elif verified_amount and conflicting_amount:
            financials.append(
                _downgrade(
                    financial,
                    "Conflicting exact financial observations for the same metric, "
                    "interval, currency, unit, and scope remain unresolved",
                    clear_value=True,
                )
            )
        elif verified_amount:
            financials.append(financial)
        else:
            financials.append(
                _downgrade(
                    financial,
                    "Exact full-page evidence does not verify metric, amount, precision, "
                    "currency, unit, entity scope and explicit reporting interval",
                    clear_value=True,
                )
            )

    events: list[CompanyEvent] = []
    for event in run.draft.recent_developments:
        if event.value is None:
            events.append(event)
            continue
        publication_verified = False
        occurrence_verified = event.value.occurred_on is None
        nip_conflict = False
        for ref in event.evidence:
            materials_for_ref = by_id.get(ref.source_id)
            if not materials_for_ref:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            for material in materials_for_ref:
                if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                    continue
                if _conflicting_nip(ref.excerpt, run.identity.nip):
                    nip_conflict = True
                if _event_publication_supported(event, ref.excerpt, run, material):
                    publication_verified = True
                if _event_occurrence_supported(event, ref.excerpt, run):
                    occurrence_verified = True

        rejections: list[str] = []
        value = event.value
        if value.occurred_on is not None and not occurrence_verified:
            value = value.model_copy(update={"occurred_on": None})
            rejections.append("Unverified event occurrence date removed")
        clear_event = not publication_verified
        if clear_event:
            rejections.append(
                "Event publication date or content could not be verified; details cleared"
            )
        retained_value: EventDetails | None = None if clear_event else value
        if nip_conflict:
            rejections.append("Cited full-page text contains a conflicting explicit NIP")

        reason = event.reason
        for rejection in rejections:
            reason = _append_rejection_reason(reason, rejection)
        if event.state == "supported" and (clear_event or nip_conflict):
            event = _downgrade(
                event, reason or "Event evidence was rejected", clear_value=clear_event
            )
            if not clear_event and value is not None:
                event = event.model_copy(update={"value": value})
        elif rejections:
            event = event.model_copy(update={"value": retained_value, "reason": reason})
        events.append(event)

    # Preserve all retained IDs cited by immutable identity and draft candidates;
    # collapse to strongest kind.
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
    used_ids.update(
        material.source.source_id for material in run.sources if material.kind == "registry"
    )
    rank = {"search_snippet": 0, "full_page": 1, "registry": 2}
    sources: list[ProfileSource] = []
    for source_id in sorted(used_ids):
        materials_for_id = by_id.get(source_id)
        if not materials_for_id:
            raise ValueError(f"unknown evidence source ID: {source_id}")
        strongest = max(
            materials_for_id,
            key=lambda material: (
                rank[material.kind],
                material.source.retrieved_at,
                str(material.source.url),
            ),
        )
        sources.append(ProfileSource(**strongest.source.model_dump(), kind=strongest.kind))

    identity = run.identity.model_copy(deep=True)
    limitations = list(run.draft.limitations)
    # Ensure every downgraded candidate has an explicit visible gate reason.
    for field_name, gated in (
        ("business description", business),
        ("products/services", products),
        ("industries", industries),
        ("markets", markets),
        ("employees", employees),
    ):
        if (
            gated.state == "uncertain"
            and gated.reason
            and gated.reason not in limitations
            and getattr(
                run.draft,
                {
                    "business description": "business_description",
                    "products/services": "products_services",
                    "industries": "industries",
                    "markets": "markets",
                    "employees": "employees",
                }[field_name],
            ).state
            == "supported"
        ):
            limitations.append(f"{field_name}: {gated.reason}")
    for financial_old, financial_new in zip(run.draft.financials, financials, strict=True):
        if (
            financial_old.state == "supported"
            and financial_new.state == "uncertain"
            and financial_new.reason
        ):
            limitations.append(f"{financial_new.metric}: {financial_new.reason}")
    for event_old, event_new in zip(run.draft.recent_developments, events, strict=True):
        if event_old.state == "supported" and event_new.state == "uncertain" and event_new.reason:
            limitations.append(f"Recent development: {event_new.reason}")

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
