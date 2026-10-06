# Canonical data and evidence contract

[OG-150](https://linear.app/tpg96/issue/OG-150) established the canonical models in [`src/company_bi/models.py`](../src/company_bi/models.py). The gate in [`src/company_bi/evidence.py`](../src/company_bi/evidence.py) and issue history below describe the earlier implementation. The current normative semantic rules are in [STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md), with case classification in [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md).

The OG-150 through OG-153 implementation narrative and adversarial correction history below document the earlier contract. They are preserved historical context, not the current semantic specification; historical examples/results do not establish strict-contract execution.

## Models

| Model | Responsibility |
| --- | --- |
| `InputRow` | Row number and normalized ten-digit NIP shape. `nip.py` performs normalization/checksum validation before any registry request; the schema itself still checks shape only. |
| `CompanyIdentity` | Fixed NIP and supported resolved legal name, explicit-state identifiers/address/city/website, and an aware resolution timestamp. No unresolved company profile. |
| `Source` | Retriever-owned ID, final HTTP(S) URL, title, aware retrieval timestamp, optional publication date and optional validated redirect chain. |
| `ProfileSource` | Final source metadata plus required `registry`, `search_snippet` or `full_page` provenance; researched supported facts require retained full-page evidence. |
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

**A user/model-supplied `Source` is not proof of retrieval.** The application owns the ledger. The deterministic gate checks:

1. The source ID exists in the trusted successful-retrieval ledger, and metadata matches it.
2. The excerpt exists in the stored extracted source text, allowing only consistent whitespace normalization—not fuzzy matching, paraphrase, fabricated ellipses or search-only snippets.
3. The source identifies the resolved NIP/legal entity without conflicting identifiers. The LLM cannot resolve the legal entity from a similar name.
4. Financial evidence includes the same metric, reporting interval, currency, unit and stated entity/group scope as the candidate amount.
5. The evidence directly supports the observation; ambiguity/conflict/freshness issues are not hidden.

Exact excerpt presence alone is not semantic proof. Uncertain observations stay uncertain unless a new deterministic gate decision has adequate evidence. Failed reads do not become `Source` entries; record their reasons in limitations. Research candidate output grants no authority over identity, source creation or final supported publication.

The OG-150 foundation alone did not implement retrieval, excerpt matching or semantic evidence verification. The subsequent sections describe the implemented boundaries; schema-valid examples alone are not evidence-verified reports.

## Quantities, dates and coverage

- Employee `value` uses `{ "kind": "exact", "count": 120 }` or `{ "kind": "range", "minimum": 51, "maximum": 200 }`. Bounds are nonnegative integers; reversed or wholly unbounded ranges are invalid. The same exact or range representation survives JSON serialization. Missing observation date stays null; a retrieval/publication date is not silently an employee observation date.
- Financial `value` is a finite `Decimal`, serialized as a JSON string to preserve precision. `unit` is `units`, `thousands`, `millions` or `billions`; retain the reported amount, not a silently scaled number. Negative net results and explicitly reported zero amounts are valid.
- Every asserted financial amount, even an uncertain candidate, requires metric, `period.start/end`, three-letter currency code, unit and scope. A group amount also names the reported group. No group-to-legal-entity conversion. Incomplete context means no asserted amount; retain uncertainty and explain missing context.
- Unknown financial records always name the requested metric. Period/currency/unit/scope may be null when unavailable; they are not guessed. Known context may remain on an unknown record, but there is no asserted amount. Both requested metrics must be represented, with at most six records covering at most three reporting intervals.
- Recent items must have a publication date in the inclusive preceding 12 calendar months relative to `generated_at`; February 29 uses February 28 in the preceding year. Event dates remain null unless known. No retrieved recent items requires an explicit limitation, not a claim that no events occurred.
- Complete means supported coverage of the requested core sections, both financial metrics for at least one shared explicit reporting interval, and no limitations. A supported address or city satisfies location coverage; the unknown alternative is not an additional required observation. Unknown optional KRS/REGON/website fields alone do not force partial under OG-153; conflicts in those fields still do. Missing or uncertain core observations remain partial, never proof of nonexistence.

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
Supported descriptive/list values in a draft are atomic extractive observations: retain verbatim source-language spans with enough company/relation/qualifier context. They are not translations or claimed verified narrative synthesis; a candidate without an eligible statement remains uncertain or unknown.

Small retrieval/run records live alongside those canonical models. Registry identity provenance, Tavily snippets and full-page text remain distinct material kinds with fetch mode and successful-retrieval metadata. A full-page read keeps the same host source ID and does not erase its discovery snippets; repeated IDs across snapshot kinds/versions are intentional. The draft, unchanged identity, retained material and diagnostics are persisted under ignored per-run artifacts, not final BI profile/Markdown paths.

The one agent exposes search, source-ID-only page reads and an in-memory progress checkpoint. Checkpoints must validate against the draft schema and known host source IDs; they grant no filesystem capability. On a deadline, provider error or hard usage limit, return the last valid checkpoint (or explicit unknowns when no findings were obtained), with the stop reason. This is needed to preserve actual partial findings without a second agent or an unbounded finalization call.

Host validation rejects invented source IDs and identity fields; the run model also rejects orphan identity/draft references on construction or JSON load and impossible retrieval/resolution timestamps. Agent output/progress and persisted-run validation require retained full-page/text evidence for every numerical financial candidate, including uncertain values and zero; search snippets, registry material and unreadable PDFs cannot supply amounts. Structural schemas retain quantity/financial context; draft and final-profile financial coverage share the same existing invariant. Excerpt matching, semantic verification and promotion to final supported publication remain OG-153 work.

## OG-153: publication and recovery contract extensions

This section records the earlier OG-153 behavior. For the current accepted grammar
and date/citation rules, the strict contract below supersedes its semantic heuristics.

The deterministic gate consumes the trusted `CompanyResearchRun`, not an LLM-supplied source list, and produces `CompanyProfile`. Final `ProfileSource` records preserve the strongest retained provenance kind and retriever-owned metadata; full bodies remain in research artifacts. Registry material establishes identity only. Discovery-only material may explain uncertain candidates but never authorizes researched `supported` facts.

Excerpt matching uses Unicode NFC canonical normalization and whitespace collapse (`" ".join(text.split())`) identically for excerpt and retained content. Matching remains case-sensitive and contiguous: no punctuation deletion, fuzzy similarity, paraphrase or silent ellipsis repair. Quote occurrence is necessary, not sufficient; conservative deterministic entity, claim, quantity, metric, unit, period, scope and date checks must additionally support the observation. Unverifiable interpretations downgrade rather than claiming semantic proof.

Date roles are checked before retaining structured dates, including already-uncertain candidates. Employee `as_of` requires an exact full-page employee observation with the explicit date; source publication metadata is insufficient. Event `occurred_on` requires an explicit event-associated date, not a publication-labeled date or inferred first day of a month. Unverified optional dates become null. Event `published_on` requires matching full-page publication metadata or an explicit publication-role statement attached to the verified event content. Without that proof, required `EventDetails` cannot be retained: clear `value`, preserve references/reasons and downgrade a supported proposal to uncertain. The original candidate remains in the raw run, not asserted as a final structured date.

The user's OG-153 completeness rule supersedes the foundation's optional-identifier coverage penalty: missing KRS/REGON/website is displayed but does not alone force partial. Required core gaps and identity conflicts still do. `BatchResult` may additionally retain the actual `ResearchDiagnostics` and a `research_path`; no inferred usage/cost is substituted for unavailable data.

Final paths remain `outputs/<nip>.json`, `outputs/<nip>.md` and `outputs/batch_summary.csv`. A concrete filesystem checkpoint records company outcomes after each company, preserving duplicates as separate ordered input rows. Summary evidence counts include the six canonical identity facts and researched facts. Resume re-gates valid same-NIP retained research with the current deterministic rules and republishes its pair, preserving original diagnostics; a schema-valid old profile alone cannot authorize reuse. Missing/corrupt/mismatched research triggers fresh processing. Explicit partial/failed retry or force controls repeated research. No storage/provider/orchestration framework is added.

## Adversarial correction contract

**Earlier-contract history:** the issue-specific rules below record the earlier heuristic publication design and its observed corrections. They are retained for provenance, not a description of the strict contract's accepted language. The current normative grammar, full-unit scope, and evaluation taxonomy are in [STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md) and [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md). Historical measurements remain earlier-contract evidence.

### Strict contract and semantic scope

The strict contract replaces the earlier heuristic assertion rules with exact finite productions. Its unit of semantic analysis is the entire retained `full_page.content`, NFC-normalized and stripped only at the outer edges, no more than 4096 Unicode code points. The whole unit must match one production, including the final full stop. No sentence/window extraction, favorable-clause selection, header or neighboring context, tables, combined assertions, ignored trailing content, or retrieval-time clipping can manufacture a match.

Entity matching is literal against the resolved legal name after NFC and whitespace-run normalization; case, punctuation, legal form, spelling, and order are not relaxed. Labels must be source-quoted JSON strings decoded as labels; values are opaque, exact, and cannot be inferred from unquoted text, synonyms, translations, substrings, or delimiters. The contract's English/Polish qualitative productions, optional modifiers, and exact predicates are enumerated in the normative document; unlisted variants are not implicitly accepted.

The recognized qualitative shapes are only the listed products/services predicates (`offers`, `provides`, `sells`, `manufactures`, `supplies`; Polish `oferuje`, `świadczy`, `sprzedaje`, `produkuje`, `dostarcza`), optional `currently`/`obecnie`, English/Polish “operates as,” and exact industry/market bridges. They require the literal resolved entity, fixed case-sensitive grammar, one opaque quoted label, and final period. No other modifier, predicate, prefix, tail, alias, translation, or inferred category is admitted. Employees require the exact English `employs COUNT people` or Polish `zatrudnia COUNT pracowników` shape, optionally followed by an explicit valid `as of`/`na dzień` Gregorian date; count is ASCII digits, no grouping/range/approximation, and cannot be later than run generation. Financials have only `reported`/`recorded` × `revenue`/`net profit`/`net loss`/`net result`; currency is exactly PLN/EUR/USD, scale exactly units/thousand/million/billion, amount is a bounded ASCII decimal with the specified sign rules, and both complete ISO interval dates are required. Actual standalone legal-entity scope is mandatory; no group scope, conversion, rounding, table/column assembly, neighbor borrowing, guidance, delta, conditional result, or extra amount/context is accepted. Events are only opened/launched/signed or otworzyła/uruchomiła/podpisała with one opaque quoted label and optional explicit occurrence date; title equals label and summary equals the entire assertion unit. Publication date must come from that same page's publication metadata within the recent-event window; occurrence and publication dates cannot substitute for one another. Every list member needs its own complete, independently eligible unit. The normative contract specifies exact regex-level bounds and edge cases; these examples are not an extension point.

Registry identity is also structurally finite: only mapped fields in recognized MF JSON or the exact host-generated legacy snapshot can establish identity. Arbitrary registry prose, unrelated JSON paths, evidence strings alone, and identity inferred from researched text are not substitutes. Existing host ownership, source-ID quarantine, redirect lineage, citation membership, and model invariants remain mandatory.

Already-decoded registry fields compare to candidate identity values using only NFC
and whitespace-run normalization; literal quotation marks are data. Only the explicit
citation path may JSON-decode an excerpt, and it compares that semantic value to the
same mapped field after checking occurrence in the referenced retained material.

The canonical matrix still passes 262/262 actual CLI cases, including 97 contract positives. The final micro-correction passes 696 tests, the prior 26 local CLI smoke cases, and 19 new CLI/unchecked-SDK smoke cases; see [FINAL_BOUNDARY_REVIEW.md](FINAL_BOUNDARY_REVIEW.md), which preserves the earlier 683-test snapshot separately. The original 70-case blind corpus remains failed fixture construction, not semantic evidence. Exact external replays and fresh external release acceptance remain unclaimed; legacy-envelope rejection is not a semantic success.

The three evidence states, financial field schema, dependencies and usage budgets remain. The proposal instructions explain the deliberately narrower publication boundary. Current boundary changes and limitations are in [FINAL_BOUNDARY_REVIEW.md](FINAL_BOUNDARY_REVIEW.md); the [b521edf strict report](STRICT_CONTRACT_REVIEW.md) and [earlier correction history](ADVERSARIAL_CORRECTIONS.md) retain their original populations and metrics.

### Earlier-contract assertion qualification (superseded)

Literal presence is still necessary, but a nearby verb is not sufficient. Current business/catalog claims require a recognized company-linked affirmative relation in the retained enclosing statement. The finite contract recognizes direct present relations, selected Polish present forms, restricted copular/product-list and passive forms. Actual events have a separate past-event relation set. A past offering, plan, hypothetical/conditional statement or discontinued activity is not a current offering. An excerpt cannot gain support by trimming away an enclosing condition. Recognized contrast clauses can retain an affirmative observation even when a different clause describes a plan or denial.

The relation must govern the candidate, not merely occur nearby. Active offerings use a direct-object slot with restricted determiners; industry relations use explicit `in`/`within` bridges. The clause subject must match a recognized company/pronoun/property form rather than restart at a nested pronoun. Passive claims must name the direct subject, not a phrase inside its purpose or customer complement. For example, `sells machinery to retailers of cloud services` supports `machinery`, not `cloud services`; `Machines for cloud services are sold by Example` supports the machine subject, not an offering of cloud services.

This remains a bounded heuristic grammar, **not general natural-language entailment**. Unrecognized phrasing, complex scope, attribution and unsupported languages can lose valid observations. A downgrade reason identifies a failed assertion contract without claiming that every rejected sentence has been disproved. Rejected proposed catalog values are cleared; the raw research run retains the original candidate and quote.

### Earlier-contract financial rules (superseded)

In addition to metric, interval, currency, unit, precision and entity scope, evidence must match a direct realized/reporting assertion or the narrow labeled-row form. A single leading `For YYYY-MM-DD to YYYY-MM-DD,` reporting-interval adjunct is excluded from direct-subject analysis; it does not relax any interval match or subject requirement. Targets, forecasts, denials and conditions do not establish actual financial results, including qualifiers after the amount. This is not a universal financial-table or document parser.

An exclusive unsigned `net loss`/`strata netto` magnitude is interpreted as a negative **observation** for comparison. A wrong positive candidate is cleared and downgraded, never silently rewritten to the negative amount. Explicit signs remain meaningful; a combined `net profit/(loss)` label does not itself impose a minus sign. An explicitly reported zero remains valid. Distinct actual amounts for the same metric/context remain a conflict with both citations.

### Earlier-contract employee-date rules (superseded)

An observation date must belong to the cited employee observation, using a recognized explicit date role such as `as of` or `na dzień`. Publication/retrieval dates do not supply that role. Invalid optional `as_of` is cleared independently of an otherwise verified count. Dated past-tense observations may remain supported within the existing freshness policy; future hiring does not establish headcount.

Differing counts for the same verified date remain uncertain. Distinct verified observation dates are not automatically contradictory. If either date is unresolved, differing counts remain a conflict; the gate does not arbitrarily select the newest source or infer a missing candidate date. Group and other-entity observations are not company alternatives merely because their numbers differ.

### Redirect provenance and trust boundary

`Source.redirect_chain` is empty when no redirect was observed. Otherwise it records two to six HTTP(S) request URLs: the discovered URL, each validated redirect target, and the final URL. A real self-redirect may repeat a URL; the existing five-redirect limit still bounds loops. Retained discovery snippets keep their original URL; full-page/profile metadata keeps the final URL and chain. JSON and Markdown expose that relationship.

Every static hop is public-target validated, and each response URL must match its actual request before response/redirect handling. Static thin-shell → dynamic fallback retains the static chain. An unexplained browser URL change is rejected, not invented as another validated hop. Existing private-target, redirect-limit and browser resource guards remain in force.

Run validation, page storage and publication share the lineage checks. For current records, chain endpoints must agree with retained discovery/full-page URLs; registry/snippet material cannot claim a full-page chain. Without a chain, repeated source IDs require the same normalized URL, ignoring fragments. Neither `www` nor a trailing path slash is silently removed.

The shared host key identifies the discovery URL, not the final page URL. It removes
default ports and fragments while preserving path/query. For trusted web material,
the redirect-chain start (or the unredirected source URL) cannot belong to two source
IDs. Distinct discoveries may legitimately converge on the same final URL. Registry
records have separate ownership; blocked groups cannot veto trusted discovery ownership.

The research-run format has no historical version field. Its narrow read-compatibility distinction is the actual serialized source shape: all raw source dictionaries for a non-registry ID omit `redirect_chain`, yet their normalized URLs differ. The reader copies the affected mapping branches and adds `Source.publication_blocked_reason = "unproven_legacy_url_relationship"` to the whole ID group. It does not infer hops or repair the original URLs. Typed/native inputs and current records with an explicit `redirect_chain` field, including `[]`, are not inferred to be legacy.

That marker only removes permission. The group remains visible in JSON, Markdown and limitations, but none of its material may support a researched fact, supply a date or create a conflict against independent eligible evidence. Registry identity and unrelated eligible sources remain usable, so one ambiguous legacy source need not destroy a partial profile. The denial survives a run JSON round-trip. `SourceStore` refuses marked material for current writes; mixed/trusted/contradictory marked groups and identity-integrity failures still reject the run.

The chain and denial marker are application metadata, **not cryptographic proof for arbitrary edited JSON**. Structural consistency cannot authenticate a fabricated ledger or establish that a remote publisher's assertions are true. Historical redirects still cannot be reconstructed from URL similarity; compatibility does not make affected legacy material eligible.

## Earlier-contract implementation and limits

This section records the earlier-contract verifier boundary, not a guarantee of strict-contract implementation. Both the earlier and strict specifications are finite, but their accepted languages differ; strict semantic scope is the complete retained assertion unit described above and in the normative contract. Adversarial evaluation must report unsafe acceptance and conservative rejection separately. Passing selected negatives alone is not a safety certification, and declining positives is not proof of invalidity.

Identity coherence is an internal consistency check: retained registry evidence and supported identity fields must agree with the resolved NIP/legal entity, including paths that bypass ordinary model validation. This can reject detectable contradictory mutation, but it is not cryptographic ledger authenticity. A coherently forged or edited source ledger is not authenticated, and consistent retained evidence does not establish that a publisher tells the truth.

The current frozen candidate still has an observed financial target qualifier defect: a negative post-amount target assertion that was withheld at baseline is now accepted as supported, while its positive actual-revenue control still passes (baseline 2/2, current 1/2). The contract description above is therefore not a claim that every described boundary is correctly enforced. Release status and complete current blocker evidence are in [the v0.1.1 quality report](V0_1_1_QUALITY.md#11-frozen-remediation-candidate-blocked).

