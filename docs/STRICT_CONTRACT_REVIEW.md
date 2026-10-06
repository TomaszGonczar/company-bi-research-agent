# Strict-contract candidate review

## Decision

**BLOCKED — not approved for release.** The architectural contraction is implemented
and the local canonical matrix is green. Independent holdout acceptance is **not
established**: the fresh author's envelopes failed model-state validation before the
intended probes. No replacement holdout, repaired rerun, post-holdout production change,
push, merge, tag or release was performed.

This is a new contract, not a claim that the earlier heuristic candidate became a
successful broad-coverage research product. The norm is
[STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md); taxonomy and historical
label corrections are in [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md).

## Architecture and surface

- `assertions.py`: one bounded whole-retained-page parser. Exact legal name, opaque JSON
  quoted labels, finite predicates and modifiers, no ignored prefix/tail.
- `evidence.py`: source eligibility, whole-unit citation coverage, exact proposed-value
  matching, recognized numeric conflicts, optional-date removal, and profile assembly.
- `models.py`: structural MF `result.subject` mapping or the explicitly recognized
  existing host snapshot. Comments, archived fields and arbitrary equal strings cannot
  establish another identity field. Unknown formats reject identity publication.
- `evaluation.py`: explicit five-class adjudication; declared-positive eligibility,
  value/context checks, separate identity/research denominators, and unexercised
  envelopes instead of manufactured semantic successes.

Removed sentence/proximity windows, inferred subjects/aliases, lexical qualifiers and
candidate-term/catalog inference, financial nearest-number/component assembly, and
neighbor-event date selection. Their replacements are the documented complete
productions and typed `TextObservation`, `EmployeeObservation`, `FinancialObservation`
and `EventObservation`; old logic was not moved into another helper module.

Qualitative publication requires quoted complete labels. Employment accepts exact
integer counts only. Finance accepts one standalone observation with metric, actuality,
sign, amount, one of PLN/EUR/USD, unit and both ISO period bounds. Events require a
complete quoted-object assertion and source-owned publication metadata. Incorrect
optional employee/event dates can be cleared without discarding independently verified
content. Real prose, tables, groups, unquoted labels and surrounding paragraphs normally
abstain. Retrieval must not clip pages to manufacture compliance.

## Actual code contraction

Whole-module physical lines; no minification or relocation discount. The audit contains
per-file hashes and nonblank/noncomment counts (including docstrings).

| Scope | Before `66dbbc89` | After | Reduction |
| --- | ---: | ---: | ---: |
| `evidence.py` | 2,864 | 497 | 2,367 / 82.65% |
| Entire publication core: evidence + models + new assertions | 3,701 | 1,514 | 2,187 / 59.09% |
| Expanded semantic surface, also including agent + evaluator | 4,964 | 3,084 | 1,880 / 37.87% |
| All production Python modules | 7,425 | 5,545 | 1,880 / 25.32% |

Counting the complete evaluator includes its new taxonomy/adjudication code; the result
is not an `evidence.py`-only reduction claim. Unchanged schema/lineage code is included in
both whole-model counts.

## Canonical verification

The matrix has **32 literal predicate shapes**, each with three positives, three unsafe
near-misses and two true out-of-contract controls, plus six independent context/registry
controls. It exercises complete labels, modifiers, employee zero/dates, financial
sign/unit/period binding, event context, identity mapping and provenance.

Actual installed CLI: **262/262 passed**; **97/97 contract positives** supported;
64 true out-of-contract cases abstained; 98 unsafe, two provenance-invalid and one
identity-invalid controls satisfied their expectations. No unsafe support, OOC support
or accepted invalid identity was observed in this matrix. These are authored regression
controls, not an untouched independent population or real-world precision estimate.

Before implementation freeze: **621 pytest tests passed**, Ruff check and format check
passed, and mypy passed for 16 source files. Thirty existing lxml `strip_cdata`
deprecation warnings remain; they were not suppressed.

Actual smoke paths covered the installed `company-bi verify` command for a supported
quoted assertion, an unquoted true assertion, a qualified unsafe assertion, and a
comment-only identity-address claim. Exit codes were respectively 0, 0, 0 and 2;
researched states were supported, uncertain and uncertain, while the invalid identity
emitted no profile. JSON and Markdown were inspected. The public offline reviewer
script also ran, including the actual local `FunctionModel` interruption path, without
provider calls and under OS network denial.

Pre-freeze corrections were recorded, not erased: the initial matrix had an expectation
nesting error and two missing-amount fixtures; code corrections covered the documented
English `the` literal and preserving count evidence after clearing a wrong employee
date. First outputs remain archived. No lexical inventory was expanded to close them.
Active legacy tests retain truth/unsafe distinctions or use canonical fixtures when
exercising provenance rather than the old language contract. Original tests, gold,
corpora and earlier failed results are retained separately.

## Separate historical replays

These populations are not additive and do not replace unavailable original reviews.

| Population | Strict-contract observation |
| --- | --- |
| Original repository suite | 12 original cases / 174 original gold-claim checks: 160 correct, 14 research checks unassessed after envelope rejection; 12/12 eligible identity positives; no eligible researched strict positives. |
| OMP original 120 | 13 identity/provenance boundary expectations met; 107 research probes unexercised because their registry fragments are outside the recognized formats. |
| Astra local reconstruction 40 | 8 assessed expectations met, including two retained Asseco identity positives; 32 research envelopes unexercised. Not the original 130. |
| Opus local reconstruction 38 | 2 assessed expectations met, including one retained Asseco identity positive; 36 research envelopes unexercised. Not the original 100. |
| Previous fresh holdout 54 | 6 boundary expectations met; 48 research envelopes unexercised. Five wrong-company former positives are explicitly unsafe, not false rejections. |
| Original Astra v1 / Opus v1 | Complete original envelopes/runners unavailable; no exact replay claimed. |
| Separate v2 review | Report/results/excerpts available; complete 80 original envelopes/runner unavailable and distinct Astra-v2/Opus-v2 attribution unproven. No exact replay claimed. |

The repository replay's 174 checks are **claim checks within 12 cases**, not 174
independent companies. Its identity/research split is 72/102 checks; 12 eligible
identity positives are from the actual Asseco/LPP/Orlen host snapshots. Controlled
unheaded `Registry identity: ...` material is not a valid strict registry format.
The 14 unassessed research checks are not credited as semantic abstention successes.

Two local Astra identity controls were initially misclassified as unsupported registry
prose; source inspection showed actual valid host snapshots. A local Opus control also
had a root-identity path instead of a fact path. Corrected views and records were saved;
the **same saved CLI outputs** were rescored, without rerunning or changing input runs.

The previous holdout's original labels/results remain immutable. In addition to the
five wrong-company positive errors, its three source-reported negative net-result
values correctly match loss/deficit magnitudes; their negative original labels and
source-backed true-OOC adjudications are both retained.

The v2 reviewer-reported 20/40 unsafe and 34/40 accepted observations, and its reported
old-population replay, remain external historical reports—not new local results.
Earlier **47/47**, **5/19**, **0/7**, **1/13**, and earlier live zero-support results are
unchanged earlier-contract evidence. No new live-company research was performed.

## Fresh independent holdout: fixture failure, not a semantic pass

Production and the normative contract were hash-frozen before commissioning a new
context. The author received only the contract and public validation/serialization
JSON schemas, not implementation, old cases, tests or outcomes. Public JSON schemas do
not encode every cross-field Pydantic validator; the restricted authoring package did
not supply those public validator implementations. That input-contract gap and the
author's missing identity evidence are fixture-authoring failures, not a verifier
success. They are preserved rather than repaired into an independent-pass claim.

The frozen corpus has 70 authored labels: 20 contract positives, 20 true-OOC labels,
and 30 negative controls (24 unsafe, three identity-invalid, three provenance-invalid).
SHA-256 of its unchanged `holdout.json`:

```text
5028ddab490df792d35a7d4b8f7a69fb61d6b615dab6a901509cdba6a41fabca
```

It ran **once** through the real CLI. All 70 envelopes were rejected before their
intended checks. Supported KRS/REGON facts lacked evidence; unknown facts lacked a
missing-data reason. Consequently **zero valid independent positives were exercised**.
The raw checker records 6 expected rejections and 64 failures, but those six are not
proof that the intended identity/provenance cases reached their targeted boundary.
Zero emitted support here is not semantic safety evidence.

Source-only review also found label defects: SC-033/034 propose exact employee counts
from approximate wording; SC-035 turns 2.4 million into value 2,400,000 with unit
`millions`; SC-040 is syntactically a documented Polish event production rather than
out-of-contract wording. These observations are recorded separately, without replacing
original labels, expected results, source text or candidates.

No repaired replay or second corpus was generated. No production file changed after
freeze. **The independent holdout acceptance criterion remains unmet.**

## Reproduction and remaining limitations

Follow [REVIEWER_GUIDE.md](../REVIEWER_GUIDE.md) for the portable zero-key commands.
The external strict-contract review package contains exact-final-commit source, both
requested diffs, immutable inputs, all failed and final results, author inputs/outputs,
freeze records, complete payload hashes and isolated-clone logs. Clone and archive
verification records are external artifacts so adding their final commit/hash does not
create a self-referential source commit.

Release remains blocked by missing independent semantic evidence and unavailable
original external replay prerequisites. The implementation is a finite assertion
recognizer, not publisher authentication, universal natural-language truth checking or
a claim of useful live-company coverage. It cannot infer contradictions from arbitrary
unrecognized unrelated pages. The inherited network/DNS TOCTOU limitation also remains.
