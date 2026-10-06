# OG-156 — clean-clone audit

**Historical earlier-contract audit:** the clone/reviewer measurements below predate the strict publication contract. They document the then-current offline review path and immutable earlier-contract populations; they are not strict positives or current strict-contract results. See [STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md) and [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md). No strict execution result is asserted by this historical audit.

## Audited baseline and isolation

- Approved baseline: `9dcbf0b9988e63d510ef358b24d53a18b8d870fc`.
- OS: Darwin 27.0.0, arm64. Available host Python before setup: 3.14.8; uv: 0.12.3. The fixed README explicitly selected and installed CPython 3.12.13.
- First pass used a genuine `git clone --no-local` of the approved local repository into a new empty temporary directory. No remote was configured, so this was a local Git transport, not an authenticated GitHub clone.
- Separate HOME, CODEX_HOME, temporary directory, uv cache, Python installation directory and virtualenv. Git global/system configuration was disabled during the clone. No `.env`, `.env.model`, OAuth cache, original ignored `runs/` or `outputs/` was copied.
- The fixed pass was another genuine clone of a temporary audit-snapshot commit, `c0b86cd415a0f824608f2c3a04512c62e34336e3`, whose parent was the approved baseline. It contained the README and two narrow reproduction scripts; production source, dependencies and original evaluation data were unchanged. It was not an archive placed over the development checkout.
- Runtime inspection confirmed Python 3.12, `.venv` and imported package under that clone, no dotenv files/paid keys, empty Codex state, and no copied `runs/`. `outputs/` was created only by the documented offline commands.

## First README-only pass: naturally blocked

The repository root contained no `README*` or `readme*` file at the approved commit. The unfamiliar-reviewer pass stopped there: no README setup, offline/live distinction, sample command, output location or outcome explanation was available. No `PROJECT.md` or internal implementation knowledge was used to rescue that first attempt before recording the failure.

Classification: **documentation defect**, not a paid-provider or native-model failure. This is a material 10-minute-reviewer blocker; there was no successful first README-only path to claim.

## Minimal fixes and observed regressions

1. Added [README.md](../README.md) with explicit Python 3.12 locked setup, zero-key verification, sample ingestion, replay/render command, output map, source provenance, state explanations, frozen metrics and a separate LIVE RESEARCH section.
2. Added [review_offline.py](../scripts/review_offline.py), a narrow committed-fixture replay. It reuses actual ingestion/NIP validation, the evidence gate, canonical renderers and the existing guarded FunctionModel research path. It does not add a production CLI mode, provider abstraction or alternate validation rules.
3. Before the fixed-clone rerun, the actual helper command exposed missing `FunctionModel`, then `ExitStack` imports in this new helper. Both failed-before observations were retained, the imports were corrected, and the same command passed afterward. These were new-helper code defects, not a reconstruction of historical LPP failure.
4. Removed an unnecessary no-op client and preserved actual generated time/duration in the controlled failure artifact. Network/provider guards and explicit provenance distinguish one local FunctionModel invocation from zero paid/live-provider calls.

No production-source, prompt, model, schema, gate, dependency or retry/resource change was required. The missing README was the genuine initial defect; no artificial baseline defect was manufactured.

## Exact documented rerun

From the new clone root, with the isolated environment and no paid keys:

```sh
uv sync --frozen --python 3.12
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src/company_bi
uv run --frozen company-bi eval --dataset examples/evals/dataset.json --output-dir outputs/evals
uv run --frozen python scripts/review_offline.py --output-dir outputs/review
```

Observed results:

- Locked installation: passed; downloaded the selected Python and locked packages into the isolated environment. Dependency-install network access is distinct from deterministic execution.
- pytest: **265 passed**, **17 upstream `strip_cdata` warnings retained**.
- Ruff lint: passed; format check: **37 files already formatted**.
- mypy: no issues in **14 source files**.
- Offline eval: passed; no input hash errors and every expected metric object matched the approved frozen reference.
- Actual offline review command: passed, with **0 external network calls**, **0 paid/live-provider calls**, and **1 controlled local FunctionModel interruption**. No keys, login, Chromium installation, previous runs or outputs were required.
- JSON, Markdown, provenance manifest and typed failed-research artifact were opened and checked, not inferred from test success alone.

## Reviewer path and outcome inspection

| Review artifact | Provenance and observed outcome |
| --- | --- |
| `outputs/review/review-manifest.json` | Input/result/provenance map; sample `5220003782` and `1234563218` accepted, `123` rejected by the actual checksum/format validator. No MF lookup is implied by checksum validity. |
| `outputs/review/retained/asseco-poland.{json,md}` | Retained public real research, republished through the unchanged gate; **PARTIAL**. |
| `outputs/review/retained/lpp.{json,md}` | Retained public real research; **PARTIAL**. |
| `outputs/review/retained/orlen.{json,md}` | Retained public real research; **PARTIAL**. |
| `outputs/review/controlled/synthetic-complete.{json,md}` | Existing fictional final-profile fixture; **COMPLETE**, explicitly synthetic, not real extraction yield. |
| `outputs/review/controlled/provider-interruption-research.json` | Controlled local provider interruption through actual research code; **FAILED**, `MODEL_FAILURE`, safe stage/class diagnostics, one model-function request. No CompanyProfile or final-report path is fabricated. |
| `outputs/evals/results.{json,md}` | Separate deterministic evaluation report, not per-company BI output. |

PARTIAL is valid: supported registry identity and any supported research may coexist with uncertain/unknown fields. A missing financial value is null, never zero. COMPLETE synthetic data demonstrates the output contract; it does not conceal the retained real **0 complete / 3 partial / 0 failed** outcome or **0/7** eligible real researched yield.

The README gives commands and paths before internal architecture material. It explains research JSON versus final batch JSON/Markdown, source citations versus debug dumps, why completeness differs from research completion, and which examples are controlled versus retained real. These resolve the material entrypoint/provenance/where-is-the-output friction without OG-157 presentation packaging.

## Hosted CI

**NOT VERIFIED.** `git remote -v` returned no configured remote and the GitHub device had no repository target. There was no known authenticated GitHub destination to push safely; no repository/remote was guessed or created and no push was attempted. A hosted workflow could therefore not be observed.

The existing workflow was exercised locally through the documented checks in a real fresh clone. That is not a claim that GitHub Actions ran.

## Single final live smoke

After the clean-clone rerun and paired experiment, exactly one fresh Asseco Poland (`5220003782`) CSV row was submitted through the normal native batch path:

```sh
uv run --frozen --env-file .env company-bi batch outputs/og156-final-smoke-9f64f344/input.csv --output-dir outputs/og156-final-smoke-9f64f344/reports --runs-dir runs/og156-final-smoke-9f64f344 --model openai-codex:gpt-6-luna
```

The configured dotenv was loaded only by the live command; its contents and native authentication cache were not inspected or copied. There were no force/retry flags, subsequent smoke attempts or post-result tuning.

| Observation | Actual result |
| --- | --- |
| Batch / canonical profile | **PARTIAL**, one row; research diagnostics `completed` |
| Identity | Fresh MF lookup; legal name, KRS, REGON and registered address supported |
| Searches / page reads / dynamic reads | **5 / 4 / 0** |
| Model requests / output repairs | **4 / 1** |
| Input / output tokens | **47,556 / 3,388** |
| Research duration / complete command wall time | **88.374794 / 90.40 seconds** |
| Reported monetary cost | Unavailable (`cost_usd: null`) |
| Post-gate researched states, excluding registry-only identity | **0 supported / 7 uncertain / 3 unknown** |
| Financials | Both unknown with null values; no snippet-derived amount or attributable-profit substitution |

Two official HTML news pages were retained as static full-page sources. Two official annual-report PDF reads returned unsupported content; no document parser or browser retry was added. One initial output was rejected at `employees.evidence.0.excerpt` (`EVIDENCE_VALIDATION_FAILURE`, stage `evidence_validation`, `_DraftValidationFailure`, attempt 1). The one allowed output repair completed. Both PDF failures remain recorded as `FETCH_FAILURE`, stage `static_fetch`, `_UnsupportedContent`, attempt 1, source IDs `S003` and `S001`. No validated progress was retained.

Diagnostics retain `failure_code: EVIDENCE_VALIDATION_FAILURE` and the fetch stop reason even though the repaired research completed. These are recorded attempt-level failures, not a claim that the batch failed. Final JSON/Markdown preserved the group/segment-versus-legal-entity ambiguity as uncertain and cleared unverified news details. No researched claim was published supported.

The actual canonical JSON, Markdown, `batch_summary.csv`, `_batch_state.json` and newly created `research.json` were inspected. Evidence remains in the ignored `outputs/og156-final-smoke-9f64f344/` and `runs/og156-final-smoke-9f64f344/` directories; raw generated outputs are not committed. This smoke exercised fresh identity → Tavily → Scrapling → native model → gate → JSON/Markdown. Its new initial rejection is not the historical LPP incident.

## Frozen safety/product contract and limits

The observed frozen evaluation remains:

| Metric | Result |
| --- | ---: |
| Overall supported precision | 47/47 |
| Researched supported precision | 5/5 |
| Eligible researched recall | 5/19 |
| Unsupported-as-supported | 0 |
| Registry precision / identity correctness | 42/42 / 10/10 |
| Correct uncertainty / strict unknown | 28/28 / 40/41 |

The denominator is small and diagnostic. Native `openai-codex:gpt-6-luna`, exact instructions, required Fact/financial fields, evidence gate, one repair and bounded operations remain frozen. This audit does not improve recall or establish acceptable real yield.

DNS validate-before-connect is not IP pinning; rebinding/TOCTOU remains possible. Browser redirects can be blocked and sites can refuse retrieval. CSV/XLSX input is supported, but retrieved financial PDF/XML/archive/office parsing is not. Existing dependency warnings remain visible.

Historical optional LPP diagnostics cannot reveal its exact old validation cause. The controlled reviewer failure is not that incident. Existing initial-invalid/still-invalid/validated-progress regressions were retained and passed in the 265-test fresh run; no historical failure was artificially recreated.

## Final credential-free verification

The implementation checkout's final run also passed: **265 tests**, **17 retained upstream warnings**, Ruff lint, **39 files formatted**, and mypy for **14 source files**. The JUnit results confirm the existing initial-invalid output, still-invalid repair, malformed/invalid progress and retained-safe-progress regressions passed. No historical LPP cause was reconstructed.

The unchanged deterministic evaluation matched **every frozen metric object**, with no input-hash errors. The invalid-source and invalid-NIP cases retained their intended rejection/invalid-input outcomes. All **33 protected source/config/original-evaluation Git content hashes**, **20 explicitly frozen SHA-256 entries**, and the exact instruction SHA-256 `8a61dde9032724d667636cc2d0fa5d67c8b2ade77ee99e09aa79f36382b04a6b` matched the approved reference. Native provider behavior, schemas, gate, repair/resource limits, lock and original gold/baselines/snapshots were not changed.
