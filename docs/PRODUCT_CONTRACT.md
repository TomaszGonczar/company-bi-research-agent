# Company BI v0.1 — historical product contract

**Contract-version note:** This document records the earlier v0.1 product design and its broader profile aspirations, not the current strict publication language. The current product thesis is broad agent proposals plus narrow finite deterministic publication and abstention outside recognized semantics; it is not general language understanding or a useful broad-coverage research claim. See the normative [strict publication contract](STRICT_PUBLICATION_CONTRACT.md) and [holdout adjudication](HOLDOUT_ADJUDICATION.md). This document's prior examples/measurements do not count as strict-contract results.

## Input and identity

- One mandatory `nip` column, one company NIP per row. Read NIPs as text. Deterministic ingest may remove `PL`, spaces and hyphens; never pad, repair a checksum, or infer a NIP from a company name.
- Validate the Polish NIP and resolve its legal entity before research. The LLM researches that company; it does **not** decide which legal company the NIP represents. Invalid or unresolved rows receive a failure/status entry, not a guessed profile.
- Duplicate normalized NIPs share one company run/report; every input row still has a batch-summary entry. Name-only lookup is refused.

## Profile and output

| Section | Contract |
| --- | --- |
| Identity | Resolved legal name and NIP; KRS/REGON, registered address or city and official website where obtained, with evidence/state. Never infer a city from free-form address text. |
| Business | Concise activity description; products/services, industries and markets supported by retrieved sources. |
| Employees | Exact count or source-provided range, evidence and source date; unknown observation date stays null. A range never becomes a midpoint estimate. |
| Financials | Revenue and net result, best-effort, for up to three most recent available reporting periods found. Every asserted amount retains metric, period, currency, reported unit and legal-entity/group scope; unavailable amounts stay null. No promise of financial coverage. |
| Recent developments | Up to three meaningful items published in the 12 calendar months preceding report generation; title/summary, publication date, event date if known, and evidence. No items found does not mean no events occurred. |
| Provenance / gaps | Retriever-owned source IDs, URLs, retrieval timestamps, publication dates where known, evidence excerpts, generation timestamp and explicit conflicts/missing-data/limit reasons. |

For each resolved NIP: `outputs/<nip>.json` is canonical, and `outputs/<nip>.md` is rendered deterministically from the same validated profile. `outputs/batch_summary.csv` starts with `row_number,input_nip,nip,status,json_path,markdown_path,reason,completed_at` and may append useful legal-name, evidence-count, research-usage, duration and error-code fields. States: `complete`, `partial`, `invalid_input`, `unresolved`, `failed`. Failed/unresolved rows have no report paths. A company failure must not abort other rows; save progress after each company.

A complete profile has supported observations in every requested core section, both financial metrics for at least one shared explicit reporting interval, and no unexplained gaps. Location requires a supported registered address or city; an unknown alternative is not an extra required section. Partial profiles retain uncertain observations, unknown core observations and limit/fetch reasons. Under OG-153, missing optional KRS/REGON/website fields alone do not force partial; conflicts still do. Missing is never evidence of nonexistence. “Complete” describes coverage, not exhaustive knowledge.

## Evidence and limits

- **supported:** retrieved evidence directly supports this observation for the resolved company and stated scope. Supported by a citation does not mean independently proven universal truth.
- **uncertain:** candidate evidence exists, but conflict, identity, scope, interpretation or freshness prevents supported publication; explain why. An unresolved conflict may have no selected value.
- **unknown:** no defensible value; `value: null` and a reason, never invented `0`, `false`, or a guess. No confidence percentages.
- The deterministic gate checks trusted retrieval, excerpt presence, identity conflicts and financial context. JSON/Markdown preserve states; no second LLM rewrites or promotes observations.
- Structured dates require their own evidence even on uncertain candidates: page publication does not establish employee observation or event occurrence. Unverified optional dates stay null; an event without a verified required publication date retains uncertainty/references but no structured details.
- Initial per-company ceilings: 6 searches, 10 page reads, 2 browser reads, 1 output repair, 180 seconds. Exhaustion returns a partial result with a reason.
- OG-152 drafts reuse evidence states as candidate proposals. Host identity/source IDs and structural/date constraints are checked; numerical financial candidates additionally require eligible retained page/text material, never discovery-only snippets. `supported` is not publication-approved until the OG-153 gate. Draft run artifacts live under `runs/`, separate from the final product paths above.

## Refusals

No name-only/global entity resolution, CRM/lead scoring, people/contact enrichment, outreach, universal financial-statement parser, autonomous crawling, multiple agents, DeepAgents, skills discovery, RAG/vector DB, database/queue infrastructure, frontend/SaaS/authentication, product MCP server, generic provider interfaces or custom orchestration framework. Financial documents requiring general PDF/XML parsing are unavailable in v0.1, not an invitation to expand scope. No static HTML index is included in this baseline.

Details: [architecture](ARCHITECTURE_DECISIONS.md), [evidence/model contract](EVIDENCE_MODEL.md), [financial decision](FINANCIAL_DATA_DECISION.md).
