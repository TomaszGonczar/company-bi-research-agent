# v0.1.1 pre-holdout integrity and freeze record

**HISTORICAL PRE-HOLDOUT FREEZE RECORD — superseded for current holdout status by [the independent Holdout B result](V0_1_1_HOLDOUT_RESULT.md).**

This record preserves the earlier freeze evidence and the then-current authorization to proceed to external holdout. Holdout B subsequently passed on certified semantic commit `9f80eb7a7dcdb4c563a4bec897f22361cdbbae45`; current status is post-holdout release preparation, not release authorization. See the result report for exact outcomes, artifact hashes, audit provenance and limitations.

## Integrity correction from 29beb50

Baseline: `29beb50d40f829bd2666e908cdca5a06c1221b11`, on
`fix/v0.1.1-adversarial-corrections`. The strict publication grammar and normative
contract remain byte-identical. No new live research, provider calls, vocabulary,
ordinary-prose coverage or research architecture were added.

The independent Astra corpus, component oracle and coverage matrix were not opened
or inspected during this implementation task. External public-model preflight and
external verifier executions are both zero. Local regression fixtures below are
not independent holdout evidence.

### Implemented integrity boundaries

1. **IPv6 identity:** origin checks use `(scheme, hostname, effective_port)`;
   redirect discovery/final endpoints also require canonical URL/path agreement.
   Reconstructed IPv6 authorities retain brackets, so
   `https://[2001:db8::1]:8080/` differs from `https://[2001:db8::1:8080]/`.
   Explicit/default HTTPS 443 agree. SourceStore, lineage, ownership and legacy
   grouping share the corrected URL key. Ordinary model validation and unchecked
   publication recheck lineage; legitimate redirects remain valid.
2. **Strict author specification:** public `AuthorSpec` rejects unknown nested
   keys and unsupported field placement. Builder errors carry `case_id`. Known
   boundary-patch fields can still deliberately contain invalid values; typo keys
   cannot silently disappear.
3. **Financial context:** only `period`, `currency`, `unit`, `scope`, `group_name`
   are permitted. A context cannot replace authored value, state, metric or evidence.
4. **Decimal intent:** non-null financial author amounts must be finite decimal
   strings. JSON floats, integers and booleans reject. The string
   `"123456789012345678.123456"` survives builder and public-model JSON round-trip.
5. **Preflight targets:** the shared resolver accepts only documented concrete fact
   surfaces and existing indexed entries. Bogus paths fail readiness even for
   intentionally invalid identity/provenance controls. Preflight never executes
   publication semantics.
6. **Component oracle:** [HOLDOUT_ORACLE.md](HOLDOUT_ORACLE.md) and the public
   `HoldoutOracle` model freeze explicit rejection stages, final state/value,
   reason/evidence checks and financial/employee/event components. Omitted checks
   are unassessed; explicit nullable checks require clearing/absence. The repository
   scorer resolves the declared target from a complete profile. Wrong values,
   retained invalid optional metadata, missing targets/values and missing output
   cannot become success. Scoring implementation is excluded from the author ZIP.
7. **Taxonomy:** positive assertions must be in contract; OOC truth is synthetic
   stipulated truth expected to abstain; unsafe claims must be falsifiable from
   supplied evidence/contract, not a private claim that the publisher lies.
   Identity/provenance controls remain separate from semantic executions.
8. **Scope:** the external release holdout is a sampled independent population.
   The repository's canonical regression matrix supplies broader deterministic
   grammar coverage. The one-page builder does not claim multi-page conflicts,
   cross-page composition, complete redirect lineage, every literal grammar
   alternative or every Unicode boundary.
9. **Runtime:** release evidence uses Python **3.12** and Pydantic **2.13.5**;
   the exercised interpreter is **3.12.13**. Broader project constraints are not
   described as equivalent release evidence.

### Separate local verification

| Gate / population | Observed result |
| --- | --- |
| Locked pytest suite | **740 passed**, 30 existing lxml warnings |
| Ruff check / format / mypy | **PASS / 56 files / 19 source files** |
| Unchanged canonical CLI matrix | **262/262**, including **97/97** positives; zero unsafe/OOC support and accepted invalid identity/provenance |
| Prior boundary CLI smoke | **26/26** |
| Prior micro CLI + unchecked SDK smoke | **19/19**, unchanged local case content |
| IPv6 CLI + unchecked SDK smoke | **11/11** |
| Author/preflight CLI smoke | **10/10**, also in public-only isolation |
| Component-scoring runtime smoke | **5/5**, using an actual CLI profile; supported employee parent retained while unverified date clears |
| Public schemas and neutral examples | Four schemas match their public models; two examples validate; no verifier invoked |

Initial integration failures are retained in the external audit: missing local
initializations in lineage/oracle validation, typing/lint errors, and a new test
that confused an absent optional date with a retained invalid date. A brittle
annotation-wording assertion was removed; behavior assertions remain. No frozen
external data, labels or expectations were changed.

The final commit, clean-worktree proof, exact-commit isolated-clone logs, public-only
package manifest and archive SHA-256 are recorded in the external integrity audit.
Every command uses an allowlisted environment and OS network denial. No credential
or environment files were inspected. Earlier archives remain immutable.

### Deferred, not silently implemented

General Unicode-category redesign; NIP checksum expansion at this boundary;
general JSON NaN hardening; empty legacy unknown-reason hardening; multi-page author
builder; 256+ or full 3/3/2 external holdout matrices; transaction-safe filesystem
redesign; semantic grammar changes; live research. The finite-Decimal author check
does not claim general JSON hardening.

### Later Astra Holdout A protocol

Only a subsequent execution task may inspect the supplied independent corpus.
Verify its SHA-256
`d39d1d30990f63f12666d45d1de81f827839aecd7df407c2434ba1fd83450e77`
and complete FREEZE manifest. Rerun public-model preflight on those exact same bytes
in the final pinned runtime, preserving a separate new log. STOP on unexpected
validation differences; do not run the verifier. Otherwise execute the production
verifier exactly once, preserve first outputs, and score against the independently
frozen component oracle without rewriting it. No case, label or expectation changes
after results. Model-boundary controls and semantic executions must be reported
separately; every predeclared positive remains in the positive denominator.

No release holdout was executed here. No version bump, push, merge, tag or release.

## Previous micro-correction (29beb50; historical)

Historical status: **V0.1.1 STILL BLOCKED — BLOCKED — DO NOT RELEASE**.

Baseline: `6ccae67dff94867c3cf7ab60760165b0f6b63393`, on the existing correction
branch. Only two boundary corrections were authorized. The normative publication
contract remains byte-identical; grammar, synonyms, research architecture, budgets,
dependencies and package version are unchanged.

### Raw registry values and citations

Candidate identity values now match already-decoded mapped registry fields using
only NFC and whitespace-run normalization. Literal quotation marks remain data.
The separate citation helper accepts a matching plain excerpt or one JSON-string
decoding of the excerpt, compared against that mapped field. Same-field,
same-registry-source binding and retained occurrence remain mandatory. NIP/name
agreement, duplicate-key rejection, unsupported-format rejection and all-record
conflict checks remain in force at model validation and unchecked publication.

### Actual host source ownership

`SourceStore._source_for` allocates an ID by normalized **discovery URL**.
`add_search` retains each snippet under that ID. Fetch copies the ID to its page,
stores the final URL and records `redirect_chain`; `snapshots` retains registry
material, all snippets and one current page per ID.

The host and lineage validator now share the original host URL key: lowercased
scheme/hostname, default-port removal, empty path `/`, preserved path/query and
discarded fragment. Registry provenance remains a separate namespace. For trusted
web material, the owner is the chain start for a redirected page and its source
URL otherwise. One owner cannot appear under different IDs, even with identical
content. `validate_source_lineage` enforces this at model validation, page storage
and `build_profile`, including unchecked copies.

Final URLs are **not** unique keys. Distinct discoveries A→F and B→F, or A→F
alongside direct F, remain valid. Existing endpoint/discovery checks, repeated
snippets, one-page replacement and real self-redirects are preserved.

**Quarantine decision, unchanged:** blocked evidence cannot support a claim and
does not veto trusted publication or enter trusted conflict detection. Blocked
groups are excluded from discovery ownership collisions; mixed trusted/blocked
groups and blocked registry identity still reject. A strict, conflicting employee
assertion regression exercises independent trusted publication.

### Separate post-micro measurements

- Full suite: **696 passed**, including **13 new micro-boundary regressions**;
  30 existing lxml deprecation warnings. Ruff check passes; format check passes
  for **51 files**; mypy passes for **16 source files**.
- Canonical CLI matrix: **262/262**, including unchanged **97/97** contract
  positives; zero unsafe/OOC support and zero invalid identity/provenance accepted.
- Previous local boundary CLI smoke: **26/26**.
- New local micro smoke: **19/19**, each through installed CLI and unchecked SDK
  publication; includes quoted fields, duplicate ownership and host-built redirects.
- Historical strict replay: **174 assertions; 160 correct, 14 unassessed, 0 failed**.
- Complete retained utility baseline: **0/13** researched gold supported
  (Asseco 0/6; SONEL 0/7); precision remains undefined with zero supported observations.
- Separate retained Asseco and SONEL CLI replays: each **0 researched facts**
  and **4 supported registry identity fields**, with partial profiles.

First failures remain in the audit: four old distinct-page fixtures reused one URL,
one new quarantine fixture referenced an uninstalled ID, local smoke used an invalid
quarantine marker, formatting failed, and toolkit sealing found copied `.DS_Store`
metadata. Fixture provenance/metadata and formatting were corrected without changing
expected semantic outcomes, historical corpus inputs or gold. The final author
archive excludes that metadata and has an exact verified manifest.

### Unavailable exact replay gates

The latest supplied Astra report/results describe recovered original v1 (130),
v2 (80), previous independent strict (124), and latest Astra (90) inputs. The
referenced `company-bi-v011-final-independent-evidence.zip`, complete raw runs and
original runners are not locally supplied. Separate latest Opus inputs/runner are
also unavailable. The reports and hashes are preserved, but none of these five
exact post-micro population replays is claimed. New local regressions are not their
reconstruction or replacement. This missing replay evidence blocks the requested
readiness declaration; the expected absence of a fresh blind release holdout does
**not** itself block pre-holdout preparation.

All executed checks used an allowlisted environment and OS network denial, without
provider calls or credential inspection. The restricted
`company-bi-v011-pre-holdout-author.zip` refreshes public models/schemas only; it
contains no parser, gate, verifier, old cases or results. Its neutral example builds
and preflights `VALID`; a malformed semantic envelope preflights `INVALID`.
No independent release holdout was authored or run. The original failed 70-case
holdout and previous archives remain immutable.

Final commit, exact-commit isolated-clone evidence, separate inputs/results, first
failures and verified package hashes are recorded outside the repository in
`company-bi-v011-pre-holdout-review.zip`. No version bump, push, merge, tag or release.

## Previous boundary correction (6ccae67; historical)

Baseline: `b521edf066e2d57b0339149eae7391ffc7e62e7c` on
`fix/v0.1.1-adversarial-corrections`. This is a bounded correction, not another
semantic redesign. The [strict publication contract](STRICT_PUBLICATION_CONTRACT.md)
is unchanged. No ordinary-language coverage, synonyms, providers, research budgets or
financial grammar were added.

Agent proposes broadly. Verifier publishes narrowly. Unknown semantics abstain.

## Implemented boundaries

| Boundary | Correction and exercised result |
| --- | --- |
| Retrieval kind/mode | Only `registry/registry`, `search_snippet/tavily`, `full_page/static`, `full_page/dynamic`. All other combinations reject. `RetrievedSource`, run validation and `build_profile` recheck the invariant, including unchecked `model_copy`. |
| Retained full-page multiplicity | More than one non-blocked full page per source ID rejects, even for the same URL. No favorable-page selection or merging. Snippets plus one full page remain valid. SourceStore's existing one-page replacement behavior is unchanged. |
| Finance across scales | Conflict amounts use exact Decimal exponent shifts into base units. Conflict key contains metric, currency, scope and both period bounds, not display unit. Equivalent scales do not conflict; differing values and equal-magnitude profit/loss do. Cited candidate value/unit matching remains as narrow as before. Decimal sign normalization does not round under ambient context. |
| Output destinations | Before payload writes, all four destinations are compared by resolved path and, when present, same inode. Output-output symlinks/hardlinks and existing output-input aliases reject with `ValueError`, preserving input and existing payload bytes. This is preflight, not transactional or race-proof filesystem storage. |
| Event language | English predicates accept only optional `on DATE`; Polish predicates only optional `w dniu DATE`. Both mixed-language forms abstain as out of contract. |
| Event exactness | Summary comparison uses NFC plus outer trim only. Internal double spaces, NBSP, escaped JSON labels and decoded exact titles are preserved; altered summaries abstain. |
| Registry citations | NFC/whitespace-normalized citation occurrence is required in the same referenced material, together with mapped-field and identity matching. A matching string in another material/field or a decoded string absent from retained escaped JSON is not evidence. NIP/name, duplicate-key and unsupported-format guards remain. |
| Markdown inline values | CRLF/CR/LF are flattened in the shared inline escaping helper. Profile and verification Markdown do not gain injected headings/lists from titles, values or rejected excerpts. JSON semantic strings retain their original characters. |

The SourceStore regression uses a real host-created Tavily snippet plus a same-ID static
page explicitly denying the offering. Untampered input withholds. Changing only the
snippet's `kind` to `full_page`, while retaining `fetch_mode=tavily`, rejects at run
validation and unchecked publication. A retained positive/retraction pair with valid
page modes also rejects by the multiplicity invariant.

## Local verification

All execution used an allowlisted environment and OS network denial, without provider
credentials or new live-company research.

- `uv run --frozen --offline pytest -q`: **683 passed**, 30 existing lxml
  `strip_cdata` deprecation warnings; warnings were not suppressed.
- `uv run --frozen --offline ruff check .`: passed.
- `uv run --frozen --offline ruff format --check src tests scripts`: **50 files** formatted.
- `uv run --frozen --offline mypy src`: passed, **16 source files**.
- Actual installed CLI boundary smoke: **26/26**, including source provenance, duplicate
  pages, scale equivalence/conflicts, event language/whitespace, registry normalization,
  CR/LF rendering, and symlink/hardlink/input-alias rejection. The unchecked SDK guard
  was also exercised directly. Input hashes and existing payload bytes were preserved.
- Actual offline review helper exercised a local `FunctionModel` interruption; no provider
  was contacted. Supported/OOC examples and historical snapshots remain separate.

First integration failures are preserved in external audit logs: a script-import
collection failure, formatting/lint/type issues, and three new test-fixture/expectation
errors. Corrections did not change historical inputs or expectations. They are not
independent holdout executions.

The exact final commit, changed-file inventory, isolated-clone logs and package hashes
are recorded outside the source tree in the final review package; no self-referential
commit hash is embedded here.

## Separate populations

| Population | Observed result / limitation |
| --- | --- |
| Canonical strict CLI matrix | **262/262**, including **97/97** contract positives; 64 true-OOC, 98 unsafe, two provenance-invalid and one identity-invalid controls. Zero unsafe/OOC support and zero accepted invalid identity/provenance. Original matrix inputs and expected outcomes unchanged. |
| Historical strict replay | **174 assertions: 160 correct, 14 unassessed**, no failed assessments. The 12 eligible positives are identity assertions, all correct; no eligible researched strict positives. Semantic-execution counters: 25 executed, 14 unexercised, 135 not applicable. |
| Utility replay, complete retained baseline run set | **0/13** gold researched claims supported: Asseco 0/6, SONEL 0/7. Zero supported observations, so precision denominator is zero and precision is undefined, not perfect. No new extraction or provider call occurred; embedded diagnostics belong to the old retained runs. |
| Retained Asseco CLI run | Partial profile; **0 researched facts published**. Four registry-backed identity fields remain supported. |
| Retained SONEL live-run CLI replay | Partial profile; **0 researched facts published**. Four registry-backed identity fields remain supported. The archived raw CompanyResearchRun was replayed, not reconstructed from a final profile. |
| Exact original adversarial v1 | External b521edf report says 0 unsafe / 65 negatives, 130 total inputs. Complete original inputs/runner are not locally supplied; **no post-correction exact replay claimed**. |
| Exact original adversarial v2 | External b521edf report says 0 unsafe / 40 negatives, 80 total inputs. Complete original inputs/runner are not locally supplied; **no post-correction exact replay claimed**. |
| Latest boundary/Astra-requested corpus | Report and per-case results are supplied, including 47/47 new semantic unsafe probes withheld and 60/62 paired positives accepted at b521edf. The referenced 124-execution corpus/evidence ZIP and runner are absent locally. Source excerpts/results are not full run envelopes; **no reconstructed exact replay claimed**. |
| Latest separate Opus strict corpus | User reports zero unsafe replay and all its strict positive controls accepted. Raw corpus and runner are unavailable locally; **not a new local measurement**. |

The external report identifies its 124-execution corpus by SHA-256
`a347bd9f3d0d0b968a589da73545ac412de4ff62fbb0536195f340cf4bfe4589`.
The accompanying evidence ZIP containing those inputs and the original 130/80 inputs
is a missing prerequisite. Separate vendor attribution is not established by the generic
report filenames. Known reproductions were added as local correction regressions; they
are not a substitute for replaying an entire external population.

Asseco/SONEL zero researched publication is strict abstention under ordinary retained
web prose, **not useful BI output**. It is not evidence that those companies lack the
reported activities. The complete baseline utility run set was selected explicitly;
the historical candidate utility directory lacks an Asseco run and only records its
capture failure. Those populations were not mixed.

Earlier **47/47, 5/19, 0/7, 1/13**, and older live-zero measurements remain unchanged
history under their earlier contracts. The [b521edf strict report](STRICT_CONTRACT_REVIEW.md)
is also a distinct snapshot, not overwritten by this correction.

## External fixture toolkit and holdout status

- [`scripts/strict_case_builder.py`](../scripts/strict_case_builder.py) owns synthetic
  registry material, identity evidence, timestamps, diagnostics, source IDs, unknown
  reasons and a valid baseline. Authors supply source assertion, candidate, target,
  classification, expected action and optional publication metadata.
- [`scripts/preflight_strict_cases.py`](../scripts/preflight_strict_cases.py) calls
  `CompanyResearchRun.model_validate_json` on every run and reports `VALID`/`INVALID`.
  It does not execute the verifier. Invalid boundary controls receive a separate
  manual-review annotation, never a semantic-pass claim.
- [Toolkit instructions](EXTERNAL_HOLDOUT_TOOLKIT.md) describe all fact families,
  explicit finance context, narrow boundary mutations and immutable authoring outputs.
- A separate restricted author package contains only the frozen contract, public
  models/schemas, builder/preflight, dependencies and minimal usage example/instructions.
  It excludes the parser, evidence gate, verifier, regression suite, old cases and results.
- The restricted package was exercised outside the repository: imports resolved to its
  copied public model; parser/gate/verifier modules were unavailable. The neutral example
  built and preflighted `VALID` with exit 0. A deliberately broken semantic envelope
  returned `INVALID`/exit 1 for its missing unknown reason. Neither is release holdout data.

The original **70-case holdout remains permanently FAILED FIXTURE CONSTRUCTION**,
SHA-256 `5028ddab490df792d35a7d4b8f7a69fb61d6b615dab6a901509cdba6a41fabca`.
It was not modified or rerun. All 70 intended probes were unexercised in its original
execution; the six raw expected rejections are not targeted-boundary proof.

**Historical pre-holdout status (superseded):** At this record's freeze point, no fresh
external release holdout had been supplied, frozen or executed. The authoring instructions
above described the then-planned external population and one-execution process; they are
not the current status. Holdout B later passed on the certified commit. Its independent
first-execution evidence, exact population results and artifact audit are recorded in the
[Holdout B result](V0_1_1_HOLDOUT_RESULT.md). The original 70-case fixture-construction
failure above remains immutable history.

## Release hygiene and stop

Holdout B passed, superseding this record's earlier holdout-pending disposition. Current
preparation is metadata-only v0.1.1 hygiene: package/lock version metadata changes from
0.1.0 to 0.1.1, with no dependency-version or semantic implementation change. CI's Ruff
format scope is aligned with the local gate to cover `src tests scripts`; optional action
pinning is not part of this metadata-only change.

Local release-preparation gates passed: 740 tests, Ruff, formatting, mypy, the 262/262
canonical CLI population (97/97 positives), and the deterministic offline reviewer path.
These are separate regression checks, not another Holdout B execution. Check the final
commit SHA and exact-commit clean-clone evidence in the external release-review package.
Hosted CI is pending authorization and is not claimed as passed; its push/PR workflow
requires a published commit. No push, merge, tag or release is authorized or claimed.
This is post-holdout release preparation, **not a release**. See the
[Holdout B result](V0_1_1_HOLDOUT_RESULT.md) for evidence and limits.
