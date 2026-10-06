# v0.1.1 final strict-contract boundary correction

**V0.1.1 STILL BLOCKED**

**BLOCKED — DO NOT RELEASE**

Baseline: `b521edf066e2d57b0339149eae7391ffc7e62e7c` on
`fix/v0.1.1-adversarial-corrections`. This is a bounded correction, not another
semantic redesign. The [strict publication contract](STRICT_PUBLICATION_CONTRACT.md)
is unchanged. No ordinary-language coverage, synonyms, providers, research budgets or
financial grammar were added.

Agent proposes broadly. Verifier publishes narrowly. Unknown semantics abstain.

## Implemented boundaries

| Boundary | Correction and exercised result |
| --- | --- |
| Retrieval kind/mode | Only `registry/registry`, `search_snippet/tavily`, `full_page/static`, `full_page/dynamic`. All other combinations reject. `RetrievedSource`, run validation and `build_profile` recheck the invariant, including unchecked `model_copy`. |
| Retained full-page multiplicity | More than one non-blocked full page per source ID rejects, even for the same URL. No favorable-page selection or merging. Snippets plus one full page remain valid. SourceStore's existing one-page replacement behavior is unchanged. |
| Finance across scales | Conflict amounts use exact Decimal exponent shifts into base units. Conflict key contains metric, currency, scope and both period bounds, not display unit. Equivalent scales do not conflict; differing values and equal-magnitude profit/loss do. Cited candidate value/unit matching remains as narrow as before. Decimal sign normalization does not round under ambient context. |
| Output destinations | Before payload writes, all four destinations are compared by resolved path and, when present, same inode. Output-output symlinks/hardlinks and existing output-input aliases reject with `ValueError`, preserving input and existing payload bytes. This is preflight, not transactional or race-proof filesystem storage. |
| Event language | English predicates accept only optional `on DATE`; Polish predicates only optional `w dniu DATE`. Both mixed-language forms abstain as out of contract. |
| Event exactness | Summary comparison uses NFC plus outer trim only. Internal double spaces, NBSP, escaped JSON labels and decoded exact titles are preserved; altered summaries abstain. |
| Registry citations | NFC/whitespace-normalized citation occurrence is required in the same referenced material, together with mapped-field and identity matching. A matching string in another material/field or a decoded string absent from retained escaped JSON is not evidence. NIP/name, duplicate-key and unsupported-format guards remain. |
| Markdown inline values | CRLF/CR/LF are flattened in the shared inline escaping helper. Profile and verification Markdown do not gain injected headings/lists from titles, values or rejected excerpts. JSON semantic strings retain their original characters. |

The SourceStore regression uses a real host-created Tavily snippet plus a same-ID static
page explicitly denying the offering. Untampered input withholds. Changing only the
snippet's `kind` to `full_page`, while retaining `fetch_mode=tavily`, rejects at run
validation and unchecked publication. A retained positive/retraction pair with valid
page modes also rejects by the multiplicity invariant.

## Local verification

All execution used an allowlisted environment and OS network denial, without provider
credentials or new live-company research.

- `uv run --frozen --offline pytest -q`: **683 passed**, 30 existing lxml
  `strip_cdata` deprecation warnings; warnings were not suppressed.
- `uv run --frozen --offline ruff check .`: passed.
- `uv run --frozen --offline ruff format --check src tests scripts`: **50 files** formatted.
- `uv run --frozen --offline mypy src`: passed, **16 source files**.
- Actual installed CLI boundary smoke: **26/26**, including source provenance, duplicate
  pages, scale equivalence/conflicts, event language/whitespace, registry normalization,
  CR/LF rendering, and symlink/hardlink/input-alias rejection. The unchecked SDK guard
  was also exercised directly. Input hashes and existing payload bytes were preserved.
- Actual offline review helper exercised a local `FunctionModel` interruption; no provider
  was contacted. Supported/OOC examples and historical snapshots remain separate.

First integration failures are preserved in external audit logs: a script-import
collection failure, formatting/lint/type issues, and three new test-fixture/expectation
errors. Corrections did not change historical inputs or expectations. They are not
independent holdout executions.

The exact final commit, changed-file inventory, isolated-clone logs and package hashes
are recorded outside the source tree in the final review package; no self-referential
commit hash is embedded here.

## Separate populations

| Population | Observed result / limitation |
| --- | --- |
| Canonical strict CLI matrix | **262/262**, including **97/97** contract positives; 64 true-OOC, 98 unsafe, two provenance-invalid and one identity-invalid controls. Zero unsafe/OOC support and zero accepted invalid identity/provenance. Original matrix inputs and expected outcomes unchanged. |
| Historical strict replay | **174 assertions: 160 correct, 14 unassessed**, no failed assessments. The 12 eligible positives are identity assertions, all correct; no eligible researched strict positives. Semantic-execution counters: 25 executed, 14 unexercised, 135 not applicable. |
| Utility replay, complete retained baseline run set | **0/13** gold researched claims supported: Asseco 0/6, SONEL 0/7. Zero supported observations, so precision denominator is zero and precision is undefined, not perfect. No new extraction or provider call occurred; embedded diagnostics belong to the old retained runs. |
| Retained Asseco CLI run | Partial profile; **0 researched facts published**. Four registry-backed identity fields remain supported. |
| Retained SONEL live-run CLI replay | Partial profile; **0 researched facts published**. Four registry-backed identity fields remain supported. The archived raw CompanyResearchRun was replayed, not reconstructed from a final profile. |
| Exact original adversarial v1 | External b521edf report says 0 unsafe / 65 negatives, 130 total inputs. Complete original inputs/runner are not locally supplied; **no post-correction exact replay claimed**. |
| Exact original adversarial v2 | External b521edf report says 0 unsafe / 40 negatives, 80 total inputs. Complete original inputs/runner are not locally supplied; **no post-correction exact replay claimed**. |
| Latest boundary/Astra-requested corpus | Report and per-case results are supplied, including 47/47 new semantic unsafe probes withheld and 60/62 paired positives accepted at b521edf. The referenced 124-execution corpus/evidence ZIP and runner are absent locally. Source excerpts/results are not full run envelopes; **no reconstructed exact replay claimed**. |
| Latest separate Opus strict corpus | User reports zero unsafe replay and all its strict positive controls accepted. Raw corpus and runner are unavailable locally; **not a new local measurement**. |

The external report identifies its 124-execution corpus by SHA-256
`a347bd9f3d0d0b968a589da73545ac412de4ff62fbb0536195f340cf4bfe4589`.
The accompanying evidence ZIP containing those inputs and the original 130/80 inputs
is a missing prerequisite. Separate vendor attribution is not established by the generic
report filenames. Known reproductions were added as local correction regressions; they
are not a substitute for replaying an entire external population.

Asseco/SONEL zero researched publication is strict abstention under ordinary retained
web prose, **not useful BI output**. It is not evidence that those companies lack the
reported activities. The complete baseline utility run set was selected explicitly;
the historical candidate utility directory lacks an Asseco run and only records its
capture failure. Those populations were not mixed.

Earlier **47/47, 5/19, 0/7, 1/13**, and older live-zero measurements remain unchanged
history under their earlier contracts. The [b521edf strict report](STRICT_CONTRACT_REVIEW.md)
is also a distinct snapshot, not overwritten by this correction.

## External fixture toolkit and holdout status

- [`scripts/strict_case_builder.py`](../scripts/strict_case_builder.py) owns synthetic
  registry material, identity evidence, timestamps, diagnostics, source IDs, unknown
  reasons and a valid baseline. Authors supply source assertion, candidate, target,
  classification, expected action and optional publication metadata.
- [`scripts/preflight_strict_cases.py`](../scripts/preflight_strict_cases.py) calls
  `CompanyResearchRun.model_validate_json` on every run and reports `VALID`/`INVALID`.
  It does not execute the verifier. Invalid boundary controls receive a separate
  manual-review annotation, never a semantic-pass claim.
- [Toolkit instructions](EXTERNAL_HOLDOUT_TOOLKIT.md) describe all fact families,
  explicit finance context, narrow boundary mutations and immutable authoring outputs.
- A separate restricted author package contains only the frozen contract, public
  models/schemas, builder/preflight, dependencies and minimal usage example/instructions.
  It excludes the parser, evidence gate, verifier, regression suite, old cases and results.
- The restricted package was exercised outside the repository: imports resolved to its
  copied public model; parser/gate/verifier modules were unavailable. The neutral example
  built and preflighted `VALID` with exit 0. A deliberately broken semantic envelope
  returned `INVALID`/exit 1 for its missing unknown reason. Neither is release holdout data.

The original **70-case holdout remains permanently FAILED FIXTURE CONSTRUCTION**,
SHA-256 `5028ddab490df792d35a7d4b8f7a69fb61d6b615dab6a901509cdba6a41fabca`.
It was not modified or rerun. All 70 intended probes were unexercised in its original
execution; the six raw expected rejections are not targeted-boundary proof.

**No fresh external release holdout has been supplied, frozen or executed.** The operator
has not self-authored one or renamed local regressions as independent evidence. The next
external author receives only the restricted package and should produce approximately
20 positives, 20 true-OOC, 30 unsafe, five provenance-invalid and five identity-invalid
cases. Preflight semantics first, freeze/hash, then exactly one verifier execution.
No edits after seeing outcomes. Release gates remain unmet until that evidence exists.

## Release hygiene and stop

Package version remains **0.1.0** because the user conditions the 0.1.1 bump on passing
code/tests **and** a fresh external holdout. CI formatting currently covers `src tests`,
while the exercised local gate also covers `scripts`; the conditional CI alignment and
optional action pinning are deferred, not silently claimed complete.

Hosted CI has not run on the exact final merge candidate. The configured push/PR workflow
requires a published commit, and this task forbids pushing. An isolated local clone is
separate evidence, not hosted CI.

The final review package contains full committed source, both requested diffs, separate
results and availability records, toolkit, original failed holdout, all check/clone logs,
and a complete SHA-256 manifest. It contains no invented fresh holdout or fabricated
exact replay result. No push, merge, tag or release is authorized.

**BLOCKED — DO NOT RELEASE**
