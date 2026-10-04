# Reviewer guide — Company BI in ten minutes

Use this path from the repository root; no PROJECT.md, internal history, API keys, login, browser installation or previous outputs are required. The target is ten minutes of reading and offline verification after dependencies are installed; download time depends on the machine/network. If you already ran README's commands, reuse their outputs.

## 0–2 minutes — Understand the boundary

Read the [README opening and architecture](README.md#architecture): CSV/XLSX NIPs become company intelligence profiles. **One bounded agent proposes knowledge; deterministic code approves publication.** NIP and the public registry anchor legal identity. The model selects searches/pages and extracts `CompanyResearchDraft`; it cannot invent host source IDs or approve `CompanyProfile` publication. Schema-valid JSON is not evidence.

Start the locked setup if needed:

```sh
uv sync --frozen --python 3.12
```

Installation may download Python/packages. The remaining main path makes no live service calls.

## 2–4 minutes — Run the deterministic proof

```sh
uv run --frozen pytest -q
uv run --frozen company-bi eval --dataset examples/evals/dataset.json --output-dir outputs/evals
```

Read the console counts or `outputs/evals/results.md`, not raw eval JSON first:

| Metric | Frozen result |
| --- | ---: |
| Overall supported precision | 47/47 |
| Researched supported precision | 5/5 |
| Eligible researched recall | 5/19 |
| Unsupported-as-supported | 0 |
| Registry precision | 42/42 |
| Identity correctness | 10/10 |
| Correct uncertainty handling | 28/28 |
| Strict unknown handling | 40/41 |

The 12 cases are nine controlled examples and three retained-real replays. Precision counts correctly supported observations over published supports; recall counts published eligible research over eligible retained gold. **5/5 is not production precision; 5/19 is low coverage.** Registry successes must not hide the real-company researched yield of **0/7**. The missing strict-unknown obligation belongs to a safely rejected run with no final Fact, not an invented unknown profile.

## 4–6 minutes — Inspect two adversarial boundaries

```sh
uv run --frozen pytest -q \
  tests/test_evidence.py::test_month_only_event_occurrence_does_not_become_first_of_month \
  tests/test_evidence.py::test_operating_profit_is_not_net_result
```

Open those named functions in [`tests/test_evidence.py`](tests/test_evidence.py), not the whole suite:

- **Date precision:** source text says “In July this year.” A supported event remains supported, but candidate occurrence `2026-07-01` is cleared to `None`; publication date does not authorize an occurrence day.
- **Metric substitution:** operating-profit evidence proposed as net result becomes `uncertain` with no selected amount.

These are actual deterministic gate regressions, not invented model demonstrations or proof of arbitrary research quality.

## 6–8 minutes — Inspect three outcome classes

```sh
uv run --frozen python scripts/review_offline.py --output-dir outputs/review
```

Open `outputs/review/review-manifest.json`, then these exact artifacts:

| Label | Artifact | What to inspect |
| --- | --- | --- |
| **CONTROLLED FIXTURE — COMPLETE** | `outputs/review/controlled/synthetic-complete.md` and `.json` | Existing fictional `examples/profiles/complete.json`; supported core fields show the rendering contract, not real extraction yield. |
| **REAL RETAINED RUN — PARTIAL** | `outputs/review/retained/asseco-poland.md` and `.json` | Current gate applied to the committed public Asseco run; uncertain entity/Group context and unknown/null financial values remain visible. |
| **CONTROLLED FAILURE — FAILED** | `outputs/review/controlled/provider-interruption-research.json` | `diagnostics.status: failed`, `MODEL_FAILURE`, one guarded local FunctionModel interruption. The manifest has `company_profile_or_report: null`; no final report is fabricated. |

The helper has zero external/paid-provider calls and one in-process model function call. Its failure timestamp/duration reflect this local invocation. The real input is [`examples/evals/retained/asseco-poland.json`](examples/evals/retained/asseco-poland.json): inspect `draft`, `sources` (IDs, kind, retained content, metadata) and `diagnostics` to follow one actual historical AI run without credentials.

**PARTIAL is a valid product result**, not a crash. Missing financials alone do not mean FAILED. Research `completed` means a candidate draft exists, not complete publication. Unresolved identity is a separate safe no-profile outcome.

## 8–10 minutes — Read the falsification, not a sales claim

**2/19 → failure classification → regression-first corrections → 5/19; false-supported 0 → 0.** Three controlled claims recovered; retained-real researched yield stayed **0/7**. This demonstrates a measured correction process, not good coverage. Retrieval/extraction/gate/unavailable-context attribution uses distinct populations; no frozen gold was rewritten to improve the score.

Scrapling remains the full-page retrieval mechanism. The paired experiment demonstrated **no additional published supported facts**, and only one pair exercised retrieval. The result is limited/inconclusive, not superiority or universal ineffectiveness.

Read only the relevant sections if you want to challenge a claim:

- [Evaluation methodology](docs/EVAL_SPEC.md#separate-metrics) and [current result](docs/EVAL_RESULTS.md#og-154a--targeted-recovery-separate-from-the-frozen-baseline).
- [Before/after and remaining misses](docs/RECALL_RECOVERY.md#same-frozen-set-before--after).
- [Clean-clone audit and post-hardening PARTIAL smoke](docs/CLEAN_CLONE_AUDIT.md#single-final-live-smoke).
- [Scrapling falsification](docs/SCRAPLING_EXPERIMENT.md#verdict).

Keep the non-claims visible: weak real yield, unsupported financial PDF/XML/archive/Office parsing, DNS rebinding/TOCTOU, provider/web variability and unrecoverable historical LPP output-failure cause. No population-accuracy or production-SaaS claim.

### Optional live run — outside the timed proof

Follow [README's separately configured live command](README.md#optional-live-research) only if credentials are available. It uses the three public company NIPs in `examples/research_batch.csv`, Tavily and the tested native Codex path; it can incur costs. No live run is required for this review.

## Maintainer appendix — outside the timed path

### Static checks

```sh
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen ruff format --check src tests
```

### Final isolated reviewer audit

The OG-157 package passed a genuine `git clone --no-local` of temporary review snapshot `246610bfb020a4c0985206e5a3b004470290fcb6` (parent `05dafda`). HOME, Codex state, config, cache, temporary files, Python installation and virtualenv were isolated. No dotenv files, paid-key variables, authentication cache or prior runs were copied; runtime inspection confirmed Python **3.12.13** and package/virtualenv paths inside the clone.

Using only the README/guide commands: locked installation, **265 tests**, the **two named adversarial tests**, offline eval, the review helper, Ruff lint, mypy (**14 source files**) and formatting (**25 files**) passed without rescue. The command sequence took **20.94 seconds**, including installation on this machine—not a portable setup-time promise. **17 upstream `strip_cdata` warnings** remain visible.

The generated JSON, Markdown and provenance manifest were inspected: controlled COMPLETE, real Asseco PARTIAL with null financials, and controlled FAILED with `MODEL_FAILURE` and no report. All frozen metric objects matched with no input-hash errors. The final implementation-checkout validation also passed. Production source, tests, scripts, lock, gold and retained fixtures stayed unchanged. Relative documentation links were checked and the Mermaid diagram rendered; no frontend or application feature was added.

### Instrumentation decision

**AgentCanvas: SKIPPED.** There is no active trace-producing setup. Adding instrumentation/configuration would expand packaging work without improving this short evidence path. Retained provenance, diagnostics and deterministic reports already expose the important boundaries.

### Public-repository safety and metadata

At approved baseline `05dafda`, all eight reachable commits' 120 distinct text blobs (about 2.98 MB) were inspected by local pattern scanning for API/provider keys, private-key blocks, bearer/JWT material, credential assignments/URLs/headers, emails and absolute machine paths. No known committed credentials, private customer records or machine-local paths were found. Hits were one synthetic Bearer sentinel in a sanitization regression and two corporate role addresses retained in public Asseco/ORLEN source text. No credential/session paths were tracked. This is a bounded audit, not proof that automated scanning finds every secret. Ignored dotenv/authentication state was not opened.

Package metadata remains `company-bi` 0.1.0, Python `>=3.12`; the tested reviewer environment is Python 3.12. `.env.example` contains placeholders only; dotenv files, caches, `runs/` and `outputs/` remain ignored. No tracked scratch/generated clutter required removal. Historical project and experiment documents remain as evidence, outside the timed path.

### License and publication

The operator selected the [MIT License](LICENSE): copyright © 2026 Tomasz Gonczar.

Publication target: [TomaszGonczar/company-bi-research-agent](https://github.com/TomaszGonczar/company-bi-research-agent). The pre-publication OG-157 audit recorded hosted CI as **NOT VERIFIED** because no remote existed then. Check [Actions → CI](https://github.com/TomaszGonczar/company-bi-research-agent/actions/workflows/ci.yml) for the reviewed commit's actual hosted result; local verification alone is not a hosted pass.

The `v0.1.0` checkpoint requires a successful public push, a **VERIFIED PASS** hosted run and a fresh public zero-key clone. No GitHub Release or generated marketing copy is required.
