# Reviewer guide — Company BI

This is a credential-free offline review path. `uv sync` may download Python and dependencies; verification itself makes no model, registry, search, page, or other network calls. No API key, login, browser, or prior outputs are needed.

## Thesis and contract

A research agent may propose broadly. Deterministic publication is deliberately narrow: it recognizes a finite contract and abstains when semantics are unknown or outside that contract. This is neither general language understanding nor a demonstrated broad-coverage research product. See the [README](README.md), normative [strict publication contract](docs/STRICT_PUBLICATION_CONTRACT.md), and [holdout adjudication](docs/HOLDOUT_ADJUDICATION.md).

The contract's semantic unit is the entire retained full-page text, NFC-normalized and outer-trimmed, limited to 4096 Unicode code points. It must match one complete production exactly, including its final full stop; clipping, surrounding context, extra clauses/sentences, or combining assertions is not allowed. The resolved legal name must match literally after NFC/whitespace-run normalization; labels are exact opaque quoted strings, not a vocabulary. Each qualitative list item needs its own supported unit. Employees, financials, and events have separate exact finite productions and component rules. Source ownership, full-page provenance, lineage, identity consistency, citation membership, and existing structural invariants remain required. The contract defines every allowed shape and boundary; do not infer unlisted synonyms, formats, or semantic rules.

The agent's proposal is not publication approval. The gate does not authenticate arbitrary edited ledgers, prove publisher truth, or interpret text outside its finite language. Structured output validates shape, not truth. Unrecognized true prose is out of contract, not disproven.

**v0.1.1 was released** at annotated tag `v0.1.1`, commit `83a9e42940190d88ed065c5804be331d3b40d48e`; [release](https://github.com/TomaszGonczar/company-bi-research-agent/releases/tag/v0.1.1). Holdout B remains historical PASS on certified commit `9f80eb7a7dcdb4c563a4bec897f22361cdbbae45`: one independent first execution of 80 calls (70 semantic, 10 boundary; zero reruns), 20/20 supported positives, 20/20 true-OOC abstentions, 30/30 unsafe with no support, and 5/5 each provenance/identity model-rejections. [Original result and limitations](docs/V0_1_1_HOLDOUT_RESULT.md). Its separate 740-test and 262-case local gates are not research accuracy. Earlier defective/missing populations remain historical, not retroactively repaired. v0.2 changes presentation only; its checks below are not a new holdout certification.

The separate v2 reviewer-reported record lists 20/40 unsafe and 34/40 accepted; it was not local CLI execution, is not a current strict-matrix result, and its distinctness from other vendor corpora is unproven. Keep it separate; see [quality report §13](docs/V0_1_1_QUALITY.md#13-separate-v2-reviewer-reported-evidence-not-a-local-strict-result).

## Zero-key v0.2 dossier review

```sh
uv sync --frozen --python 3.12
uv run --frozen python scripts/review_dossier.py --output-dir outputs/dossier-review
```

Choose a fresh root. The script runs nine actual CLI scenarios in network/model-blocked subprocesses and writes one deterministic `review-summary.json`. The two expected refusals are successful review cases, not product success. Inspect:

1. `rich/5220003782.dossier.pdf`: **synthetic**, all eight research fields/observations approved by the unchanged gate; `12.5000` revenue, `-0.7500` net result, PLN millions, explicit legal-entity interval. Main page plus sources/details.
2. `supported/5220003782.dossier.pdf`: **synthetic**, one approved service; unknown finance/employees stay unknown. Questions are fixed prompts, not inferred sales opportunities.
3. `out_of_contract/` and `unsafe/`: zero approved researched facts, uncertain product state, no candidate value or excerpt promoted. These yield identical truthful PDFs but different forensic verification reports.
4. `real-asseco/`: original real capture, partial, **zero** supported research fields; generated **2026-10-03T12:25:47.507942+00:00**. Registry identifiers and quarantined source metadata remain visible. No new live research.
5. `zero-finance/`, `stress/`: labelled synthetic boundary/layout examples; supported zero, long Polish legal name, 40 service labels, markup-like text, source URLs and reasons.
6. `failed-run/`: exit 1, only diagnostic JSON/Markdown/manifest; no profile/PDF. `identity_invalid`: exit 2 and no directory.

[Committed bundles](examples/dossier/generated/) use the same case names. All successful bundles contain the PDF, existing final profile JSON/Markdown, existing verification JSON/Markdown and completion manifest. Check manifest hashes before trusting bundle completeness. This is not an authenticated source signature or a directory-atomic transaction. The companion verification files intentionally contain original proposals; the PDF facts use only the final profile.

To reproduce one example:

```sh
uv run --frozen company-bi dossier examples/dossier/rich.json --output-dir outputs/dossier-rich --synthetic
```

The `--synthetic` flag is a caller classification, not verification of real-world authenticity. Use retained research, not a direct profile. Safe bundle publication requires POSIX no-follow/directory-descriptor primitives; native Windows is not supported. Existing destinations and symlink/hardlink aliases are refused, including symlink ancestors; choose physical paths. On macOS use `/private/tmp`, not symlink `/tmp`, if using temporary absolute paths.

### Layout / package reproduction

Runtime requires only frozen package dependencies and bundled DejaVu Sans 2.37; no Poppler or pypdf. Development-only pypdf checks text, fonts and links. For visual inspection with existing Poppler:

```sh
mkdir -p .work/v0.2/reviewer-pages
pdftoppm -r 150 -png outputs/dossier-rich/5220003782.dossier.pdf .work/v0.2/reviewer-pages/page
uv build --out-dir .work/v0.2/dist
```

Open every rendered page, not just the first. The recorded review inspected all **47 pages** across seven PDFs: 1–2 main pages each, readable 10.5 pt body, full appendix. Text extraction alone does not prove visual quality. Repeat renders were byte-identical in the tested locked environment; no universal cross-platform/library-version byte guarantee.

For a clean wheel smoke, export locked runtime requirements with `uv export --frozen --no-dev --no-emit-project --format requirements-txt --output-file .work/v0.2/runtime-requirements.txt`, create a fresh Python 3.12 environment outside the checkout, install those requirements and the wheel, then invoke its installed `company-bi dossier` with an absolute retained-run input and a fresh physical output directory. Confirm imports come from that environment's `site-packages`, not `src/`, and that both TTFs and LICENSE are in `company_bi/assets/fonts/`. [Actual commands/results, wheel hash, visual findings and release checkpoint](docs/V0_2_RELEASE_CHECKS.md).

Tomasz owns product direction/constraints and release authorization; OMP implemented and ran the recorded checks. No independent human accuracy review or external portfolio reception is asserted.

## Zero-key strict matrix review

Set up if needed:

```sh
uv sync --frozen --python 3.12
```

Run the canonical saved supported-contract matrix input through the offline verifier:

```sh
uv run --frozen company-bi verify examples/strict_contract/supported.json --output-dir /tmp/company-bi-strict-supported
```

The matrix uses five explicit classes: `SUPPORTED_CONTRACT_POSITIVE`, `OUT_OF_CONTRACT_TRUE`, `UNSAFE_NEGATIVE`, `IDENTITY_INVALID`, `PROVENANCE_INVALID`. True OOC abstention is correct, not a missed positive. Invalid wrappers are reported as unexercised, not as successful semantic probes. The audit preserves all initial failures, source-backed adjudication corrections and raw CLI outputs; see [observed results](docs/FINAL_BOUNDARY_REVIEW.md).

The existing [`examples/verification/`](examples/verification/) fixtures and frozen real-company runs are earlier-contract evidence. They can be inspected through the verifier, but are not strict positives and may be rejected for legacy-format provenance or whole-unit/grammar mismatch. For example, the older controlled fixture can be run separately:

```sh
uv run --frozen company-bi verify examples/verification/controlled-financial-sign.json --output-dir /tmp/company-bi-earlier-contract
```

Exit `0` means verification completed, not that every candidate was supported. Downgraded/cleared values must be read from the final side; preserved uncertain/unknown facts are not accepted. Verification does not overwrite the input or fetch source content.

Additional zero-key checks:

```sh
uv run --frozen company-bi verify examples/strict_contract/out_of_contract.json --output-dir /tmp/company-bi-strict-ooc
uv run --frozen python scripts/review_offline.py --output-dir /tmp/company-bi-offline-review
uv run --frozen python scripts/replay_strict_adjudication.py examples/evals/strict-historical.json --output /tmp/company-bi-strict-history.json
uv run --frozen pytest
uv run --frozen ruff check src tests scripts
uv run --frozen ruff format --check src tests scripts
uv run --frozen mypy src
```

The offline review separates current strict probes, historical snapshots and an actual
local `FunctionModel` interruption. It does not call a provider. In the review ZIP,
`audit/holdout/frozen-original/` contains the unchanged defective independent inputs;
`audit/holdout/first-cli/` and `fixture-defects.json` preserve their first rejection and
why it is not an independent semantic pass. Do not silently repair or replace that
population when reproducing this candidate.

## Independent author handoff

Use the [public fixture toolkit](docs/EXTERNAL_HOLDOUT_TOOLKIT.md), not manually assembled
envelopes. Its preflight validates public models only; it never executes the verifier.
Give the external author only the separate restricted author package, not the full
review ZIP containing implementation, old cases and regression outcomes. Preflight all
semantic envelopes, inspect intentional boundary errors, freeze/hash, then execute the
verifier once. No local regression or neutral toolkit example is an independent holdout.

Actual retained Asseco and SONEL replays each publish **0 researched facts**. This is
strict abstention on ordinary retained web prose, **not useful BI output**. The complete
retained baseline utility run set yields 0/13 gold researched claims; its earlier
diagnostics are historical, not new provider calls.


## Historical evidence and population separation

These remain immutable **earlier-contract** measurements, not strict positives or current strict-contract performance:

| Earlier-contract population / measure | Historical result |
| --- | ---: |
| Frozen overall supported precision | 47/47 |
| Eligible researched recall | 5/19 |
| Retained-real researched yield | **0/7** |
| Locked candidates re-gated in the two-company Asseco + SONEL utility set | **1/13 supported; 0 incorrect observed** |
| Asseco-only retained verification | **1/6 supported** |
| Three earlier fresh live end-to-end runs | **zero supported researched observations** |

The 47/47 includes registry facts; 5/19 is limited research coverage. The 1/13, 1/6, 0/7, and earlier live zeros are distinct populations. None establishes strict-contract performance, broad usefulness, or population-level precision. The earlier blocked `66dbbc89` failures and missing original Astra/Opus envelopes remain limitations. Historical counts and documents are preserved, not rewritten as strict-contract outcomes.

The earlier frozen set contains nine controlled and three retained-real replays. Its gold and source snapshots remain historical evidence. Later corrections are regression evidence, not an untouched holdout. The blocked frozen candidate also has an observed post-amount financial-target false support and three conservative full-suite failures; its exact observed status and separated measurements are in the [quality report](docs/V0_1_1_QUALITY.md#11-frozen-remediation-candidate-blocked). Historical methods/results remain in [evaluation specification](docs/EVAL_SPEC.md), [evaluation results](docs/EVAL_RESULTS.md), and [adversarial correction history](docs/ADVERSARIAL_CORRECTIONS.md).

## Offline real-input examples and limitations

The [Asseco verification report](examples/review/asseco-poland-verification.md) and [Sonel partial profile](examples/review/sonel-20261005.md) are historical earlier-contract artifacts, not strict success or fresh strict research. Asseco's earlier report recorded one supported researched observation among six eligible observations; neither artifact is a strict-contract positive.

The documented product boundary is narrow and finite. It does not claim production autonomous coverage, population-level precision, universal semantic verification, comprehensive financial extraction, or reliable real-company researched yield. Retrieved PDF/XML/archive/Office financial parsing remains unsupported. Provider and website behavior vary. URL/DNS checks do not eliminate SSRF; DNS rebinding/TOCTOU remains residual risk. Live research is a separately configured experimental route in the [README](README.md#experimental-live-research-route), not part of this review path.
