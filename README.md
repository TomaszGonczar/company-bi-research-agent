# Company BI

## v0.2.0 — Polish PDF dossier

Offline, human-readable presentation of the **final verified profile**: one or two A4 main pages plus a full sources/details appendix. The v0.1.1 publication language and profile schema **0.1** are unchanged. Better presentation is not better research.

```sh
uv sync --frozen --python 3.12
uv run --frozen company-bi dossier examples/strict_contract/supported.json --output-dir outputs/dossier-supported --synthetic
```

Use a **fresh** destination each time. This synthetic example publishes one approved service and preserves unknown sections. No key, login, network, browser or Poppler is needed to generate the PDF. Fonts and their license ship in the package.

The successful directory contains `5220003782.dossier.pdf`, `profile.json`, `profile.md`, `verification.json`, `verification.md` and `dossier-manifest.json`. Input is a retained `CompanyResearchRun`, **not** a bare profile. Exit **0** = published complete/partial; **1** = valid failed run, diagnostics only; **2** = invalid run or file/render failure, no completed bundle. Original research dates are never replaced by today's date.

Bundles use exclusive fresh-directory creation and a **completion-manifest-last** protocol, not whole-directory atomicity. Accept a bundle only when the manifest and all listed SHA-256 hashes validate. Existing paths, traversal, symlink paths and hardlink aliases are refused; use physical paths (on macOS `/tmp` is a symlink). Safe publication targets POSIX systems; macOS was tested locally and Linux CI is a release gate. Native Windows refuses unsupported primitives. Hashes and `--synthetic` classification do not authenticate the input.

[Demo PDFs and companion bundles](examples/dossier/generated/) · [Dossier contract](docs/V0_2_DOSSIER_CONTRACT.md) · [QA / release evidence](docs/V0_2_RELEASE_CHECKS.md) · [GitHub releases](https://github.com/TomaszGonczar/company-bi-research-agent/releases)

```sh
# Nine cases, real CLI subprocesses, blocked network/model entrypoints:
uv run --frozen python scripts/review_dossier.py --output-dir outputs/dossier-review
```

Six labelled synthetic PDF demos cover approved/unknown, rejected, rich, zero/negative and long-content layouts. One original Asseco capture produces a **partial dossier with zero supported researched fields**, dated 2026-10-03; registry identity is explicitly separate. A valid failed run produces diagnostic files only; invalid identity produces no dossier. The rich synthetic fixture is not a researched company result.

### Existing research → dossier

```sh
# Live step: existing Tavily configuration and native Codex authentication required.
uv run --frozen company-bi research 5220003782 --output runs/company-research.json --model openai-codex:gpt-6-luna
# Offline step: no provider calls or new research.
uv run --frozen company-bi dossier runs/company-research.json --output-dir outputs/company-dossier
```

Existing `batch` behavior is unchanged. Its retained runs are `<runs-dir>/<nip>/<UTC YYYYMMDDTHHMMSSffffffZ>/research.json`; use each normalized company's `BatchResult.research_path` in `<output-dir>/_batch_state.json`, not a guessed latest timestamp or a presumed CSV column. Pass that path to `dossier`. Unresolved/failed upstream input is not fabricated into a company report. No automatic batch PDFs were added.

### Contributions and limits

Tomasz set product direction, evidence constraints, the M5 plan and autonomous release authorization. The OMP coding assistant implemented the dossier, fixtures and smoke tooling, repaired observed defects, and performed the recorded semantic/visual/package checks. This does not claim Tomasz independently reviewed each PDF, an external reviewer approved accuracy, or an employer/client received the material. OG-201 remains a separate reception decision.

## Research boundary and v0.1.1 history

A research agent may propose broadly; deterministic publication recognizes only a narrow finite contract and abstains when meaning is outside it. This is not general language understanding or a useful broad-coverage research claim.

Under the [strict publication contract](docs/STRICT_PUBLICATION_CONTRACT.md), the one quoted direct assertion shown here is supported: `Example sp. z o.o. offers "cloud services".` The plausible unquoted assertion `Example sp. z o.o. offers cloud services.` is true but out of contract, so publication abstains. Labels are opaque, not a vocabulary of validated meanings.

**v0.1.1 RELEASED** — [GitHub Release](https://github.com/TomaszGonczar/company-bi-research-agent/releases/tag/v0.1.1). Hosted CI passed on the [release commit on `main`](https://github.com/TomaszGonczar/company-bi-research-agent/actions/runs/37543629186) and [tag `v0.1.1`](https://github.com/TomaszGonczar/company-bi-research-agent/actions/runs/37543759926). The clean public checkout also passed the locked local gates.

**Holdout B: PASS on the sampled frozen finite publication contract.** Certified commit `9f80eb7a7dcdb4c563a4bec897f22361cdbbae45`; the independent first-execution result and limitations are summarized in the [Holdout B report](docs/V0_1_1_HOLDOUT_RESULT.md). Separate local release-preparation gates passed: **740 tests**, Ruff, formatting and mypy, **262/262** canonical CLI cases (**97/97** contract positives), boundary/micro smoke **26/26** and **19/19**, IPv6 CLI/SDK smoke **11/11**, public-toolkit smoke **10/10**, and component-scoring smoke **5/5**. No combined accuracy, publisher-truth, exhaustive-coverage, or useful broad-coverage claim follows. Asseco and SONEL still have **0 researched facts published**. Strict real-world researched yield remains poor.

## Historical evidence (earlier contract)

The earlier-contract fixed populations remain distinct: **47/47** historical overall supported precision, **5/19** eligible researched recall, **0/7** retained-real researched yield, and **1/13** locked-candidate support in the separate two-company utility set (with 0 incorrect observed). Three earlier live end-to-end runs produced zero supported researched observations. These numbers predate the strict contract; none establishes strict-contract performance, population-level accuracy, or useful coverage. The prior blocked `66dbbc89` failures and missing original Astra/Opus envelopes remain limitations, not results repaired by this docs edit; see the [quality report](docs/V0_1_1_QUALITY.md#11-frozen-remediation-candidate-blocked) for the preserved blocker record.

## Offline review

The [reviewer guide](REVIEWER_GUIDE.md) provides the verified zero-key path using `examples/strict_contract/`. Frozen controlled/real-company inputs and the [Asseco](examples/review/asseco-poland-verification.md) / [Sonel](examples/review/sonel-20261005.md) generated reports remain earlier-contract evidence; they are not strict positives and may be rejected for provenance or assertion-unit mismatch.

The verifier inspects a supplied retained run; it does not authenticate arbitrary edited JSON, fetch sources, or prove that a publisher is truthful. Pydantic structured output validates shape, not truth. Unknown semantics remain unpublished rather than inferred.

## Product and evaluation limits

Not demonstrated: production autonomous coverage or population-level precision; universal semantic verification; comprehensive financial extraction; reliable real-company researched yield; or general superiority of a retrieval approach. A finite grammar can abstain on true prose outside its productions. Zero incorrect observations in a small population is not precision proof.

## Zero-key offline review

Use the strict matrix's canonical saved runs as zero-key review inputs without re-research or network access:

```sh
uv sync --frozen --python 3.12
uv run --frozen company-bi verify examples/strict_contract/supported.json --output-dir /tmp/company-bi-strict-supported
```

This writes profile and verification JSON/Markdown. The saved `supported`, `out_of_contract`, `unsafe`, and `identity_invalid` inputs exercise distinct outcomes: only `supported` publishes the researched service; the next two abstain, and invalid identity exits `2` without a profile. [Observed results](docs/FINAL_BOUNDARY_REVIEW.md) · [normative contract](docs/STRICT_PUBLICATION_CONTRACT.md) · [adjudication](docs/HOLDOUT_ADJUDICATION.md).

The existing `examples/verification/` fixtures and frozen real-company runs are earlier-contract examples. They can be inspected with the offline verifier, but are not strict positives and may be rejected for legacy-format provenance or assertion-unit mismatch.

```sh
uv run --frozen company-bi verify examples/verification/controlled-financial-sign.json --output-dir outputs/verification
```

Legacy inputs are historical probes, not strict positives. A rejected legacy envelope exits `2` before producing a profile; it does not demonstrate execution of the research grammar.

## Architecture and report interpretation

```mermaid
flowchart TD
  subgraph I["Deterministic identity"]
    CSV["CSV / XLSX"] --> NIP["Validate Polish NIP"]
    NIP --> MF["MF public registry"]
    MF --> Identity["MF-anchored CompanyIdentity"]
  end
  subgraph A["Probabilistic research"]
    Agent["One bounded PydanticAI agent"] --> Draft["CompanyResearchDraft"]
  end
  subgraph H["Host-owned tools"]
    Search["Tavily discovery"] --> Sources["Source IDs, URLs, timestamps, retained text"]
    Read["Guarded Scrapling page read"] --> Sources
  end
  Identity --> Agent
  Agent --> Search
  Agent --> Read
  Sources --> Agent
  subgraph P["Deterministic publication and offline verification"]
    Identity --> Gate["Evidence gate"]
    Draft --> Gate
    Sources --> Gate
    Gate --> Profile["CompanyProfile"]
    Profile --> Reports["JSON / Markdown"]
    Draft --> Verify["Offline candidate-to-final comparison"]
    Sources --> Verify
    Profile --> Verify
    Verify --> VReports["Verification JSON / Markdown"]
  end
```

The model may choose searches and propose facts; deterministic code owns identity, source IDs, retained evidence, and publication. The strict gate accepts only complete recognized assertion units from eligible retained full-page material; when meaning is unknown or outside the finite grammar, it abstains. **Pydantic structured output validates shape, not truth.** The verifier checks the supplied retained run and its ledger; it does not authenticate arbitrary edited JSON or prove that a publisher is truthful. No source text is fetched during verification.

Exit `0` means verification completed, even if facts were downgraded or cleared; it does **not** mean every candidate claim is supported. Preserved uncertain/unknown facts remain non-supported, not accepted. Invalid input, gate, or file errors exit `2`. Verification does not overwrite its input. See the [reviewer guide](REVIEWER_GUIDE.md) for the strict matrix review path and interpretation.

## Evaluation and adversarial evidence

Historical frozen replay/contract metrics are retained as historical results, not results newly produced by this interface:

| Population / measure | Result |
| --- | ---: |
| Historical overall supported precision | 47/47 |
| Historical eligible researched recall | 5/19 |
| Historical retained-real eligible researched yield | **0/7** |
| Fixed two-company real-source utility set (Asseco 6 + SONEL 7), locked baseline candidates re-gated | **1/13 supported; 0 incorrect observed** |
| Asseco retained verification report | **1/6 supported** |
| Three fresh live end-to-end runs | **zero supported researched observations** |

The historical 47/47 overall count includes registry supports and does not establish autonomous research precision. The two-company 1/13 and Asseco-only 1/6 are distinct scopes; fresh-live zero-support results are another population. None establishes population-level accuracy or useful coverage. The historical replay's changed 4/19 researched recall and 15/19 over-downgrade are reported separately in the [latest quality report](docs/V0_1_1_QUALITY.md#11-frozen-remediation-candidate-blocked). The old historical LPP run failed at its single repair ceiling; its exact cause is unrecoverable. The verifier is a finite publication contract, not a general semantic-safety guarantee.

The historical frozen set selected 12 cases (9 controlled, 3 retained-real); original drafts, gold, and source snapshots remain frozen. Historical researched support precision was 5/5 and eligible recall 5/19; 5/5 is not production precision. A later adversarial review exposed finite counterexamples and corrections; those cases are regression evidence, not an untouched holdout. [Evaluation methodology](docs/EVAL_SPEC.md) · [historical results](docs/EVAL_RESULTS.md) · [adversarial corrections and current measurements](docs/ADVERSARIAL_CORRECTIONS.md) · [quality and scoped utility evidence](docs/V0_1_1_QUALITY.md).

## Experimental live research route

Live research remains an experimental, separately configured path; it is not the offline verifier. It contacts MF, Tavily, websites, and a model and may incur costs. Export `TAVILY_API_KEY` through your usual secret-management method, then use standard `codex login`. The tested path is `openai-codex:gpt-6-luna`, with SDK-managed authentication and no required `OPENAI_API_KEY`. An explicitly selected `openai:` model requires `OPENAI_API_KEY`; this is not a provider-agnostic validation claim. Optional [`.env.example`](.env.example) contains placeholders only; create an ignored `.env` without overwriting existing configuration, then explicitly add `--env-file .env` to `uv run` if using it. Never commit keys or auth caches.

```sh
uv run --frozen company-bi batch examples/research_batch.csv --output-dir outputs --runs-dir runs --model openai-codex:gpt-6-luna
```

Live results, costs, and availability vary. `research` emits a draft/run; `batch` emits final reports and `batch_summary.csv`, with retained research under `runs/`. The measured live samples above published no supported researched observations.

## Reliability, safety, and scope limits

Per-company ceilings: 180 seconds, 6 searches, 10 page reads, 2 browser attempts, 12 model requests, 24 tool calls, and one output repair. [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md#og-152-bounded-research-implementation) record the bounds and trust tradeoffs.

Not production SaaS or multi-tenant; not a complete Polish financial-data platform, universal web extraction, multi-agent orchestration, or resolution of every fact. Retrieved **PDF/XML/archive/Office financial parsing is unsupported** (CSV/XLSX NIP input works). Provider/web variability remains. URL/DNS checks do **not** eliminate SSRF; DNS rebinding/TOCTOU is residual risk. Scrapling remains the full-page mechanism; its supported-fact advantage was not demonstrated in the limited paired experiment.

## Repository map

- `src/company_bi/agent.py` — bounded research; `search.py` / `fetch.py` — Tavily / guarded retrieval.
- `src/company_bi/sources.py` — host ledger; `evidence.py` — publication gate; `verification.py` — offline comparison; `renderer.py` — JSON/Markdown; `batch.py` — failure-isolated, resumable batches.
- `examples/` — controlled fixtures, input, and retained public runs; `tests/` — deterministic regressions.
- `docs/` — [evaluation methodology](docs/EVAL_SPEC.md), [historical results](docs/EVAL_RESULTS.md), [recovery](docs/RECALL_RECOVERY.md), [clean-clone audit](docs/CLEAN_CLONE_AUDIT.md), [Scrapling experiment](docs/SCRAPLING_EXPERIMENT.md).

Licensed under the [MIT License](LICENSE), copyright © 2026 Tomasz Gonczar.
