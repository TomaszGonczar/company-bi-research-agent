"""Deterministic evidence gate from research drafts to publishable profiles."""

from __future__ import annotations

import calendar
import re
import unicodedata
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any

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
    _validate_registry_identity,
    profile_has_gaps,
    validate_source_lineage,
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
_ASSERTION_CLAUSE_BREAK = re.compile(
    r";|\b(?:but|however|although|whereas)\b"
    r"|\band(?=\s+(?:does|do|did|has|have|is|are|was|were|will|plans|intends|aims|not|never|no|could|might|may))"
    r"|\bi(?=\s+nie\b)",
    re.I,
)
_ASSERTION_NEGATION = {
    "not",
    "never",
    "no",
    "without",
    "neither",
    "nie",
    "nigdy",
    "żaden",
    "discontinued",
    "ceased",
    "formerly",
    "previously",
    "replaced",
    "used",
}
_ASSERTION_MODALITY = {
    "will",
    "shall",
    "would",
    "could",
    "might",
    "may",
    "if",
    "whether",
    "unless",
    "plan",
    "plans",
    "planned",
    "intend",
    "intends",
    "intended",
    "aim",
    "aims",
    "aimed",
    "hope",
    "hopes",
    "expected",
    "expect",
    "expects",
    "proposed",
    "proposes",
    "scheduled",
    "planuje",
    "planowano",
    "zamierza",
    "zamierzają",
    "będzie",
    "będą",
}
_CURRENT_RELATIONS = {
    "provide",
    "provides",
    "sell",
    "sells",
    "offer",
    "offers",
    "manufacture",
    "manufactures",
    "produce",
    "produces",
    "supply",
    "supplies",
    "include",
    "includes",
    "serve",
    "serves",
    "operate",
    "operates",
    "design",
    "designs",
    "specialize",
    "specializes",
    "employ",
    "employs",
    "is",
    "are",
    "has",
    "have",
    "świadczy",
    "oferuje",
    "sprzedaje",
    "produkuje",
    "wytwarza",
    "prowadzi",
    "jest",
    "są",
    "zatrudnia",
}
_EVENT_RELATIONS = {
    "opens",
    "opened",
    "launches",
    "launched",
    "acquired",
    "signed",
    "appointed",
    "transferred",
    "built",
    "introduced",
    "founded",
    "expanded",
    "uruchomiła",
}
_PASSIVE_RELATIONS = {"provided", "offered", "sold"}
_ASSERTION_PREDICATES = (
    _CURRENT_RELATIONS
    | _EVENT_RELATIONS
    | _PASSIVE_RELATIONS
    | {
        "manufactured",
        "produced",
        "supplied",
        "included",
        "served",
        "operated",
        "employed",
        "was",
        "were",
        "had",
    }
)
_FINANCIAL_NONACTUAL = {
    "will",
    "shall",
    "would",
    "could",
    "might",
    "may",
    "target",
    "targets",
    "targeted",
    "forecast",
    "forecasts",
    "forecasted",
    "project",
    "projects",
    "projected",
    "planned",
    "plan",
    "plans",
    "guidance",
    "outlook",
    "projection",
    "budget",
    "budgets",
    "aim",
    "aims",
    "expected",
    "expects",
    "estimate",
    "estimated",
    "considering",
    "potential",
    "if",
    "whether",
    "unless",
    "not",
    "never",
    "no",
    "without",
    "nie",
    "nigdy",
    "prognoza",
    "prognozowane",
    "planowany",
    "docelowy",
}
_FINANCIAL_REALIZED = {
    "reported",
    "reports",
    "recorded",
    "records",
    "generated",
    "generates",
    "earned",
    "earns",
    "posted",
    "posts",
    "incurred",
    "incurs",
    "recognized",
    "recognised",
    "realized",
    "realised",
    "actual",
    "is",
    "are",
    "was",
    "were",
    "wykazano",
    "wykazała",
    "osiągnął",
    "osiągnęła",
    "uzyskał",
    "uzyskała",
    "odnotował",
    "odnotowała",
    "wyniósł",
    "wyniosła",
}
_FINANCIAL_REPORT_VERBS = _FINANCIAL_REALIZED - {"actual", "is", "are", "was", "were"}
_FINANCIAL_SUBJECT_BRIDGES = {
    "a",
    "an",
    "the",
    "currently",
    "group",
    "holding",
    "holdings",
    "company",
    "issuer",
    "it",
    "its",
    "standalone",
    "non",
    "consolidated",
    "individual",
    "jednostkowy",
    "jednostkowe",
    "jednostkowo",
}
_FINANCIAL_METRIC_BRIDGES = {
    "a",
    "an",
    "the",
    "standalone",
    "non",
    "consolidated",
    "individual",
    "net",
    "annual",
    "total",
    "gross",
    "operating",
    "jednostkowy",
    "jednostkowe",
    "jednostkowo",
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


def _bounded_source_contexts(
    content: str, excerpt: str, *, prefer_source_lines: bool = False
) -> list[str]:
    """Return canonical contexts, optionally bounded by retained source lines."""
    quote = _norm(excerpt)
    if not quote:
        return []

    def enclosing_sentences(text: str) -> list[str]:
        sentence_starts = [0]
        sentence_starts.extend(match.end() for match in _SOURCE_SENTENCE_BREAK.finditer(text))
        contexts: list[str] = []
        offset = 0
        while (offset := text.find(quote, offset)) >= 0:
            sentence_index = max(
                index for index, start in enumerate(sentence_starts) if start <= offset
            )
            start = sentence_starts[max(0, sentence_index - 2)]
            quote_end = offset + len(quote)
            end = next(
                (boundary for boundary in sentence_starts if boundary > quote_end), len(text)
            )
            if end < len(text) and text[end - 1 : end] == ";":
                end = next((boundary for boundary in sentence_starts if boundary > end), len(text))
            contexts.append(text[start:end])
            offset += 1
        return contexts

    if not prefer_source_lines:
        return enclosing_sentences(_norm(content))
    source_lines = unicodedata.normalize("NFC", content).splitlines()
    line_contexts = [
        context
        for index, line in enumerate(source_lines)
        if (normalized_line := _norm(line)) and quote in normalized_line
        for window in [_norm(" ".join(source_lines[max(0, index - 2) : index + 3]))]
        for context in enclosing_sentences(window)
    ]
    if line_contexts:
        return line_contexts

    paragraphs: list[str] = []
    lines: list[str] = []
    for line in unicodedata.normalize("NFC", content).splitlines():
        if line.strip():
            lines.append(line)
        elif lines:
            paragraphs.append(_norm(" ".join(lines)))
            lines.clear()
    if lines:
        paragraphs.append(_norm(" ".join(lines)))
    paragraph_contexts = [
        context
        for paragraph in paragraphs
        if quote in paragraph
        for context in enclosing_sentences(paragraph)
    ]
    return paragraph_contexts


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


def _legal_name_occurrences(tokens: list[str], run: CompanyResearchRun) -> list[tuple[int, int]]:
    """Find the full legal-name core with its registered form or a same-form abbreviation."""
    name = _company_name_tokens(run)
    core = _legal_name_core_tokens(run)
    if not core:
        return []
    registered_suffix = tuple(name[len(core) :])
    equivalent_forms = {
        ("spółka", "z", "ograniczoną", "odpowiedzialnością"): (
            ("spółka", "z", "ograniczoną", "odpowiedzialnością"),
            ("sp", "z", "o", "o"),
        ),
        ("spółka", "komandytowo", "akcyjna"): (
            ("spółka", "komandytowo", "akcyjna"),
            ("sp", "k", "a"),
        ),
        ("spółka", "komandytowa"): (("spółka", "komandytowa"), ("sp", "k")),
        ("spółka", "partnerska"): (("spółka", "partnerska"), ("sp", "p")),
        ("spółka", "jawna"): (("spółka", "jawna"), ("sp", "j")),
        ("spółka", "akcyjna"): (("spółka", "akcyjna"), ("s", "a"), ("sa",)),
        ("sp", "z", "o", "o"): (
            ("spółka", "z", "ograniczoną", "odpowiedzialnością"),
            ("sp", "z", "o", "o"),
        ),
        ("sp", "k", "a"): (("spółka", "komandytowo", "akcyjna"), ("sp", "k", "a")),
        ("sp", "k"): (("spółka", "komandytowa"), ("sp", "k")),
        ("sp", "p"): (("spółka", "partnerska"), ("sp", "p")),
        ("sp", "j"): (("spółka", "jawna"), ("sp", "j")),
        ("s", "a"): (("spółka", "akcyjna"), ("s", "a"), ("sa",)),
        ("sa",): (("spółka", "akcyjna"), ("s", "a"), ("sa",)),
    }
    suffixes = set(equivalent_forms.get(registered_suffix, (registered_suffix,)))
    recognized_suffixes = sorted(_LEGAL_FORM_SUFFIXES, key=len, reverse=True)
    occurrences: list[tuple[int, int]] = []
    for start in range(len(tokens) - len(core) + 1):
        if tokens[start : start + len(core)] != core:
            continue
        suffix_start = start + len(core)
        source_form = next(
            (
                suffix
                for suffix in recognized_suffixes
                if tuple(tokens[suffix_start : suffix_start + len(suffix)]) == suffix
            ),
            (),
        )
        if source_form in suffixes:
            occurrences.append((start, suffix_start + len(source_form)))
    return occurrences


def _legal_form_tokens(run: CompanyResearchRun) -> set[str]:
    name = _company_name_tokens(run)
    suffix = tuple(name[len(_legal_name_core_tokens(run)) :])
    aliases = {
        ("spółka", "z", "ograniczoną", "odpowiedzialnością"): {"sp", "z", "o", "oo"},
        ("spółka", "komandytowo", "akcyjna"): {"sp", "k", "a"},
        ("spółka", "komandytowa"): {"sp", "k"},
        ("spółka", "partnerska"): {"sp", "p"},
        ("spółka", "jawna"): {"sp", "j"},
        ("spółka", "akcyjna"): {"s", "a", "sa"},
    }
    return set(suffix) | aliases.get(suffix, set())


def _has_company_antecedent(
    context: str, run: CompanyResearchRun, *, equivalent_legal_form: bool = False
) -> bool:
    sentences = _sentences(context)
    if len(sentences) < 2:
        return False
    if not equivalent_legal_form:
        name = _company_name_tokens(run)
        if not name:
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
    company_tokens = set(_company_name_tokens(run))
    for index in range(len(sentences) - 2, -1, -1):
        words = _WORD.findall(sentences[index])
        tokens = [word.casefold() for word in words]
        name_occurrences = _legal_name_occurrences(tokens, run)
        if not any(
            start == 0 or start == 1 and tokens[:1] == ["the"] for start, _ in name_occurrences
        ):
            continue
        named_positions = {
            position for start, end in name_occurrences for position in range(start, end)
        }
        if any(
            word[:1].isupper()
            and word.casefold() not in company_tokens
            and position not in named_positions
            for position, word in enumerate(words[1:], start=1)
        ):
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
    for sentence, tokens in zip(sentences, token_lists, strict=True):
        if name_tokens.issubset(set(tokens)):
            entities = [index for index, token in enumerate(tokens) if token in name_tokens]
            claims = [index for index, token in enumerate(tokens) if token in anchors]
            if claims and min(abs(entity - claim) for entity in entities for claim in claims) <= 8:
                return True
        # Longer named predicates are admitted only within one assertion clause and
        # only when the quote contains the registered legal form (or its equivalent).
        for clause in _ASSERTION_CLAUSE_BREAK.split(sentence):
            clause_tokens = [token.casefold() for token in _WORD.findall(clause)]
            clause_occurrences = _legal_name_occurrences(clause_tokens, run)
            claim_positions = [
                index for index, token in enumerate(clause_tokens) if token in anchors
            ]
            if (
                clause_occurrences
                and claim_positions
                and set(clause_tokens) & (_CURRENT_RELATIONS | {"focus", "focuses"})
                and min(
                    abs(entity - claim)
                    for start, end in clause_occurrences
                    for entity in range(start, end)
                    for claim in claim_positions
                )
                <= 24
            ):
                return True
    if len(sentences) < 2 or len(sentences) > 3:
        return False
    for entity_index, tokens in enumerate(token_lists):
        legal_occurrences = _legal_name_occurrences(tokens, run)
        if not name_tokens.issubset(set(tokens)) and not legal_occurrences:
            continue
        entity_positions = [
            index + sum(len(item) for item in token_lists[:entity_index])
            for index, token in enumerate(tokens)
            if token in name_tokens
        ]
        entity_positions.extend(
            start + sum(len(item) for item in token_lists[:entity_index])
            for start, _ in legal_occurrences
        )
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


def _shared_contrast_entity_attached(
    context: str, anchors: set[str], run: CompanyResearchRun
) -> bool:
    company_name = _company_name_tokens(run)
    allowed_names = (
        set(company_name)
        | anchors
        | {
            "it",
            "its",
            "they",
            "their",
            "company",
            "issuer",
            "the",
        }
        | _SENTENCE_INITIAL_NON_NAMES
    )
    for sentence in _sentences(context):
        company_named = False
        for clause in _ASSERTION_CLAUSE_BREAK.split(sentence):
            tokens = [token.casefold() for token in _WORD.findall(clause)]
            if company_named and set(tokens) & anchors:
                words = _WORD.findall(clause)
                if not any(
                    word[:1].isupper() and word.casefold() not in allowed_names for word in words
                ):
                    return True
            company_named |= _contains_sequence(tokens, company_name)
    return False


def _source_entity_attached(text: str, anchors: set[str], run: CompanyResearchRun) -> bool:
    if _conflicting_nip(text, run.identity.nip) or _tokens(text) & (
        _OTHER_ENTITY_MARKERS | {"group"}
    ):
        return False
    sentences = _sentences(text)
    if not sentences:
        return False
    if _entity_attached(sentences[-1], anchors, run):
        return True
    if _has_company_antecedent(text, run, equivalent_legal_form=True):
        return any(
            set(token.casefold() for token in _WORD.findall(sentence)) & anchors
            for sentence in sentences[1:]
        )
    return _shared_contrast_entity_attached(text, anchors, run)


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


_MONTHS = {
    "january": 1,
    "jan": 1,
    "styczeń": 1,
    "stycznia": 1,
    "february": 2,
    "feb": 2,
    "luty": 2,
    "lutego": 2,
    "march": 3,
    "mar": 3,
    "marzec": 3,
    "marca": 3,
    "april": 4,
    "apr": 4,
    "kwiecień": 4,
    "kwietnia": 4,
    "may": 5,
    "maj": 5,
    "maja": 5,
    "june": 6,
    "jun": 6,
    "czerwiec": 6,
    "czerwca": 6,
    "july": 7,
    "jul": 7,
    "lipiec": 7,
    "lipca": 7,
    "august": 8,
    "aug": 8,
    "sierpień": 8,
    "sierpnia": 8,
    "september": 9,
    "sep": 9,
    "wrzesień": 9,
    "września": 9,
    "october": 10,
    "oct": 10,
    "październik": 10,
    "października": 10,
    "november": 11,
    "nov": 11,
    "listopad": 11,
    "listopada": 11,
    "december": 12,
    "dec": 12,
    "grudzień": 12,
    "grudnia": 12,
}


def _assertion_qualified(text: str, run: CompanyResearchRun, *, mode: str = "current") -> bool:
    """Fail closed on denial, modality, conditions, and bounded temporal qualifiers."""
    normalized = _norm(text).casefold()
    tokens = _tokens(normalized)
    if re.search(
        r"\b(?:deny|denies|denied|denial|untrue|false|rumou?r|nieprawda|zaprzeczył)\b",
        normalized,
    ):
        return False
    if tokens & (_ASSERTION_NEGATION | _ASSERTION_MODALITY) or "?" in text:
        return False
    if re.search(
        r"\b(?:subject\s+to|once|provided\s+that|pending|if|unless|"
        r"pod\s+warunkiem|po\s+uzyskaniu|w\s+razie)\b",
        normalized,
    ):
        return False
    if mode in {"event", "financial"}:
        return True

    generated = run.generated_at.date()
    temporal = False
    dates: list[tuple[date, date]] = []
    for match in _DATE_PATTERN.finditer(text):
        try:
            raw = match.group()
            value = (
                date.fromisoformat(raw)
                if "-" in raw
                else date(int(raw[6:]), int(raw[3:5]), int(raw[:2]))
            )
        except ValueError:
            continue
        dates.append((value, value))
    for match in re.finditer(
        r"\b("
        + "|".join(sorted(map(re.escape, _MONTHS), key=len, reverse=True))
        + r")\s+(?:of\s+)?(\d{4})\b",
        normalized,
    ):
        temporal = True
        month, year = _MONTHS[match.group(1)], int(match.group(2))
        dates.append((date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])))
    quarter_pattern = re.compile(
        r"\b(?:(?:q|quarter)\s*([1-4])\s*(?:of\s+)?(\d{4})|"
        r"(i{1,3}|iv|[1-4])\s*\.?\s*kwarta(?:ł|łu)\s*(\d{4}))\b"
    )
    for match in quarter_pattern.finditer(normalized):
        temporal = True
        quarter = int(
            match.group(1)
            or {"i": "1", "ii": "2", "iii": "3", "iv": "4"}.get(match.group(3), match.group(3))
        )
        year = int(match.group(2) or match.group(4))
        month = (quarter - 1) * 3 + 1
        last_month = month + 2
        dates.append(
            (date(year, month, 1), date(year, last_month, calendar.monthrange(year, last_month)[1]))
        )

    future_cue = bool(re.search(r"\b(?:starting|beginning|from|since|od|począwszy)\b", normalized))
    month_names = "|".join(sorted(map(re.escape, _MONTHS), key=len, reverse=True))
    polish_expiry = re.search(
        r"\b(?:aż\s+)?do\s+(?:\d{4}-\d{2}-\d{2}|\d{2}[./]\d{2}[./]\d{4}|"
        r"(?:q|quarter)\s*[1-4]\s*\d{4}|(?:i{1,3}|iv|[1-4])\s*\.?\s*kwarta(?:ł|łu)\s*\d{4}|"
        + month_names
        + r"\s+\d{4})\b",
        normalized,
    )
    expiry_cue = bool(re.search(r"\b(?:until|through|thru)\b", normalized) or polish_expiry)
    status_cue = bool(
        re.search(r"\b(?:as\s+(?:of|at|on)|na\s+dzień|według\s+stanu\s+na)\b", normalized)
    )
    if future_cue or expiry_cue or status_cue:
        temporal = True
    if not temporal:
        return True
    if not dates:
        return False
    if (future_cue or status_cue) and any(start > generated for start, _ in dates):
        return False
    if expiry_cue and all(end < generated for _, end in dates):
        return False
    return True


def _positive_assertion_qualifies(
    context: str,
    phrase_tokens: list[str],
    run: CompanyResearchRun,
    *,
    mode: str = "current",
    claim_sentence: str | None = None,
) -> bool:
    """Match a bounded company-subject assertion, optionally at one canonical sentence."""
    if set(phrase_tokens) & {"leader", "leaders", "leadership", "leading"}:
        return False
    company_subjects = set(_legal_name_core_tokens(run)) | {
        "it",
        "its",
        "they",
        "their",
        "we",
        "our",
        "company",
        "issuer",
    }
    relations = _CURRENT_RELATIONS | _PASSIVE_RELATIONS
    if mode == "event":
        relations |= _EVENT_RELATIONS
    conditional_scope = False
    for sentence in _sentences(context):
        sentence_tokens = [token.casefold() for token in _WORD.findall(sentence)]
        explicitly_named = any(
            set(sentence_tokens[:start]).issubset(
                {"the", "currently", "separately", "obecnie", "aktualnie"}
            )
            for start, _ in _legal_name_occurrences(sentence_tokens, run)
        )
        sentence_conditional = bool(set(sentence_tokens) & {"if", "whether", "unless"})
        if claim_sentence is not None and sentence != claim_sentence:
            conditional_scope |= sentence_conditional
            continue
        if explicitly_named and not sentence_conditional:
            conditional_scope = False
        if claim_sentence is None:
            conditional_scope = False
        clauses = _ASSERTION_CLAUSE_BREAK.split(sentence)
        prior_company_subject = False
        for clause in clauses:
            tokens = [token.casefold() for token in _WORD.findall(clause)]
            if not tokens:
                continue
            if not _assertion_qualified(clause, run, mode=mode):
                continue
            has_company_subject = bool(set(tokens) & company_subjects)
            if conditional_scope:
                prior_company_subject |= has_company_subject
                continue
            if set(tokens) & {"if", "whether", "unless"}:
                conditional_scope = True
                prior_company_subject |= has_company_subject
                continue
            if set(tokens) & (_ASSERTION_NEGATION | _ASSERTION_MODALITY):
                prior_company_subject |= has_company_subject
                continue
            for start in range(len(tokens) - len(phrase_tokens) + 1):
                end = start + len(phrase_tokens)
                if tokens[start:end] != phrase_tokens:
                    continue
                application_sector = any(
                    tokens[marker : marker + 2] == ["for", "the"]
                    and "production" in tokens[:marker]
                    and 0 < start - marker <= 16
                    for marker in range(start)
                )
                for index, token in enumerate(tokens):
                    if token not in relations | {"focus", "focuses"} or abs(index - start) > (
                        24 if application_sector else 16
                    ):
                        continue
                    preceding = tokens[max(0, index - 8) : index]
                    subject_positions = [
                        position
                        for position in range(max(0, index - 12), index)
                        if tokens[position] in company_subjects
                    ]
                    subject_prefix_words = {
                        "separately",
                        "in",
                        "during",
                        "on",
                        "at",
                        "the",
                        "this",
                        "year",
                        "published",
                        "january",
                        "february",
                        "march",
                        "april",
                        "may",
                        "june",
                        "july",
                        "august",
                        "september",
                        "october",
                        "november",
                        "december",
                    }
                    subject_continuations = (
                        {
                            "a",
                            "an",
                            "the",
                            "currently",
                            "also",
                            "obecnie",
                            "aktualnie",
                            "actively",
                            "primarily",
                            "mainly",
                            "products",
                            "services",
                            "offerings",
                            "business",
                            "group",
                        }
                        | set(_company_name_tokens(run))
                        | _legal_form_tokens(run)
                    )
                    activity_focus_subject = (
                        token in {"focus", "focuses"}
                        and subject_positions
                        and tokens[: subject_positions[0]]
                        in (["the", "activities", "of"], ["the", "activities", "of", "the"])
                    )
                    if subject_positions:
                        subject_position = subject_positions[-1]
                        subject = (
                            all(
                                word in subject_prefix_words
                                or word in company_subjects
                                or word.isdigit()
                                for word in tokens[:subject_position]
                            )
                            and all(
                                word in subject_continuations
                                for word in tokens[subject_position + 1 : index]
                            )
                        ) or activity_focus_subject
                    else:
                        subject = (
                            prior_company_subject
                            and not has_company_subject
                            and all(
                                word in {"currently", "also", "actively", "primarily", "mainly"}
                                for word in tokens[:index]
                            )
                        )
                    passive_auxiliary = index - 1
                    if (
                        passive_auxiliary >= 0
                        and tokens[passive_auxiliary] not in {"is", "are", "was", "were"}
                        and passive_auxiliary > 0
                        and tokens[passive_auxiliary - 1] in {"is", "are", "was", "were"}
                        and tokens[passive_auxiliary] in {"currently", "also", "actively"}
                    ):
                        passive_auxiliary -= 1
                    passive_subject = tokens[index + 2 : index + 3]
                    passive_subject_is_company = (
                        bool(passive_subject) and passive_subject[0] in company_subjects
                    ) or tokens[index + 2 : index + 4] == ["the", "company"]
                    passive = (
                        token in _PASSIVE_RELATIONS
                        and index > start
                        and passive_auxiliary >= 0
                        and tokens[passive_auxiliary] in {"is", "are", "was", "were"}
                        and tokens[index + 1 : index + 2] == ["by"]
                        and passive_subject_is_company
                        and not tokens[:start]
                    )
                    if token in _PASSIVE_RELATIONS and not passive:
                        continue
                    if not subject and not passive:
                        continue
                    if token in {"is", "are"}:
                        if index >= start:
                            continue
                        between = tokens[index + 1 : start]
                        simple_copula = len(between) <= 2 and set(between).issubset(
                            {
                                "a",
                                "an",
                                "the",
                                "in",
                                "within",
                                "among",
                                "active",
                                "leading",
                                "major",
                            }
                        )
                        production_bridge = token == "is" and between == ["in", "production", "of"]
                        leader_production_bridge = token == "is" and between == [
                            "a",
                            "leader",
                            "in",
                            "the",
                            "production",
                            "of",
                        ]
                        leader_production_phrase_bridge = (
                            token == "is"
                            and between == ["a", "leader", "in", "the"]
                            and tokens[start : start + 2] == ["production", "of"]
                        )
                        product_list = (
                            token == "are"
                            and bool(set(preceding) & {"products", "services", "offerings"})
                            and between
                            and between[-1] == "and"
                            and between.count("and") == 1
                            and len(between) <= 8
                            and not any(word.endswith("ing") for word in between)
                        )
                        application_sector_bridge = (
                            token == "is"
                            and application_sector
                            and "leader" in between
                            and "production" in between
                            and any(
                                between[marker : marker + 2] == ["for", "the"]
                                for marker in range(len(between))
                            )
                        )
                        if (
                            not simple_copula
                            and not production_bridge
                            and not leader_production_bridge
                            and not leader_production_phrase_bridge
                            and not application_sector_bridge
                            and not product_list
                        ):
                            continue
                    elif index < start and not passive:
                        between = tokens[index + 1 : start]
                        determiners = {"a", "an", "the", "this", "these", "its", "their"}
                        direct_object = all(word in determiners for word in between)
                        industry_bridge = (
                            token in {"operate", "operates", "specialize", "specializes"}
                            and between[:1] in (["in"], ["within"])
                            and all(word in determiners for word in between[1:])
                        )
                        activity_bridge = token in {"focus", "focuses"} and between[:1] == ["on"]
                        catalog_header = [
                            "a",
                            "wide",
                            "range",
                            "of",
                            "products",
                            "including",
                        ]
                        catalog_tail = between[len(catalog_header) :]
                        catalog_bridge = (
                            token in {"offer", "offers"}
                            and between[: len(catalog_header)] == catalog_header
                            and not set(catalog_tail + phrase_tokens) & _ASSERTION_PREDICATES
                            and (
                                not catalog_tail
                                or len(catalog_tail) <= 8
                                and (
                                    catalog_tail[-1] == "and"
                                    or clause[: list(_WORD.finditer(clause))[start].start()]
                                    .rstrip()
                                    .endswith(",")
                                )
                            )
                        )
                        if not (
                            direct_object or industry_bridge or activity_bridge or catalog_bridge
                        ):
                            continue
                    elif (
                        index > start
                        and not passive
                        and not (mode == "event" and start <= index < end)
                        and not (
                            token in {"focus", "focuses"}
                            and activity_focus_subject
                            and "providing" in tokens[index + 1 :]
                        )
                    ):
                        continue
                    return True
            prior_company_subject |= has_company_subject
    return False


def _ordered_phrase_supported(
    phrase: str,
    excerpt: str,
    run: CompanyResearchRun,
    source_content: str | None = None,
    *,
    mode: str = "current",
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
        exact_claim = bool(claim_tokens) and _contains_sequence(sentence_tokens, claim_tokens)
        exact_phrase = _contains_sequence(sentence_tokens, phrase_tokens)
        matched_tokens = claim_tokens if exact_claim else phrase_tokens if exact_phrase else []
        contexts = (
            _bounded_source_contexts(source_content, sentence, prefer_source_lines=True)
            if source_content is not None
            else [sentence]
        )
        attachment = _source_entity_attached if source_content is not None else _entity_attached
        if not matched_tokens:
            continue
        for context in contexts:
            for claim_sentence in _sentences(context):
                claim_words = [token.casefold() for token in _WORD.findall(claim_sentence)]
                if not _contains_sequence(claim_words, matched_tokens):
                    continue
                if not attachment(context, anchors, run) and not (
                    mode == "event"
                    and _legal_name_occurrences(claim_words, run)
                    and _entity_attached(claim_sentence, anchors, run)
                ):
                    continue
                if not phrase_is_negative and _nearby_negation(claim_sentence, anchors):
                    continue
                if _positive_assertion_qualifies(
                    context,
                    matched_tokens,
                    run,
                    mode=mode,
                    claim_sentence=claim_sentence,
                ):
                    return True
    return False


def _lexical_support(
    fact: Fact[Any],
    evidence: list[tuple[EvidenceRef, RetrievedSource]],
    run: CompanyResearchRun,
) -> list[tuple[EvidenceRef, RetrievedSource]]:
    phrases = _candidate_terms(fact.value)
    if not phrases:
        return []
    supporting: set[int] = set()
    for phrase in phrases:
        phrase_pairs = {
            index
            for index, (ref, material) in enumerate(evidence)
            if _ordered_phrase_supported(phrase, ref.excerpt, run, material.content)
        }
        if not phrase_pairs:
            return []
        supporting.update(phrase_pairs)
    return [pair for index, pair in enumerate(evidence) if index in supporting]


def _has_unqualified_text_assertion(
    fact: Fact[Any],
    refs: list[EvidenceRef],
    run: CompanyResearchRun,
    by_id: dict[str, list[RetrievedSource]],
) -> bool:
    company_tokens = set(_company_name_tokens(run))
    for ref in refs:
        for material in by_id.get(ref.source_id, []):
            if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                continue
            for phrase in _candidate_terms(fact.value):
                phrase_tokens = [token.casefold() for token in _WORD.findall(_norm(phrase))]
                claim = [token for token in phrase_tokens if token not in company_tokens]
                if not claim:
                    continue
                for sentence in _sentences(ref.excerpt):
                    tokens = [token.casefold() for token in _WORD.findall(sentence)]
                    if not _contains_sequence(tokens, claim):
                        continue
                    contexts = _bounded_source_contexts(material.content, sentence)
                    if not any(
                        _source_entity_attached(context, set(claim), run) for context in contexts
                    ):
                        continue
                    if not any(
                        _positive_assertion_qualifies(context, claim, run) for context in contexts
                    ):
                        return True
    return False


_DATE_PATTERN = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}|\d{2}/\d{2}/\d{4})\b")
_LEADING_FINANCIAL_PERIOD = re.compile(
    r"^\s*for\s+\d{4}-\d{2}-\d{2}\s+to\s+\d{4}-\d{2}-\d{2}\s*,?\s*",
    re.IGNORECASE,
)
_AMOUNT_PATTERN = re.compile(
    r"(?<![\w])(?:\(\s*\d+(?:[ ,.]\d{3})*(?:[.,]\d+)?\s*\)|"
    r"[+\-−]?\s*\d+(?:[ ,.]\d{3})*(?:[.,]\d+)?)(?![\w])"
)


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
    compact = raw.replace(" ", "").replace("'", "").replace("−", "-")
    negative = compact.startswith("(") and compact.endswith(")")
    compact = compact.strip("()")
    sign = Decimal("-1") if negative else Decimal("1")
    if compact.startswith(("+", "-")):
        sign *= Decimal("-1") if compact[0] == "-" else Decimal("1")
        compact = compact[1:]
    values: set[Decimal] = set()
    try:
        if "," in compact and "." in compact:
            decimal_sep = "," if compact.rfind(",") > compact.rfind(".") else "."
            grouping_sep = "." if decimal_sep == "," else ","
            values.add(sign * Decimal(compact.replace(grouping_sep, "").replace(decimal_sep, ".")))
        elif "," in compact:
            values.add(sign * Decimal(compact.replace(",", ".")))
            if len(compact.rsplit(",", 1)[1]) == 3:
                values.add(sign * Decimal(compact.replace(",", "")))
        elif "." in compact:
            values.add(sign * Decimal(compact))
            if len(compact.rsplit(".", 1)[1]) == 3:
                values.add(sign * Decimal(compact.replace(".", "")))
        else:
            values.add(sign * Decimal(compact))
    except Exception:
        return set()
    return values


def _same_precision_amount(raw: str, value: Decimal) -> bool:
    return any(
        number == value and number.as_tuple().exponent == value.as_tuple().exponent
        for number in _numeric_values(raw)
    )


def _normalize_amount(raw: str, text: str, start: int) -> str:
    normalized = raw.strip()
    if normalized.startswith("(") and normalized.endswith(")"):
        return "-" + normalized[1:-1].strip()
    normalized = normalized.replace("−", "-").replace(" ", "")
    if re.search(r"\bminus\s*$", text[max(0, start - 24) : start].casefold()):
        normalized = "-" + normalized.lstrip("+")
    return normalized


def _observed_metric_amount(text: str, fact: FinancialFact) -> str | None:
    """Return a single amount tied to the requested financial metric."""

    if fact.period is None:
        return None
    without_dates = _DATE_PATTERN.sub(lambda match: " " * len(match.group()), text)
    tokens = [token.casefold() for token in _WORD.findall(without_dates)]
    metrics = _metric_spans(tokens, fact.metric)
    currencies = _currency_spans(tokens, fact.currency or "")
    units = _unit_spans(tokens, fact.unit or "")
    if not metrics or not currencies or not units:
        return None
    date_matches = list(_DATE_PATTERN.finditer(text))
    period_pairs = [
        (date_matches[index], date_matches[index + 1])
        for index in range(0, len(date_matches) - 1, 2)
    ]

    amounts: list[tuple[int, str]] = []
    for match in _AMOUNT_PATTERN.finditer(without_dates):
        token_index = len(_WORD.findall(without_dates[: match.start()]))
        if len(period_pairs) > 1:
            following_pairs = [pair for pair in period_pairs if match.start() <= pair[0].start()]
            if following_pairs:
                period_pair = min(following_pairs, key=lambda pair: pair[0].start() - match.start())
            else:
                period_pair = max(period_pairs, key=lambda pair: pair[1].end())
            if not (
                _date_present(period_pair[0].group(), fact.period.start)
                and _date_present(period_pair[1].group(), fact.period.end)
            ):
                continue
        near_currency = any(
            abs(token_index - min(max(token_index, start), end - 1)) <= 12
            for start, end in currencies
        )
        near_unit = any(
            abs(token_index - min(max(token_index, start), end - 1)) <= 12 for start, end in units
        )
        normalized = _normalize_amount(match.group(), without_dates, match.start())
        prior = tokens[max(0, token_index - 5) : token_index]
        is_delta = "by" in prior[-4:] and bool(
            set(prior[-4:]) & {"up", "down", "increase", "increased", "decrease", "decreased"}
        )
        if near_currency and near_unit and not is_delta:
            amounts.append((token_index, normalized))

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


def _financial_assertion_kind(text: str, fact: FinancialFact, run: CompanyResearchRun) -> str:
    """Recognize direct report clauses or a literal, fully labeled financial row."""
    if ";" in text:
        table_kind = _financial_assertion_kind(text.replace(";", " "), fact, run)
        if table_kind == "table":
            return table_kind
    clauses = _ASSERTION_CLAUSE_BREAK.split(text)
    if len(clauses) > 1:
        kinds = [_financial_assertion_kind(clause, fact, run) for clause in clauses]
        if "reported" in kinds:
            return "reported"
        if "table" in kinds:
            return "table"
        return "nonactual" if "nonactual" in kinds else "unsupported"
    if not _assertion_qualified(text, run, mode="financial"):
        return "nonactual"
    assertion_text = _LEADING_FINANCIAL_PERIOD.sub("", text, count=1)
    without_dates = _DATE_PATTERN.sub(" ", assertion_text)
    tokens = [token.casefold() for token in _WORD.findall(without_dates)]
    metrics = _metric_spans(tokens, fact.metric)
    core = (
        set(_legal_name_core_tokens(run))
        | _tokens(fact.group_name or "")
        | {
            "company",
            "issuer",
            "it",
            "its",
        }
    )
    subject_bridges = (
        _FINANCIAL_SUBJECT_BRIDGES
        | {token for suffix in _LEGAL_FORM_SUFFIXES for token in suffix}
        | {"s"}
        | ({"of"} if fact.scope == "group" and fact.group_name else set())
    )
    scope_words = (
        {"group", "consolidated", "grupa", "skonsolidowany"}
        if fact.scope == "group"
        else {
            "standalone",
            "non",
            "consolidated",
            "individual",
            "jednostkowy",
            "jednostkowe",
            "jednostkowo",
        }
    )

    def direct_subject(before: int, bridges: set[str]) -> bool:
        # A nested pronoun must not restart the subject after an unrecognized verb.
        if not set(tokens[:before]).issubset(core | bridges):
            return False
        return any(
            token in core
            and before - index <= 8
            and set(tokens[index + 1 : before]).issubset(bridges)
            for index, token in enumerate(tokens[:before])
        )

    for start, end in metrics:
        if any(
            tokens[index] in _FINANCIAL_NONACTUAL
            for index in range(max(0, start - 8), min(len(tokens), end + 13))
        ):
            return "nonactual"

        for index, token in enumerate(tokens):
            if token in _FINANCIAL_REPORT_VERBS and 0 <= start - index <= 10:
                predicate_to_metric = tokens[index + 1 : start]
                if (
                    len(predicate_to_metric) <= 5
                    and set(predicate_to_metric).issubset(_FINANCIAL_METRIC_BRIDGES)
                    and direct_subject(index, subject_bridges)
                ):
                    return "reported"
            if token in {"is", "are", "was", "were"} and end <= index <= end + 3:
                if direct_subject(start, subject_bridges | scope_words):
                    return "reported"
            if (
                token == "actual"
                and index < start
                and start - index <= 2
                and direct_subject(index, subject_bridges)
            ):
                return "reported"
            if (
                token in _FINANCIAL_REPORT_VERBS
                and end <= index <= end + 4
                and "by" in tokens[index + 1 : index + 4]
                and any(subject in tokens[index + 1 : index + 7] for subject in core)
                and set(tokens[:start]).issubset(core | subject_bridges)
            ):
                return "reported"
            if (
                token in _FINANCIAL_REPORT_VERBS
                and end <= index <= end + 8
                and any(
                    scope_end <= start and start - scope_end <= 2
                    for _, scope_end in _phrase_spans(tokens, scope_words)
                )
                and any(
                    end <= name_start
                    and name_end <= index
                    and index - name_end <= 2
                    and set(tokens[end:name_start]).issubset({"spółki", "spółka", "of"})
                    for name_start, name_end in _legal_name_occurrences(tokens, run)
                )
            ):
                return "reported"

        currencies = _currency_spans(tokens, fact.currency or "")
        units = _unit_spans(tokens, fact.unit or "")
        scopes = _phrase_spans(tokens, scope_words)
        amounts = [
            len(_WORD.findall(without_dates[: match.start()]))
            for match in _AMOUNT_PATTERN.finditer(without_dates)
        ]
        for scope_start, scope_end in scopes:
            for currency_start, currency_end in currencies:
                for unit_start, unit_end in units:
                    if not (
                        scope_end
                        <= start
                        <= end
                        <= currency_start
                        <= currency_end
                        <= unit_start
                        <= unit_end
                        and start - scope_end <= 2
                        and currency_start - end <= 2
                        and direct_subject(scope_start, subject_bridges)
                    ):
                        continue
                    if any(unit_end <= amount <= unit_end + 4 for amount in amounts):
                        return "table"
    return "unsupported"


def _financial_assertion_amount(
    text: str, fact: FinancialFact, observed: str, run: CompanyResearchRun
) -> str | None:
    if _financial_assertion_kind(text, fact, run) not in {"reported", "table"}:
        return None
    if fact.metric != "net_result":
        return observed
    tokens = [token.casefold() for token in _WORD.findall(_DATE_PATTERN.sub(" ", text))]
    metrics = _metric_spans(tokens, fact.metric)
    selected_loss = any(
        tokens[start:end] in (["net", "loss"], ["strata", "netto"]) for start, end in metrics
    )
    if not selected_loss:
        return observed
    if observed.startswith("+"):
        return None
    if any(number < 0 for number in _numeric_values(observed)):
        return observed
    return f"-{observed}"


def _date_present(text: str, value: date) -> bool:
    normalized = _norm(text)
    return (
        value.isoformat() in normalized
        or value.strftime("%d.%m.%Y") in normalized
        or value.strftime("%d/%m/%Y") in normalized
    )


def _financial_observations(
    fact: FinancialFact,
    excerpt: str,
    run: CompanyResearchRun,
    source_content: str | None = None,
) -> list[str]:
    if fact.period is None or fact.currency is None or fact.unit is None:
        return []
    metric_words = _METRICS[fact.metric]
    contexts = (
        _bounded_source_contexts(source_content, excerpt) if source_content is not None else []
    ) or [excerpt]
    observations: list[str] = []
    if fact.period.end > run.generated_at.date():
        return []
    for context in contexts:
        for window in _context_windows(context):
            if (
                len(_sentences(window)) > 1
                and _financial_assertion_kind(window, fact, run) != "table"
            ):
                continue
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
                normalized = _financial_assertion_amount(window, fact, observed, run)
                if normalized is not None and normalized not in observations:
                    observations.append(normalized)
    return observations


def _employee_observation_date(text: str) -> date | None:
    """Return only an explicitly observation-attached date, never page metadata."""
    dates: set[date] = set()
    for match in _DATE_PATTERN.finditer(text):
        raw = match.group()
        try:
            value = (
                date.fromisoformat(raw)
                if "-" in raw
                else date(int(raw[6:]), int(raw[3:5]), int(raw[:2]))
            )
        except ValueError:
            continue
        before = text[max(0, match.start() - 48) : match.start()].casefold()
        after = text[match.end() : match.end() + 32].casefold()
        if re.search(
            r"(?:as\s+of|as\s+at|as\s+on|na\s+dzień|według\s+stanu\s+na)[\s:,-]*$",
            before,
        ) or re.match(
            r"[\s:,-]*(?:as\s+of|as\s+at|na\s+dzień|według\s+stanu\s+na)\b",
            after,
        ):
            if not _publication_date_present(text, value):
                dates.add(value)
    return next(iter(dates)) if len(dates) == 1 else None


def _employee_subject_bound(
    clause: str, run: CompanyResearchRun, context: str | None = None
) -> bool:
    tokens = [token.casefold() for token in _WORD.findall(clause)]
    employment = {
        "employs",
        "employ",
        "employed",
        "employing",
        "has",
        "have",
        "zatrudnia",
        "zatrudniają",
        "zatrudniał",
        "zatrudnienie",
    }
    modifiers = {
        "currently",
        "also",
        "actively",
        "primarily",
        "mainly",
        "obecnie",
        "aktualnie",
        "separately",
        "is",
        "are",
        "was",
        "were",
    }
    owner_blockers = _EMPLOYEE_RELATION_BLOCKERS | {
        "partner",
        "partnera",
        "subsidiary",
        "affiliate",
        "dostawca",
        "klient",
    }
    spans = set(_legal_name_occurrences(tokens, run))
    name = _company_name_tokens(run)
    spans.update(
        (start, start + len(name))
        for start in range(len(tokens) - len(name) + 1)
        if tokens[start : start + len(name)] == name
    )
    core = _legal_name_core_tokens(run)
    spans.update(
        (start, start + len(core))
        for start in range(len(tokens) - len(core) + 1)
        if core and tokens[start : start + len(core)] == core
    )
    for start, end in spans:
        prefix = tokens[:start]
        if set(prefix) & owner_blockers:
            continue
        if any(
            word
            not in {
                "the",
                "company",
                "currently",
                "obecnie",
                "aktualnie",
                "as",
                "of",
                "in",
                "on",
                "at",
                "during",
                "nip",
                "issuer",
            }
            and not word.isdigit()
            for word in prefix
        ):
            continue
        following = tokens[end:]
        if following[:1] == ["s"] or set(following[:4]) & owner_blockers:
            continue
        relation = next(
            (index for index, token in enumerate(following[:5]) if token in employment), None
        )
        if relation is not None and relation <= 3 and set(following[:relation]).issubset(modifiers):
            return True
    if spans:
        return False

    relation = next((index for index, token in enumerate(tokens[:6]) if token in employment), None)
    if relation is None or not set(tokens[:relation]).issubset(
        {
            "it",
            "its",
            "they",
            "their",
            "we",
            "our",
            "the",
            "company",
            "currently",
            "obecnie",
            "aktualnie",
        }
    ):
        return False
    if set(tokens) & owner_blockers or "s" in tokens[:relation]:
        return False
    return _employee_entity_attached(context or clause, run)


def _employee_assertion_supported(
    context: str,
    run: CompanyResearchRun,
    expected: tuple[int | None, int | None] | None = None,
    expected_date: date | None = None,
) -> bool:
    for sentence in _sentences(context):
        for clause in _ASSERTION_CLAUSE_BREAK.split(sentence):
            tokens = _tokens(clause)
            if (
                _employee_range_observation(clause) is None
                or not _assertion_qualified(clause, run)
                or not _employee_subject_bound(clause, run, context)
            ):
                continue
            if expected is not None and _employee_range_observation(clause) != expected:
                continue
            if expected_date is not None and _employee_observation_date(clause) != expected_date:
                continue
            if (
                tokens & {"employed", "had", "was", "were"}
                and _employee_observation_date(clause) is None
            ):
                continue
            words = [token.casefold() for token in _WORD.findall(clause)]
            employment_verbs = {
                "employs",
                "employ",
                "employed",
                "employing",
                "zatrudnia",
                "zatrudniają",
                "zatrudniał",
            }
            employee_terms = {
                "employees",
                "employee",
                "staff",
                "personnel",
                "people",
                "persons",
                "person",
                "pracowników",
                "pracownicy",
                "zatrudnionych",
            }
            if not set(words) & employee_terms:
                continue
            if not set(words) & employment_verbs and not (
                set(words) & {"has", "have"}
                and set(words) & {"employees", "employee", "staff", "personnel", "pracowników"}
            ):
                continue
            if set(words) & {"served", "serves", "trained", "train"}:
                continue
            return True
    return False


def _has_unqualified_employee_assertion(
    fact: EmployeeFact,
    refs: list[EvidenceRef],
    run: CompanyResearchRun,
    by_id: dict[str, list[RetrievedSource]],
) -> bool:
    if fact.value is None:
        return False
    expected = (
        (fact.value.count, fact.value.count)
        if isinstance(fact.value, ExactEmployees)
        else (fact.value.minimum, fact.value.maximum)
    )
    for ref in refs:
        for material in by_id.get(ref.source_id, []):
            if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                continue
            for sentence in _sentences(ref.excerpt):
                if _employee_range_observation(sentence) != expected:
                    continue
                contexts = _bounded_source_contexts(material.content, sentence)
                if any(
                    _employee_entity_attached(context, run)
                    and not _employee_assertion_supported(context, run, expected)
                    for context in contexts
                ):
                    return True
    return False


def _employee_supported(
    fact: EmployeeFact, excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    value = fact.value
    if isinstance(value, ExactEmployees):
        expected = (value.count,)
        for sentence in _sentences(excerpt):
            contexts = _bounded_source_contexts(material.content, sentence)
            if _employee_observation(sentence) == expected and any(
                _employee_assertion_supported(context, run, (value.count, value.count))
                and _employee_entity_attached(context, run)
                for context in contexts
            ):
                return True
    if isinstance(value, EmployeeRange):
        expected_bounds = (value.minimum, value.maximum)
        for sentence in _sentences(excerpt):
            contexts = _bounded_source_contexts(material.content, sentence)
            if _employee_range_observation(sentence) == expected_bounds and any(
                _employee_assertion_supported(context, run, expected_bounds)
                and _employee_entity_attached(context, run)
                for context in contexts
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
    if fact.value is None:
        return False
    for ref in fact.evidence:
        for material in by_id.get(ref.source_id, []):
            if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                continue
            for sentence in _sentences(ref.excerpt):
                contexts = _bounded_source_contexts(material.content, sentence)
                matches_value = (
                    isinstance(fact.value, ExactEmployees)
                    and _employee_observation(sentence) == (fact.value.count,)
                ) or (
                    isinstance(fact.value, EmployeeRange)
                    and _employee_range_observation(sentence)
                    == (fact.value.minimum, fact.value.maximum)
                )
                expected = (
                    (fact.value.count, fact.value.count)
                    if isinstance(fact.value, ExactEmployees)
                    else (fact.value.minimum, fact.value.maximum)
                )
                if matches_value and any(
                    _employee_assertion_supported(context, run, expected, fact.as_of)
                    and _employee_entity_attached(context, run)
                    for context in contexts
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


def _event_contexts(
    event: CompanyEvent,
    excerpt: str,
    run: CompanyResearchRun,
    source_content: str | None = None,
) -> list[str]:
    value = event.value
    if value is None:
        return []
    phrases = [phrase for phrase in (value.title, value.summary) if phrase]
    return [
        context
        for sentence in _sentences(excerpt)
        for context in (
            _bounded_source_contexts(source_content, sentence, prefer_source_lines=True)
            if source_content is not None
            else [sentence]
        )
        if all(
            _ordered_phrase_supported(phrase, sentence, run, source_content, mode="event")
            for phrase in phrases
        )
    ]


def _event_publication_supported(
    event: CompanyEvent, excerpt: str, run: CompanyResearchRun, material: RetrievedSource
) -> bool:
    value = event.value
    contexts = _event_contexts(event, excerpt, run, material.content)
    if value is None or not contexts:
        return False
    if material.source.published_on is not None:
        return material.source.published_on == value.published_on
    return any(_publication_date_present(window, value.published_on) for window in contexts)


def _event_date_owned(clause: str, value: EventDetails, occurred_on: date) -> bool:
    tokens = [token.casefold() for token in _WORD.findall(clause)]
    date_index = next(
        (
            len(_WORD.findall(clause[: match.start()]))
            for match in _DATE_PATTERN.finditer(clause)
            if _date_present(match.group(), occurred_on)
        ),
        None,
    )
    if date_index is None:
        return False
    relations = [index for index, token in enumerate(tokens) if token in _EVENT_RELATIONS]
    for phrase in (value.title, value.summary):
        phrase_tokens = [token.casefold() for token in _WORD.findall(_norm(phrase))]
        if not phrase_tokens:
            continue
        for start in range(len(tokens) - len(phrase_tokens) + 1):
            if tokens[start : start + len(phrase_tokens)] != phrase_tokens:
                continue
            end = start + len(phrase_tokens)
            if any(
                min(abs(relation - start), abs(relation - (end - 1))) <= 8
                and abs(date_index - relation) <= 12
                for relation in relations
            ):
                return True
    return False


def _event_occurrence_supported(
    event: CompanyEvent, excerpt: str, run: CompanyResearchRun, source_content: str | None = None
) -> bool:
    value = event.value
    if value is None or value.occurred_on is None:
        return value is not None
    if value.occurred_on > run.generated_at.date():
        return False
    phrases = [phrase for phrase in (value.title, value.summary) if phrase]
    for sentence in _sentences(excerpt):
        contexts = (
            _bounded_source_contexts(source_content, sentence, prefer_source_lines=True)
            if source_content is not None
            else [sentence]
        )
        for context in contexts:
            for assertion in _sentences(context):
                clauses = re.split(r"\band\s+(?=(?:a|an|the)\b)", assertion, flags=re.I)
                for clause in clauses:
                    if (
                        _date_present(clause, value.occurred_on)
                        and _event_date_owned(clause, value, value.occurred_on)
                        and not _publication_date_present(clause, value.occurred_on)
                        and _assertion_qualified(clause, run, mode="event")
                        and all(
                            _ordered_phrase_supported(phrase, clause, run, mode="event")
                            for phrase in phrases
                        )
                    ):
                        return True
    return False


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
            if ref.source_id not in by_id:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            materials_for_ref = eligible_by_id.get(ref.source_id, [])
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
            valid_pairs = _lexical_support(fact, eligible, run)
        if kind == "employees" and isinstance(fact, EmployeeFact) and valid_pairs:
            expected: tuple[int | None, int | None]
            candidate = fact.value
            if isinstance(candidate, ExactEmployees):
                expected = (candidate.count, candidate.count)
            else:
                assert isinstance(candidate, EmployeeRange)
                expected = (candidate.minimum, candidate.maximum)
            candidate_date = (
                fact.as_of if _employee_as_of_supported(fact, run, eligible_by_id) else None
            )
            conflicts: list[tuple[RetrievedSource, str, tuple[int | None, int | None]]] = []
            for material in run.sources:
                if material.kind != "full_page" or material.source.source_id in blocked_ids:
                    continue
                for sentence in _sentences(material.content):
                    observed = _employee_range_observation(sentence)
                    contexts = _bounded_source_contexts(material.content, sentence)
                    observation_date = _employee_observation_date(sentence)
                    if (
                        observed is None
                        or not any(
                            _employee_assertion_supported(context, run, observed)
                            and _employee_entity_attached(context, run)
                            for context in contexts
                        )
                        or observed == expected
                    ):
                        continue
                    if (
                        candidate_date is not None
                        and observation_date is not None
                        and candidate_date != observation_date
                    ):
                        continue
                    conflicts.append((material, sentence, observed))
            if conflicts:
                alternative_refs = [
                    EvidenceRef(source_id=material.source.source_id, excerpt=sentence)
                    for material, sentence, _ in conflicts
                ]
                unique_refs = {
                    (ref.source_id, ref.excerpt): ref for ref in [*fact.evidence, *alternative_refs]
                }
                return _downgrade(
                    fact,
                    "Conflicting employee observations for the same or unresolved observation date",
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
            supported_refs = list(
                {(ref.source_id, ref.excerpt): ref for ref, _material in valid_pairs}.values()
            )
            return fact.model_copy(update={"evidence": supported_refs})
        reason = (
            "No exact full-page citation verifies the candidate value, entity, and required context"
        )
        clear_value = False
        if not exact_refs:
            reason = (
                "Evidence is absent, snippet-only, or not an exact "
                "NFC/whitespace-normalized excerpt from a retained full page"
            )
        elif isinstance(fact, EmployeeFact) and _has_unqualified_employee_assertion(
            fact, exact_refs, run, eligible_by_id
        ):
            reason = (
                "Cited employee count lacks a recognized current assertion or an explicitly "
                "attached observation date"
            )
            clear_value = True
        elif kind != "employees" and _has_unqualified_text_assertion(
            fact, exact_refs, run, eligible_by_id
        ):
            reason = (
                "Cited page contains the candidate wording but not a recognized bounded "
                "affirmative relation for the resolved company"
            )
            clear_value = True
        return _downgrade(fact, reason, clear_value=kind == "employees" or clear_value)

    business = gate(run.draft.business_description, "text")
    products = gate(run.draft.products_services, "text")
    industries = gate(run.draft.industries, "text")
    markets = gate(run.draft.markets, "text")
    employees = gate(run.draft.employees, "employees")
    if employees.as_of is not None and not _employee_as_of_supported(
        employees, run, eligible_by_id
    ):
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
        supporting_financial_refs: list[EvidenceRef] = []
        conflicting_amount = False
        nonactual_assertion = False
        unsupported_assertion = False
        candidate_mismatch = False
        nip_conflict = False
        for ref in financial.evidence:
            if ref.source_id not in by_id:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            if any(
                material.kind == "full_page"
                and _exact_excerpt(material, ref.excerpt)
                and _conflicting_nip(ref.excerpt, run.identity.nip)
                for material in eligible_by_id.get(ref.source_id, [])
            ):
                nip_conflict = True
        for source_id, source_materials in eligible_by_id.items():
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
                observations: list[str] = []
                for ref in cited:
                    cited_observations = _financial_observations(
                        financial, ref.excerpt, run, material.content
                    )
                    if not cited_observations:
                        context = "\n".join(_bounded_source_contexts(material.content, ref.excerpt))
                        kind = _financial_assertion_kind(context or ref.excerpt, financial, run)
                        nonactual_assertion |= kind == "nonactual"
                        unsupported_assertion |= kind == "unsupported"
                    else:
                        observations.extend(cited_observations)
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
                    observations.extend(
                        _financial_observations(financial, combined, run, material.content)
                    )
                matching_observation = False
                for observed in observations:
                    if financial.value is not None and _same_precision_amount(
                        observed, financial.value
                    ):
                        verified_amount = True
                        matching_observation = True
                    else:
                        conflicting_amount = True
                        candidate_mismatch = True
                if matching_observation:
                    supporting_financial_refs.extend(cited)
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
            financials.append(
                financial.model_copy(
                    update={
                        "evidence": list(
                            {
                                (ref.source_id, ref.excerpt): ref
                                for ref in supporting_financial_refs
                            }.values()
                        )
                    }
                )
            )
        else:
            reason = (
                "Exact full-page evidence does not verify metric, reporting interval, currency, "
                "unit, entity scope, and amount"
            )
            if nonactual_assertion:
                reason = (
                    "Cited financial assertion is a target, forecast, denial, or conditional, "
                    "not an actual reported result"
                )
            elif candidate_mismatch:
                reason = (
                    "Cited actual financial amount or sign does not match the candidate "
                    "at the declared precision"
                )
            elif unsupported_assertion:
                reason = (
                    "Cited financial text does not match the bounded reported-observation "
                    "or labeled-row contract"
                )
            financials.append(_downgrade(financial, reason, clear_value=True))

    events: list[CompanyEvent] = []
    for event in run.draft.recent_developments:
        if event.value is None:
            events.append(event)
            continue
        publication_verified = False
        occurrence_verified = event.value.occurred_on is None
        nip_conflict = False
        supporting_event_refs: list[EvidenceRef] = []
        for ref in event.evidence:
            if ref.source_id not in by_id:
                raise ValueError(f"unknown evidence source ID: {ref.source_id}")
            for material in eligible_by_id.get(ref.source_id, []):
                if material.kind != "full_page" or not _exact_excerpt(material, ref.excerpt):
                    continue
                if _conflicting_nip(ref.excerpt, run.identity.nip):
                    nip_conflict = True
                supports_event = _event_publication_supported(event, ref.excerpt, run, material)
                supports_occurrence = _event_occurrence_supported(
                    event, ref.excerpt, run, material.content
                )
                publication_verified |= supports_event
                occurrence_verified |= supports_occurrence
                if supports_event or supports_occurrence:
                    supporting_event_refs.append(ref)

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

        event_reason = event.reason
        for rejection in rejections:
            event_reason = _append_rejection_reason(event_reason, rejection)
        if event.state == "supported" and (clear_event or nip_conflict):
            event = _downgrade(
                event, event_reason or "Event evidence was rejected", clear_value=clear_event
            )
            if not clear_event and value is not None:
                event = event.model_copy(update={"value": value})
        elif rejections:
            event = event.model_copy(update={"value": retained_value, "reason": event_reason})
        elif event.state == "supported":
            event = event.model_copy(
                update={
                    "evidence": list(
                        {
                            (ref.source_id, ref.excerpt): ref for ref in supporting_event_refs
                        }.values()
                    )
                }
            )
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
    used_ids.update(blocked_ids)
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
    limitations.extend(
        f"Source {source_id}: publication blocked: unproven_legacy_url_relationship"
        for source_id in sorted(blocked_ids)
    )
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
