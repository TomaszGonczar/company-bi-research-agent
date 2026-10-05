# Adversarial corrections against d4423da

Local corrective package for possible v0.1.1; not a release or a claim of green CI. Reference commit: `d4423da54ed84cfa20104dee5cb8cc5decde19bd`. Branch: `fix/v0.1.1-adversarial-corrections`.

The bounded publication contracts are in [EVIDENCE_MODEL.md](EVIDENCE_MODEL.md#assertion-qualification). The original corrections introduced no new model/provider, dependencies, research instructions, budgets or financial-document parser. Extended Stage C later measured exactly two instruction-only changes, documented separately below; provider, dependencies, budgets and publication rules stayed unchanged.

The original A1–A4 measurements below were recorded for corrective commit `17fdc9d9cfc4e4a3dccf8f5e77e5ca5ecc9f4ffd`. Later sections extend that history with the attachment, legacy compatibility, fresh-context review and usefulness measurements; they do not overwrite the earlier measurements.

**Latest compatibility result:** the subsequent legacy-read correction below restores local replay and the offline reviewer helper without trusting unproven legacy material. The earlier exit-1 measurements remain historical evidence, not the current result. No remote CI or release is claimed.

**Latest product result:** four fixed-source extraction attempts and five live attempts published zero supported researched observations. The practical usefulness target was not met. The [actual live PARTIAL example](../examples/review/sonel-20261005.md) is evidence of that limitation, not a successful BI demonstration.

## Evidence populations and preservation

These measurements are deliberately separate:

1. **Original independent cross-check:** 15 actual-package publication scenarios. Its 33 surviving scripts/output files were preserved byte-for-byte with a SHA-256 manifest before branch or code changes. Regenerated outputs are not labeled as originals.
2. **Regression-first adversarial set:** 40 publication-path cases measured against unchanged `d4423da`; 21 failed and 19 passed. Two earlier redirect-fixture assembly attempts were preserved but excluded from product measurements: an incomplete Scrapling response double and a citation validated before its matching ledger was installed.
3. **Expanded adversarial suite:** those same 40 cases plus 13 supplemental boundary/control cases identified during review and integration. Full-run validation, `build_profile`, JSON serialization and Markdown rendering are exercised; redirect transport is mocked, not the publication gate.
4. **Predeclared offline holdout:** ten separately recorded inputs, six negative and four positive. A separate past-tense dated-employee smoke also exercised actual publication.
5. **Frozen replay/contract evaluation:** the original dataset, gold, retained snapshots and historical baselines, without relabeling or mutation. This is not fresh-agent performance.

The external audit bundle is named `d4423da-corrective-20261004`. Its directories distinguish `original-crosscheck/`, `before/`, first integration `after/`, second integration `after-final/`, and the final successful code verification `after-verified/`. The misleadingly early directory name `after-final` is explicitly superseded by its measurement-status record; its failures were not overwritten. Source hash manifests connect each runtime measurement to the tested working tree. The final commit linkage is recorded outside the repository after commit creation.

## Before/after on the original 40 cases

| Finding | Before | Corrected |
| --- | --- | --- |
| A1: meaning/currentness | 5 false-supported assertions; 2 other denied candidates retained values despite uncertainty | 0 false-supported; rejected values cleared; affirmative controls retained |
| A2: financial sign/actuality | 7 false-supported assertions; 2 correctly signed loss controls lost | 0 false-supported; both signed-loss controls retained; no candidate sign repair |
| A3: redirect publication and lineage | 0/4 complete positive controls; 6/6 rejection guards passed | 4/4 complete positive controls; 6/6 rejection guards passed |
| A4: observation-date conflicts | 1/2 positive controls retained | 2/2 retained; same-date and unresolved-date conflicts remain uncertain |
| All original cases | 19/40 passed | 40/40 passed |
| Semantic/date positive controls | 10/13 retained | 13/13 retained |

A3's original same-host case did publish a supported product, but lacked the required lineage. The other three positive controls failed publication on the old host-consistency guard. These are not counted as false-supported assertions.

Final expanded suite: **53/53 passed**, including 23 affirmative publication controls and 30 negative/rejection cases. The 13 additions cover clipped conditions, past/embedded catalog claims, current assertions after planned contrast, direct design/product-list positives, embedded financial aspiration, post-amount target qualification, combined profit/loss labels, historical dated employment, self-redirects and unexplained same-host path replacement.

Final original smoke: **15/15 expectations met**, versus seven false-supported facts, one lost dated employee observation and one redirect gate error before correction. Final predeclared holdout: **10/10**, including **4/4 positives** and no false support among its six negatives. Historical `employed 100 employees as of 2025-12-31` remained supported with that observation date.

Intermediate integration runs exposed real regressions, including financial-conflict handling, optional employee-date handling and an embedded financial aspiration. They were fixed and retained in the verification history; no test expectation or frozen gold was weakened to hide them. The holdout contrast case subsequently became a permanent regression, so its final rerun is not an untouched holdout estimate.

## Frozen replay: an intentional compatibility loss, not a green result

The replay command exits **1**. `retained_asseco_poland` is now rejected because source `S006` has two URLs and no recorded redirect chain:

- Discovery: `https://asseco.com/news/5723?L=-6815`
- Full page: `https://asseco.com/news/5723/?L=-6815`

A trailing slash is not universally equivalent HTTP resource identity. The correction does not invent a historical redirect or silently normalize it away. The frozen snapshot and its expected published outcome remain unchanged. This is an observable compatibility regression; the current CI evaluation step would remain red on this branch. It is not described as a successful replay or a release-ready result.

| Metric | Historical/before | Corrected replay |
| --- | ---: | ---: |
| Identity correctness | 10/10 | 10/10 |
| Identity-field correctness | 60/60 | 60/60 |
| Supported precision | 47/47 | 43/43 |
| Registry precision | 42/42 | 38/38 |
| Researched precision | 5/5 | 5/5 |
| Unsupported-as-supported | 0 | 0 |
| Eligible researched recall | 5/19 | 5/19 |
| Over-downgrade rate | 14/19 | 13/19 |
| Correct uncertain handling | 28/28 | 20/28 |
| Strict unknown handling | 40/41 | 38/41 |
| Eligible supported / uncertain / missing | 5 / 14 / 0 | 5 / 13 / 1 |
| Retained-real researched yield | 0/7 | 0/7 |

Every aggregate change comes from the rejected Asseco run: four registry-supported outputs, eight expected uncertain outputs and two expected unknown outputs are absent; one eligible researched observation moves from uncertain to missing. The lower over-downgrade count is **not a coverage improvement**. The nested safety metrics mirror the uncertain/unknown rows. Retained LPP and ORLEN still publish partial reports; Asseco no longer publishes. Eligible retained denominators remain Asseco 1, LPP 6, ORLEN 0. All other case count objects are unchanged.

The two clear positive replay assertions temporarily lost during integration—direct `designs` activity and `Its products are X and Y`—are retained by the final bounded grammar. No historical score was repinned. The preserved benchmark remains an honest historical result, not evidence that the original gate handled these new adversarial cases.

## Executed verification

- Full suite: **318 passed**.
- Separate adversarial run: **53 passed**.
- Ruff lint and formatting check: passed; 29 Python files checked for formatting.
- mypy: passed, 14 source files.
- Original smoke, predeclared holdout and historical-employee smoke: actual JSON/Markdown publication exercised; representative rendered values, reasons, employee dates and redirect links inspected.
- Original replay: executed separately; exit 1 and all metric deltas disclosed above; no input-hash errors.
- SHA-256 comparison: 26 protected example/evaluation, lock/config, research-instruction and CI files unchanged from the reference commit.
- No live model, registry, search or page-retrieval calls. Existing `lxml`/Scrapling `strip_cdata` deprecation warnings remain visible; no warning suppression was added.

Reproduce from the corrective checkout, using a fresh ignored output directory:

```sh
uv run --frozen pytest -q
uv run --frozen pytest tests/adversarial -q
uv run --frozen ruff check .
uv run --frozen ruff format --check src tests
uv run --frozen mypy src
uv run --frozen company-bi eval --dataset examples/evals/dataset.json --output-dir outputs/adversarial-replay
```

The last command is expected to expose the unchanged Asseco outcome mismatch described above. Do not change gold, reconstruct hops from similar URLs, suppress the exit status, or claim green CI to conceal it.

## Limits and release boundary

There are no remaining false-supported outcomes in the exercised corrected adversarial/smoke populations. This is not a guarantee for arbitrary prose, accounting notation, complex document layouts, attribution or unseen linguistic constructions. The gate remains a finite heuristic with known conservative recall limits, not a semantic verifier. A matching source claim is also not proof that the publisher tells the truth.

Redirect lineage is host-recorded metadata, not authentication of arbitrary edited JSON. Unobserved browser URL changes and inconsistent legacy source ledgers are rejected. Missing historical HTTP lineage cannot be recovered from the frozen artifacts without new evidence.

This package is local and reviewable. It does not authorize a push, merge, new tag, v0.1.1 release, paid/live research, presentation work or outreach. The original `main` and `v0.1.0` reference are preserved.

## Independent predicate-attachment correction

A later read-only review identified a residual risk outside the original measured populations. Actual offline publication at `17fdc9d` confirmed it:

```text
Example sp. z o.o. sells machinery to retailers of cloud services.
```

Both `machinery` and `cloud services` were published as company products. Only the former follows from that assertion. This establishes a residual defect; the commit that originally introduced it was not determined.

The text gate now requires bounded positive subject/predicate/argument attachment instead of accepting any candidate phrase near a recognized verb. Restricted direct-object determiners, industry bridges, business/product copulas and direct passive-subject forms remain recognized. A nested customer activity or product-purpose phrase does not inherit the company predicate. No new forbidden-topic word, dependency, model, financial rule or provenance policy was added.

Seven publication-path regressions cover the observed customer complement, direct-product retention, an embedded customer subject, direct passive offerings and passive subject/purpose separation. An initial integration lost six existing/new positive controls; those failures were preserved, and the forms were corrected without changing their expectations. In particular, month-only/publication-led event dates are still not promoted to invented occurrence dates.

Final independent verification:

- Full suite: **325 passed**.
- Separate adversarial suite: **60 passed**.
- Original attachment reproduction and positive control: **2/2** matched through JSON/Markdown publication.
- Six predeclared supplemental attachment boundaries: **6/6**, including three negative and three positive cases. The passive subject/purpose pair subsequently became a permanent regression; this final rerun is not an untouched holdout estimate.
- Ruff, formatting and mypy passed.
- Frozen replay: still exits **1**, with every metric unchanged from `17fdc9d`; the Asseco lineage incompatibility above remains unresolved.
- The same 26 protected input/config/instruction files remain byte-identical to `d4423da`. No live calls were made.

The separate evidence bundle is `overnight-quality-20261004T211518Z`: `complement-scope/` preserves the failing-before result, `after/` the first integration, and `iteration-2/` the final corrected measurements. Source-hash manifests and the local commit record identify the tested revision. The bounded-language and release limitations above still apply.

## Legacy read compatibility — extended Stage A

The prior whole-run rejection was too coarse: it discarded independent registry identity and unrelated eligible material when one old source-ID relationship was not provable. The actual legacy/current distinction is serialized `redirect_chain` absence, not a guessed date, URL equivalence, company or domain exception; the run has no historical version discriminator.

The reader now marks the entire ambiguous, pre-lineage non-registry ID group with `publication_blocked_reason: "unproven_legacy_url_relationship"`. Original inputs and URLs remain unchanged. The group retains an auditable trace and explicit limitation but loses all publication/date/conflict permission. Typed/current source records, valid redirect chains, `SourceStore` write guards and identity-integrity rejection remain strict. The permission removal survives serialization.

The frozen Asseco run publishes a **partial** profile again. `S006` and `S010` are explicitly blocked legacy groups; neither becomes researched support. Independent registry facts survive. A separate cross-domain/path fixture demonstrates the same behavior without an Asseco-specific rule, and independent employee evidence is not poisoned by a quarantined conflicting count.

Verification:

- Regression-first accepted baseline: 4 expected failures and 5 passes on unchanged `bc1d1cb`; final legacy set: **10 passed**, including the current-store denial guard.
- Full suite: **335 passed**; separate adversarial suite: **70 passed**.
- Ruff, format checks including `scripts/`, and mypy passed.
- Original frozen replay: **exit 0**. Every metric object matches the historical baseline: supported precision 47/47, researched precision 5/5, researched recall 5/19, unsupported-as-supported 0, retained-real yield **0/7**.
- `scripts/review_offline.py`: **exit 0**, all three retained real partial profiles and both explicitly controlled artifacts generated with zero external/provider calls.
- JSON and Markdown show the denial marker and source-specific limitations. Raw-Markdown spelling/copy assertions were removed rather than repinned to escaping; structural permission, identity, independent-support and round-trip behavior remain tested.

Restored counts come from restoring publication of the Asseco partial profile, not from new researched facts. Historical datasets, gold, snapshots and baselines were not changed. This is compatibility/correctness evidence, **not new live usefulness**.

The preserved evidence is under `d4423da-corrective-20261004/extended-20261005T070952Z/stage-a/`: invalid fixture setup is explicitly excluded in `before/`, accepted red tests are in `before-valid/`, initial runtime/replay/reviewer output is in `iteration-1/`, and final behavior-focused checks are in `verified/`.

## Fresh-context review — extended Stage B

A separate checker selected 19 new publication cases from the public contracts and candidate `9cae47f`, without prior findings or patch rationale. The parent executed its saved harness centrally. An initial invalid financial-scope fixture crashed; that attempt is preserved and excluded from product metrics.

The valid baseline matched **17/19** expectations with **zero observed incorrect supports**. Two legitimate financial positives were lost: a leading `For 2025-01-01 to 2025-12-31,` adjunct prevented the existing direct-subject rule from recognizing the subsequent company reporting clause. These were conservative coverage losses, not invalid facts. The original positive controls were retained rather than moved to an easier word order after seeing results.

The correction admits only that bounded English ISO-interval prefix before the existing financial assertion grammar. It does not add arbitrary prepositions to subject bridges or relax metric, period, scope, amount, actuality or identity checks. Five permanent regressions cover the two reported-unit positives, forecast, foreign subject and nested attribution.

The unchanged 19-case harness then matched **19/19** through the real models, gate and JSON/Markdown renderers, including dated employees, current redirect validation, source ownership and retained-run re-gating/isolation. Those exposed cases are now regressions, not an untouched holdout. A separate test-helper identity-evidence omission caused an intermediate full-suite failure; the fixture was repaired without removing identity validation. Final integration: **340 tests passed**, Ruff/format/mypy passed, frozen replay **exit 0** with unchanged historical metrics.

Raw inventory versions, the excluded crash, all before/after outputs and source hashes are retained under `extended-20261005T070952Z/stage-b/`. These are synthetic adversarial publication measurements, not fresh extraction or live usefulness.

## Measured usefulness — extended Stage C

The predeclared purposive sample was **Asseco Poland** (`5220003782`, previously examined), **SONEL** (`8840033448`, a smaller focused manufacturer), and **APATOR** (`8790166896`, held out until tuning ended). Official discovery and fresh MF lookups independently established the NIPs/legal identities before predictions. No company was replaced after seeing results.

Reference collection used **6 searches, 5 official page reads and 3 MF requests**: conservatively 8 of the 9 reference-read allowance. Five real page snapshots were frozen. A separate checker checked all **9 provisional atomic references** before seeing predictions: four Asseco observations and five Sonel observations, with entity, marketing, industry, laboratory and date limitations. These are selected self-description observations, not representative gold or proof of the publishers' truthfulness.

Baseline code was `9bd835c`; candidate code was frozen as `9f7c2d2`. Exactly two prompt-only interventions followed observed losses: source-language atomic values instead of translated/synthesized support, and a legal-entity about/offer read plus early minimal progress before broader research. No gate, identity rule, provider/model, dependency or per-run budget changed. No failed attempt was rerolled.

### Fresh extraction from fixed real sources

This used the normal configured agent/model, output validation and publication gate with local retrieval of the frozen real corpus. The model did not receive the reference inventory. Run-local source-ID rebinding is recorded; URLs, text, timestamps and existing redirect evidence were preserved. Tool search/read counts below are **local controlled retrieval**, not external web calls.

| Company / phase | Research result | Researched support | Model requests | Local searches / reads | Input / output tokens | Research seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Asseco baseline | FAILED, ModelAPIError; no profile | 0 | 2 | 4 / 0 | 2,858 / 138 | 12.30 |
| Sonel baseline | PARTIAL | 0 | 3 | 4 / 1 | 20,983 / 705 | 34.04 |
| Asseco candidate | PARTIAL | 0 | 5 | 5 / 1 | 35,537 / 1,129 | 42.91 |
| Sonel candidate | FAILED, ModelAPIError; no profile | 0 | 3 | 1 / 1 | 7,364 / 53 | 7.26 |

Sonel baseline proposed all five reference concepts but translated Polish source assertions into English values; none passed publication. The candidate Asseco draft retained source-language spans but still lost all four reference obligations through unread specific offerings and finite relation/entity/context checks. Failed runs have no assessable final-profile recall/precision denominator; no replacement profile was fabricated. **Controlled extraction did not demonstrate useful supported output.**

### Live end-to-end research

Each attempt used the actual CSV batch path, fresh registry lookup, Tavily, guarded retrieval, configured `openai-codex:gpt-6-luna`, gate and renderer.

| Company / phase | Final outcome | Researched support | Model requests | Searches / page reads | Input / output tokens | Research seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Asseco baseline | PARTIAL | 0 | 4 | 5 / 5 | 47,783 / 1,716 | 82.09 |
| Sonel baseline | FAILED, invalid excerpts after allowed repair | 0 | 5 | 6 / 3 | 93,676 / 5,113 | 123.44 |
| Asseco candidate | PARTIAL | 0 | 9 | 5 / 6 | 110,414 / 1,556 | 78.30 |
| Sonel candidate | PARTIAL | 0 | 8 | 3 / 2 | 73,499 / 1,385 | 66.00 |
| APATOR final held-out | FAILED, invalid excerpts after allowed repair | 0 | 9 | 3 / 3 | 78,323 / 1,905 | 71.88 |

The two development candidate profiles cover **0/4 Asseco and 0/5 Sonel references as supported**. Correctly retained unknown financial/employee/geography/date gaps are not useful-research successes. APATOR additionally encountered static TLS certificate failures, unsupported document content and the existing two-browser-attempt ceiling. No certificate policy was relaxed, no failed company was rerun, and no change was tuned on the held-out result. There is no APATOR gold denominator.

Every published researched support was checked against the retained evidence; there were **none**, so zero incorrect supports is vacuous and not a precision claim. Across both fresh populations: **48 model-request attempts, 470,437 reported input tokens and 13,700 reported output tokens**. Live research used 22 searches, 19 page-read operations, 2 browser attempts and 5 MF lookups; reference collection is counted separately above. Counts are application operations, not independently captured redirect/subresource HTTP traffic. Reported usage may omit failed-request billing. **Actual cost was unavailable, not assumed zero.**

**PRODUCT UTILITY NOT YET DEMONSTRATED.** The target of two companies with three correct non-registry observations across two sections each was not met. The remaining concrete bottleneck is the fit between useful source prose and the finite publication relation/entity contract, compounded by provider failures and nonliteral evidence proposals. Another synonym list, relaxed evidence permission or retry-until-success is not justified by this pass.

The [curated live Sonel JSON](../examples/review/sonel-20261005.json), [Markdown](../examples/review/sonel-20261005.md) and [provenance](../examples/review/sonel-20261005.provenance.json) preserve the actual PARTIAL output and dates from `9f7c2d2`, with no provider payloads or full source dumps. Raw protocol, hashes, reference reviews, every attempt and independent assessments remain in `extended-20261005T070952Z/stage-c/`. Historical replay, synthetic adversarial checks, fixed-source extraction and live research remain separate populations.

## Final quality audit of the offline verifier

The subsequent audit of `d9a8ababaa37a4073f5c3bca49b9e3a42df80c71` is recorded in [the quality report](V0_1_1_QUALITY.md#9-final-independent-quality-audit). It adds no production correction and does not overwrite any population above. In the independently authored, attribution-repaired paired corpus, all **57/57** unsafe negative assertions were withheld, but only **15/57** affirmative controls survived. There were **42 false-rejected positive controls**, plus six negative event cases with collateral loss of valid content; zero false-supported negatives and zero candidate-to-final report inconsistencies were observed.

The remaining language/entity, financial-format and event-content losses are explicitly deferred rather than addressed with an open-ended semantic engine. Original inputs, the attribution-only fixture repair, all failed assertions and a withdrawn financial-fix hypothesis are retained in the external review bundle. The separate blind driver remains **74 passed / 48 failed**; the repository's 390-test suite, including its 120-test adversarial subset, is a different population. No new live research, dependency change or release is part of this audit.
