# v0.1.1 utility and evidence quality report

**Result: product utility is still not demonstrated.** This report records the corrective branch's frozen-source and fresh-source evidence without changing the historical populations or treating missing captures as model outcomes. The report is not a release, publication, or claim of general correctness.

The authorized comparison is between the approved start `a99b959c8eb510fd0526a301a23466a30067c9ec`, utility candidate `5c36e045a1f32336c403b0b254f1c6faa7cfe641`, and production final `7f781a035915a9372b306e82625611cd641b0e1b`. Tracked machine-readable results: [comparison](../examples/utility_v011/comparison.json), [first-loss ledger](../examples/utility_v011/loss-ledger.json), [fresh live summary](../examples/utility_v011/live-summary.json), [adversarial summary](../examples/utility_v011/adversarial-summary.json), and [independent assessment of the locked baseline output](../examples/utility_v011/assessments/locked-baseline.json). The earlier corrective findings and their preserved populations remain in [ADVERSARIAL_CORRECTIONS.md](ADVERSARIAL_CORRECTIONS.md); this report supplements rather than replaces that history.

## 1. What correctness defects followed v0.1.0?

The subsequent correction history documents concrete false-support, lost-positive, lineage, date, attachment, and compatibility defects. The original A1–A4 set covered incorrect meaning/currentness, financial sign/actuality, redirect publication/lineage, and observation-date conflicts. Later work found that a nearby recognized verb could incorrectly attach a customer's activity to the company; ambiguous legacy source-ID groups lacked provable URL lineage; and a bounded dated-financial-prefix construction caused legitimate current financial assertions to be missed. The correction-history report records their examples, before/after measurements, retained regressions, failed integration attempts, and limitations. Its historical populations and measurements are not re-scored here.

## 2. What actually changed?

The correction history records the A1–A4 repairs, the later predicate-attachment repair, legacy quarantine, and dated-financial-prefix repair. For the utility/evidence sprint specifically, the publication gate and extraction instructions changed in bounded ways:

- Legal-form equivalence is bounded and uses the longest matching form.
- Entity and predicate must attach to the same canonical source occurrence; finite activity, catalog, and sector assertion shapes are recognized. List-member evidence is assessed independently.
- One instruction iteration, about 50 words, asks for narrow literal current-activity values, excludes strategy/goals/history from current offerings, and prioritizes unread relevant official homepage/about/offer material over repeated discovery.
- A final correction removes irrelevant evidence pairs, including pairs from the same source but different excerpts. A separately named subject can reset an earlier conditional, but clipped or anaphoric conditions remain blocked. An explicit group financial subject is admitted without weakening period, currency, unit, scope, sign, or actuality requirements.

There were two utility correction cycles and one final independent-review correction cycle, with no further tuning. The first utility variant caused real regressions: a clipped conditional, a wrong legal-form prefix, and entity/predicate proof combined across different quote occurrences could become false-supported. That variant was rejected; its outputs remain in the external audit. Initial probe fixture/assertion mistakes are also preserved but are not product defects. Pipeline trace diagnostics were corrected to select exact `full_page` material, reconstruct canonical bounded source contexts, and pair entity and predicate at the same occurrence. Earlier excerpt-only/first-source traces are archived, not overwritten; the instrumentation correction changes no production code, gold, candidate, or publication outcome.

Production changes in this sprint are confined to `src/company_bi/agent.py` and `src/company_bi/evidence.py`. Dependencies, provider/model, budgets, schemas, financial-document parsing, and fetch/render/batch implementations are unchanged. A separate offline evaluator and behavior-focused regression tests were added.

## 3. What do the historical replay metrics say?

Historical frozen replay remains distinct from this sprint's utility cohort. The legacy-read correction restored historical replay and the offline helper to exit 0. The historical replay metrics match the retained `og154a-comparison.after_metrics`; the retained-real researched yield remains **0/7**, unchanged. See the historical metric table and explanation in [ADVERSARIAL_CORRECTIONS.md](ADVERSARIAL_CORRECTIONS.md#legacy-read-compatibility--extended-stage-a). Restoring partial-profile publication and registry facts was compatibility recovery, not new researched support or new live usefulness.

| Historical replay metric | Unchanged result |
| --- | ---: |
| Supported / registry / researched precision | 47/47 / 42/42 / 5/5 |
| Eligible researched recall / over-downgrade | 5/19 / 14/19 |
| Incorrect supported | 0 |
| Identity / identity-field correctness | 10/10 / 60/60 |
| Correct uncertain / strict unknown handling | 28/28 / 40/41 |
| Retained-real researched yield | 0/7 |

Earlier populations must also remain distinct: the prior completed usefulness pass had **4 fixed-source and 5 live attempts**, with zero researched supports. The current sprint had **4 fixed-source and 3 live attempts**. Neither population overwrites the other, and neither changes the historical retained-real denominator.

## 4. What was the new independent/frozen real-source evaluation?

The sprint locked a new gold set of **13** source-backed observations: six for Asseco Poland and seven for SONEL. It covers three qualitative fields. Gold was defined from real source material before prediction and independently reviewed. The comparison evaluates whole output values, not just whether a phrase appears in a source: supported precision therefore requires independent whole-value assessment.

For reproducible conservative credit, the source-language Contract A uses literal gold-anchor matching after Unicode NFC normalization, whitespace normalization, and case-insensitive word-boundary matching. This lexical rule is a measurement rule, not a semantic entailment or truth oracle; whole-value support is independently assessed. The frozen prediction comparison applies the final gate to the retained baseline outputs and candidate outputs. It is separate from fresh retrieval/extraction, the earlier history's frozen replay, and adversarial probes.

The frozen baseline records no citation first-loss events across the 13 gold observations and no span-only rescues. All gold spans fit within the existing 16,000-character read surface; unread-source losses were not truncation losses. Span-backed schema migration was therefore evaluated and rejected, not implemented. These facts do not establish that citations or source selection are generally reliable; the later live Asseco citation failure remains an explicit limitation.

## 5. Was there measured real utility improvement?

**Yes, on the locked retained-output comparison, narrowly; no, on the sprint's fresh live outcomes.** The actual locked baseline outputs on the final gate move from **0/13** to **1/13** correctly supported gold claims: Asseco is **1/6**, SONEL **0/7**. The one Asseco business-description value was independently checked against its cited full-page business statement. The measured candidate support has **1/1 independently assessed supported values** (precision 1/1); this denominator of one is far too small to imply broad precision. The ledger classifies the locked replay's first losses as follows:

| First-loss stage | Locked baseline | Locked candidate on final gate |
| --- | ---: | ---: |
| Source presentation | 3 | 3 |
| Extraction | 2 | 2 |
| Value normalization | 1 | 1 |
| Citation | 0 | 0 |
| Entity attachment | 7 | 4 |
| Polarity/modality/time | 0 | 0 |
| Other gate rejection | 0 | 2 |
| Published gold claims | 0 | 1 |

The count reduction at entity attachment is not itself utility; the one published, independently assessed whole value is the narrow positive result. The ledger assigns the locked candidate's two other gate losses conservatively rather than attributing them to an unproven specific cause.

Fresh extraction did not reproduce that gain. SONEL produced **0/7** supported gold outcomes. Asseco research ran, but capture failed with a `NameError` and lost the output and usage; six gold outcomes are therefore unobservable, not observed misses. There was no reroll. The retained-output aggregate reports **0/13**, including the absent Asseco output, and is **not** a complete fresh-model recall estimate. In the fresh loss ledger, the observed SONEL outcomes are four entity-attachment losses and three other-gate losses, with six Asseco outcomes unobservable. The diagnostic stage assignments are based on actual candidate/profile and canonical-context inspection, not inferred from literal matching alone.

All three new live attempts—Asseco Poland, SONEL, and APATOR—ended with **zero supported researched observations and no useful sections**. Asseco failed output evidence validation after the allowed repair; SONEL completed as partial with no support; APATOR completed as partial with no support after structured-output/fetch failures. Exact per-attempt status and failure details are in [live-summary.json](../examples/utility_v011/live-summary.json). The sample gate of at least three real facts across at least two sections was not met. No representative-success artifact or README success claim was created.

The separate adversarial population recorded **43/43** checks passing, including **15/15** positive controls, zero observed false supports, and zero citation failures. Initial invalid fixtures/assertions are preserved in the external audit; the final reruns are regression checks, not untouched holdout measurements. These sampled offline checks are evidence about those cases, not a replacement for real-source usefulness.

Observed production-final verification recorded 377 pytest passes, 107 adversarial subset passes, Ruff success, formatting success on 36 files, and mypy success on 14 files. Historical replay, utility modes, and the offline helper exited 0; guarded external calls were zero. The actual batch resume removed a stale false support, generated exact JSON/Markdown, and a second resume made no rewrite; it made no registry/research calls and preserved original run bytes. These are observed production-final results only: **isolated verification of the exact final commit remains separately recorded in the external audit after the documentation commit and is not claimed as passed here.**

## 6. What remains unsupported?

The target utility threshold remains unmet, and one locked success does not show repeatable or representative benefit. Fresh SONEL yielded nothing; the failed Asseco capture prevents a complete fresh two-company estimate. The current three-live sample also provides no usable researched output. Finite source-language predicates and entity boundaries can conservatively reject real prose; other source selection, extraction, provider, retrieval, and capture failures remain. The 43 probe outcomes sample boundaries rather than exhaustively testing entailment or real-world source diversity. The sprint did not measure population-wide utility or precision.

Across all sprint-native attempts, observed usage was **39 model requests, 311,079 input tokens, and 8,962 output tokens**, plus **one attempt with unmeasured usage**. Cost is unavailable, not zero. See the [comparison record](../examples/utility_v011/comparison.json) for totals and the [live summary](../examples/utility_v011/live-summary.json) for per-company failures and usage.

## 7. What claims are explicitly not made?

This report does **not** claim general correctness, population-level precision, representative utility, complete fresh-model recall, a remote-CI result, release readiness, or a v0.1.1 publication. It does not claim that the historical 0/7 yield improved, that a zero observed false-support count proves zero risk, or that the probe suite is an untouched holdout. It makes no claim that one independently checked support generalizes, that matching literal text proves full-value truth, or that partial profiles are useful BI output. The measured result remains **PRODUCT UTILITY STILL NOT DEMONSTRATED**.

## 8. Offline verifier productization after the accepted utility experiment

**Company BI v0.1.1 does not claim demonstrated autonomous research utility. Its demonstrated artifact is the evidence-backed verification/publication boundary around agent-produced research.** This follow-up exposes existing behavior; it does not improve recall, change publication rules, or replace the experiment above.

The first-class zero-key interface is:

```sh
uv run --frozen company-bi verify examples/verification/controlled-financial-sign.json --output-dir outputs/verification
```

The command validates a retained `CompanyResearchRun`, calls the existing `build_profile`, uses the existing profile renderers, and writes `profile.json`, `profile.md`, `verification.json`, and `verification.md`. The typed delta records candidate/final states, values, field context, reasons, evidence references, and changed paths. Financial metric/period/currency/unit/scope and employee/event dates remain explicit. Retained source metadata covers candidate and final references, including removed citations and blocked provenance; full retained page bodies are not copied into the report. The input basename and byte SHA-256 identify the supplied artifact.

Decisions describe the gate result, not another semantic implementation:

- `accepted`: the supported claim survives, possibly with a narrowed evidence list.
- `downgraded`: a supported candidate becomes non-supported; a removed final value is shown as null, not copied from the candidate.
- `cleared`: an asserted value or context component is removed without a state downgrade, such as an unverified occurrence date on an otherwise supported event.
- `preserved`: an uncertain/unknown candidate remains non-supported. This is not acceptance.

Gate reasons remain visible. A rejection can reflect insufficient context, unresolved scope, ineligible evidence, a contradiction, or a provenance limitation; it is not automatically labeled a hallucination. Candidate assertions and unverified evidence are distinguished from final support in Markdown.

Exit 0 means verification completed, not that every claim was accepted. A valid run marked as failed research produces only the two verification files, `not_published`, retained diagnostics, and no invented profile or deltas; exit 1. Invalid JSON, invalid references/identity evidence, file errors, and input/output collisions fail with exit 2. Failed-run output refuses pre-existing profile artifacts instead of presenting a mixed old/new bundle. Verification neither fetches sources nor authenticates arbitrarily edited input or proves publisher truth.

### Demonstrated interface behavior

| Input population | Observed result |
| --- | --- |
| Controlled financial-sign example | Current cloud services accepted; candidate +PLN 10 million net result downgraded and cleared against explicit standalone net loss |
| Controlled planned-activity example | Planned cloud accounting software not published as a supported current offering |
| Controlled current-service example | Explicit current cloud services remain supported |
| Existing real retained Asseco run | One accepted business description, three downgraded fields, three preserved unknown observations; partial profile |

The [real retained verification report](../examples/review/asseco-poland-verification.md) is generated from the committed [Asseco input](../examples/utility_v011/runs/baseline/asseco-poland.json), not manually authored and not successful BI. Report decisions count fields/financial observations; they are not the atomic gold-claim denominator. The two-company fixed-source utility result remains **1/13**, with zero observed incorrect supports, and the three fresh live results remain zero. No new companies, model/Tavily/MF research, rerolls, or recall tuning occurred.

At the productization stage, README led with the verification boundary and the reviewer guide put accepted/rejected output inspection before large metric tables. That stage's conclusion that coverage was the current bottleneck applied only to then-exercised regression sets; subsequent independent blockers supersede it. The present candidate has both unsafe acceptance and conservative rejection, as documented in section 11.

### Executed productization checks

- Full pytest: **390 passed**. Adversarial subset: **120 passed**, included in 390. The new interface contributes 13 behavior tests, including actual financial/planned rejection, preserved states, partial date clearing, exact final evidence, deterministic real reports, invalid/failed inputs, file safety, blocked network/service entrypoints, and Markdown final-value/injection boundaries.
- Ruff lint passed; format check passed on **38 Python files**; mypy passed on **15 source files**.
- Historical replay, both v0.1.1 utility modes, and the existing offline reviewer helper exited 0. Historical metrics and both utility count objects matched the accepted results structurally; no gold or publication behavior changed.
- The actual CLI produced the four files for all three controlled examples and the real retained run under OS network denial, without credentials. Failed-run and invalid-JSON CLI scenarios returned the required 1 and 2, without fabricated profiles.
- After installation, the controlled financial demo took **1.374 seconds** in the measured Darwin arm64 development environment; the other controlled/real commands took 0.762–0.790 seconds. This is one observed run per final command, not a latency guarantee or installation-time promise.
- A read-only interface review caught a missing gate import before the first recorded successful demos. Initial static checks then caught line-length and tuple-typing defects; they were corrected without changing the gate. Those findings and command outputs remain in the external productization audit.

The exact final local commit's isolated README/reviewer-guide replay is recorded separately after this documentation is committed; this section does not claim a future run passed. The earlier utility failures, unobservable Asseco capture, small denominators, finite-language limits, and unresolved retrieval/security limitations remain part of the engineering record.

## 9. Final independent quality audit

The final audit started from `d9a8ababaa37a4073f5c3bca49b9e3a42df80c71`, with a clean corrective branch and byte hashes for all 105 tracked files. Baseline verification passed: 390 tests, including the 120-test adversarial subset; Ruff, mypy and formatting; historical replay; both utility modes; and all four verifier demonstrations. Repeating the demonstrations produced identical bytes for all 16 output-file comparisons.

**The new paired corpus is not green.** Independent authors worked from the public contract, exported schema and synthetic template, without inspecting gate branches or existing tests. The corpus contains 57 negative cases, 57 affirmative controls and six separately counted interface-integrity cases.

| New paired population | Observed result |
| --- | ---: |
| Negative unsafe assertions withheld | **57/57** |
| Negative cases meeting every expectation, including preservation of valid event content | **51/57** |
| False-supported negative cases | **0** |
| Positive controls accepted with their complete value/context | **15/57** |
| False-rejected positive controls | **42/57** |
| Separate interface-integrity cases | **6/6** |
| Candidate-to-final report inconsistencies | **0** |

The six additional negative-case failures are collateral losses: the gate removes an invalid occurrence date but also clears otherwise valid event content. They are not false supports and are not hidden inside the 57/57 safety count. Positive acceptance by family is Polish language 0/8, English language 0/8, entity attachment 6/10, financial observations 0/14, events 0/8, and provenance 9/9. There is no combined accuracy score. These controls show that the gate is not simply rejecting everything, but they also expose substantial fail-closed undercoverage.

### Corpus integrity and limits of blinding

An initial pre-result review found a missing group-affiliation premise; it was added to both financial pair members before execution. Two revenue pairs were also added before execution to cover the explicitly requested revenue/forecast boundary. Original generators and inputs were archived.

The first full execution then prompted a stricter, outcome-blind fixture review. That reviewer found that all 16 language pairs used generic actors without connecting their retained page to the resolved company. The original independent author added only a shared publisher/NIP/own-activities header. Every assertion sentence, candidate value, quoted excerpt, ID and expected state remained unchanged; a second independent review confirmed the attribution premise. The original corpus and failures remain immutable, and the attributed version was separately hashed before execution. **This repaired population is not an untouched holdout.** Both versions produced the same counts; the attributed version above has valid target-company premises. Missing attribution was a fixture defect, not a reason to weaken the production identity gate.

The actual CLI retained every input, exit status and output. Its 113 published profiles, one failed-input diagnostic report and six input rejections were compared with normalized candidates and final JSON. The checker parsed actual verification Markdown roles and JSON value/context blocks, rather than treating candidate text anywhere in the document as final support. Additional, explicitly non-blind CLI probes exercised a supported event losing only its occurrence date and a mixed product list losing an unsupported member; both passed. All four decisions were exercised.

### Findings and bounded disposition

- **P2 — language/entity undercoverage:** ordinary affirmative wording, pronoun attribution, Polish inflection and unrecognized relations lose valid observations. The attributed controls remain failures; no synonym list, relaxed identity rule or general semantic engine was added.
- **P2 — financial undercoverage:** natural-language reporting intervals and financial prose fall outside the current numeric-date, explicit-scope and bounded reporting grammar. The legitimate zero, signed-loss and decimal controls remain visible failures of the complete observation path; they are not relabeled invalid or fixed by broadening parsing.
- **P2 — event undercoverage and collateral clearing:** valid event summaries/date relationships are lost, including the six date-negative cases whose remaining event content should survive. Broader event/coreference interpretation is explicitly deferred.
- A proposed adjacent-forecast financial fix was **not justified**. A diagnostic pair using the existing numeric-date and explicit-standalone contract accepted the actual EUR 31 million and blocked the adjacent EUR 34 million expectation. The original cases had already failed date/context checks; a fallback rejection reason mentioning forecasts did not establish that forecasts caused their publication loss. No speculative qualifier change was made.

No production, dependency, schema, historical gold, retained utility input, or existing test was changed by this audit. No corrective implementation cycle was attempted: the reproduced remaining losses require a separately bounded semantic/coverage contract rather than an evidenced small safety repair. This is an explicit deferral, not a green blind-suite result.

The valid fresh public-only reviewer answered all ten understanding questions without material misunderstanding; no README expansion was warranted. Supply-chain review found mutable first-party `actions/checkout@v7` and `actions/setup-python@v7` tags, but no inspected policy requiring their SHA pinning or reproduced reproducibility break. `setup-uv` is SHA-pinned, Actions permissions are `contents: read`, checkout credentials are not persisted, Python 3.12 selections agree, and offline lock validation passed. No dependency upgrade or new pinning policy was introduced; remote CI was not run.

Final working-tree verification repeated **390 repository passes**, including **120 adversarial subset passes**; Ruff, mypy (15 source files) and formatting (38 files) passed. Historical replay, both utility modes, the offline reviewer helper, all four demos and the two additional interface CLI probes exited 0. Historical metrics and both utility count objects remained unchanged. The attributed blind CLI again had 72 passing cases and 48 failures; its independent pytest driver had 74 passes and 48 failures, including two corpus checks. All **454 emitted blind output files** were byte-identical to the preceding attributed-corpus run. The offline helper reported zero external/provider calls and one deliberately local `FunctionModel` interruption.

The external `company-bi-v011-external-review.zip` contains the actual tracked checkout, v0.1.0-to-final patch, complete blind generators/corpora/driver, original failures, repaired-corpus results, independent reviews, command logs and file hashes. Final checks and the one exact-final-commit clean-clone run are recorded there after commit creation. The blind driver has **74 passes and 48 failures** (120 cases plus two corpus checks), separate from the repository suite; the failures are retained, not skipped or converted to expected passes. No new live research, model/provider, Tavily or MF calls were made. **External review is warranted; release is not recommended.**

## 10. Overnight blocker remediation: preserved starting evidence

Independent reviews of `aac9c9fefdad23d33e79f7234687e31d76fcfcdc`
found ordinary false-supported facts beyond the earlier exercised populations.
Publication safety is therefore an active correction target, not a solved
problem behind research coverage. This run performs no new live research and
does not rewrite the historical gold, retained inputs, or failed audit results.

| Separate reviewed population | Negatives | Unsafe accepted | Positive controls | Fully accepted |
| --- | ---: | ---: | ---: | ---: |
| Existing OMP blind corpus | 57 | 0 | 57 | 15 |
| Astra reported original population | 65 | 18, including identity | 65 | 61 |
| Opus reported original population | 53 | 16 facts + 1 identity | 47 | 24 |

OMP additionally had six negative preservation failures and six passing
interface-integrity cases. These are not additional ordinary negatives.
Astra's report and result summary were available locally, but its original
130 input envelopes/runner were not found. The original Opus corpus and full
report were unavailable; only the operator-supplied findings were available.
Local Astra/Opus reproductions consequently have their own denominators and
are not labeled as exact replays or fresh unseen holdouts.

Before production edits, the new minimal actual-CLI population contained
33 negatives and 23 affirmative controls: 27 ordinary unsafe facts and four
identity contradictions were accepted; 16 controls passed completely.
The two other ordinary negatives were already withheld. The corresponding
pytest module also includes two unchecked-`model_copy` identity cases; these
are not added to the 56-case CLI denominator.

The first shared-contract correction reduced minimal ordinary false supports
to two but did not clear the gate: guidance/outlook remained unsafe, two
positive controls were rejected, and the full suite recorded 420 passes and
28 failures, including employee/financial runtime regressions. Its outputs and
source snapshot are preserved in the external remediation audit rather than
overwritten by the next cycle. Astra local reproductions passed 40/40 at that
intermediate point; Opus local reproductions passed 36/38. Neither result
changes the original reported review denominators above.

## 11. Frozen remediation candidate: BLOCKED

**Release remains BLOCKED, not cleared.** Production implementation is frozen at `6a3a1156f7156708dcbd8c4347baafc83fd209b1` after two semantic cycles per family. The freeze is not a successful release gate; no third semantic cycle is authorized. The identity consistency and canonical context/ownership improvements are real, finite gains, but do not clear the remaining defects. The observed source records are the external audit's `after/known-populations-before-freeze.json`, `KNOWN_BLOCKER_MATRIX.md`, `after/cycle2-integrated-full-pytest.json`, and `cycle-ledger.json`.

### Independent populations remain distinct

| Population | Observed result |
| --- | --- |
| Minimal actual CLI, post-cycle 2 | 56/56 expectations: all 33 negatives withheld; all 23 affirmative controls fully accepted |
| Local Astra reproduction | 40/40; reconstruction, not exact replay of original |
| Local Opus reproduction | 38/38; reconstruction, not exact replay of original |
| Integrated OMP CLI | 72 passed / 48 failed; 57/57 negatives withheld, six negative preservation failures, 15/57 positive controls fully accepted, interface 6/6, report mismatches 0 |
| Full repository pytest | 444 passed / 4 failed |

The minimal CLI includes 33 negatives and 23 controls; its two additional unchecked-`model_copy` pytest identity cases are outside that CLI denominator. Original reported review populations are not reproduced results: Astra reported **65 negatives / 18 unsafe** and **65 positives / 61 complete**; Opus reported **53 negatives / 17 unsafe** (16 facts plus identity) and **47 positives / 24 complete**. The original Astra inputs/runner and original Opus corpus/full report were unavailable; local reproductions have separate denominators. Do not combine populations or recast reconstructed results as original replays.

The exact frozen-code local checks also observed Ruff exit 0, format check exit 0 across 39 `src`/`tests`/`scripts` files, and mypy exit 0 across 15 source files. These checks do not override the failing full suite or establish release readiness.

### Residual release blockers and historical limits

The existing financial negative with a target qualifier **after the amount** regressed from baseline withheld to current unsafe supported. Its actual-revenue positive remains correct: baseline pair 2/2, current pair 1/2. This is a known release blocker, not an unobserved risk. The other three full-suite failures are the positive current assertion after planned contrast and two frozen dated-employee cases. No expectation or historical gold was changed.

The historical evaluator exited 0, but its current output differs from the preserved historical population: supported **46/46** (historical 47/47); registry **42/42** unchanged; researched **4/4** (historical 5/5); eligible researched recall **4/19** (historical 5/19); over-downgrade **15/19** (historical 14/19); retained-real researched yield **0/7** unchanged. These are two separately labeled result sets, not revisions to old gold. Locked utility remains **1/13 supported, 0 incorrect observed, 4 uncertain, 8 missing**. The fresh retained view is SONEL **0/7** and Asseco **6 unobservable**; it is not complete fresh recall. Earlier utility, historical replay, OMP, Astra, Opus and minimal CLI populations must remain separate.

The known identity checks establish detectable internal consistency, not provenance authenticity: there is no cryptographic ledger authenticity, and a coherently forged ledger is not excluded. The verifier does not authenticate publishers or establish truth. Adversarial evaluation measures both unsafe acceptance and conservative rejection; passing a selected negative set alone is not a general safety guarantee, and conservative rejection is a real quality loss.

The final frozen-code local commands reproduced the full suite at 444 passed / 4 failed (exit 1) and the overlapping adversarial subset at 176 passed / 2 failed (exit 1); these overlapping counts must not be added together. The independent OMP pytest driver reported 74 passed / 48 failed; it is a distinct population from the 72/48 actual-CLI run. Historical replay and both utility modes exited 0. Four actual verifier demos each exited 0; the offline reviewer helper exited 0 with zero external/paid calls and a local `FunctionModel` only. These local results do not constitute remote CI or a clean-clone result.

Clean-clone verification remains unobserved. No clean-clone success, CI success, or release clearance is asserted. No live research, provider/model, Tavily or MF calls were made for this remediation.

## 12. Fresh post-freeze holdout: adverse, release remains blocked

A fresh independent author generated 27 pairs / 54 cases across nine categories after the implementation freeze. The raw input was hashed before validation. Two genuine fixture-construction defects were repaired with originals preserved: the `run.complete` wrapper affected all 54 cases, and an additional list-nesting defect affected six. Source text, scalar values, and expectations were unchanged; corrected envelope/schema errors were zero. The production CLI was executed once against the corrected saved population.

| Holdout measure | Observed result |
| --- | ---: |
| Ordinary negatives withheld without unsafe support | 24/24 |
| Identity contradictions accepted | 0/3 |
| Negative event-content preservation failures | 3 |
| Ordinary positive controls fully accepted | 0/24 |
| Identity positive controls fully accepted | 3/3 |
| Total expectations met / not met | 27/54 / 27/54 |
| Corrected report-integrity mismatches | 0 |

This result does **not** establish useful safety or generalization: although no unsafe assertion was accepted in these 27 negatives, all 24 ordinary positive controls were rejected or incomplete, and three negative cases lost valid event content. Identity controls alone do not compensate for broad conservative rejection.

The original checker reported 48 false Markdown mismatches because it compared raw LF against the renderer's visible escaped newline. The external checker defect was corrected and the same saved CLI artifacts rescored; there was no CLI rerun and no code or corpus outcome tuning. Original raw measurements remain preserved. No second micro-holdout was generated: no post-freeze production correction was authorized and no reroll occurred. The earlier target-qualifier safety regression already triggered the two-cycle BLOCKED stop. Package version remains **0.1.0**; this evidence does not authorize v0.1.1 release or version hygiene.
