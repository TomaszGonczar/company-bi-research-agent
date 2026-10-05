# Reviewer guide — Company BI

Follow these sections in order from the repository root. They describe a credential-free, offline review path; `uv sync` may download Python and dependencies. The section labels organize the review and are not a timing guarantee. No live service calls, API keys, login, browser, prior outputs, or internal history are needed.

## 0–2 — Thesis and architecture

The bounded PydanticAI research agent proposes candidate company facts; deterministic code applies the publication gate and the offline verifier compares candidate with final facts using the retained source ledger. Read the [README architecture](README.md#architecture-and-report-interpretation). Polish NIP validation and the registry anchor legal identity; the model chooses research and proposes claims, but cannot assign host source IDs or approve publication. Structured output validates shape, not truth.

The verifier inspects the supplied retained run; it does not authenticate arbitrary edited JSON, prove publisher truth, or fetch sources. It makes accepted, downgraded, cleared, and preserved outcomes inspectable. A preserved uncertain or unknown fact is not accepted support.

Set up if needed:

```sh
uv sync --frozen --python 3.12
```

## 2–4 — Compare accepted and rejected claims

Run the controlled financial-sign fixture first:

```sh
uv run --frozen company-bi verify examples/verification/controlled-financial-sign.json --output-dir outputs/verification
```

It writes `profile.json`, `profile.md`, `verification.json`, and `verification.md`. Inspect `outputs/verification/verification.md` first: the explicitly current product is accepted, while the candidate **+PLN 10m net result** is rejected against retained evidence of a standalone **−PLN 10m net loss**. This is a controlled synthetic fixture, not evidence of real-company yield.

Two more controlled examples:

```sh
uv run --frozen company-bi verify examples/verification/controlled-planned-activity.json --output-dir outputs/verification-planned
uv run --frozen company-bi verify examples/verification/controlled-current-service.json --output-dir outputs/verification-current
```

The planned cloud-service assertion is downgraded rather than treated as a current offering; the current-service fixture provides another controlled positive.

Exit `0` means verification completed, even when facts were downgraded or cleared; it does **not** mean every candidate claim is supported. Preserved uncertain/unknown facts remain non-supported, not accepted. Clearing can be partial: an event may stay supported while an unverified occurrence date becomes null; inspect final snapshots and changed paths rather than carrying candidate values forward. A valid failed research run produces only `verification.json` and `verification.md`, with `not_published`, diagnostics/reason, and empty deltas; it has no profile and exits `1`. Invalid input, gate, or file errors exit `2`. The verifier does not overwrite its input.

## 4–6 — Inspect adversarial boundaries

These existing adversarial regression tests exercise defined verifier and deterministic-gate cases; they do not establish general semantic safety or arbitrary research quality:

```sh
uv run --frozen pytest -q \
  tests/adversarial/test_verification.py \
  tests/test_evidence.py::test_month_only_event_occurrence_does_not_become_first_of_month \
  tests/test_evidence.py::test_operating_profit_is_not_net_result
```
Review [`tests/adversarial/test_verification.py`](tests/adversarial/test_verification.py) for verifier-specific regression cases and the named functions in [`tests/test_evidence.py`](tests/test_evidence.py) for gate boundaries:

- **Date precision:** source text says “In July this year.” Candidate occurrence `2026-07-01` is cleared to `None`; publication date does not authorize an occurrence day.
- **Metric substitution:** operating-profit evidence proposed as net result becomes uncertain with no selected amount.

The verifier reports observed candidate-to-final changes; it does not add a separate semantic interpretation layer. The exercised regression sets support only the bounded conclusion: **current bottleneck is research coverage, not publication safety in those sets**. Cleared values must be read from the final side, not inferred from candidate values.

## 6–8 — Evaluation populations and tests

Run the deterministic suite and frozen evaluation if desired:

```sh
uv run --frozen pytest -q
uv run --frozen company-bi eval --dataset examples/evals/dataset.json --output-dir outputs/evals
```

Keep the populations separate:

| Population | Result |
| --- | ---: |
| Historical frozen overall supported precision | 47/47 |
| Historical eligible researched recall | 5/19 |
| Historical retained-real researched yield | **0/7** |
| Fixed two-company real-source utility set: Asseco 6 + SONEL 7, locked baseline candidates re-gated | **1/13 supported; 0 incorrect observed** |
| Asseco retained verification report | **1/6 supported** |
| Three fresh live end-to-end runs | **zero supported researched observations** |

The historical overall precision includes registry facts; 5/19 is low eligible research coverage. **Neither 47/47 nor historical 5/5 researched support precision is production precision.** In the fixed two-company real-source utility set (Asseco 6 + SONEL 7), locked baseline candidates re-gated by the current verifier yielded 1/13 with 0 incorrect observed; the Asseco report alone yielded 1/6. These are not a single-run 1/13 result or 1/1 production precision. Zero incorrect observed with one support—or zero supports in the fresh live runs—is not precision evidence. Keep the historical, two-company re-gating, Asseco-only, and fresh-live populations separate.

The historical 12-case frozen set contains nine controlled and three retained-real replays. Its source snapshots and gold remain historical evidence. A later adversarial review exposed finite counterexamples; corrections are regression evidence, not an untouched holdout. The earlier historical failed pass remains part of the record and is not claimed fixed by the verifier interface. See [evaluation methodology](docs/EVAL_SPEC.md), [historical results](docs/EVAL_RESULTS.md), [adversarial corrections and measurements](docs/ADVERSARIAL_CORRECTIONS.md), and [quality and scoped utility evidence](docs/V0_1_1_QUALITY.md).

## 8–10 — Real retained input and limits

The real input command is also offline and writes to a separate output directory:

```sh
uv run --frozen company-bi verify examples/utility_v011/runs/baseline/asseco-poland.json --output-dir outputs/asseco-verification
```

[`examples/review/asseco-poland-verification.md`](examples/review/asseco-poland-verification.md) is a **REAL RETAINED VERIFICATION**, not successful BI or fresh research. It reports exactly one researched support out of Asseco's six eligible observations (**1/6**). The fixed real-source utility set covers Asseco (6) and SONEL (7), with 1/13 supported researched observations across the two companies. The input is an existing retained run; no copy, re-research, or network call is part of this review.

The demonstrated capability is deterministic identity anchoring, provenance and evidence rules, replay, failure isolation, and transparent publication decisions. Not demonstrated: production autonomous coverage, population-level precision, universal semantic verification, comprehensive financial extraction, or reliable real-company researched yield. Retained-real historical researched yield remained **0/7**; current utility is weak and experimental.

Substantive limits remain: retrieved **PDF/XML/archive/Office financial parsing is unsupported**; provider and website behavior vary; Scrapling's supported-fact advantage was not demonstrated in a limited paired experiment; URL/DNS checks do **not** eliminate SSRF, with DNS rebinding/TOCTOU residual risk. The historical LPP run failed at its single repair ceiling and its exact cause is unrecoverable. No production-SaaS, population accuracy, or universal extraction claim follows from these demonstrations.

Live research is a separately configured **experimental** route documented in [README](README.md#experimental-live-research-route); it is not part of the reviewer path and is not required to inspect the verifier.
