# Strict holdout adjudication and replay

`examples/evals/dataset.json`, `gold-corrections.json`, the controlled/retained inputs, and prior results are immutable historical artifacts. The ordinary repository evaluator reports them as `historical_earlier_contract`; it preserves their prior labels and does not claim strict-contract scoring. Revision 3 of the complete historical assertion adjudication lives separately in `examples/evals/strict-historical.json`. It explicitly covers every original `metadata.claim`, preserves each full gold claim and original raw candidate (including `null` where no candidate assertion existed), marks all seven unrecognized controlled registry envelopes `PROVENANCE_INVALID`, and recognizes only the 12 identity facts mapped by the three accepted retained MF host snapshots as strict identity positives. Identity/research denominators are separate. The five wrong-company prior-holdout corrections are a different population in `examples/evals/strict-adjudicated.json`; they are never included in the original-suite denominator. Revisions supersede only adjudication metadata; original gold and first replay artifacts remain unchanged.

The normal command remains the historical view:

```sh
uv run company-bi eval
```

It defaults to `examples/evals/dataset.json`; its `results.json` carries
`"view": "historical_earlier_contract"` and its report heading says so. Strict
adjudicated populations require the explicit replay commands below.

The strict taxonomy is:

- `SUPPORTED_CONTRACT_POSITIVE`: a source-backed observation fits the complete finite production; publication of the adjudicated target is required.
- `OUT_OF_CONTRACT_TRUE`: a true target-company observation outside the finite grammar; abstention is correct and it is excluded from eligible-positive recall.
- `UNSAFE_NEGATIVE`: false, wrong-entity, mismatched or ambiguous proposed component; support is forbidden.
- `IDENTITY_INVALID`: structural identity conflict; rejection is required.
- `PROVENANCE_INVALID`: evidence/provenance is invalid; reject the envelope or withhold the affected fact, without counting a grammar execution.

The evaluator provides `run_strict_view()` separately from historical `run_dataset()`. Every `SUPPORTED_CONTRACT_POSITIVE` remains in the eligible-positive denominator even when rejected or unexercised; those cases are recorded as failed/unassessed rather than dropped. `OUT_OF_CONTRACT_TRUE` abstentions do not enter recall. Strict output separately reports `semantic_execution` (`executed`, `unexercised`, or `not_applicable` for identity/provenance boundaries), assessment totals (`correct`, `failed`, `unassessed`), provenance-rejected/withheld facts, and unsafe supports. Boundary handling is not mislabeled as semantic grammar execution.

```sh
uv run python scripts/replay_strict_adjudication.py examples/evals/strict-historical.json --output /tmp/strict-historical-results.json
uv run python scripts/replay_strict_adjudication.py examples/evals/strict-adjudicated.json --output /tmp/strict-previous-holdout-results.json
```

## Corrected historical positive labels

The five historical cases below were labeled positive in the old population but are wrong-company claims. The target and assertion subject are recorded in the retained input; gate outcomes are not the basis for these adjudications. Each is classified `UNSAFE_NEGATIVE`, never `OUT_OF_CONTRACT_TRUE`:

| Case | Target identity | Assertion subject | Family |
|---|---|---|---|
| `p06-01-positive` | Northglass Works sp. z o.o. | Brindle Harbor | employee semantics/entity |
| `p06-02-positive` | Northglass Works sp. z o.o. | Juniper Vale | employee semantics/entity |
| `p07-01-positive` | Quiet Amber sp. z o.o. | Brindle Harbor | event denial/full context |
| `p07-02-positive` | Quiet Amber sp. z o.o. | Lumen Orchard | event denial/full context |
| `p07-03-positive` | Quiet Amber sp. z o.o. | Copper Finch | event denial/full context |

The five byte-for-byte inputs are vendored under `examples/evals/adjudicated/previous_holdout/`; their SHA-256 hashes are recorded alongside each strict-view case and match the preserved audit originals. Original audit result records (`results.rescored.json`, `results.json`) remain in the audit tree and are not treated as strict labels.

## Population and provenance boundaries

The strict-view format accepts separate case populations with explicit `case_id`, `classification`, `family`, `shape`, fact `path`, raw `run`/source envelope, expected behavior, rationale and optional original-label/source provenance. Replay them one population at a time and write each raw output to a distinct destination. Do not combine historical, OMP, Astra, Opus, or prior holdout denominators. In particular, the originally executed Astra/Opus v1/v2 inputs and runners are unavailable; reconstructions are not exact replays. The available OMP, Astra reproduction and Opus reproduction corpora are separate reconstructed/source populations and must retain their provenance status. A provenance-rejected envelope is recorded separately from an assertion grammar execution; it provides no semantic support result.

For an available retained corpus, `scripts/convert_adjudications.py` converts only
cases covered by a separate human-authored override JSON. Each override must explicitly
name its taxonomy class, expected behavior, rationale, and source reference; cases
without overrides are emitted as `unadjudicated_case_ids`. It never maps old `role`,
pass/fail, or gate outcomes into strict labels. Example invocation (repeat separately
for each source population):

```sh
uv run python scripts/convert_adjudications.py \
  /path/to/corpus.cases.json /path/to/manual-overrides.json \
  --output /tmp/population-strict.json
uv run python scripts/replay_strict_adjudication.py \
  /tmp/population-strict.json --output /tmp/population-replay.json
```

Available source populations include the audit's OMP cases and
`corpora/astra-reproductions/astra.cases.json` /
`corpora/opus-reproductions/opus.cases.json`. Their original exact executed Astra
and Opus v1/v2 envelopes are unavailable. The conversion interface retains each
reconstruction's source population/case ID and makes absent human adjudications
visible instead of manufacturing labels.

No network/provider/model calls or original corpus generators are involved in replay. The five previous-holdout raw inputs are exact SHA-256-verified copies in their separate view directory; audit originals, original repository historical inputs/gold/results, and external corpus inputs remain unchanged.
