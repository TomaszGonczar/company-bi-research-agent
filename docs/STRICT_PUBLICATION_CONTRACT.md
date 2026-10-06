# Strict publication contract — v0.1.1 candidate

Normative replacement of the earlier heuristic contract. Written before implementation.
The agent may propose broadly; deterministic publication recognizes only the finite
language below. This is not a general natural-language verifier. Truth outside this
language is not a verifier-positive requirement. No live research is part of this change.

## 1. One assertion unit and one entity

A research assertion unit is the **entire retained `full_page.content`**, after NFC
normalization and stripping outer whitespace, at most 4096 Unicode code points.
It must match exactly one production, including the final full stop. There are no
sentence windows, favorable clause selection, headings, introductions, surrounding
paragraphs, tables, multiple assertions, inferred subjects, or ignored residual text.
An extra denial, retraction, forecast, condition, explanation or second sentence
makes the entire unit unsupported, regardless of the candidate's excerpt.
This deliberately excludes ordinary multi-paragraph web pages. Retrieval must never
clip a page into a synthetic assertion to claim compliance with this contract.

`ENTITY` is the resolved legal name after NFC and whitespace-run normalization to
single ASCII spaces. Its spelling, case, punctuation and legal form must match
literally. No aliases, reordered/subset tokens, abbreviated legal forms, pronouns,
name-only resolution, neighboring company headers or implicit NIP-based aliases.
Grammar separators are single ASCII spaces. Internal source whitespace is not
rewritten to make a production match. The finite literals below are case-sensitive.

A supporting citation must cover that whole unit, under the existing NFC/whitespace
citation normalization; a clipped substring is insufficient. The parser always reads
retained content, never an excerpt as a substitute for source context. Known host-owned
source IDs, full-page provenance, redirect lineage and source-ID-wide quarantine remain
mandatory. Unknown IDs and inconsistent registry identity are errors, not soft support.
Parsing each eligible full page once is sufficient; no candidate-specific context scan.

## 2. Opaque quoted labels, not a vocabulary

`LABEL` is one JSON double-quoted string, decoded using JSON string rules. Its decoded
value is 1–256 code points, has no leading/trailing whitespace, and contains no Unicode
control/format/surrogate characters (Unicode categories beginning `C`). NFC is allowed;
case, punctuation and internal spaces are preserved. Escaped quotes are data. The
complete decoded label must equal the candidate scalar or list item. No substring,
paraphrase, translation, sector inference or delimiter splitting is permitted.

Quotes are required **in the source**, not invented around an unquoted source phrase.
This boundary was explicitly selected by the user. For example:

- in contract: `Example sp. z o.o. offers "cloud services".` → `["cloud services"]`;
- true but out of contract: `Example sp. z o.o. offers cloud services.`;
- unsafe candidate: `Example sp. z o.o. offers "gas detectors".` → `["gas"]`;
- unsupported: `Example sp. z o.o. offers "cloud services" after approval.`.

Labels are opaque names, not clauses to interpret. A label containing the words
`after approval` cannot be shortened to an unconditional service. There is no catalog
of acceptable label meanings and no expanding qualifier/synonym denylist.

## 3. Qualitative productions

Each literal predicate alternative is a grammar shape for matrix coverage. Optional
modifier variants must also be exercised. No modifier other than the two listed below
is recognized; no optional prefix or tail exists.

| Field | Complete production | Alternatives |
|---|---|---|
| products_services (English) | `ENTITY [currently ]PRED LABEL.` | `offers`, `provides`, `sells`, `manufactures`, `supplies` |
| products_services (Polish) | `ENTITY [obecnie ]PRED LABEL.` | `oferuje`, `świadczy`, `sprzedaje`, `produkuje`, `dostarcza` |
| business_description | `ENTITY operates as LABEL.` | one English shape |
| business_description | `ENTITY działa jako LABEL.` | one Polish shape |
| industries | `ENTITY operates in the LABEL industry.` | one English shape |
| industries | `ENTITY działa w branży LABEL.` | one Polish shape |
| markets | `ENTITY operates in the LABEL market.` | one English shape |
| markets | `ENTITY działa na rynku LABEL.` | one Polish shape |

The business scalar must equal the label. Every item in a qualitative list must have
its own complete supporting unit; a list is supported only if all its items are
verified. Distinct pages may prove distinct list items; components of an individual
assertion may never be combined across pages. Evidence is narrowed to matching refs.
An industry cannot be inferred from a product, nor a market from an address.

## 4. Exact employment

Two shapes:

```text
ENTITY employs COUNT people[ as of DATE].
ENTITY zatrudnia COUNT pracowników[ na dzień DATE].
```

`COUNT` is `0` or an ASCII nonzero digit followed by up to 11 ASCII digits; no signs,
grouping, fractions, approximate counts, employee ranges, people served/trained or
unit inference. `DATE` is a valid Gregorian `YYYY-MM-DD`, not later than the run's
`generated_at` date. The predicate, count, date and exact legal subject occupy the
same complete unit. Candidate count must equal the parsed integer, including zero.

The optional candidate `as_of` is retained only when it equals that same observation's
explicit date. If only the candidate date is wrong/unverified, clear it and preserve
the independently verified count. A missing date means observation time is unspecified,
not a claim that the count is current. Do not fill a missing candidate date from metadata.
A future source observation is unsupported as a whole, not repaired by dropping its date.
Different counts at the same or unresolved date conflict; differing explicitly dated
observations do not conflict solely because their dates differ. Examine all recognized
eligible retained units, not just citations selected by the model.

## 5. Atomic financial observation

Eight shapes (two reporting predicates × four metric predicates):

```text
ENTITY REPORT standalone METRIC of CURRENCY AMOUNT SCALE for START to END.
```

- `REPORT`: `reported` or `recorded` (actuality is explicit, not inferred).
- `METRIC`: `revenue`, `net profit`, `net loss`, `net result`.
- `CURRENCY`: exactly `PLN`, `EUR` or `USD`.
- `SCALE`: `units`, `thousand`, `million`, `billion`; model units respectively
  `units`, `thousands`, `millions`, `billions`. No scale conversion or rounding.
- `START`, `END`: complete Gregorian ISO dates; `START <= END < generated_at.date()`.
  No year-only, quarter, fiscal-year or partial-year inference. The explicit interval
  need not be a calendar year. A period ending today is not yet completed.
- Scope is exactly `legal_entity`, with `group_name = null`; group observations are
  outside this contract.

`AMOUNT` is optional ASCII `+`, ASCII `-` or Unicode minus `−`, followed by `0` or
1–18 ASCII digits without a leading zero, optionally a dot and 1–6 ASCII digits.
No comma decimals, grouping characters, exponents, currency symbols, parentheses,
trailing sign, written numerals, multiple amounts or accounting/table formats.
`Decimal` equality is exact (trailing decimal zeros do not change the amount).

`revenue` and `net result` use the explicit numeric sign, default positive.
`net profit` permits unsigned or explicit-plus nonnegative values, never a minus sign.
`net loss` permits only an unsigned magnitude and maps it to a negative `net_result`;
zero remains zero. Explicit signed loss magnitudes are deliberately unsupported.
Contradictory profit/loss signs never publish. Candidate value, metric, currency, unit,
scope, group name and **both** period boundaries must match this single observation.

No metric/amount/currency/scale/period assembly from neighbors, comparative columns,
guidance, targets, deltas, conditional results, summaries or nearest numbers.
Any extra amount, currency, scale, period or trailing qualification fails the full
production. Recognized observations with different amounts for the same metric,
interval, currency, unit and scope conflict, including uncited retained observations.

## 6. Completed events

Six shapes:

```text
ENTITY PRED LABEL[ on DATE].       # opened | launched | signed
ENTITY PRED LABEL[ w dniu DATE].   # otworzyła | uruchomiła | podpisała
```

The label is the complete event object. Candidate `title` must equal its decoded label;
`summary` must equal the entire NFC-normalized, outer-trimmed assertion unit. This
retains the completed predicate instead of inferring a paraphrased event. Extra text,
second events, retractions, denials and qualifications make the whole unit unsupported.

`published_on` must equal explicit `Source.published_on` on the same cited full page,
within the profile's existing previous-12-month window and not in the future. Neither
retrieval time nor occurrence text may substitute for publication metadata.
Occurrence `DATE`, when present, must be valid and not future. Candidate `occurred_on`
is retained only if it equals that exact event's date. Clear only an incorrect optional
candidate occurrence date when title, summary and publication remain verified; do not
discard those independently supported components. Never borrow a neighboring date.
An invalid/future source occurrence makes the source assertion unsupported as a whole.

## 7. Structural registry identity

Every registry material must be recognized and self-consistent. JSON duplicate keys,
ambiguous declarations, unsupported formats, missing NIP/legal name, conflicting NIP
or legal name, and a supported identity field without its mapped source value reject
the run. `CompanyIdentity` requires a supported legal name, so an unrecognized registry
format cannot silently produce a publishable identity. Recheck at `build_profile`,
including unchecked `model_copy` mutations. Only registry material can prove identity.

### MF JSON

A JSON object with object `result.subject` maps only these fields:

| Identity field | Mapped source field |
|---|---|
| nip | result.subject.nip |
| legal_name | result.subject.name |
| regon | result.subject.regon |
| krs | result.subject.krs |
| registered_address | nonempty result.subject.workingAddress, otherwise result.subject.residenceAddress |

Mapped values must be strings. NIP is the exact canonical 10-digit NIP. There is no
city extraction or website inference from MF JSON. Other JSON paths, comments,
archived addresses and evidence strings do not establish field values. A field-value
citation (plain or JSON-quoted) still needs the actual mapped field and exact retained
membership; finding the string elsewhere is insufficient. Registry string comparisons
use NFC and whitespace-run normalization, preserving case and punctuation.

### Legacy host-generated text snapshot

The recognized legacy format is exactly the existing `SourceStore` serialization:
first line `MF VAT register identity material (not a raw registry response):`, named
field declarations, optional named evidence rows, and final `NIP: 1234567890`.
The six fields are `legal_name`, `krs`, `regon`, `registered_city`,
`registered_address`, `website`, each declared once. A declaration is `FIELD: VALUE`
or `FIELD: unknown; REASON` / `FIELD: uncertain; REASON`. Non-supported declarations
cannot prove a supported field. Evidence rows have the form
`FIELD evidence from SOURCE_ID: EXCERPT`; they are not field declarations. Unknown
lines, duplicate declarations, multiline/ambiguous values and missing required
structure reject the snapshot. No unheaded ad-hoc registry prose fallback is retained.
Evidence rows alone never override their named field declaration.

Both formats retain exact normalized citation membership and source-ID ownership.
Supported values must match their mapped field on the cited record; all retained
registry records must agree on the target NIP and legal name. No arbitrary string
search can replace structural mapping. SourceStore's legacy format remains readable
because it is the actual current host format, not an inferred external schema.

## 8. States, conflicts and provenance

Only input `supported` candidates are eligible for supported publication; `uncertain`
and `unknown` are never promoted. A supported research candidate without a complete
matching production becomes `uncertain`, with its unverified value cleared and a
visible reason; original proposals remain in the retained run/verification report.
Clear employee as-of with a failed count. Preserve context fields required by the
financial model even when the amount is cleared. Preserve explicit zero and negatives.
Optional employee/event date rejection follows the component rules above.

The gate certifies retained source assertions, not universal real-world truth. It
cannot detect a false source or interpret prose outside the finite language. It does
not claim to discover contradictions in unrecognized unrelated pages. Recognized
numeric conflicts abstain; no proximity-based conflict inventory remains.

Existing schema validation, retrieval-time checks, evidence reference ownership,
source-ID-wide publication quarantine, redirect lineage, recent-event limits and
financial coverage invariants remain in force. JSON and Markdown render the same
final profile. No renderer or agent proposal validator decides semantic support.

## 9. Evaluation taxonomy and historical separation

Every adjudicated assertion case declares exactly one:

- `SUPPORTED_CONTRACT_POSITIVE`: source, candidate and provenance satisfy this contract;
  full correct support is required (or expressly declared optional-date removal).
- `OUT_OF_CONTRACT_TRUE`: a true target-company assertion outside the finite grammar;
  abstention is correct and is not a missed verifier positive.
- `UNSAFE_NEGATIVE`: false, contradicted, wrong-entity, mismatched or ambiguous proposed
  fact/component; no support for that component is allowed.
- `IDENTITY_INVALID`: identity conflicts with structural registry data; run rejection.
- `PROVENANCE_INVALID`: unsupported/invalid evidence envelope, source ownership,
  registry format or lineage; no publication based on that envelope.

Taxonomy is source/contract adjudication, not a label inferred from gate outcomes.
Wrapper/schema fixture defects are reported separately. In historical replay, a
provenance-rejected envelope does not demonstrate execution of the research grammar;
retain its assertion classification and report the unexercised layer separately.
Original inputs, gold, labels, results and failed runs remain byte-for-byte preserved.
New adjudications are a separate view with original labels and reasons retained.

Each literal grammar shape above needs >=3 positives, >=3 near-miss negatives and
>=2 true out-of-contract controls. Cover lexical alternatives, optional modifiers,
zero/sign/date boundaries, whole objects, clipped citations, extra tails and source
context. Historical, OMP, Astra v1/v2, Opus v1/v2 and prior holdout populations remain
separate; missing original envelopes/runners are missing prerequisites, not exact
replay or a license to merge reconstructed denominators.

After implementation freeze, a fresh author receives only this document and public
models/schema: 20 contract positives, 20 true out-of-contract cases, 30 unsafe negatives.
Freeze/hash before execution. Preserve defects and first outcomes; no reroll, lexical
patching or retrospective contract widening. If a safe finite implementation requires
open-ended lexical inventories, report redesign failure rather than grow them.
