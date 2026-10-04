# Adversarial corrections against d4423da

Local corrective package for possible v0.1.1; not a release or a claim of green CI. Reference commit: `d4423da54ed84cfa20104dee5cb8cc5decde19bd`. Branch: `fix/v0.1.1-adversarial-corrections`.

The bounded publication contracts are in [EVIDENCE_MODEL.md](EVIDENCE_MODEL.md#assertion-qualification). No new model/provider, dependencies, research instructions, budgets or financial-document parser were introduced.

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
