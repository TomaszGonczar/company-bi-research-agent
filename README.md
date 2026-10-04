# Company BI — operational guide

A deterministic Polish NIP ingestion and identity workflow followed by bounded, evidence-gated company research. The publication gate preserves uncertainty rather than filling gaps. Start with the credential-free offline review; live research is a separate, explicitly networked operation.

## Prerequisites and setup

- `uv`
- Python 3.12

```sh
uv sync --frozen --python 3.12
```

The frozen sync installs locked runtime and development dependencies. Offline checks and examples below need no API keys, dotenv file, Codex login, or live requests.

## Credential-free checks and evaluation

```sh
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy src/company_bi
uv run --frozen company-bi eval --dataset examples/evals/dataset.json --output-dir outputs/evals
```
The frozen evaluation counts are reported in [`docs/EVAL_RESULTS.md`](docs/EVAL_RESULTS.md); the three retained replay outcomes are partial.
Evaluation writes `outputs/evals/results.json` and `outputs/evals/results.md`. It replays deterministic controlled cases and committed retained-real snapshots; no live calls are made. The dataset is small and diagnostic, not a population-level accuracy estimate.

## Offline end-to-end review

```sh
uv run --frozen python scripts/review_offline.py --output-dir outputs/review
```

This command makes no external network or paid/live provider calls. It runs one local controlled `FunctionModel` interruption to show the actual failed-research path; it reads no credentials or prior run state and writes a provenance manifest plus inspectable outputs:

- `outputs/review/review-manifest.json` records input provenance and outcome labels.
- `outputs/review/retained/{asseco-poland,lpp,orlen}.json` and `.md` replay the three committed research snapshots through the real evidence gate (`build_profile`) and JSON/Markdown renderers. These are **retained real partial reports**, not demonstrations of complete real-company yield.
- `outputs/review/controlled/synthetic-complete.json` and `.md` render `examples/profiles/complete.json`. This is a **controlled synthetic COMPLETE** example, not real-company evidence or yield.
- `outputs/review/controlled/provider-interruption-research.json` records diagnostics from the actual research path with a guarded local `FunctionModel` interruption. This is one controlled in-process model invocation, not a live or paid provider call; it contains no fabricated `CompanyProfile` or final report paths.

The console and manifest identify each provenance class. Re-running replaces the same named files; retained profile replay is stable, while the controlled failed-research artifact preserves the actual invocation time and duration. The sample `examples/nips.csv` has header `nip` and rows `5220003782`, `123`, and `1234563218`: the existing NIP validator accepts checksum-valid input and rejects invalid input; it does not infer or repair identifiers.

## Input → evidence → publication

For normal operation, CSV/XLSX input passes through deterministic ingestion and checksum validation, then identity resolution. Research candidates must cite retained sources. The evidence gate checks the validated research run and creates a `CompanyProfile` only when its publication rules allow; the unchanged renderers then produce final JSON and Markdown. The single-company `research` command writes research JSON; the `batch` command applies the gate and writes final JSON/Markdown reports as well as research artifacts. Failed research has diagnostics/research data, not a made-up report. Offline examples exercise this path using committed data rather than reaching the MF registry or research providers.

Committed evidence and fixtures:

- `examples/nips.csv` — sample NIP input.
- `examples/profiles/` — controlled final-profile examples; `complete.json` is synthetic.
- `examples/evals/dataset.json` and `examples/evals/controlled/` — active evaluation index and controlled inputs.
- `examples/evals/retained/` — three retained public Asseco Poland, LPP, and ORLEN research snapshots; the offline review republishes their current gate outcomes.
- `docs/EVAL_RESULTS.md` — detailed frozen evaluation findings and limitations.

Expected frozen OG-154A diagnostic metrics: overall supported precision **47/47**, researched supported precision **5/5**, researched eligible recall **5/19**, unsupported-as-supported **0**, and retained real yield **0 complete / 3 partial / 0 failed** (retained eligible researched gold supported: **0/7**). The `5/5` researched precision denominator is very small; it does not imply reliable coverage. Low real yield must remain visible, not be optimized away by weakening evidence rules.

OG-156 evidence: [clean-clone audit and final live smoke](docs/CLEAN_CLONE_AUDIT.md), [paired Scrapling experiment](docs/SCRAPLING_EXPERIMENT.md).

## LIVE RESEARCH — explicit network use

Live research is distinct from the offline review and may contact the Polish Ministry of Finance VAT registry and external search/retrieval services. For the default native Codex model, use standard Codex CLI sign-in (`codex login`) and its normal authentication management; an OpenAI API key is **not required** for native Codex authentication. The research and batch CLI paths do require `TAVILY_API_KEY` for search. Alternatively, when explicitly selecting an OpenAI API model, provide `OPENAI_API_KEY` through your usual secret-management method. Never commit credentials.

A single-company research call is explicitly live and writes a research artifact, not a final profile report:

```sh
uv run --frozen company-bi research 5220003782 --model openai-codex:gpt-6-luna --output outputs/research/5220003782.json
```

For an input batch, use the live batch path (final profiles are written under the output directory and research artifacts under the runs directory):

```sh
uv run --frozen company-bi batch examples/research_batch.csv --output-dir outputs --runs-dir runs --model openai-codex:gpt-6-luna
```

Check the CLI before using retry/force options; retries can incur additional provider and retrieval activity. Offline review is not a live-service smoke test. Residual limitations include DNS-rebinding risk in outbound URL retrieval, unsupported PDF/XML/archive content, and weak real researched yield in the retained corpus. During the OG-156 audit no remote was configured, so hosted CI was **NOT VERIFIED**.
