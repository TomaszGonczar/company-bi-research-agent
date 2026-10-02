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

The foundation checkpoint is `6cfcfe4`. OG-151 now implements deterministic CSV/XLSX ingest and MF-registry identity resolution only. The research agent, generic evidence extractor/gate, financial extraction, Markdown/BI rendering, full BI batch runner and CI remain unimplemented. Do not proceed to OG-152 without explicit instruction.

- [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md): minimum pipeline, dependency responsibilities, trust boundaries and rejected technologies.
- [One-page product contract](docs/PRODUCT_CONTRACT.md): exact input, output, evidence states, limits and refusals.
- [Canonical model/evidence contract](docs/EVIDENCE_MODEL.md): the ten required Pydantic models and publication invariants.
- [Financial decision](docs/FINANCIAL_DATA_DECISION.md): two-company live spike; official issuer HTML/text with linked CSV where available, then UNKNOWN. No PDF/XML/archive financial parser.
- [`examples/profiles/`](examples/profiles/): complete, partial and conflicting-source **synthetic** JSON fixtures, not real retrieved company reports.

Current runtime dependencies are Pydantic and openpyxl. CSV, checksum calculation, HTTP and the CLI use the standard library; development typing stubs cover openpyxl. Research libraries remain documented decisions for their assigned implementation stages. Python 3.12 is selected in `.python-version`; `uv.lock` fixes package versions.

### Offline checks

```sh
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen ruff check src tests
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

These results completed the four **foundation** issues, not the functional MVP or portfolio gate. Current OG-151 behavior is below; research evidence/excerpt/semantic verification and BI reports remain later work. Linear status was not changed through the read-only connection.

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

Limitations: this one register is not universal Polish-entity coverage; the [Ministry's shared search limits](https://www.gov.pl/web/kas/api-wykazu-podatnikow-vat) can cause operational failures. Website discovery is deliberately absent rather than guessed. CSV is comma-separated and XLSX uses the first worksheet; no general importer is promised. Full research, BI profiles/reports, evidence gate and financial extraction are still out of scope.

**Definition of Done satisfied locally:** one command converts a small CSV/XLSX NIP file into persisted deterministic identity records with independent row outcomes. Stop here; OG-152 has not started.
