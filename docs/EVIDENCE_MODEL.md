# Canonical data and evidence contract

[OG-150](https://linear.app/tpg96/issue/OG-150) · Authoritative code: [`src/company_bi/models.py`](../src/company_bi/models.py). These are publication models, not an implemented research agent, identity resolver, evidence gate or renderer.

## Models

| Model | Responsibility |
| --- | --- |
| `InputRow` | Row number and normalized ten-digit NIP shape. Normalization, checksum and registry checks belong to OG-151, not this schema. |
| `CompanyIdentity` | Fixed NIP and supported resolved legal name, optional identity observations with explicit states, and an aware resolution timestamp. No unresolved company profile. |
| `Source` | Successful-retrieval metadata: application-assigned ID, HTTP(S) URL, title, aware retrieval timestamp and optional publication date. |
| `EvidenceRef` | Existing source ID plus a nonblank excerpt; never a bare URL citation. |
| `Fact[T]` | Typed value, evidence state, evidence references and a missing-data/uncertainty reason. |
| `EmployeeFact` | Exact count **or** explicitly typed range, plus observation date if known. Open-ended ranges are allowed; do not calculate midpoints. |
| `FinancialFact` | Revenue/net result and decimal reported amount, explicit reporting interval, currency, unit and legal-entity/group scope. |
| `CompanyEvent` | A fact containing title, summary, publication date and optional event date; independent state and evidence for each item. |
| `CompanyProfile` | Canonical version `0.1`, coverage status, generation timestamp, identity, business/scale/financial/news observations, source ledger and limitations. |
| `BatchResult` | One summary-CSV entry per input row, normalized NIP where valid, outcome, paired report paths and an aware completion timestamp. |

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
- Complete means supported coverage of every requested section and no limitations. Partial means an uncertain/unknown observation or explicit limitation. This is coverage, not proof that a company has no unreported activity. Missing optional identifiers count as coverage gaps.

## JSON and rendering

The canonical profile alone contains everything needed to render deterministic identity/business/scale/financial/recent-development sections, state labels, dates, citation links and gap explanations. Rendering is ordinary code in the later rendering issue, not another LLM call. Stable ordering and formatting must be applied there; schema validation does not sort facts or allocate source IDs.

Examples in [`examples/profiles/`](../examples/profiles/) are **synthetic contract fixtures**, with reserved `.example` domains and invented company/evidence text. They demonstrate complete, partial and conflicting-source states. They were not retrieved from real companies, do not prove the evidence gate works, and must never be presented as actual BI reports. The financial spike uses separate real public sources documented in `FINANCIAL_DATA_DECISION.md`.
