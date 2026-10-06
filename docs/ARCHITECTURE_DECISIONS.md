# Architecture decisions — Company BI v0.1

**Earlier-contract architecture record:** this file preserves the v0.1 implementation and prior publication-gate design. It is not the current strict semantic contract or evidence that strict productions have passed. The present product thesis is broad agent proposals with narrow finite deterministic publication and abstention outside recognized semantics. See [STRICT_PUBLICATION_CONTRACT.md](STRICT_PUBLICATION_CONTRACT.md) and [HOLDOUT_ADJUDICATION.md](HOLDOUT_ADJUDICATION.md).

Contract for [OG-148](https://linear.app/tpg96/issue/OG-148). The purpose is a small NIP-to-BI-file product, not stack imitation. The foundation choices remain frozen; OG-151 implements the deterministic ingest/identity leg only, not the research or BI-report pipeline.

## Minimum architecture

```text
CSV/XLSX with NIP
  → deterministic normalization, checksum validation and legal identity
  → one bounded PydanticAI research agent
      Tavily discovers URLs → Scrapling reads selected pages
      → candidate facts referencing retriever-owned evidence
  → deterministic evidence gate
  → canonical CompanyProfile → deterministic JSON and Markdown
  → filesystem outputs and one batch-summary row per input row
```

**NIP is the identity anchor.** The registry resolver owns legal name and identifiers. Research cannot substitute a similarly named company or change the resolved NIP. An unresolved identity never enters research and never produces a guessed company profile.

The LLM chooses queries, selects sources, interprets text and proposes observations. Code validates identity, assigns source IDs, retains retrieved text, checks evidence and financial context, sets publication states, and renders reports. There is no second report-writing LLM pass.

Use ordinary Python functions and one `company_bi` package. `models.py` owns the publication contract. Do not add service layers, provider interfaces, a workflow framework, or persistence adapters. Later stages add only the concrete ingest, registry, research, gate and rendering functions they require.

## Use / don't use / why

| Component | Decision | One concrete responsibility |
| --- | --- | --- |
| Python 3.12 | Use | A conservative interpreter baseline for the selected Python libraries. |
| uv | Use now | Reproducible environment and dependency lock; commit `uv.lock`. |
| Pydantic v2 | Use now | Canonical typed JSON and local structural/cross-reference invariants. |
| openpyxl | Use from OG-151 | Read the first XLSX worksheet's NIP column; not financial-document ingestion. |
| types-openpyxl | Use from OG-151, development only | Type-check the concrete XLSX reader against library stubs. |
| Hatchling | Use now, build-time only | Install the small `src/company_bi` package. |
| pytest | Use now, development only | Offline tests for consumer-visible schema and identity-row behavior. |
| Ruff | Use now, development only | Lint and format Python code. |
| mypy | Use now, development only | Type-check the package, including the concrete CSV/XLSX and registry code. |
| PydanticAI | Use later | One structured research/extraction agent; no orchestration framework. |
| Tavily | Use later | Discover candidate public URLs; search snippets alone do not become final evidence. |
| Scrapling | Use later | Retrieve full text from selected URLs; static fetch first, browser fetch only when necessary. No broad crawling. |
| PydanticAI `UsageLimits` | Use later | Bound model requests, tool calls and token usage. Separate deterministic counters and a deadline enforce search/read/browser/time limits. |
| Pydantic AI Harness guardrails | Don't add to baseline | No additional wrapper without a concrete threat and a demonstrated benefit over bounded typed tools and deterministic URL checks. No invented dependency/import is frozen. |
| Pydantic Evals | Use in OG-154, not installed now | A small reproducible local evaluation dataset measuring identity, supported-claim precision, coverage, failures and resource usage. |
| GitHub Actions | Use in OG-155, not created now | Run deterministic checks from a clean environment; live API access is not required for CI. |
| Logfire | Optional, disabled in baseline | Development/demo traces only; not required to run or evaluate the product. |
| AgentCanvas | Optional, not installed | A final reviewer trace artifact only if Logfire is actually used; not a runtime dependency. |

The foundation installed only Pydantic; OG-151 adds openpyxl for actual XLSX input and its development typing stubs. CSV, HTTP, checksum calculation and the CLI use the standard library. Research and extraction libraries remain decisions, not unused installations. Each later dependency must still have its named responsibility when introduced.

## Bounds and trust

Initial per-company limits: **6 searches, 10 page reads, 2 browser reads, 1 structured-output repair, 180 seconds**. Repair consumes the same budget. Limit exhaustion produces a partial profile with an explanation, not an unbounded retry. Model request/token ceilings will be selected with the actual model in the research issue; they are not fabricated here.

Tools have no arbitrary shell, filesystem or code-execution access. URLs and redirects must pass deterministic web-safety checks before retrieval; retrieved pages are untrusted data, not instructions. Source IDs and retrieval timestamps are assigned by the application, never invented by the model. Browser fallback is bounded and may fail explicitly.

The retriever stores selected page text in per-run filesystem artifacts. Canonical JSON contains source metadata and evidence excerpts, not entire pages. The gate must use the trusted retrieval ledger and stored text; a schema-valid profile alone is **not** verified evidence. A quote match proves the excerpt exists, not that an interpretation is necessarily correct. Conflicts, ambiguous identity/scope and insufficient evidence remain uncertain/unknown.

Outputs are `outputs/<nip>.json`, `outputs/<nip>.md`, and `outputs/batch_summary.csv`. Persist after each company; a failed company does not abort the batch. No database, queue, web service or worker is needed for the sample batch. Financial scope is frozen in [FINANCIAL_DATA_DECISION.md](FINANCIAL_DATA_DECISION.md).

## Explicit rejections

| Technology/capability | Why not v0.1 |
| --- | --- |
| DeepAgents, subagents, multi-agent swarms | One bounded research task; extra agents expand budgets and obscure identity/evidence ownership. |
| Skills discovery / plugin system | The required tools are known; discovery adds an unnecessary capability and trust surface. |
| RAG / vector database | A small, per-company set of retrieved pages needs direct evidence lookup, not a persistent retrieval subsystem. |
| PostgreSQL / other database infrastructure | Sequential per-company progress and outputs fit the filesystem. |
| Redis / Celery / scheduler | No distributed workload, asynchronous worker fleet or scheduled product requirement. |
| Next.js / frontend / full SaaS shell / authentication | Files and a CLI demonstrate the required workflow without a web product. |
| Generic provider abstractions / custom agent framework | There is one selected search path and one agent implementation, not two real implementations requiring an interface. |
| Product MCP server | No product-facing remote tool integration is required. Developer access to Linear is separate tooling, not application infrastructure. |
| Universal PDF/XML financial parser | Unbounded document variation would become a second product; unavailable financials are valid. |
| CRM / lead scoring / contacts / outreach | Different business workflows, not this product. |
| Name-only / global entity resolution | Conflicts with the deterministic Polish NIP anchor. |

No optional technology blocks the functional MVP. Reopening a decision requires evidence from the assigned issue, not a hypothetical future requirement.

## OG-151 registry choice

Use one fixed public source: the [MF VAT-register REST API](https://wl-api.mf.gov.pl/), `GET /api/search/nip/{nip}?date=YYYY-MM-DD`. It is accessed anonymously with standard-library HTTPS, a 10-second network timeout, no automatic retries, and one lookup per unique normalized NIP within a file. The query date is the current Polish date; source URLs and aware retrieval/resolution timestamps retain the snapshot context.

The actual NIP must match the returned `subject.nip` before any legal name/identifier is accepted. Preserve NIP, KRS and REGON strings exactly. `workingAddress` is documented as the registration address; preserve it rather than parsing a city. No website is provided by this source, so website is unknown. Other response fields (people, PESEL, bank accounts) are ignored.

`result.subject: null` means unresolved in this register, not that no legal entity exists. HTTP, network, mismatched-identity and response-schema failures become explicit failed rows. The [Ministry documents 100 search requests/day](https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat); shared-IP limits and incomplete register coverage are accepted constraints, not reasons to add another provider or retry framework.

The OG-151 checkpoint executes only `company-bi resolve`: CSV/XLSX → checksummed NIP → MF identity → JSON row outcomes. It did not include research, financial extraction, evidence gating, BI reports or infrastructure. OG-152's separate implementation boundary follows.

## OG-152 bounded research implementation

Use one PydanticAI agent with `ResearchDeps` carrying the trusted OG-151 identity, a concrete `SourceStore`, bounded counters, one Tavily client and the last validated progress draft. Its output is the canonical research-stage `CompanyResearchDraft`, not `CompanyProfile`. PydanticAI's supported run iterator observes actual request/repair attempts; no second agent, custom graph/workflow or provider interface is added.

Use Tavily basic discovery (structured hits, optional provider ranking score, host IDs) and Scrapling static HTML/text extraction; allow only two browser fallbacks. Store every discovery snippet separately from full-page material under stable IDs, plus registry identity provenance. Page reads accept IDs rather than model-supplied URLs. The in-memory progress tool grants no filesystem access and avoids an extra/unbounded finalization call on exhaustion.

Ceilings: 6 searches, 10 reads, 2 browser attempts, 180 seconds, 12 model requests, 24 tool calls and one output repair, with PydanticAI token limits and per-request timeouts. Provider/tool failures stay bounded and preserve actual saved findings; no fake successful fallback. SDK retries are disabled. Native Codex does not support a per-response output-token setting; do not claim one. Browser retry configuration is one total attempt.

URL/DNS checks reject non-HTTP(S) and nonpublic targets. Static redirect targets are checked; browser redirects are conservatively blocked because Playwright does not route later hops. This can reduce dynamic coverage. Requests are not pinned to checked IPs, so DNS-rebinding/TOCTOU remains an explicit limitation rather than a claimed network sandbox.

Offline checks (118 tests, Ruff, mypy), real static/browser retrieval and a real Tavily → Scrapling component run pass. The full native `openai-codex:gpt-6-luna` run completed with 6 model requests, 5 searches, 6 reads, 1 browser attempt and 1 output repair in 81.125 seconds; both financial attempts correctly remained unknown. PydanticAI 2.54+ supplies the native provider using the standard Codex CLI OAuth cache without application token handling, custom transport or a gateway. Agent/progress and persisted-run validation reject numerical financial candidates backed only by snippets or unreadable documents. Model-proposed `supported` states and non-exact excerpts are not publication approval. Final evidence/excerpt/semantic gating, deterministic BI rendering and research batching remain OG-153.

## OG-153 publication and recovery implementation

Use three concrete modules, not another framework: `evidence.build_profile(CompanyResearchRun)` returns canonical `CompanyProfile`; `renderer.render_json/render_markdown` consume only that profile; async `batch.run_batch` connects unchanged input, identity and bounded research sequentially. No model runs in the gate or renderer.

Final `ProfileSource` adds required material-kind provenance without changing OG-152 `Source`/`RetrievedSource`. The gate preserves trusted identity, verifies exact NFC/whitespace-normalized excerpts against retained eligible material and applies conservative claim-specific context checks. Unsupported IDs fail; ambiguous or altered candidates downgrade. The optional-identifier completeness adjustment is explicit in the product/evidence contracts, not an identity lookup change.

Persist canonical JSON/Markdown pairs at the frozen paths, original research under per-run artifacts, ordered summaries at `outputs/batch_summary.csv` and a concrete checkpoint at `outputs/_batch_state.json`. Reuse requires valid same-NIP retained research under `runs/<nip>/`, re-applies the current gate, and republishes deterministic pairs while retaining original diagnostics. Profile/status/path checks prevent mismatched recovery; a schema-valid stale profile alone is insufficient. Per-company failures stay independent; explicit retry/force controls expensive work. Interrupted publication can recover from valid retained research; no scheduler, queue, database, generic storage/provider interface or fallback-output fiction is added.

## OG-155 reliability and deterministic CI

Use one Python 3.12 GitHub Actions job with locked uv installation, pytest, Ruff lint/format, mypy and offline evaluation. Default tests block live network/provider entry points; live research commands remain separate. CI isolates Codex state and supplies no paid credentials. No dependency/provider or architecture expansion is needed.

Operational failures are additive typed records in research/tool diagnostics, not a retry framework or telemetry platform. Native PydanticAI hooks observe schema errors; the existing output validator records domain rejections before its unchanged `ModelRetry`. Safe class/path/kind/attempt/progress information replaces raw exception/payload dumps. Valid progress, resource counters and per-company isolation remain intact; finite client cleanup cannot replace a valid result.

Public-target validation explicitly rejects local/internal hostnames, non-global/mixed DNS addresses, unsafe schemes and userinfo. Source-ID-only reads and pre-follow redirect checks remain the concrete boundary. DNS validation is still not connection IP pinning; this is not a complete network sandbox. Frozen prompts, evidence gating, financial schemas, model/provider, gold and resource/repair limits are unchanged. [PROJECT.md](../PROJECT.md#og-155--offline-ci-reliability-and-webtool-safety) documents commands, failure taxonomy, diagnostics and remaining limitations.

