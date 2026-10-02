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
- registered city / location,
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

The foundation is frozen; the application is **not implemented**. No ingest, checksum/registry resolver, research agent, evidence gate, Markdown renderer, batch runner or CI has been added. Do not proceed to OG-151 without explicit instruction.

- [Architecture decisions](docs/ARCHITECTURE_DECISIONS.md): minimum pipeline, dependency responsibilities, trust boundaries and rejected technologies.
- [One-page product contract](docs/PRODUCT_CONTRACT.md): exact input, output, evidence states, limits and refusals.
- [Canonical model/evidence contract](docs/EVIDENCE_MODEL.md): the ten required Pydantic models and publication invariants.
- [Financial decision](docs/FINANCIAL_DATA_DECISION.md): two-company live spike; official issuer HTML/text with linked CSV where available, then UNKNOWN. No PDF/XML/archive financial parser.
- [`examples/profiles/`](examples/profiles/): complete, partial and conflicting-source **synthetic** JSON fixtures, not real retrieved company reports.

Only Pydantic is currently a runtime dependency. Research libraries remain documented decisions for their assigned implementation stages. Python 3.12 is selected in `.python-version`; `uv.lock` fixes package versions.

### Offline schema checks

```sh
uv sync --frozen
uv run --frozen pytest -q
uv run --frozen ruff check src tests
uv run --frozen ruff format --check src tests
uv run --frozen mypy src
```

Verification recorded on 2026-10-02: **43 invariant tests passed**, Ruff lint/format checks passed, and mypy passed for the two source files. A throwaway consumer loaded all three examples, serialized/revalidated them, displayed every profile section with states/citations without an LLM, and retained nulls, employee ranges, decimal values, units and financial scope. A separate smoke exercised the inclusive 12-month news boundary. The live LPP financial candidate retained `2.4` billion PLN, group scope and its non-calendar fiscal interval, explicitly marked uncertain/not gate-verified.

The financial spike exercised public KRS JSON, issuer HTML/CSV/text and RDF document discovery for Asseco Poland and LPP. It closed after 10.2 minutes within its 120-minute ceiling; source URLs, observed values and limitations are documented in the decision. No extraction-quality or universal coverage claim is made.

### Definition-of-Done assessment

| Issue | Result | Evidence |
| --- | --- | --- |
| OG-148 | Satisfied locally | Every direct dependency has one concrete responsibility and a use/defer/reject rationale independent of Vstorm's choices. |
| OG-149 | Satisfied locally | A single product-contract page states what v0.1 accepts, produces and refuses. |
| OG-150 | Satisfied locally | All ten required models, state/quantity/provenance invariants and three examples exist; the smoke consumed the schema without a second LLM pass. |
| OG-160 | Satisfied locally | Real-source investigation and a frozen primary route, UNKNOWN fallback, mandatory context and unsupported-format boundary permit later implementation without another financial research phase. |

These results complete the four **foundation** issues, not the functional MVP or portfolio gate. Actual retrieval/excerpt/semantic verification and deterministic NIP resolution remain later work; schema acceptance alone is not proof of either. Linear status was not changed through the read-only connection.
