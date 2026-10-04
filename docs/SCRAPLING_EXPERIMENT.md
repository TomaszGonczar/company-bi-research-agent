# OG-156 — paired Scrapling falsification experiment

## Verdict

**No additional publishable researched facts were observed: 0 → 0 across all three pairs.** ORLEN's Scrapling arm acquired one page and proposed four supported candidates, but the unchanged gate downgraded all four to uncertain. This is a negative result for published gain in this sample, not evidence that Scrapling is universally ineffective or safe to remove.

The retrieval-specific conclusion is **limited/inconclusive**: Asseco and LPP did not request a page in either arm, so those pairs do not test extraction. Weak fixed discovery and model behavior dominate them. No worse arm was rerun or manually rescued, no source was added, and no prompt/query was tuned after outcomes were seen.

## Hypothesis and predeclared sample

Hypothesis: with the same verified identity, discovered candidate URLs/snippets, native model and budgets, making guarded full-page material available produces additional `supported` researched facts without publishing unsupported facts.

Selected before execution: all three existing retained-real companies, not only known retrieval successes:

| Company | NIP | Execution order |
| --- | --- | --- |
| Asseco Poland | 5220003782 | A then B |
| LPP | 5831014898 | B then A |
| ORLEN | 7740001454 | A then B |

- **A — snippets-only:** search snippets available; full-page extraction denied; no Scrapling requests.
- **B — Scrapling available:** the unchanged current static-first guarded read, with its existing browser fallback.
- Both arms used the same committed trusted MF identity/registry source for each company. Identity was not re-resolved differently per arm. This is new live model/retrieval execution with retained identity inputs, **not** a comparison of old replay timings with new timings.

## Exact paired method

Runner: [scripts/scrapling_experiment.py](../scripts/scrapling_experiment.py).

One ordinary current basic Tavily search was captured per company, maximum five results, before either arm. Exact predeclared template:

```text
{legal_name} NIP {nip} business products services employees financial results news
```

Sanitized typed results were frozen once and replayed for every model search-tool request in that company's arms. There were **3 actual discovery-provider calls total**, counted once/shared; **0 additional Tavily provider calls per arm**. Replayed search-tool calls still consumed the normal search budget. Query text could vary in model requests, but could not change the fixed candidates or introduce new URLs.

The native model remained `openai-codex:gpt-6-luna`, with baseline reasoning/settings and exact instruction SHA-256 `8a61dde9032724d667636cc2d0fa5d67c8b2ade77ee99e09aa79f36382b04a6b`. Default ceilings stayed 180 seconds, 6 searches, 10 page reads, 2 browser attempts, 12 model requests, 24 tool calls and one structured-output repair. Both arms exposed the same tools and instructions; only full-page availability differed. A did not fabricate a failed provider request or force additional extraction. B used the existing safe source-ID/URL/redirect boundaries.

Each arm ran **once**. Output-directory overwrite is refused. No manual page extraction, extra source/query, provider/parser fallback, TLS bypass or retry increase was used. Static ORLEN retrieval encountered `CertificateVerifyError`; the ordinary bounded dynamic fallback succeeded. The certificate failure was recorded, not suppressed by disabling verification.

Paired candidate equality was independently checked against the saved discovery record and raw run source ledgers; no full page lay outside the frozen URL set:

| Company | Candidate count | Same canonical candidate SHA-256 in A/B |
| --- | ---: | --- |
| Asseco | 5 | `426c1e858d1612e191256c107ddad83496fdbb5da22c0df2b2f017983fb7b978` |
| LPP | 5 | `c0a208bde7b15fb9e370ea91b999c2a28fd9ab9819b6d33f400051a26667f576` |
| ORLEN | 5 | `b20a5e6bbcb62b471814164aa2f21dcf5e750e5c15bbac92a0a8b36f3cc616c1` |

Asseco's captured results were mostly irrelevant: a Targeo address listing plus other legal entities/Yahoo's Grodno page. LPP had Wikipedia, MarketScreener, Reuters, Investing.com and Business & Human Rights Centre. ORLEN had Forbes, official financial/meeting/investor-relations pages and Wikipedia. These discovery failures/choices were kept, not replaced with a better corpus after results.

## Observed publication and operational results

`S/U/?` below means supported / uncertain / unknown **after the actual gate**, excluding trusted registry identity facts. Each list-valued Fact counts once; each financial/news Fact counts separately. Website counts only if non-registry evidence exists. Variable model-generated news slots explain unequal totals; registry fields and pre-gate supported guesses are not the primary success metric.

| Company | A → B researched supported | Additional supported | A S/U/? → B S/U/? | Page reads A/B | Dynamic A/B | Replayed searches A/B | Model requests A/B | Repairs A/B | Runtime seconds A/B |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Asseco | 0 → 0 | 0 | 0/0/7 → 0/0/7 | 0/0 | 0/0 | 3/4 | 2/2 | 0/0 | 12.12/12.31 |
| LPP | 0 → 0 | 0 | 0/0/9 → 0/0/8 | 0/0 | 0/0 | 4/3 | 5/3 | 0/1 | 26.91/29.33 |
| ORLEN | 0 → 0 | 0 | 0/0/8 → 0/4/3 | 0/1 | 0/1 | 6/5 | 5/5 | 1/1 | 36.44/63.46 |
| Total | 0 → 0 | 0 | 0/0/24 → 0/4/18 | 0/1 | 0/1 | 13/12 | 12/10 | 1/2 | 75.47/105.10 |

| Company | Input tokens A/B | Output tokens A/B | Reported monetary cost A/B |
| --- | ---: | ---: | --- |
| Asseco | 12,647/14,930 | 433/441 | unavailable/unavailable |
| LPP | 55,640/24,339 | 1,034/1,279 | unavailable/unavailable |
| ORLEN | 53,808/64,411 | 1,570/2,403 | unavailable/unavailable |
| Total | 122,095/103,680 | 3,037/4,123 | unavailable/unavailable |

All six research executions ended `completed`; all six canonical profiles were **PARTIAL**, not COMPLETE. The complete experiment command took 191.21 seconds including shared discovery and processing. Row runtime is observed per-arm wall time, not historical replay duration or an estimated saving.

B took 29.63 seconds more in aggregate, but used two fewer model requests and 18,415 fewer input tokens, with 1,086 more output tokens. Model decision variation matters: the ORLEN pair added approximately 27.02 seconds and 10,603 input tokens while Asseco/LPP never fetched. These differences are observations, not a general causal latency/cost estimate for Scrapling.

No provider monetary price was reported. No USD amount or Tavily-credit charge was inferred from token counts. Counts/resources are actual new execution diagnostics; retained input hashes are provenance only.

## Correctness and useful-claim interpretation

- **Published incorrect/false researched supports: 0 in A, 0 in B.** Independent inspection of all six canonical profiles found no supported researched fact, so the precision denominator is **0** and precision is **not estimable**, not 100%.
- ORLEN B acquired the official [financial-results page](https://www.orlen.pl/en/investor-relations/reports-and-publications/financial-results). Its candidates for business description, products/services, industries and markets used page/navigation/group-level context. The gate found insufficient exact candidate/entity/context verification and downgraded them to uncertain. They are **four unverified proposals**, not four verified incorrect factual extractions and not four additional supported facts.
- Financial values stayed unknown/null. Download links and third-party snippets were not treated as retrieved numerical evidence; no missing financial value became zero or a proxy metric.
- Wrong-entity Asseco discovery did not become supported company facts. LPP's new first-attempt excerpt rejection was safely repaired to unknowns; this is an observed current diagnostic event, not the historical optional LPP incident.
- Frozen eligible gold belongs to different retained evidence/candidate wording. Its 1/6/0 retained-real eligible denominators cannot honestly be assigned to fresh discovery/model output as a causal paired recall score. **Fresh supported-eligible/eligible: unavailable**; do not substitute 0/7 or change original gold after inspecting these outputs. The independent frozen evaluation remains separately 5/19 overall eligible researched recall and 0/7 retained-real gold yield.

Thus the sample shows **no additional usable supported claim**. Four additional ORLEN uncertain candidates may be inspectable leads, but do not satisfy the publication target. No correctness tradeoff in published supports was observed; absence of any support prevents a precision conclusion.

## Reproduction and evidence locations

This is an explicitly **live** command, not part of credential-free tests/evaluation:

```sh
uv run --frozen --env-file .env python scripts/scrapling_experiment.py --output-dir outputs/og156-experiment
```

Use standard environment/native Codex authentication. The runner refuses an existing destination; a rerun is a new time-dependent experiment, not a way to replace a worse arm. It writes `discovery.json`, `provenance.json`, `summary.json`, and `{asseco,lpp,orlen}/{A,B}/research.json`, `summary.json`, `profile.json`, `profile.md`. Frozen discovery and typed body/citation evidence are retained locally under ignored outputs; no original ignored runs were read or copied and no raw generated experiment output, header/auth dump or credential file is committed.

The actual observed run used a fresh `outputs/og156-paired-*` directory. The tables, hashes, method and sample above are the committed evidence summary; newly querying services can change results. A controlled zero-network harness separately proved three captures/six once-only arms, equal candidate hashes/URLs, 0 versus 1 page reads, output overwrite refusal, and rejection of a wrong numeric candidate in post-gate counts. It is not a replacement for the observed live results.

## Bounded interpretation and limitations

**No supported gain demonstrated; retrieval benefit remains inconclusive.** Do not remove Scrapling or proclaim a universal win/loss from this sample. Two pairs did not exercise it; one acquired a useful body but failed the frozen publication context requirements. Static TLS trouble, browser availability, weak discovery, model nondeterminism, temporal drift and the strict full-page support requirement constrain interpretation. A is policy-ineligible to publish snippet-only claims by design; B merely makes eligible material possible, not automatic.

No crawler, universal document parser, new provider, benchmark framework, retry hierarchy, telemetry platform, claim scoring, prompt/recall tuning or evidence relaxation was added. Protected original gold/baselines/snapshots and dependency lock remain unchanged. DNS rebinding/TOCTOU, unsupported retrieved document formats, upstream warnings and weak retained real yield remain explicit limits.
