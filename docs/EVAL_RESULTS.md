# OG-154 — historical earlier-contract evaluation results

**Contract-version note:** This file preserves earlier-contract results and original inputs/gold; they are not strict-contract positives or current strict-contract performance. The strict contract and taxonomy are defined in [STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md) and [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md). No new strict evaluation result is asserted here.

**Historical frozen result:** supported precision **47/47**, researched precision **5/5**, eligible recall **5/19**, false-supported **0**; retained-real researched yield **0/7**. See the [targeted-recovery result](#og-154a--targeted-recovery-separate-from-the-frozen-baseline) below. Earlier OG-154 sections preserve the **44/44, 2/2, 2/19** baseline; all are history, not the strict-contract headline.

## Conclusion

The approved production implementation at `59e76de` was measured without changing NIP/identity, research, retrieval, evidence-gate or renderer behavior.

- No unsupported claim was published as supported in this dataset: **0**.
- Supported precision is **44/44**, but **42** observations are registry facts. Researched precision is only **2/2**; that is too little positive output to establish reliable production accuracy.
- Useful researched coverage is **2/19 (10.5%)**. Seventeen eligible claims end uncertain. This is not acceptable coverage for useful evidence-backed BI, even though conservative abstention is safer than invention.
- The retained real batch remains **0 complete / 3 partial / 0 failed** and **0/7** eligible researched gold claims supported. Its researched precision is **0/0, unavailable**, not 100%.
- All three real reports must remain partial with these inputs: none has eligible paired financial coverage. Relaxing the gate cannot manufacture missing financial context or standalone employee evidence.
- No production correction was made. The measured misses involve retrieval availability, candidate extraction/citation defects and conservative semantic/identity attachment rules, not one demonstrated small safety-preserving fix. No fuzzy matching, snippet promotion, guessed dates, financial context repair, company exception, prompt/model change or COMPLETE-target optimization was introduced.

## Reproduce

```sh
uv sync --frozen
uv run --frozen company-bi eval \
  --dataset examples/evals/dataset.json --output-dir outputs/evals
```

This command requires no Tavily key, Codex OAuth, OpenAI key or internet after dependency installation. A runtime smoke removed API-key/model configuration and denied socket connections and research calls: **12 cases, exit 0, 0 network calls, 0 research calls**. The unresolved case uses a retained HTTP response through the real MF parser, not a mocked expected identity.

Pydantic Evals **2.54.0** supplies the typed dataset, task execution, evaluator and report scores. Counts are summed, not case percentages averaged. `results.json` and `results.md` are generated together; safety failures or evaluator/task failures cause nonzero exit, while low recall remains a visible diagnostic. Expected invalid/unresolved/rejected outcomes are not unexpected task failures.

Committed evidence:

- `examples/evals/dataset.json`: active native Pydantic Evals index;
- `examples/evals/controlled/`: deliberate synthetic retained evidence and MF subject-null response;
- `examples/evals/retained/`: three public run snapshots promoted byte-for-byte into fixtures;
- `examples/evals/baseline.json`: measured reviewed baseline;
- `examples/evals/initial-dataset.json`, `initial-baseline.json`, `gold-corrections.json`: first frozen revision/results and explicit review corrections;
- [Evaluation specification](EVAL_SPEC.md): denominators, eligibility, gold and correction rules.

Original ignored `runs/`, `outputs/`, credentials and authentication caches are not committed. Promoted public snapshots are intentional offline test data, not generated production outputs.

## Dataset and split

**12 cases: nine controlled, three retained-real offline replays.** Zero new live research calls were made. The cases are diagnostic, deliberately selected and not a representative population sample.

| Case | Diagnostic intent |
| --- | --- |
| fully_supported | Eligible literal business/scale/financial/news facts, actual zero values and month-only occurrence precision. The name describes available gold, not a guaranteed complete prediction. |
| employee_exact_official | Normal abbreviated issuer name, explicit same NIP, exact employee count/date; exposes conservative entity-attachment loss. |
| employee_conflict | Credible same-date disagreeing counts; no selected quantity or average. |
| employee_range_stale | Historical 51–200 range vs invented midpoint/current date; no new freshness policy. |
| ellipsis_snippet | Altered employee citation and discovery-only business information. |
| financial_context_metric | Operating profit is not total net result; retained currency/context is incomplete. |
| invalid_source_id | Orphan source reference rejects the run instead of producing a fabricated profile. |
| invalid_nip | Actual checksum validation rejects malformed input. |
| unresolved_nip | Real MF parser reads retained subject-null response. |
| retained_asseco_poland | Segment/Group scope, unsupported PDF discovery and a nonliteral event citation. |
| retained_lpp | Full-page business/news truth, model-altered citations, Group scope, constant-currency and date-role distinctions. |
| retained_orlen | No retained full pages, read/certificate failures and exhausted dynamic budget. |

Gold is deterministic and manually reviewed against source snapshots. Every gold excerpt was checked for its source ID and contiguous NFC/whitespace-normalized occurrence before prediction. Input drafts were not repaired to help the gate. Finite approved values/context are used, not an LLM judge. Every supported fact is checked; an unannotated support is a false support.

Active dataset SHA-256: `15d38e1e635dec24ee075d10fa1be2b58611d1d2ae5178c2d60d144382f21e82`.

## Counts and denominators

| Measure | n / N | Result |
| --- | --- | --- |
| Resolved identity correctness | 10 / 10 | 100.0% |
| Explicit identity-field expectations | 60 / 60 | 100.0%; includes expected nulls in invalid/unresolved cases |
| Overall supported precision | 44 / 44 | 100.0% |
| Registry-only supported precision | 42 / 42 | 100.0% |
| Researched supported precision | 2 / 2 | 100.0%; very small positive denominator |
| Unsupported-as-supported | 0 | Absolute count, not a percentage |
| Eligible researched recall | 2 / 19 | 10.5% |
| Over-downgrade rate | 17 / 19 | 89.5% |
| Correct uncertain-handling obligations | 28 / 28 | 100.0% |
| Correct strict unknown-handling obligations | 40 / 41 | 97.6% |

Eligible outcomes: **2 correctly supported, 0 incorrectly supported, 17 uncertain, 0 unknown, 0 missing**. Missing/rejected eligible claims would remain in the denominator. All twelve case outcomes match their expected stages: nine published profiles, one rejected source ledger, one invalid input and one unresolved identity. No unexpected task/evaluator failures occurred.

The one strict unknown obligation ending missing is `invalid_source_id / identity.website`: the whole run is correctly rejected, so no final Fact exists. It is not scored as correct unknown and no fake unknown profile is synthesized. This distinction is intentionally visible. NIP is evaluated as identity, not added as a fictitious supported Fact to inflate precision.

## Real-batch failure classification

Gold eligibility refers to information publishable from the retained corpus, not everything that might exist on the internet. “Unavailable” below never means proof that no such data exists anywhere. Primary layer is manually evidenced; secondary scope/context problems may coexist.

| Company | Researched fields | Eligible researched gold | Primary retrieval / extraction / gate / unavailable losses |
| --- | ---: | ---: | --- |
| Asseco Poland | 9 | 1 | 1 / 5 / 0 / 3 |
| LPP | 10 | 6 | 0 / 5 / 3 / 2 |
| ORLEN | 10 | 0 | 10 / 0 / 0 / 0 |
| Total | 29 | 7 | 11 / 10 / 3 / 5 |

Among the **seven eligible real claims**, **four** are lost primarily through extraction/citation/qualifier defects and **three** are genuine gate false-negative opportunities. All remain uncertain; none is published as researched supported.

### Asseco

The business/services/industry/market candidates mix legal-entity claims with Group/segment text. Standalone headcount and financial amounts are absent from eligible retained text; PDF snippets are not financial gold. The appointment instrument body was not retrieved, only its index/listing. The Q1 segment news is independently verifiable: the full page contains `2026-05-27` adjacent to the article and the PLN 607m/12% segment result. The original candidate inserts an ellipsis into its citation. This is an extraction loss, not evidence that the gate should accept that altered quote.

### LPP

Official full-page bodies establish clothing design/sales, brands, marketplace/omnichannel content, fashion/retail/e-commerce and Group news. Some candidate brand quotations change actual source wording. Q2 news omits the **constant-currency** qualifier and invents July 1 from month-only occurrence evidence. Those are extraction defects even though corrected useful gold exists.

Three exact eligible candidate opportunities remain rejected by the gate: industry classification, the 4,000-store Group milestone and the 2025 Group-results news. These expose conservative literal phrase/complete legal-name/content-attachment requirements. They are measured losses, not permission for a company-specific alias or fuzzy-match exception.

The 47-market and nearly-63,000 workforce observations are Group-scoped, not exact standalone-company quantities. Financial amounts also lack the full explicit interval needed by the contract. Unknown financial output is appropriate; news about Group results does not become a standalone financial record.

### ORLEN

All researched material is discovery-only. No eligible full-page body exists in the retained run. Read/certificate failures and dynamic-budget exhaustion are recorded. Group scope and listing text create secondary candidate deficiencies, but the primary zero-yield explanation is retrieval availability, not a demonstrated gate failure. This replay cannot prove that the underlying websites lack the data.

## Regression findings and limits

- Model-added ellipses and orphan IDs do not authorize support.
- Conflicts do not become averages; a source range does not become an invented exact midpoint.
- Operating profit is not net result. Missing retained currency/context prevents amount publication.
- Guessed observation/occurrence dates are cleared. Publication and occurrence are distinct.
- An explicit zero employee count survives; zero-valued financial gold is still eligible but suffers citation/context-related recall loss in this diagnostic input. Zero is not treated as missing by the metric evaluator.
- Strict literal/entity attachment and multi-clause evidence matching discard useful truth, including a correctly dated same-NIP employee observation using an abbreviated issuer name.
- Eligible gold is broader than whether a bad original candidate can safely be published. This measures end-to-end yield; field-level annotations distinguish extraction defects from pure gate misses.

No production before/after fix comparison exists because **no production fix was introduced**. Core-source hashes in initial and reviewed results are identical. The reviewed baseline is the unchanged-system result, not a tuned gate.

## Explicit initial-gold review corrections

The first frozen index (`82165a718e37c6f42dc0cfce8374fc741b1ae08c4c9144148e23fe70c8cefb61`) and its result are preserved. Its safety assertions failed because annotations incorrectly represented absent news as typed unknown, required the gate to replace a bad employee candidate with the gold range, referenced the wrong financial row/metric, and demanded erasure of context when only the amount must be rejected. These contradicted the fixed input/model contract and were corrected explicitly in `gold-corrections.json`; loss-layer clarifications did not change eligible truth.

An evaluator defect was also corrected: partial nested null-date constraints must accept either cleared event details or full details with a null occurrence, but reject an uncertain value carrying an unsupported precise day. A permanent regression covers all three transitions. This is evaluator implementation, not a production-gate change.

Identity scoring was also hardened during evaluator review: a published profile's identity is compared with gold, rather than trusting the retained input identity when a published profile exists. A regression proves that a changed published NIP cannot hide behind a correct trusted input NIP. Dataset metrics remain unchanged because the actual production profiles preserve identity.

**All input snapshots, eligible claims, approved supported values, precision, false-supported count, recall and over-downgrade counts stayed unchanged** across these documented corrections. Initial unsafe-state scores are not silently replaced or presented as a production improvement.

## Resource/latency observations

| Retained company | Requests | Searches / reads | Browser attempts / repairs | Input / output tokens | Original research seconds |
| --- | ---: | --- | --- | --- | ---: |
| Asseco | 5 | 4 / 3 | 0 / 0 | 57,142 / 2,103 | 73.281 |
| LPP | 6 | 6 / 8 | 0 / 0 | 105,926 / 2,427 | 81.944 |
| ORLEN | 4 | 4 / 7 | 2 / 1 | 36,096 / 2,540 | 68.010 |

Actual provider cost is null. `dynamic_reads` is the recorded browser-attempt counter. Source research diagnostics and Pydantic Evals replay `task_duration`/`total_duration` are recorded separately; replay duration is not the original research latency. Controlled diagnostic counters are synthetic fixture metadata, not live usage. No token/context optimization, cost instrumentation or analytics infrastructure was added.

## Quality and remaining limitations

205 tests passed; Ruff lint/format and mypy passed (24 Python files formatted, 14 source files typed). Fourteen upstream Scrapling/lxml warnings remain visible. The actual no-credentials/no-network evaluation surface was smoke-run, not inferred from tests alone.

The set is small and deliberately adversarial. Gold depends on manual source interpretation, finite approved wording and fixed snapshots. It does not estimate population precision/recall, live retrieval reliability, semantic completeness or universal factual accuracy. Live content may change and needs new human-reviewed gold. Registry-preservation metrics do not claim fresh live MF coverage. Production remains safe-but-low-yield in these cases; the evaluation does not hide that result behind registry precision.

OG-154's twelve repository/evaluation criteria are satisfied. Linear updates remain blocked: only read routes are mounted and the authenticated browser relay is unavailable. No completed status/comment update is claimed. Stop before OG-155.

## OG-154A — targeted recovery, separate from the frozen baseline

The approved OG-154 baseline is frozen at `46bdd26`; every original dataset/gold/replay byte and `baseline.json` remains unchanged. It was reproduced before production edits: researched precision **2/2**, recall **2/19**, false supports **0**.

Regression-first exact extraction admission and bounded claim-local entity attachment recover three controlled observations: products, industry and a dated same-NIP employee count. The same set now measures overall precision **47/47**, registry **42/42**, researched **5/5**, recall **5/19**, over-downgrade **14/19**, false supports **0**. Identity **10/10**, uncertainty **28/28** and strict unknown **40/41** are unchanged. No historical candidate, quote or gold was repaired to improve metrics.

**Retained real yield remains 0/7.** The three LPP semantic gate opportunities and four real extraction losses remain visible. A fresh optional LPP sanity run failed at the existing single output-repair ceiling despite six retained full pages; it is not a successful live demonstration or part of the frozen before/after benchmark. No retry or further tuning followed.

[RECALL_RECOVERY.md](RECALL_RECOVERY.md) contains the pre-fix 17-claim inventory, accepted/rejected intermediate decisions, exact recoveries, safety regressions, separate stage populations and live/resource limitations. [`og154a-comparison.json`](../examples/evals/og154a-comparison.json) contains machine-readable before/after metrics, frozen hashes and per-claim recovery.

Verification: **231 tests**, Ruff lint/format, mypy (14 source files) and actual no-credentials/no-network CLI/JSON/Markdown smoke passed. No financial/retrieval/provider/budget weakening, new architecture or OG-155 work.

