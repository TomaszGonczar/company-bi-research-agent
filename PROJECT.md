# Company BI v0.1

## Mission

Build a deliberately small portfolio-grade AI system that turns a list of Polish company NIPs into evidence-backed Business Intelligence profiles.

```text
CSV/XLSX with Polish NIPs
        ↓
deterministic company identity
        ↓
bounded web research
        ↓
source extraction
        ↓
structured candidate facts
        ↓
deterministic evidence validation
        ↓
JSON + Markdown BI files
        ↓
batch summary + evaluation report
```

The project is intended to demonstrate product-oriented AI engineering rather than framework engineering.

## Input

v0.1 accepts a CSV or XLSX file containing one mandatory Polish NIP per row.

NIP is the deterministic identity anchor.

The LLM may research the company after identity resolution, but it must not decide which legal entity the NIP represents.

Name-only company lookup is explicitly outside v0.1.

## Output

For every successfully resolved company, generate:

- canonical JSON profile,
- human-readable Markdown BI file,
- batch status entry in `batch_summary.csv`.

### BI profile sections

#### Identity

- legal company name,
- NIP,
- KRS / REGON where available,
- registered address or city / location, without guessing a city from address text,
- official website where identifiable.

#### Business

- concise description of what the company does,
- main products and services,
- industries and markets where supported by sources.

#### Scale

- employee count or source-provided range,
- source and date,
- no invented point estimate when only a range is available.

#### Financials

Best-effort in v0.1:

- revenue,
- net result,
- up to three recent available reporting periods,
- period,
- currency,
- legal-entity vs group scope.

If financial data cannot be extracted reliably, return `unknown` rather than expanding the project into a universal financial-statement parser.

#### Recent developments

- up to three meaningful recent events,
- publication date,
- event date where known,
- supporting sources.

#### Provenance and quality

- source IDs attached to facts,
- source URLs,
- retrieval timestamps,
- publication dates where available,
- explicit uncertainty / missing data / conflicts,
- report-generation timestamp.

## Evidence semantics

Every publishable observation must have one of three states:

- `supported` — retrieved evidence directly supports the observation for the resolved company and stated scope,
- `uncertain` — candidate evidence exists, but identity, scope, interpretation, freshness, or source conflict prevents strong publication,
- `unknown` — insufficient evidence was obtained.

Rules:

- Do not use decorative confidence percentages.
- `unknown` must never silently become `0`, `false`, or a guessed value.
- `supported` means supported by the cited source, not independently proven universal truth.
- Employee ranges remain ranges unless an exact count is explicitly supported.
- Financial facts must preserve metric, period, currency, and entity/group scope.

## Core architecture

```text
CSV/XLSX
  → input validation
  → NIP validation
  → deterministic company identity resolution
  → bounded web search
  → page extraction
  → evidence-backed structured extraction
  → deterministic evidence gate
  → canonical JSON
  → deterministic Markdown rendering
  → batch summary
```

## Preferred stack

Use only where justified:

- Python
- `uv`
- Pydantic v2
- openpyxl for XLSX NIP input (not financial-document parsing)
- PydanticAI
- Tavily for web search / discovery
- Scrapling for reading selected web pages
- PydanticAI `UsageLimits`
- Pydantic AI Harness guardrails where they solve a concrete safety problem
- pytest
- Ruff
- type checking
- GitHub Actions

Optional after the functional MVP exists:

- Logfire for observability
- AgentCanvas for a reviewer-friendly trace visualization
- Pydantic Evals for the evaluation harness

## Search vs extraction

Search discovers candidate sources.

Scrapling reads selected sources.

Do not use Scrapling as a justification for broad autonomous crawling.

Preferred fetch strategy:

1. ordinary/static fetch first,
2. dynamic/browser fetch only when necessary,
3. explicit failure when a source remains unavailable.

Do not claim a universal quality improvement such as “+70%”. If useful, measure the value of full-page extraction on this project’s own evaluation set.

## PydanticAI role

Use one bounded research/extraction agent.

The agent may:

- decide what to search,
- select relevant sources,
- interpret unstructured company information,
- extract candidate structured facts,
- identify potentially meaningful recent developments.

The agent must not receive:

- arbitrary shell access,
- arbitrary filesystem access,
- unrestricted code execution,
- authority to create final source IDs,
- authority to publish unsupported claims as facts.

## Deterministic evidence gate

Code verifies at minimum:

- referenced source was actually retrieved,
- evidence excerpt exists in stored source content,
- company identifiers do not conflict with the resolved NIP,
- financial values preserve metric, period, currency, and scope,
- `uncertain` / `unknown` observations cannot be rendered as `supported`,
- missing data remains missing,
- source metadata and retrieval timestamp exist.

Do not build a generic verification framework.

## Rendering

Final JSON and Markdown reports are generated deterministically from validated structured data.

Do not add a second LLM pass whose job is to “write a nicer report”.

The same validated profile should render the same output.

## Resource limits

Initial configurable limits per company:

- max ~6 search queries,
- max ~10 page reads,
- max ~2 dynamic/browser reads,
- max 1 structured-output repair,
- max ~180 seconds research time.

Hitting a limit returns a partial profile with an explicit explanation.

One company failure must not stop the full batch.

Persist progress after each company.

## Explicit non-goals for v0.1

Do not add unless a current issue explicitly requires it:

- name-only company lookup,
- global entity resolution,
- CRM functionality,
- lead scoring,
- people/contact enrichment,
- outreach generation,
- multi-agent orchestration,
- subagents,
- DeepAgents,
- vector databases,
- RAG,
- PostgreSQL,
- Redis,
- Celery,
- frontend application,
- authentication,
- MCP server,
- plugin system,
- generic provider abstraction,
- custom agent framework,
- scheduler,
- universal financial-document parsing.

Prefer deleting complexity over generalizing it.

## v0.1 success condition

The functional MVP exists when this works:

```text
input.xlsx
    ↓
valid Polish NIPs
    ↓
resolved company identities
    ↓
bounded AI research
    ↓
validated facts
    ↓
outputs/
    ├── <nip>.json
    ├── <nip>.md
    └── batch_summary.csv
```

The system must demonstrate at least three outcomes:

- complete profile,
- partial profile with honest gaps,
- failed / unresolved company handled safely.

## Evaluation

Use a small but varied evaluation set, approximately 8–12 companies/cases.

Measure at minimum:

- identity correctness,
- supported-claim precision,
- incorrect unsupported facts published as supported,
- useful-field coverage,
- safe handling of conflicts and missing data,
- number of searches / page reads,
- runtime per company.

Do not optimize toward one flattering aggregate score.

## Portfolio quality gate

The project is ready to show externally only when:

- clean clone works,
- deterministic tests and CI are green,
- complete / partial / failure examples are included,
- surfaced factual claims have traceable evidence and state,
- evaluation results are documented,
- limitations and non-claims are explicit,
- reviewer path takes approximately 10 minutes or less,
- the repository is useful independently of any recruitment process.

## Scope control

If development starts expanding, cut in this order:

1. presentation polish,
2. static HTML batch index,
3. AgentCanvas visualization,
4. dynamic-browser support for unusual pages,
5. deeper financial document support,
6. extra registries/providers.

Do not cut:

- NIP identity anchor,
- source provenance,
- `supported / uncertain / unknown` semantics,
- evidence gate,
- reproducible evaluation.

## Foundation contracts — OG-148 / OG-149 / OG-150 / OG-160

The foundation checkpoint is `6cfcfe4`; OG-151 is committed at `8701453`, OG-152 at `c8aa7a2` and OG-153 at `59e76de`. Deterministic CSV/XLSX identity, bounded research, deterministic publication, BI rendering and sequential batch are implemented. OG-154 adds reproducible offline evaluation with separately measured precision and coverage; its low-yield baseline is documented below. CI, fuller web hardening and later retrieval experiments remain future issues.

- [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md): minimum pipeline, dependency responsibilities, trust boundaries and rejected technologies.
- [One-page product contract](docs/PRODUCT_CONTRACT.md): exact input, output, evidence states, limits and refusals.
- [Canonical model/evidence contract](docs/EVIDENCE_MODEL.md): the ten required Pydantic models and publication invariants.
- [Financial decision](docs/FINANCIAL_DATA_DECISION.md): two-company live spike; official issuer HTML/text with linked CSV where available, then UNKNOWN. No PDF/XML/archive financial parser.
- [`examples/profiles/`](examples/profiles/): complete, partial and conflicting-source **synthetic** JSON fixtures, not real retrieved company reports.

Runtime dependencies are Pydantic, openpyxl, `pydantic-ai-slim[openai]`, `tavily-python` and `scrapling[fetchers]`. The slim PydanticAI distribution installs only the selected OpenAI SDK integration, not every model provider. Scrapling's fetchers extra supplies its static HTTP and Playwright browser support. `pytest-asyncio` is a development-only pytest extension for deterministic async tool/agent tests. CSV, checksum calculation and registry HTTP still use the standard library; development typing stubs cover openpyxl. Python 3.12 and `uv.lock` fix the environment.

### Offline checks

```sh
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check src tests
uv run --frozen mypy src
```

Foundation verification at `6cfcfe4` on 2026-10-02: **43 invariant tests passed**, Ruff lint/format checks passed, and mypy passed for the then-two source files. A throwaway consumer loaded all three examples, serialized/revalidated them, displayed every profile section with states/citations without an LLM, and retained nulls, employee ranges, decimal values, units and financial scope. A separate smoke exercised the inclusive 12-month news boundary. The live LPP financial candidate retained `2.4` billion PLN, group scope and its non-calendar fiscal interval, explicitly marked uncertain/not gate-verified.

The financial spike exercised public KRS JSON, issuer HTML/CSV/text and RDF document discovery for Asseco Poland and LPP. It closed after 10.2 minutes within its 120-minute ceiling; source URLs, observed values and limitations are documented in the decision. No extraction-quality or universal coverage claim is made.

### Definition-of-Done assessment

| Issue | Result | Evidence |
| --- | --- | --- |
| OG-148 | Satisfied locally | Every direct dependency has one concrete responsibility and a use/defer/reject rationale independent of Vstorm's choices. |
| OG-149 | Satisfied locally | A single product-contract page states what v0.1 accepts, produces and refuses. |
| OG-150 | Satisfied locally | All ten required models, state/quantity/provenance invariants and three examples exist; the smoke consumed the schema without a second LLM pass. |
| OG-160 | Satisfied locally | Real-source investigation and a frozen primary route, UNKNOWN fallback, mandatory context and unsupported-format boundary permit later implementation without another financial research phase. |

These results completed the four **foundation** issues, not the functional MVP or portfolio gate. OG-151, OG-152 and OG-153 execution boundaries are documented below. Linear status was not changed through the read-only connection.

## OG-151 — executable deterministic identity slice

```sh
uv sync --frozen
uv run --frozen company-bi resolve examples/nips.csv
# For a supplied workbook:
uv run --frozen company-bi resolve input.xlsx --output outputs/identities-xlsx.json
```

The default output is `outputs/identities.json`: a JSON array of canonical `BatchResult` records, **not** final BI profiles. Each input row records original input, normalized/validated NIP where valid, outcome, identity if resolved, source metadata, optional failure code/reason and completion timestamp. BI report paths remain null. Output directories are created automatically; an existing output is replaced after successful input processing, but the input file cannot be overwritten.

### Input and validation

- UTF-8 CSV (optional BOM), comma separator, or the first worksheet of XLSX. Exactly one `nip` header, matched case-insensitively with surrounding whitespace removed. Other columns are ignored, never used to infer a company. No legacy XLS or import-plugin framework.
- Every data record is represented, including blank/missing NIP cells. Row numbering starts at 2, counting the header; CSV numbering follows logical records.
- Text may contain a leading `PL` (case-insensitive), whitespace and ASCII hyphens. Only these decorations are removed. The result must contain ten ASCII digits and satisfy the Polish checksum weights `(6, 5, 7, 2, 3, 4, 5, 6, 7)` modulo 11; remainder 10 is invalid.
- Exact integer XLSX cells are converted to their existing decimal digits without padding. Floats, booleans, dates and formulas are rejected, not rounded/evaluated. Lost leading zeros are never reconstructed, and checksums are never repaired.
- Malformed NIPs do not reach the registry. File/header/encoding/read errors exit with code 2 before lookup; a completely processed file exits 0 even when individual rows fail. Inspect JSON row statuses for row-level failures.

### One deterministic source

Use the [MF VAT-register API](https://wl-api.mf.gov.pl/) directly by NIP for the current Polish date, with a 10-second network timeout and no automatic retry. Duplicate normalized NIPs share one successful, absent or failed lookup snapshot within a file. No API key is required.

The returned NIP must match the validated input. Legal name, NIP, REGON and KRS come from that response, with identifier strings preserved exactly. The [official API schema](https://www.gov.pl/attachment/9a515a2c-17d5-405a-a7fd-2df4cba2c15c) defines `workingAddress` as the registration address; preserve it and leave the separate city unknown rather than parsing it. The API supplies no website, so website remains unknown with an explicit reason.

| Row outcome | Meaning |
| --- | --- |
| `resolved` | Exact NIP matched a supported legal identity; optional missing fields may still be unknown. No BI completeness claim. |
| `invalid_input` / `INVALID_NIP` | Presence/type/format/length/checksum failure; normalized NIP, identity and sources are empty. |
| `unresolved` / `COMPANY_NOT_FOUND` | Valid NIP, successful MF response with `subject: null`; no guessed company. Not proof that no entity exists outside this source. |
| `failed` | Operational/source problem: `REGISTRY_NETWORK_ERROR`, `REGISTRY_HTTP_ERROR`, `REGISTRY_INVALID_RESPONSE` or `REGISTRY_IDENTITY_MISMATCH`. No guessed identity; other rows continue. |

Source URLs retain the query date, and retrieval/resolution/completion timestamps are aware. Registry-field provenance uses source IDs and the retrieved JSON field values; no unstructured research/evidence gate is implemented. Determinism means explicit validation and exact authoritative identity mapping, not permanently identical external data or timestamps.

### OG-151 verification and exit

- **78 offline tests passed**: known-valid/checksum-invalid/malformed NIPs; normalization; resolved/absent/mismatched registry data; missing identifiers; mixed and duplicate rows; CSV/XLSX, blank/formula cells and headers; operational failures; canonical provenance/path constraints. Tests block live registry calls and use controlled raw responses.
- Ruff lint/format checks passed; mypy passed for all six source files.
- Actual `company-bi resolve examples/nips.csv` wrote one resolved, one invalid and one unresolved row. A temporary XLSX with equivalent integer/string cells produced the same outcomes; its temporary workbook was removed.
- Inspected live records: `"ASSECO POLAND" SPÓŁKA AKCYJNA`, NIP `5220003782`, REGON `010334578`, KRS `0000033391`, registration address `OLCHOWA 14, 35-322 RZESZÓW`. Identifier leading zeros survived, city/website stayed unknown, and both malformed `123` and valid unresolved `1234563218` produced structured outcomes.
- All three synthetic profile fixtures were explicitly migrated to the address/city contract and round-tripped successfully. No source/confidence semantics or financial decision was replaced.

Limitations of the identity slice: this one register is not universal Polish-entity coverage; the [Ministry's shared search limits](https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat) can cause operational failures. Website discovery is deliberately absent rather than guessed. CSV is comma-separated and XLSX uses the first worksheet; no general importer is promised.

**OG-151 Definition of Done satisfied locally:** one command converts a small CSV/XLSX NIP file into persisted deterministic identity records with independent row outcomes.

## OG-152 — bounded one-company research draft

```sh
uv sync --frozen
uv run --frozen playwright install chromium
# Supply TAVILY_API_KEY in the environment or ignored .env.
# Log in once with the standard Codex CLI if needed:
codex login
uv run --frozen --env-file .env company-bi research 5220003782 \
  --model openai-codex:gpt-6-luna --output runs/asseco/research.json
```

The default model is `openai-codex:gpt-6-luna`; `--model` or `COMPANY_BI_MODEL` selects the model. PydanticAI 2.54+ supplies its native Codex OAuth provider and reads the standard `~/.codex/auth.json` (or `$CODEX_HOME/auth.json`) itself; the application does not parse, export, copy or persist OAuth/session tokens. `OPENAI_API_KEY` is not required for Codex. The native provider's refreshed tokens remain in memory; CLI login remains the standard credential-management path.

The ordinary existing `openai:<model>` SDK path can still use `OPENAI_API_KEY`/`OPENAI_BASE_URL`. Already-exported shell variables take precedence over uv dotenv files. Local credential files, outputs, browser caches and run artifacts must never be committed. No custom OAuth adapter, gateway, authentication service or credential store is part of the product.

`research` validates one NIP and calls the unchanged MF lookup before creating one `Agent[ResearchDeps, CompanyResearchDraft]`. The host's identity, including name/NIP/KRS/REGON/location, is copied unchanged into the run. The agent output schema cannot replace identity or create sources. It has only Tavily search, source-ID-only Scrapling reads and an in-memory progress checkpoint; no shell, filesystem-write or arbitrary-code tools.

Default output: `runs/<nip>/<UTC-run-timestamp>/research.json`, or `--output`. This typed `CompanyResearchRun` retains the unchanged identity, candidate draft, every registry/snippet/full-page material snapshot and diagnostics. A stable host ID can have multiple snippet versions and a page snapshot; reading a page does not discard its snippets or full stored text. Tool-facing page text is capped at 16,000 characters, independently of the retained content. These are **not** canonical final BI profiles or Markdown reports.

### Bounds, failures and provenance

- At most 6 Tavily searches (5 results/query), 10 page-read attempts, 2 dynamic attempts and 180 seconds of research. PydanticAI also limits model requests to 12, tool calls to 24, input tokens to 120,000, output tokens to 16,000 and total tokens to 136,000. Each model request has a 30-second timeout. Native Codex does not support a per-response `max_tokens` cap; only the ordinary API-key path has the 6,000-token response setting. Codex uses low reasoning effort plus the supported usage ceilings/deadline, without claiming a nonexistent output cap.
- One output-repair request maximum; zero model SDK or tool automatic retries. Scrapling browser `retries=1` means one **total** attempt, unlike static mode's `retries=0`.
- `completed` means a model returned a structurally valid **candidate** draft, not complete BI coverage or verified publication. `partial` retains validated saved findings after interruption; `failed` has no saved model findings and explicit unknowns. Limit/tool failure reasons are retained in the draft and diagnostics. Exit code 0 covers completed/partial drafts, 1 a failed research run, and 2 configuration/input/identity/file errors.
- Only public HTTP(S) page targets are allowed. DNS/IP checks reject local/private/link-local/nonpublic destinations. Static redirects are checked before following; browser HTTP redirects are blocked before following because Playwright routes only their first hop. Browser rendering has service workers/downloads disabled. DNS checks are not IP pinning: DNS rebinding/TOCTOU protection is incomplete and is not claimed as an OG-155 safety guarantee.
- Static HTML/text/CSV first; dynamic fallback only for failed or contentless/recognizable-JS-shell pages. PDF/XML/ZIP/office/image payloads are refused, not parsed as financial evidence. Publication dates require explicit article/date-published metadata, never a guessed year.
- Source-ID membership and schema/date/context constraints are deterministic. Financial amounts, including uncertain values and zero, require the frozen OG-160 metadata and retained full-page/text evidence in both agent/progress validation and persisted-run validation; discovery-only snippets and unreadable PDFs cannot supply amounts. Excerpt occurrence, entity semantics and final promotion of `supported` candidates remain **OG-153** work. Employee ranges, uncertainty/conflicts and unknowns are retained.

### Observed verification and OG-152 exit

- **118 offline tests passed**; Ruff lint/format checks (16 Python files) and mypy for 10 source files passed. Tests disable real model/provider calls and use controlled SDK responses and PydanticAI test/function models. Financial regressions proved failing-before/passing-after rejection of snippet-only amounts, including uncertain zero and serialized-run reloads; the same source ID becomes eligible only when full-page material is retained.
- Real MF identity plus a real static Scrapling read of Asseco's investor financial-highlights page succeeded. A separate controlled-discovery/static-shell smoke exercised actual redirect-guarded Chromium extraction successfully. These are retrieval smokes, **not** a full Tavily/model research demonstration.
- The actual research CLI resolved the real MF identity, ran a controlled PydanticAI test model, persisted/reloaded the typed research artifact and retained unknown financial nulls. Its temporary output was removed. This proves CLI persistence, not a live model/Tavily research run.
- Asseco's investor site returned HTTP 403 to the browser routing transport in one smoke; that failure stayed explicit. Site blocking and missing eligible financial context can legitimately leave facts unknown. Upstream Scrapling/lxml emits a `strip_cdata` deprecation warning in the offline HTML fixtures; it is not suppressed.
- An earlier live agent attempt reached an OpenAI-compatible API-key endpoint (`openai:gpt-5.4-mini`), which returned “insufficient credits” on its first request. It retained a truthful failed/unknown artifact rather than claiming research success. The operator subsequently chose native Codex OAuth; that API-key funding failure is not a prerequisite for the native path.
- A separate **real Tavily → Scrapling** component run succeeded: 1 search, 1 static read, 0 dynamic reads. Host source `S002` is `https://pl.asseco.com/en`; full retained text describes “a global software producer for business and administration” and lists its sector offerings. The provider ranking score is discovery metadata, not fact confidence. This is not substituted for an agent-generated draft.
- The **full native live CLI run** resolved NIP `5220003782` through unchanged MF identity, then used `openai-codex:gpt-6-luna`, real Tavily and real Scrapling. Its ignored artifact is `runs/5220003782/og152-codex-verified.json`; typed reload succeeded. Actual diagnostics: `completed`, **6 model requests, 5 searches, 6 page reads, 1 dynamic attempt, 1 output repair, 77,794 input tokens, 2,351 output tokens, 81.125 seconds**. Cost is `null` because no actual provider cost was available; no estimate is invented.
- Manually inspected identity: `"ASSECO POLAND" SPÓŁKA AKCYJNA`, NIP `5220003782`, KRS `0000033391`, REGON `010334578`, address `OLCHOWA 14, 35-322 RZESZÓW`. Registry city/website remain unknown. Both financial metrics are **unknown**, with null value/currency/unit/period/scope: the located official PDFs were not eligible retrieved text.
- The live draft proposes Polish software/services activity, sector offerings and **2,465 employees as of 2025-12-31**. Business source `S016` and employee source `S004` remain discovery snippets after failed/refused reads, so these are unverified candidate observations, not published facts. Retrieved official news pages `S006` and `S007` contain explicit publication dates **2026-08-27** and **2026-05-27** and Asseco Poland **segment**, not legal-entity, activity. Draft summaries preserve that scope.
- Manual excerpt inspection found model-added ellipses/non-exact excerpts even for some retrieved pages. No excerpt/semantic publication approval is claimed. PDF refusal, an ESG-site certificate/browser failure and all gaps remain explicit. The earlier live artifact with snippet-only revenue is now rejected by the persisted-run model; the corrected artifact reloads successfully.
- **OG-152 Definition of Done is satisfied:** bounded one-company typed research, actual retained sources, truthful diagnostics, offline checks and full live/manual verification. Native credentials stay in the standard SDK/CLI path. No final evidence gate, BI renderer, research batch, eval/CI expansion, provider framework or runtime subagents were introduced. Stop before OG-153.

## OG-153 — evidence-backed publication and batch

```sh
uv run --frozen --env-file .env company-bi batch examples/research_batch.csv \
  --model openai-codex:gpt-6-luna
# Reuse saved outcomes by default; retry deliberately:
uv run --frozen --env-file .env company-bi batch examples/research_batch.csv --retry-partial
uv run --frozen --env-file .env company-bi batch examples/research_batch.csv --retry-failed
# Explicitly repeat all normalized NIPs:
uv run --frozen --env-file .env company-bi batch examples/research_batch.csv --force
```

`--output-dir` defaults to `outputs`; `--runs-dir` defaults to `runs`. The sample deliberately spans software (Asseco Poland), apparel retail (LPP) and energy (ORLEN). Asseco/LPP NIPs were established in the prior live slices and financial decision; ORLEN NIP `7740001454` is stated in its [official regulatory notice](https://www.orlen.pl/en/investor-relations/reports-and-publications/regulatory-announcements/2026/02/Regulatory-announcement-no-17-2026). Missing/unreadable financial evidence is a normal partial outcome, not permission to infer totals.

The batch reuses OG-151 input/identity and OG-152 research unchanged. Only `evidence.py` decides final states; `renderer.py` consumes the validated `CompanyProfile` without another model call. `batch.py` processes unique normalized NIPs sequentially, writes independent `<nip>.json`/`<nip>.md` pairs, and retains ordered input rows (including duplicates) in `batch_summary.csv`.

Each completed company checkpoints `outputs/_batch_state.json`; raw research remains at `runs/<nip>/<UTC timestamp>/research.json`. Resume requires valid same-NIP retained research and re-applies the current gate before republishing deterministic JSON/Markdown. This prevents an older profile from preserving observations rejected by a corrected gate. Typed profile, status, pair content and expected paths are checked; missing/corrupt/mismatched research cannot authorize reuse. Valid retained research can also recover an interruption immediately before checkpointing. Partial/failed/unresolved records are reused by default; retry flags opt into new research and `--force` includes complete records. A failed retry must not erase the earlier usable report.

Final source records retain `registry`, `full_page` or `search_snippet` provenance. Registry supplies legal identity only; researched supported claims require retained full-page evidence. Excerpts use case-sensitive NFC plus whitespace collapse and contiguous exact matching. Ellipses/paraphrases are not silently repaired. Fact-specific claim/context checks can downgrade an exact quote when it does not establish the candidate observation. Unverified candidates, nulls and reasons remain visible; no confidence score or another LLM approves publication.

Date verification applies to uncertain candidates too. An employee observation date needs an explicitly dated employee statement, not a page's publication date. A month-only occurrence cannot become the first day of that month; an event publication date cannot become its occurrence date. Unsupported optional dates become null. If an event's required publication date or cited content is unverifiable, its structured details are cleared, retaining references and rejection reasons in the final profile and the original candidate in the raw research artifact.

Unknown optional KRS/REGON/website fields no longer alone force partial. Required core gaps, conflicts, missing paired financial coverage and limitations still do. JSON and Markdown retain quantities, decimal precision, units, explicit reporting intervals and company/group scope; event publication and occurrence dates remain separate. Research usage is actual SDK/counter data, with empty/null values for unavailable diagnostics or cost.

### Observed verification and OG-153 exit

- **193 offline tests passed**. Ruff lint and format checks passed for 22 Python files; mypy passed for 13 source files. The 14 upstream Scrapling/lxml `strip_cdata` warnings remain visible, not suppressed.
- Throwaway consumers exercised the actual gate and renderer: altered/model-ellipsis excerpts cannot support claims; employee bounds do not become exact counts; operating profit, revenue and a month number do not become total net-result amounts. An explicitly evidenced zero survives. A controlled full-page fixture reached `complete` with unknown optional identifiers, paired financial coverage and no limitations.
- A separate **controlled, synthetic** runtime batch produced `complete`, `failed`, `partial`, then a duplicate `complete` input row. Both successful report pairs and all ordered summary rows were written. The injected failure did not stop the following company; resume added no lookup/research calls. Its temporary artifacts were removed. This is branch/failure-isolation proof, not real-company coverage.
- The actual `examples/research_batch.csv` CLI used unchanged MF identity, native `openai-codex:gpt-6-luna`, Tavily and Scrapling. It wrote all three independent report pairs and the summary without manual profile editing: **0 complete, 3 partial, 0 failed/unresolved**. All final financial values are null. All researched candidates remained uncertain or unknown; each company has four supported registry identity facts. The sample did **not** attain the hoped-for real complete profile, and no real complete excerpt is available.

| Company / NIP | Supported / uncertain / unknown facts | Model requests | Searches / page reads | Browser attempts / output repairs | Input / output tokens | Research seconds |
| --- | --- | ---: | --- | --- | --- | ---: |
| Asseco Poland / `5220003782` | 4 / 6 / 5 | 5 | 4 / 3 | 0 / 0 | 57,142 / 2,103 | 73.281 |
| LPP / `5831014898` | 4 / 8 / 4 | 6 | 6 / 8 | 0 / 0 | 105,926 / 2,427 | 81.944 |
| ORLEN / `7740001454` | 4 / 8 / 4 | 4 | 4 / 7 | 2 / 1 | 36,096 / 2,540 | 68.010 |

Costs are null because the provider supplied no actual cost. Unsupported documents limited Asseco/LPP; failed reads, certificate errors and the exhausted browser budget limited ORLEN. Model completion is not BI completeness.

Manual inspection found an unsupported LPP `2026-07-01` occurrence date derived from “In July this year”, plus employee dates copied from publication metadata. General date-role sanitation now clears these values, including already-uncertain candidates. Unverified required event publication/content clears the structured event details while preserving candidate references/reasons. The corrected persisted JSON and Markdown were reloaded and compared with the current gate/renderer; identity stayed unchanged, employee dates are null, financial values are null and unverified event details are null.

The real CLI resume refreshed all six report files in 1.53 seconds. Retained research paths, hashes, timestamps and diagnostics were unchanged. A subsequent instrumented CLI resume observed **0 registry lookups and 0 research calls**. Changed rules therefore do not require repeated model work or trust stale rendered profiles.

After correction and re-inspection: **none found in the inspected sample** of surviving hallucinated published facts. Uncertain qualitative candidates and candidate excerpts remain explicitly unverified; this is not an extraction-accuracy or universal truth claim.

A temporary XLSX also exercised the actual CLI with retained real research: prefixed/hyphenated text, an exact integer cell and a duplicate NIP produced four ordered partial summary rows and three independent report pairs, with **0 lookup/research calls**. The workbook and its separate output directory were removed.

Representative **real LPP** fields after re-gating (abridged, not a complete profile):

```json
{
  "employees": {"state": "uncertain", "value": null, "as_of": null},
  "financials": [
    {"metric": "revenue", "state": "unknown", "value": null},
    {"metric": "net_result", "state": "unknown", "value": null}
  ]
}
```

Its cited “nearly 63,000 people” is approximate Group evidence, not an exact standalone-company headcount. The report does not select 63,000 or inherit the article's publication date. The controlled complete fixture, not a real report, retained `120` exact employees as of `2026-09-01`, revenue `"12.5"` million PLN and total net result `"0"` million PLN for the explicit `2025-01-01`–`2025-12-31` legal-entity interval.

### Definition-of-Done assessment

| Criterion | Exercised evidence |
| --- | --- |
| 1. Deterministic candidate gate | Actual research artifacts passed through `build_profile` before publication. |
| 2. Supported / uncertain / unknown | Canonical models, controlled complete output and all three inspected real reports preserve states and nulls. |
| 3. Unsupported source IDs rejected | Offline orphan-reference rejection and retained-source model invariants. |
| 4. Altered excerpts rejected | Exact NFC/whitespace normalization regressions, including model-added ellipses; no fuzzy repair. |
| 5. Financial context required | Metric/amount/period/currency/unit/scope regressions, conflict handling, legitimate zero and controlled fully supported financials. |
| 6. Deterministic JSON/Markdown | Canonical reload, repeated rendering and persisted pair equality without another model. |
| 7. Multiple NIPs | Three-company real CLI and ordered duplicate-row controlled batch. |
| 8. Failure isolation | Actual controlled batch writes complete/partial neighbors around an injected failure. |
| 9. Complete / partial / failed | Controlled runtime demonstrates all three; real sample honestly reports only partial. |
| 10. Practical progress/resume | Per-company checkpoint, interruption recovery, explicit retry regressions and zero-call real resume. |
| 11. Deterministic checks | 193 tests, Ruff lint/format and mypy passed. |
| 12. Real sample inspection | All three corrected Markdown reports and canonical JSON pairs were inspected. |

OG-153's twelve gate/render/batch criteria are satisfied; the live complete-profile aspiration remains unmet. The gate deliberately favors false negatives over unsupported publication: paraphrases, insufficient entity/context attachment and missing date roles may downgrade genuine information. Evidence links remain usable citations/discovery leads, not a promise that blocked or unsupported documents can be fetched. The CLI still requires configured Tavily credentials even for a cached batch. No evals, CI expansion, general PDF/XML financial parser, runtime subagents, databases/queues, provider framework, prompt/token optimization or unrelated web-safety changes were introduced. Stop before OG-154.

## OG-154 — measured reproducible evaluation

```sh
uv run --frozen company-bi eval \
  --dataset examples/evals/dataset.json --output-dir outputs/evals
```

The deterministic Pydantic Evals 2.54.0 suite has **12 cases: nine controlled and three frozen real-run replays**, with no LLM judge or live dependencies. [EVAL_SPEC.md](docs/EVAL_SPEC.md) defines eligibility/denominators; [EVAL_RESULTS.md](docs/EVAL_RESULTS.md) records gold revisions, source proofs, resource counters, baseline and limitations.

Measured unchanged production `59e76de`: identity **10/10**, supported precision **44/44** (registry **42/42**, researched **2/2**), unsupported-as-supported **0**, researched recall **2/19**, over-downgrade **17/19**, uncertainty obligations **28/28**, strict unknown obligations **40/41**. The unknown miss is a deliberately rejected run with no website Fact, not an invented value. Seven eligible real researched claims all remain uncertain: four extraction/citation/qualifier losses and three genuine gate-loss opportunities. Across 29 real researched fields, primary losses are retrieval **11**, extraction **10**, gate **3**, unavailable eligible context **5**.

This demonstrates safety on a small selected set, **not acceptable useful coverage** or established population precision. Registry successes cannot hide zero real researched support. Initial gold/constraint mistakes and corrected results are both preserved; no input, eligible truth, precision/recall count or production behavior was tuned to improve metrics. No production fix was made.

The CLI was exercised without credentials with socket/research-call guards: **12 cases, exit 0, no network or research calls**. **205 tests**, Ruff, mypy (14 source files) and formatting (24 Python files) passed; upstream warnings remain visible. Original research diagnostics and native replay timings are separate. Public snapshots and machine-readable baselines are deliberate evaluation fixtures; ignored credentials/runs/outputs are not staged.

All twelve OG-154 evaluation criteria are satisfied. Linear status/comments remain unchanged because only read tools are mounted and authenticated browser relay is unavailable. No OG-155 work was started.


## OG-154A — one measured researched-coverage iteration

OG-154 is approved and frozen at `46bdd26`. [RECALL_RECOVERY.md](docs/RECALL_RECOVERY.md) records all 17 original eligible misses before fixes, reproduced baseline, regression-first changes and remaining limits; [machine-readable comparison](examples/evals/og154a-comparison.json) preserves raw before/after metrics and immutable input hashes.

Proposed supported research citations now require exact retained full-page spans before progress/final-output acceptance. Uncertain discovery remains visible; the same one-repair allowance remains. The final gate uses at most two preceding retained sentences for exact qualitative/pronoun attachment and a narrowly guarded nearby issuer-NIP / literal registered-name-suffix association for employee counts/dates. Foreign antecedents, customer/Group ambiguity, date borrowing and conflicting employee observations do not authorize support. Financial context, exact excerpts, source IDs, provider/model and budgets remain unchanged; no retrieval expansion was justified.

Frozen-set before → after: researched precision **2/2 → 5/5**, recall **2/19 → 5/19**, over-downgrade **17/19 → 14/19**, false supports **0 → 0**. Overall precision is **47/47**, registry **42/42**; identity **10/10**, uncertainty **28/28**, strict unknown **40/41** unchanged. Three controlled claims recovered; **retained Asseco/LPP/ORLEN yield remains 0/7**. Extraction dominates remaining eligible misses; retrieval leads the broader real-field losses. No complete real profile was manufactured.

An optional fresh LPP sanity run failed at the unchanged single output-repair ceiling, with no valid progress retained. Six full pages were retained, but new researched output remained unknown. This is an explicit limit, not a successful live before/after benchmark. No extra retry, token optimization or continued tuning followed.

**231 tests**, Ruff lint/format and mypy passed; actual offline CLI, canonical JSON and Markdown were exercised with zero network/research calls. All original gold/baseline/replay files remain byte-identical. No OG-155, CI/security, AgentCanvas, new provider, parser, crawler or architecture work was started.

