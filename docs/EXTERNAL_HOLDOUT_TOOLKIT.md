# External holdout case toolkit

This toolkit turns author-written JSON case specifications into synthetic `CompanyResearchRun`
JSON envelopes and checks those envelopes against the public Pydantic models. It does not
classify assertions, decide whether a claim is true, apply the publication contract, or run the
research verifier. Authors assign labels and expected actions themselves. Component expected
results and scoring are specified separately in [HOLDOUT_ORACLE.md](HOLDOUT_ORACLE.md); that
oracle is not a required field in these existing generated case wrappers.

## Public case specification

A specification is one JSON object (or a list of objects) with required fields `case_id`,
`classification`, `source_assertion`, `candidate_fact`, and `expected_action`. Unknown fields are
errors, including misspellings such as `publication_metdata` or `contex`.

- `case_id`: unique nonempty author-assigned identifier.
- `classification`: one of `SUPPORTED_CONTRACT_POSITIVE`, `OUT_OF_CONTRACT_TRUE`,
  `UNSAFE_NEGATIVE`, `IDENTITY_INVALID`, or `PROVENANCE_INVALID`.
- `source_assertion`: object with nonempty source `text`; optional `published_on` date.
- `candidate_fact`: object with `field_path`, typed `value`, optional `state`, `context`,
  `reason`, `as_of`, and `context_fields`.
- `expected_action`: author annotation using only the high-level labels `publish`, `abstain`, or
  `reject`; it is not a publication decision made by this toolkit.

Supported candidate paths are `draft.business_description`, `draft.products_services`,
`draft.industries`, `draft.markets`, `draft.employees`, `draft.financials.revenue`,
`draft.financials.net_result`, and `draft.recent_developments`. `value` uses the matching
public-model type: text; list of texts; employee object (`{"kind":"exact","count":9}` or
range); decimal JSON string for a financial amount; or event object (`title`, `summary`,
`published_on`, optional `occurred_on`). Every non-null financial value MUST be a decimal string
(not a JSON number or boolean), so its authored precision is retained. Unknown financial values
may be null. A non-null financial value also requires `context_fields` containing `period`,
`currency`, `unit`, and `scope`; for group scope also supply `group_name`. Financial context
accepts only those five keys: the candidate value, state, metric, evidence, and reason cannot be
overridden through context. Employee `as_of` is only valid for employee facts. `context_fields`
is only valid for financial facts. `state` defaults to `supported`; `uncertain` and `unknown` are
also available. Unknown candidate values must be null; the builder supplies a reason if omitted.
Evidence context defaults to the source assertion text.

Optional `publication_metadata` accepts `url`, `title`, `published_on`, `kind`, and `fetch_mode`.
The builder supplies a fixed synthetic identity (legal name `Example Company sp. z o.o.`, NIP
`5220003782`), registry record, evidence ledger, source IDs, timestamps
(`2026-10-06T12:00:00+00:00`), complete research draft baseline, unknown reasons, and diagnostics
with zero operation counters. It fills financial metric coverage according to the public schema;
authors must supply financial context for non-null amounts.

The output also has `path` identifying the candidate's location for downstream review (for
example `financials.0` or `recent_developments.0`). The shared resolver supports documented fact
paths only, including scalar draft facts, indexed financial/development facts, and identity facts;
preflight verifies the path exists in the run before considering an intentional model-boundary
error.

For deliberate envelope-boundary controls only, optional `envelope` supports shallow identity
field changes (`{"identity":{"nip":"..."}}`) and indexed source mutations
(`{"sources":[{"index":1,"changes":{"kind":"registry"}}]}`). Mutation keys must be known
identity/source fields, while values may intentionally be model-invalid to construct a boundary
control. Unknown patch keys and malformed mutation structure are rejected. A source mutation can
change retrieval material fields, including nested source metadata. These narrow operations are
reserved for `IDENTITY_INVALID` and `PROVENANCE_INVALID` cases; they preserve the generated baseline
instead of requiring authors to recreate it. Keep the assertion and candidate fact alongside the
mutation.

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

Builder and preflight use the public `company_bi.models` schema. For release evidence, record and
use exactly Python 3.12 and Pydantic 2.13.5; broader project dependency constraints are not an
equivalent release-evidence specification. The tools use the standard library and Pydantic public
models and do not import the production parser, evidence gate, assertion extractor, or verifier.
Preflight validates each raw serialized run via `CompanyResearchRun.model_validate_json`; it
intentionally does not execute expected actions or judge semantic correctness. Every run that
validates is reported `VALID`, regardless of its author-assigned classification; this is only
public-model validity, not a semantic or expected-action judgment. Model-validation failures are
reported `INVALID`.

For an `IDENTITY_INVALID` or `PROVENANCE_INVALID` case with `expected_action: "reject"`, the
boundary annotation says to review the exact model error. These controls are reported separately
from semantic executions (`semantic_execution: not_applicable` in component scoring). A
model-rejected semantic case is `unexercised`, never a semantic-parser success. Invalid controls
with other expected actions fail readiness. A bogus or nonexistent target path always fails
readiness, including for boundary-invalid controls. Malformed shape, duplicate IDs, and invalid
semantic-class cases fail readiness; semantic classifications require valid model envelopes.

## Taxonomy and sampling

Apply these five labels consistently:

1. **SUPPORTED_CONTRACT_POSITIVE** — a complete in-contract assertion expected to publish the
   authored fact.
2. **OUT_OF_CONTRACT_TRUE** — synthetic stipulated truth outside the supported grammar,
   expected to abstain.
3. **UNSAFE_NEGATIVE** — must be falsifiable from the supplied envelope or contract itself.
   Do not use it merely because the author privately declares an otherwise perfectly supported
   source assertion false. The verifier does not authenticate publisher truth.
4. **IDENTITY_INVALID** — a deliberate identity-envelope control; it may fail public-model
   validation and is reported separately from semantic executions.
5. **PROVENANCE_INVALID** — a deliberate provenance-envelope control; it may fail public-model
   validation and is reported separately from semantic executions.

A recommended authored sample is 20 positives, 20 true out-of-contract cases, 30 unsafe negatives,
5 provenance-invalid controls, and 5 identity-invalid controls.

The external release holdout is a sampled independent population.
The repository's canonical regression matrix supplies broader deterministic grammar coverage.

Do not expand this release sample into a 256+ case exhaustive grammar matrix. A sample's coverage
notes describe only its selected cases, not every literal production or Unicode boundary.
The separate component oracle records expected results for that sample without replacing or
rewriting its classifications or original wrappers.

## Scope limits

The builder creates a single-page synthetic envelope. It does not claim coverage of multi-page
conflicts, cross-page composition, full redirect lineage, every grammar variant, or Unicode
alternatives. The toolkit is a schema-validation and authoring aid, not a research simulator or
semantic evaluator. Deferred work includes broader holdout matrices and changes to semantic or
research behavior.

## Required authoring and freeze procedure

Use the following sequence exactly; do not iterate the corpus against verifier outcomes:

1. Provide the author only the normative `STRICT_PUBLICATION_CONTRACT.md`, this toolkit, and
   public model/schema material. Ask the author to make their own independent case judgments.
2. Use the sampled corpus mix above; do not turn this release holdout into a full grammar matrix.
3. Run the builder once, then run preflight over every generated raw run. Review the exact
   model-validation error on each intentionally invalid boundary control and confirm it matches
   the intended envelope change; do not interpret that error as verifier evidence. Resolve other
   schema/envelope defects before freezing. Semantic classification is not inferred or modified
   by preflight.
4. Freeze and hash the complete authored corpus after preflight. Record the frozen hash before
   the single verifier execution.
5. Run the verifier once against that frozen corpus and preserve first outcomes. After execution,
   make no corpus edits, rerolls, lexical changes, or retrospective relabeling.
