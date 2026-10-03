# OG-154A — targeted researched-claim recovery

## Frozen OG-154 baseline

Approved commit: `46bdd26`. Initial `git status`, last-ten-commit log and diff showed that commit at HEAD and a clean working tree. Before any production edit, the existing offline command wrote `outputs/evals/before-og154a/results.json` and exited 0:

```sh
env -u TAVILY_API_KEY -u OPENAI_API_KEY -u COMPANY_BI_MODEL -u LOGFIRE_TOKEN \
  uv run --frozen company-bi eval --dataset examples/evals/dataset.json \
  --output-dir outputs/evals/before-og154a
```

All metrics, raw counts, input hashes and core production hashes matched committed `examples/evals/baseline.json` exactly. Identity: **10/10**; overall precision: **44/44**; registry precision: **42/42**; researched precision: **2/2**; false supported: **0**; eligible researched recall: **2/19**; over-downgrade: **17/19**; uncertain obligations: **28/28**; strict unknown obligations: **40/41**.

Frozen dataset SHA-256: `15d38e1e635dec24ee075d10fa1be2b58611d1d2ae5178c2d60d144382f21e82`. Frozen baseline SHA-256: `42bcbac5bf2adf66137447fd644a2c136e0d424138e38794ab9590cea0f69c09`. Original gold, baseline, historical corrections and all replay inputs are immutable in this iteration. No annotation correction was required during reproduction.

## Pre-fix inventory: 17 missed eligible researched claims

Expected state is **SUPPORTED** and actual baseline state is **UNCERTAIN** in every row. `Exact gold` means case-sensitive contiguous NFC/whitespace-normalized evidence exists in a retained **full page**, independently of candidate quality. All 17 gold evidence sets were checked against their host source IDs. Some real IDs also retain discovery snippets; those are not the eligibility proof.

| Case | Field | Expected → actual | Primary loss | Observed reason | Source type / ID | Exact gold |
| --- | --- | --- | --- | --- | --- | --- |
| `fully_supported` | `financials.0` | supported → uncertain | GATE | Exact standalone zero-revenue quote lacks full legal-name attachment and a literal unit word; period/currency/scope are explicit. | full page / `annual-report` | yes |
| `fully_supported` | `financials.1` | supported → uncertain | EXTRACTION | Candidate rewrites the revenue-and-net sentence into a nonexistent net-only excerpt. | full page / `annual-report` | yes |
| `fully_supported` | `industries` | supported → uncertain | GATE | Literal sector quote says “The company” rather than repeating the complete registry name. | full page / `annual-report` | yes |
| `fully_supported` | `markets` | supported → uncertain | GATE | Exact “serves customers in Poland” lacks an entity anchor inside that short citation. | full page / `annual-report` | yes |
| `fully_supported` | `products_services` | supported → uncertain | GATE | Exact product statement uses “Its”; no complete legal name in the citation. | full page / `annual-report` | yes |
| `fully_supported` | `recent_developments.0` | supported → uncertain | GATE | Event body uses “it”; title/summary are not the literal source sentence and lack complete legal-name attachment. | full page / `news-august` | yes |
| `fully_supported` | `recent_developments.1` | supported → uncertain | EXTRACTION | Candidate invents July 1 from month-only evidence; separate conservative event attachment also blocks it. | full page / `news-july` | yes |
| `employee_exact_official` | `employees` | supported → uncertain | GATE | Exact dated employee sentence uses abbreviated issuer name despite an explicit matching NIP in the cited body. | full page / `issuer-page` | yes |
| `employee_range_stale` | `employees` | supported → uncertain | EXTRACTION | Candidate selects exact midpoint 126 and a current date from historical 51–200 range evidence. | full page / `historical-page` | yes |
| `ellipsis_snippet` | `employees` | supported → uncertain | EXTRACTION | Model inserts a non-source ellipsis; retained candidate has no selected count. | full page / `employee-page` | yes |
| `retained_asseco_poland` | `recent_developments.0` | supported → uncertain | EXTRACTION | Model inserts ellipsis into the segment-news citation despite exact body/date/segment evidence. | full page / `S006` | yes |
| `retained_lpp` | `business_description` | supported → uncertain | EXTRACTION | Brand citation changes source wording; another exact source fragment does not establish the complete multi-clause value. | full pages / `S006`, `S007` | yes |
| `retained_lpp` | `industries` | supported → uncertain | GATE | All list labels must match one literal citation and complete legal name; independently exact fashion/e-commerce excerpts cannot cover the list. | full pages / `S007`, `S016` | yes |
| `retained_lpp` | `products_services` | supported → uncertain | EXTRACTION | Rewritten brand quote; otherwise available collections, omnichannel and marketplace evidence is not attached completely. | full pages / `S006`, `S007` | yes |
| `retained_lpp` | `recent_developments.0` | supported → uncertain | GATE | Exact Group milestone evidence is split across excerpts; event title/summary paraphrase source and do not repeat complete legal name. | full page / `S007` | yes |
| `retained_lpp` | `recent_developments.1` | supported → uncertain | EXTRACTION | Drops constant-currency growth qualifier and invents July 1. | full page / `S016` | yes |
| `retained_lpp` | `recent_developments.2` | supported → uncertain | GATE | Exact Group revenue/net-profit excerpts cannot validate a paraphrased multi-clause news value under current attachment rule. | full page / `S001` | yes |

This eligible-miss population is **17 = 8 extraction + 9 gate**, not the broader real-field population below. Four of seven eligible real claims are extraction losses; three are gate losses. No retrieval/unavailable claim belongs to this eligible population because eligible exact retained gold exists for every row.

## Retrieval inspection: separate 29-field real population

The frozen three-company corpus has **29 researched fields**, with primary losses **11 retrieval / 10 extraction / 3 gate / 5 unavailable context**. These counts must not be added to the 17 eligible-miss counts.

- **Asseco: one retrieval loss**, appointment/filing event: `S010` is an official index/listing, not the primary instrument body. Annual-report links elsewhere are PDFs refused by the existing layer. Retained normalized text contains no captured eligible HTML/text document link proving a safe follow target.
- **ORLEN: ten retrieval losses**: every researched field has only discovery material. The run records static certificate failure, browser error and both dynamic attempts exhausted; no retained full page exists. Root-cause diagnostics are run-level, not enough to assign each field a unique failed request. A one-hop link follower would not repair TLS and no retained successful index offers a supported follow target.
- **Decision:** do not introduce a crawler, disable TLS checks or add a speculative follow-through. PDF/XML/archive/document-body limitations remain explicit. HTML/text retrieval, budgets, provider and provenance behavior remain unchanged unless further concrete evidence justifies the one allowed minimal change.

## Hypothesis and experimental boundaries

Prevent nonliteral excerpts at the research extraction boundary, preserving the existing single output-repair allowance and progress behavior. Retain qualifiers, legal-entity/Group scope and explicit date precision rather than repairing old candidate values. A contract correction alone cannot improve frozen bad-candidate replays; measure its own offline extraction regression separately.

For gate misses, prefer exact identity/context and independently proven list-item attachment over fuzzy equivalence. Handle each real false negative individually; do not accept free-form paraphrases merely because a page contains matching words or numbers. Financial requirements and adversarial rejection remain non-negotiable. No arbitrary recall target; no COMPLETE-count target; one focused correction pass only.

## Three retained LPP gate opportunities: correction decision

Each unchanged candidate was replayed through the reproduced baseline and inspected against its exact retained body, date metadata and gold. These remain genuine end-to-end gate opportunities, but identity attachment alone does not prove their complete candidate meaning:

| Original field | Exact source truth | Remaining deterministic proof obligation |
| --- | --- | --- |
| `industries` | S007 names the European fashion industry; S016 states e-commerce revenue growth. | “Apparel and fashion” / “Retail and e-commerce” are interpreted category labels, not literal complete phrases. Recovering them requires a classification equivalence policy, not quote normalization. |
| `recent_developments.0` | S007 separately states the 4,000-store milestone, 47 markets, Central Asia strategy and Sinsay expansion. | The title/summary combine and paraphrase multiple claims. Matching 4,000 and “Group” alone cannot verify every clause or event direction. |
| `recent_developments.2` | S001 separately states 2025 Group revenue, net profit, store growth and investment. | A multi-clause paraphrase is not established by the two attached amount excerpts. Matching numbers alone could accept the wrong metric, scope or investment assertion. |

Do not introduce a taxonomy, semantic word-bag matcher or event parser to promote these values. Preserve their original gold eligibility and report them still lost if the targeted exact attachment corrections do not recover them. A future correctly extracted literal value can be verified separately; silently rewriting these frozen candidates would invalidate the comparison.

## Regression-first evidence

With production unchanged, the corrected offline extraction regressions produced **3 target failures / 1 pass**: a nonliteral ellipsis was accepted without repair; repeated malformed evidence completed; a malformed progress save replaced the valid literal span. The first test attempt exposed missing controlled-transport hooks, not a production defect; those fixtures were corrected before counting the failing-before proof.

With the gate unchanged, the shared attachment regressions produced **3 target failures / 8 boundary passes**: same-NIP abbreviated issuer count/date and two exact pronoun product/industry observations were downgraded. No publication/source/financial rule was changed before these failures were observed.

The extraction correction passed **21 research-agent tests** after integration. An extraction-only rerun kept the frozen **2/2** researched precision, **2/19** recall and **0** false supports; this is not presented as repair of historical candidates. Supported proposed citations now require their own retained full-page span before progress/final-output acceptance, while uncertain discovery remains visible. The existing one-repair/usage ceilings remain unchanged.

The first shared attachment measurement recovered the controlled products and industry claims: researched precision **4/4**, recall **4/19**, false supports **0**. An initial exact-core NIP bridge did not address the observed abbreviated Northstar name; the unchanged Northstar replay was added as a failing regression before the protected literal multiword-suffix/issuer-NIP correction.

An intermediate suffix patch recovered Northstar but temporarily downgraded the original legitimate zero, leaving recall **4/19**. Additional deterministic boundary cases exposed borrowed foreign-employee date attachment and rejection of an explicitly Group-qualified exact news event. That intermediate implementation was **not accepted**, even though its frozen-set false-supported count was still zero. Each boundary was observed failing before a claim-local correction; the final measured result below must preserve zero, separate company dates, conflicts and valid Group news.

## OG-154A accepted targeted recovery

Changes are confined to `agent.py` / `test_research_agent.py` and `evidence.py` / `test_evidence.py`:

- **Extraction admission:** a proposed supported citation must be a contiguous case-sensitive NFC/whitespace-normalized span in its own retained full page. Malformed final output uses only the existing single repair; malformed progress cannot replace an earlier valid draft. Uncertain discovery remains visible. The existing agent contract explicitly preserves qualifiers/scope and prohibits invented day precision. This strengthens candidate extraction, not final semantic approval.
- **Exact qualitative attachment:** inspect at most two preceding contiguous retained sentences, ending at the quoted claim. Keep ordered literal value checks and the original excerpt. Pronouns require a continuous company-reference chain from a preceding explicit company subject; intervening foreign entities cannot supply an antecedent. No following footer, cross-source stitching or paraphrase matching.
- **Employee attachment:** current quantity/date must belong to the same actual employee sentence. A shortened name requires an explicit nearby issuer-NIP declaration and an ordered full legal-name core or multiword core suffix, with legal forms excluded. Foreign issuer, customer/Group/segment scope, negation, wrong/distant/following NIP and conflicting observations stay rejected. Direct full-name zero observations retain their prior behavior. Financial matching is unchanged.

Review found two further precision hazards outside the frozen set: an intervening foreign entity could authorize employee/product pronouns, and a differently named issuer could authorize the shortened name. Both were reproduced as failing regressions, corrected before acceptance and included in the complete passing suite. A Group-news preservation fixture initially triggered the pre-existing sentence split at a legal-form period before uppercase `Group`; it was corrected to a genuinely eligible lowercase `group` statement, without changing that unrelated parser or any frozen annotation.

### Same frozen set: before → after

| Metric | OG-154 | OG-154A |
| --- | --- | --- |
| Resolved identity correctness | 10/10 | 10/10 |
| Identity-field expectations | 60/60 | 60/60 |
| Overall supported precision | 44/44 | 47/47 |
| Registry precision | 42/42 | 42/42 |
| Researched precision | 2/2 | 5/5 |
| Unsupported-as-supported | 0 | 0 |
| Eligible researched recall | 2/19 (10.5%) | 5/19 (26.3%) |
| Over-downgrade | 17/19 (89.5%) | 14/19 (73.7%) |
| Correct uncertain obligations | 28/28 | 28/28 |
| Correct strict unknown obligations | 40/41 | 40/41 |

The rejected orphan-source run still has no website Fact; the 40/41 unknown result is not hidden. All three recoveries are controlled, not real-company yield. Original supported business/zero observations remain supported; no previously correct support was sacrificed. The same 12 expected case outcomes match, and no task/evaluator failure occurred.

Machine-readable comparison: [`examples/evals/og154a-comparison.json`](../examples/evals/og154a-comparison.json), including frozen file hashes, both metric sets, every original missed claim, separate populations and the rejected intermediate. Before/after reports remain separate under `outputs/evals/before-og154a/` and `after-og154a/`:

```sh
env -u TAVILY_API_KEY -u OPENAI_API_KEY -u COMPANY_BI_MODEL -u LOGFIRE_TOKEN \
  uv run --frozen company-bi eval --dataset examples/evals/dataset.json \
  --output-dir outputs/evals/after-og154a
```

### Every original eligible miss

All rows were uncertain before. “Still lost” retains the original primary stage; no gold, candidate or input was repaired.

| Case / field | After | Recovery / remaining stage |
| --- | --- | --- |
| `fully_supported / financials.0` | uncertain | still lost — GATE; no financial unit/entity relaxation |
| `fully_supported / financials.1` | uncertain | still lost — EXTRACTION; rewritten excerpt |
| `fully_supported / industries` | supported | recovered — GATE; exact nearby company/pronoun attachment |
| `fully_supported / markets` | uncertain | still lost — GATE; conservative exact attachment |
| `fully_supported / products_services` | supported | recovered — GATE; exact nearby company/pronoun attachment |
| `fully_supported / recent_developments.0` | uncertain | still lost — GATE; event value/entity proof |
| `fully_supported / recent_developments.1` | uncertain | still lost — EXTRACTION; invented day |
| `employee_exact_official / employees` | supported | recovered — GATE; issuer NIP/name/count/date association |
| `employee_range_stale / employees` | uncertain | still lost — EXTRACTION; midpoint/current-date invention |
| `ellipsis_snippet / employees` | uncertain | still lost — EXTRACTION; altered quote |
| `retained_asseco_poland / recent_developments.0` | uncertain | still lost — EXTRACTION; altered quote |
| `retained_lpp / business_description` | uncertain | still lost — EXTRACTION; rewritten brand quote |
| `retained_lpp / industries` | uncertain | still lost — GATE; interpreted classifications |
| `retained_lpp / products_services` | uncertain | still lost — EXTRACTION; rewritten brand quote |
| `retained_lpp / recent_developments.0` | uncertain | still lost — GATE; multi-clause event paraphrase |
| `retained_lpp / recent_developments.1` | uncertain | still lost — EXTRACTION; missing qualifier/invented day |
| `retained_lpp / recent_developments.2` | uncertain | still lost — GATE; multi-clause event paraphrase |

| Stage | Before lost / after lost / recovered: original 17 eligible misses | Before / after: 29 retained-real fields |
| --- | --- | --- |
| Retrieval | 0 / 0 / 0 | 11 / 11 |
| Extraction | 8 / 8 / 0 | 10 / 10 |
| Gate | 9 / 6 / 3 | 3 / 3 |
| Unavailable context | 0 / 0 / 0 | 5 / 5 |

These populations are incompatible totals; do not add them. **Extraction dominates the remaining eligible misses (8/14)**. **Retrieval is the largest broad retained-real loss class (11/29)**, closely followed by extraction (10/29).

### Retained real replay

| Company | Eligible | SUPPORTED before → after | Eligible UNCERTAIN before → after | Eligible UNKNOWN before → after | All researched states before = after |
| --- | --- | --- | --- | --- | --- |
| Asseco Poland | 1 | 0 → 0 | 1 → 1 | 0 → 0 | 0 supported / 6 uncertain / 3 unknown |
| LPP | 6 | 0 → 0 | 6 → 6 | 0 → 0 | 0 supported / 8 uncertain / 2 unknown |
| ORLEN | 0 | 0 → 0 | 0 → 0 | 0 → 0 | 0 supported / 8 uncertain / 2 unknown |
| Total | 7 | **0/7 → 0/7** | 7 → 7 | 0 → 0 | 0 supported / 22 uncertain / 7 unknown |

No original real eligible claim recovered. Real researched precision remains **0/0, unavailable**. Missing paired financial evidence still prevents complete real profiles; no COMPLETE count was optimized.

### Safety and quality

**231 tests passed**; Ruff lint/format and mypy passed (24 Python files / 14 typed source files). Fourteen upstream Scrapling/lxml warnings remain visible. A final credential-free CLI consumer blocked socket/research calls: **12 cases, exit 0, zero network/research calls**. Actual canonical JSON and Markdown showed the recovered **84 employees as of 2026-09-30**, with its original host source and exact excerpt; the original zero survived.

Model-added ellipses, orphan IDs, range-as-exact, operating-profit-as-net-result, invented day precision, snippet-only amounts and Group/standalone overreach remain rejected. Added boundaries cover foreign/distant/footer/cross-source entity attachment, company/customer/issuer ambiguity, borrowed dates, conflicting shortened-issuer headcounts and legal-form-only aliases. No financial, retrieval, source-ID, provider, model or resource-budget relaxation was introduced.

### Optional live sanity: separate failed observation

One fresh LPP native-Codex run used the unchanged provider/budgets and retained six full pages. It **failed at the single output-repair ceiling**, with no validated progress retained: 4 model requests, 6 searches, 7 reads, 0 browser attempts, 1 repair, **72,964 input / 4,501 output tokens**, **163.185 seconds**, cost null. The actual gate produced a partial profile with seven unknown researched slots and null financial amounts. This is not a successful live coverage demonstration, and retained diagnostics do not identify the precise validation failure.

Original LPP observations were 6 requests, 6 searches, 8 reads, 0 browsers/repairs, 105,926 input / 2,427 output tokens and 81.944 seconds. Live content/model behavior differs, so these are observational differences, not a causal token-efficiency or before/after-quality benchmark. The frozen real totals remain 199,164 input / 7,070 output tokens. No context compression, token optimization, extra retry or further tuning followed this failed sanity run; live artifacts remain ignored and uncommitted.

### Decision and limits

**Precision:** 5/5 researched supports clean on this deliberately small set, not population accuracy. **Coverage:** three controlled eligible claims recovered, 2/19 → 5/19; useful real-company yield was not demonstrated. **Real replay:** 0/7 unchanged. **Remaining bottleneck:** exact extraction/semantic attachment for eligible claims, retrieval across the broad real-field population.

PDF/XML/archive/OCR and missing financial-period/scope/context limitations remain. Bounded exact copying does not verify arbitrary paraphrases, make the model reliably copy every span or guarantee fresh-run success. The live repair failure makes that limitation concrete. Stop this measured iteration; no OG-155, CI/security, AgentCanvas, provider expansion or continued recall tuning.

