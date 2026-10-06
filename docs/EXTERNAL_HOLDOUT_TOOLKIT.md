# External holdout case toolkit

This toolkit turns author-written JSON case specifications into synthetic `CompanyResearchRun`
JSON envelopes and checks those envelopes against the public Pydantic models. It does not
classify assertions, decide whether a claim is true, apply the publication contract, or run the
research verifier. Authors assign labels and expected actions themselves.

## Public case specification

A specification is one JSON object (or a list of objects) with these required fields:

- `case_id`: unique author-assigned identifier.
- `classification`: one of `SUPPORTED_CONTRACT_POSITIVE`, `OUT_OF_CONTRACT_TRUE`,
  `UNSAFE_NEGATIVE`, `IDENTITY_INVALID`, or `PROVENANCE_INVALID`.
- `source_assertion`: object with nonempty source `text`; optional `published_on` date.
- `candidate_fact`: object with `field_path`, typed `value`, optional `state`, `context`,
  `reason`, `as_of`, and `context_fields`.
- `expected_action`: author annotation: `publish`, `abstain`, or `reject`.

Supported paths are `draft.business_description`, `draft.products_services`,
`draft.industries`, `draft.markets`, `draft.employees`, `draft.financials.revenue`,
`draft.financials.net_result`, and `draft.recent_developments`. `value` uses the matching
public-model type: text; list of texts; employee object (`{"kind":"exact","count":9}` or
range); decimal JSON string for an amount; or event object (`title`, `summary`, `published_on`,
optional `occurred_on`). A numeric candidate must supply financial `context_fields`: `period`,
`currency`, `unit`, and `scope`; for group scope also supply `group_name`. The builder only
provides unknown financial baseline entries; it does not invent amount context. Employee `as_of`
is a date. `state` defaults to `supported`; `uncertain` and `unknown` are also available. Unknown
candidate values must be null; the builder supplies a reason if omitted. Evidence context defaults
to the source assertion text.

Optional `publication_metadata` can set `url`, `title`, `published_on`, `kind`, and `fetch_mode`.
The builder supplies a fixed synthetic identity (legal name `Example Company sp. z o.o.`, NIP
`5220003782`), registry record, evidence ledger, source IDs, timestamps
(`2026-10-06T12:00:00+00:00`), complete research draft baseline, unknown reasons, and diagnostics
with zero operation counters. It fills financial metric coverage according to the public schema;
authors must supply the financial context for numeric candidate facts.

The output also has `path` identifying the candidate's location for downstream review (for
example `financials.0` or `recent_developments.0`).

For deliberate envelope-boundary controls only, optional `envelope` supports shallow identity
field changes (`{"identity":{"nip":"..."}}`) and indexed source mutations
(`{"sources":[{"index":1,"changes":{"kind":"registry"}}]}`). A source mutation can change
retrieval material fields, including nested source metadata. These narrow operations are reserved
for `IDENTITY_INVALID` and `PROVENANCE_INVALID` cases; they preserve the generated baseline instead
of requiring authors to recreate it. Keep the assertion and candidate fact alongside the mutation.

Neutral example:

```json
{
  "case_id": "sample-product-01",
  "classification": "SUPPORTED_CONTRACT_POSITIVE",
  "source_assertion": {"text": "Example Company sp. z o.o. offers \"sample item\"."},
  "candidate_fact": {
    "field_path": "draft.products_services",
    "value": ["sample item"],
    "context": "Example Company sp. z o.o. offers \"sample item\"."
  },
  "expected_action": "publish"
}
```


## Commands and dependencies

From the repository root, with the project runtime dependencies installed:

```sh
PYTHONPATH=src python scripts/strict_case_builder.py author-spec.json generated-cases.json
PYTHONPATH=src python scripts/preflight_strict_cases.py generated-cases.json
```

The builder/preflight require the public `company_bi.models` module (`models.py`) and its public
validation dependencies: Python 3.12+, Pydantic 2.11+, and the standard library. They do not
import the production parser, evidence gate, assertion extractor, or verifier. Preflight validates
each raw serialized run via `CompanyResearchRun.model_validate_json`; it intentionally does not
execute expected actions or judge semantic correctness. Every run that validates is reported
`VALID`, regardless of its author-assigned classification; this is only public-model validity,
not a semantic or expected-action judgment. Model-validation failures are reported `INVALID`.
For an `IDENTITY_INVALID` or `PROVENANCE_INVALID` case with `expected_action: "reject"`, the
boundary annotation says to review the exact error and cautions that it is not evidence the
verifier rejects for the intended reason. Such intentional invalid controls do not count as
semantic probes. Boundary-invalid cases without `expected_action: "reject"` fail readiness.
Malformed shape, duplicate IDs, and invalid semantic-class cases fail readiness; all three
semantic classifications require valid model envelopes.

The builder refuses to overwrite an existing output file. Preserve author specifications and
first generated outputs unchanged after creation.

## Required authoring and freeze procedure

Use the following sequence exactly; do not iterate the corpus against verifier outcomes:

1. Provide the author only the normative `STRICT_PUBLICATION_CONTRACT.md`, this toolkit, and
   public model/schema material. Ask the author to make their own independent case judgments.
2. Recommend a corpus mix of **20 positives, 20 true out-of-contract cases, 30 unsafe negatives,
   5 provenance-invalid controls, and 5 identity-invalid controls**.
3. Run the builder once, then run preflight over every generated raw run. Review the exact
   model-validation error on each intentionally invalid boundary control and confirm it matches
   the intended envelope change; do not interpret that error as verifier evidence. Resolve other
   schema/envelope defects before freezing. Semantic classification is not inferred or modified
   by preflight.
4. Freeze and hash the complete authored corpus after preflight. Record the frozen hash before
   the single verifier execution.
5. Run the verifier once against that frozen corpus and preserve first outcomes. After execution,
   make no corpus edits, rerolls, lexical changes, or retrospective relabeling.
