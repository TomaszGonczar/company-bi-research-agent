# Canonical data and evidence contract

[OG-150](https://linear.app/tpg96/issue/OG-150) · Authoritative code: [`src/company_bi/models.py`](../src/company_bi/models.py). These are publication models, not an implemented research agent, identity resolver, evidence gate or renderer.

## Models

| Model | Responsibility |
| --- | --- |
| `InputRow` | Row number and normalized ten-digit NIP shape. `nip.py` performs normalization/checksum validation before any registry request; the schema itself still checks shape only. |
| `CompanyIdentity` | Fixed NIP and supported resolved legal name, explicit-state identifiers/address/city/website, and an aware resolution timestamp. No unresolved company profile. |
| `Source` | Successful-retrieval metadata: application-assigned ID, HTTP(S) URL, title, aware retrieval timestamp and optional publication date. |
| `EvidenceRef` | Existing source ID plus a nonblank excerpt; never a bare URL citation. |
| `Fact[T]` | Typed value, evidence state, evidence references and a missing-data/uncertainty reason. |
| `EmployeeFact` | Exact count **or** explicitly typed range, plus observation date if known. Open-ended ranges are allowed; do not calculate midpoints. |
| `FinancialFact` | Revenue/net result and decimal reported amount, explicit reporting interval, currency, unit and legal-entity/group scope. |
| `CompanyEvent` | A fact containing title, summary, publication date and optional event date; independent state and evidence for each item. |
| `CompanyProfile` | Canonical version `0.1`, coverage status, generation timestamp, identity, business/scale/financial/news observations, source ledger and limitations. |
| `BatchResult` | One input-row outcome: identity-stage `resolved` with identity/sources, or final-report outcome with paired paths, plus failure reason/code and an aware completion timestamp. |

Helper models represent exact/range employee quantities, reporting intervals and dated event values. There is no provider interface or verification framework. Unexpected fields are rejected, including `confidence`/confidence percentages. A NIP is a string, never an integer; shape validation is not checksum or legal-identity validation.

## State invariants

| State | Value | Evidence | Reason |
| --- | --- | --- | --- |
| `supported` | Required, typed | At least one reference to a retrieved source in the profile ledger | Optional |
| `uncertain` | Optional; null when no candidate can safely be selected | At least one candidate reference | Required: identify conflict, ambiguity, stale information or interpretation issue |
| `unknown` | Must be null | Empty; no assertion of supporting evidence | Required: explain insufficient evidence/unavailable data |

An explicit supported zero/false can be valid when the source actually states it. Unknown zero/false is invalid. Do not substitute empty strings, empty asserted lists or numerical confidence scores for missingness. Identity's legal name must be supported before any profile can exist; KRS/REGON/city/website not obtained remain unknown. The NIP is the pipeline's control identifier; the supported registry evidence must establish its association with the legal name.

Conflicting values must not become multiple contradictory supported observations for the same financial metric/period. Use one uncertain fact, cite both excerpts, and state the conflict. A selected uncertain value is only a candidate and must be visibly labelled in rendering; null is preferred when sources conflict irreconcilably. No renderer promotes uncertain/unknown to supported.

## Structural validation versus evidence verification

Schema validators enforce state/value consistency, nonempty evidence, known and unique source IDs, timestamps, ranges, financial context, metric/period uniqueness, at most three financial periods, at most three recent items, and complete/partial coverage consistency. A source cannot have a retrieval timestamp later than report generation. All retrieval/resolution/generation/completion timestamps carry timezone offsets.

**A user/model-supplied `Source` is not proof of retrieval.** The application owns the ledger. The later deterministic gate must independently check:

1. The source ID exists in the trusted successful-retrieval ledger, and metadata matches it.
2. The excerpt exists in the stored extracted source text, allowing only consistent whitespace normalization—not fuzzy matching, paraphrase, fabricated ellipses or search-only snippets.
3. The source identifies the resolved NIP/legal entity without conflicting identifiers. The LLM cannot resolve the legal entity from a similar name.
4. Financial evidence includes the same metric, reporting interval, currency, unit and stated entity/group scope as the candidate amount.
5. The evidence directly supports the observation; ambiguity/conflict/freshness issues are not hidden.

Exact excerpt presence alone is not semantic proof. Uncertain observations stay uncertain unless a new deterministic gate decision has adequate evidence. Failed reads do not become `Source` entries; record their reasons in limitations. The agent's candidate output will be defined in the research issue, without granting authority over identity, source creation or final supported publication.

This foundation deliberately does **not** implement retrieval, excerpt matching or semantic evidence verification. It defines their input/output contract; it does not call schema-valid examples evidence-verified reports.

## Quantities, dates and coverage

- Employee `value` uses `{ "kind": "exact", "count": 120 }` or `{ "kind": "range", "minimum": 51, "maximum": 200 }`. Bounds are nonnegative integers; reversed or wholly unbounded ranges are invalid. The same exact or range representation survives JSON serialization. Missing observation date stays null; a retrieval/publication date is not silently an employee observation date.
- Financial `value` is a finite `Decimal`, serialized as a JSON string to preserve precision. `unit` is `units`, `thousands`, `millions` or `billions`; retain the reported amount, not a silently scaled number. Negative net results and explicitly reported zero amounts are valid.
- Every asserted financial amount, even an uncertain candidate, requires metric, `period.start/end`, three-letter currency code, unit and scope. A group amount also names the reported group. No group-to-legal-entity conversion. Incomplete context means no asserted amount; retain uncertainty and explain missing context.
- Unknown financial records always name the requested metric. Period/currency/unit/scope may be null when unavailable; they are not guessed. Known context may remain on an unknown record, but there is no asserted amount. Both requested metrics must be represented, with at most six records covering at most three reporting intervals.
- Recent items must have a publication date in the inclusive preceding 12 calendar months relative to `generated_at`; February 29 uses February 28 in the preceding year. Event dates remain null unless known. No retrieved recent items requires an explicit limitation, not a claim that no events occurred.
- Complete means supported coverage of every requested section and no limitations. A supported address or city satisfies location coverage; the unknown alternative is not an additional required observation. A location conflict remains uncertain/partial. Other unknown required observations and missing optional identifiers remain coverage gaps, not proof of nonexistence.

## JSON and rendering

The canonical profile alone contains everything needed to render deterministic identity/business/scale/financial/recent-development sections, state labels, dates, citation links and gap explanations. Rendering is ordinary code in the later rendering issue, not another LLM call. Stable ordering and formatting must be applied there; schema validation does not sort facts or allocate source IDs.

Examples in [`examples/profiles/`](../examples/profiles/) are **synthetic contract fixtures**, with reserved `.example` domains and invented company/evidence text. They demonstrate complete, partial and conflicting-source states. They were not retrieved from real companies, do not prove the evidence gate works, and must never be presented as actual BI reports. The financial spike uses separate real public sources documented in `FINANCIAL_DATA_DECISION.md`.

## OG-151: documented identity-stage extensions

The original foundation models describe final BI publication. Two concrete gaps were identified before implementation:

1. `BatchResult` cannot represent a successfully resolved identity without claiming nonexistent JSON/Markdown BI reports. Add the intermediate `resolved` status, optional `identity`/`sources`, and a stable optional `error_code`; preserve all existing final-report and failure statuses. A resolved identity requires a matching NIP, a supported legal name and a valid source ledger, and must not claim report paths. Invalid input carries no normalized NIP, identity or retrieved sources. Unresolved/failed rows carry no guessed identity. The final BI-summary CSV contract is unchanged; OG-151 writes identity records as JSON, not BI reports.
2. The selected [MF API schema](https://www.gov.pl/attachment/9a515a2c-17d5-405a-a7fd-2df4cba2c15c) supplies `workingAddress`, explicitly defined as the registration address, but no separate city field. Add `CompanyIdentity.registered_address` as another explicit fact. Preserve the returned address and leave city unknown rather than extracting or guessing it. Location coverage is satisfied by a supported registered address **or** city; uncertainty still makes coverage partial. Existing examples/callers must migrate explicitly—no legacy alias or compatibility shim.

These extensions do not change the deterministic NIP anchor, evidence states, one-source lookup, financial decision or architecture. MF not-found (`result.subject: null`) means unresolved in this source, not proof that no legal company exists. HTTP/network/schema failures are operational failures, not not-found. The registry does not supply a website, so website remains unknown; no Tavily, Scrapling or LLM lookup is introduced.

### Executed identity boundary

OG-151 maps only the fixed MF JSON identity fields after exact NIP matching. Identity evidence references contain the returned fields' JSON string values and retriever-owned source IDs. This is deterministic registry provenance, not unstructured company research or a generic evidence extractor/gate. Missing fields remain unknown; no city, website or identifier is guessed. Source timestamps/URLs and matching references survive the persisted `BatchResult` JSON.

## OG-152: documented research-stage gap and implementation

Before implementation, the foundation deliberately deferred the candidate output (see “Structural validation versus evidence verification”); no `CompanyResearchDraft` existed. The narrow extension now lives in canonical `models.py`, reusing `Fact`, `EmployeeFact`, `FinancialFact` and `CompanyEvent` for business, scale, financial/news attempts and explicit limitations. Its model has no identity or source-ledger fields: the host supplies the unchanged OG-151 identity and owns every source ID. Draft `supported` is an LLM proposal, not an OG-153 publication decision.

Small retrieval/run records live alongside those canonical models. Registry identity provenance, Tavily snippets and full-page text remain distinct material kinds with fetch mode and successful-retrieval metadata. A full-page read keeps the same host source ID and does not erase its discovery snippets; repeated IDs across snapshot kinds/versions are intentional. The draft, unchanged identity, retained material and diagnostics are persisted under ignored per-run artifacts, not final BI profile/Markdown paths.

The one agent exposes search, source-ID-only page reads and an in-memory progress checkpoint. Checkpoints must validate against the draft schema and known host source IDs; they grant no filesystem capability. On a deadline, provider error or hard usage limit, return the last valid checkpoint (or explicit unknowns when no findings were obtained), with the stop reason. This is needed to preserve actual partial findings without a second agent or an unbounded finalization call.

Host validation rejects invented source IDs and identity fields; the run model also rejects orphan identity/draft references on construction or JSON load and impossible retrieval/resolution timestamps. Agent output/progress and persisted-run validation require retained full-page/text evidence for every numerical financial candidate, including uncertain values and zero; search snippets, registry material and unreadable PDFs cannot supply amounts. Structural schemas retain quantity/financial context; draft and final-profile financial coverage share the same existing invariant. Excerpt matching, semantic verification and promotion to final supported publication remain OG-153 work.
