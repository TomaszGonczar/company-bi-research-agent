# Company BI — Engineering Instructions

## Mission

Build a deliberately small portfolio MVP:

**CSV/XLSX containing Polish NIPs → evidence-backed company BI profiles in JSON and Markdown.**

The project exists to demonstrate product-oriented AI engineering, not framework engineering.

## Primary rule

Work only on the currently assigned Linear issue.

Do not start future issues, speculative infrastructure, or abstractions for hypothetical requirements.

Complete the current issue, verify its Definition of Done, commit the result, then stop.

## Architecture principle

Use probabilistic AI where judgment is useful.

Use deterministic code where correctness can be checked.

The model may:
- decide what to search,
- select useful sources,
- interpret unstructured company information,
- extract candidate facts,
- summarize business activity and meaningful news.

Deterministic code must decide:
- whether the NIP and legal identity are valid,
- whether a cited source was actually retrieved,
- whether evidence exists in the retrieved content,
- whether financial facts contain metric, period, currency, and entity scope,
- whether a fact may be published as `supported`,
- how final JSON and Markdown reports are rendered.

## Evidence states

Every publishable fact must be one of:

- `supported`
- `uncertain`
- `unknown`

Do not invent numerical confidence scores.

`unknown` is a valid result.

Missing data must never silently become `0`, `false`, or a guessed value.

## Explicit v0.1 non-goals

Do not add any of the following unless the current Linear issue explicitly requires it:

- multi-agent orchestration
- subagents
- DeepAgents
- vector databases
- RAG
- PostgreSQL
- Redis
- Celery
- web frontend
- authentication
- MCP server
- plugin system
- generic provider abstraction
- custom agent framework
- scheduler
- CRM functionality
- lead scoring
- people/contact enrichment
- outreach generation
- universal financial-document parsing
- global or name-only entity resolution

Prefer deleting complexity over generalizing it.

## Preferred stack

Use only where justified:

- Python
- uv
- Pydantic v2
- PydanticAI
- Tavily
- Scrapling
- PydanticAI UsageLimits
- pytest
- Ruff
- type checking
- GitHub Actions

Optional only after the functional MVP exists:
- Logfire
- AgentCanvas
- Pydantic Evals if not already introduced during evaluation work

## Development discipline

Do not create an abstraction until at least two real implementations require it.

Do not create interfaces for hypothetical future providers.

Do not introduce persistence infrastructure when filesystem state is sufficient.

Do not build a frontend to demonstrate functionality that can be demonstrated through sample inputs and generated files.

Do not optimize for scale before the sample batch works correctly.

## Required development order

Follow Linear project:

**Vstorm Re-entry — Company BI Research Agent**

Current sequence:

1. OG-148 — stack decisions
2. OG-149 — v0.1 product contract
3. OG-150 — Pydantic schemas and evidence model
4. OG-160 — financial-data spike
5. OG-151 — NIP ingest and deterministic identity
6. OG-152 — one-company PydanticAI research vertical slice
7. OG-153 — evidence gate, renderer, batch
8. OG-154 — evals
9. OG-155 — CI, reliability, web safety
10. OG-156 — clean-clone and Scrapling experiment
11. OG-157 — reviewer package

OG-158 is post-v0.1 and must not block shipping.

## MVP gate

The product exists when this works:

```text
input.xlsx
    ↓
valid Polish NIPs
    ↓
resolved company identities
    ↓
bounded research
    ↓
validated facts
    ↓
outputs/
    ├── <nip>.json
    ├── <nip>.md
    └── batch_summary.csv
```

Until this works, do not expand scope.

## Communication

When starting an issue:

1. Read its complete Linear description.
2. Inspect only the repository areas relevant to that issue.
3. State the smallest implementation plan.
4. Identify any assumption that could materially change the design.
5. Implement.
6. Run relevant tests.
7. Compare the result against the issue Definition of Done.
8. Report what changed, tests run, remaining limitations, and whether the issue is actually complete.

Do not mark work complete merely because code was written.