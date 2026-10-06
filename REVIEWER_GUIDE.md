# Reviewer guide — Company BI

This is a credential-free offline review path. `uv sync` may download Python and dependencies; verification itself makes no model, registry, search, page, or other network calls. No API key, login, browser, or prior outputs are needed.

## Thesis and contract

A research agent may propose broadly. Deterministic publication is deliberately narrow: it recognizes a finite contract and abstains when semantics are unknown or outside that contract. This is neither general language understanding nor a demonstrated broad-coverage research product. See the [README](README.md), normative [strict publication contract](docs/STRICT_PUBLICATION_CONTRACT.md), and [holdout adjudication](docs/HOLDOUT_ADJUDICATION.md).

The contract's semantic unit is the entire retained full-page text, NFC-normalized and outer-trimmed, limited to 4096 Unicode code points. It must match one complete production exactly, including its final full stop; clipping, surrounding context, extra clauses/sentences, or combining assertions is not allowed. The resolved legal name must match literally after NFC/whitespace-run normalization; labels are exact opaque quoted strings, not a vocabulary. Each qualitative list item needs its own supported unit. Employees, financials, and events have separate exact finite productions and component rules. Source ownership, full-page provenance, lineage, identity consistency, citation membership, and existing structural invariants remain required. The contract defines every allowed shape and boundary; do not infer unlisted synonyms, formats, or semantic rules.

The agent's proposal is not publication approval. The gate does not authenticate arbitrary edited ledgers, prove publisher truth, or interpret text outside its finite language. Structured output validates shape, not truth. Unrecognized true prose is out of contract, not disproven.

**Release status: BLOCKED, not released.** Local verification passed 262/262 canonical CLI cases and 621 pytest tests, with green Ruff/format/mypy. The fresh 70-case independent corpus failed envelope validation before its intended probes, so independent acceptance remains unproven; no reroll or production retuning followed. See the [strict review](docs/STRICT_CONTRACT_REVIEW.md). The prior `66dbbc89` failures and unavailable original Astra/Opus corpora remain separate historical evidence, not replaced denominators.

The separate v2 reviewer-reported record lists 20/40 unsafe and 34/40 accepted; it was not local CLI execution, is not a current strict-matrix result, and its distinctness from other vendor corpora is unproven. Keep it separate; see [quality report §13](docs/V0_1_1_QUALITY.md#13-separate-v2-reviewer-reported-evidence-not-a-local-strict-result).

## Zero-key strict matrix review

Set up if needed:

```sh
uv sync --frozen --python 3.12
```

Run the canonical saved supported-contract matrix input through the offline verifier:

```sh
uv run --frozen company-bi verify examples/strict_contract/supported.json --output-dir /tmp/company-bi-strict-supported
```

The matrix uses five explicit classes: `SUPPORTED_CONTRACT_POSITIVE`, `OUT_OF_CONTRACT_TRUE`, `UNSAFE_NEGATIVE`, `IDENTITY_INVALID`, `PROVENANCE_INVALID`. True OOC abstention is correct, not a missed positive. Invalid wrappers are reported as unexercised, not as successful semantic probes. The audit preserves all initial failures, source-backed adjudication corrections and raw CLI outputs; see [observed results](docs/STRICT_CONTRACT_REVIEW.md).

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
