# v0.2 release checks and continuation

## Active continuation

```json
{
  "phase": "OG-208",
  "state": "acceptance_passed_pending_commit",
  "work_branch": "feat/nipto-bi-v0.2-dossier",
  "baseline_sha": "e3da375218206354f79dac539e252f7821c1c399",
  "latest_committed_sha": "52b5c40",
  "completed_issues": ["OG-205", "OG-206", "OG-207"],
  "next_action": "Commit OG-208 CLI/bundle, then run independent semantic, visual and wheel QA",
  "tests_and_visuals": ["27 CLI/file-safety tests passed; 17 projection/PDF tests passed previously; actual CLI exits 0/1/2 observed; mypy 20 modules passed"],
  "blockers": [],
  "pending_linear_sync": ["OG-205 Done bd21fdd; OG-206 Done df7c876; OG-207 Done 52b5c40; OG-208 Done after commit; connector remains read-only"],
  "pending_github_actions": ["feature push, PR, exact-head CI, merge, main CI, annotated tag, release"],
  "repair_attempts_for_current_root_cause": 0
}
```

## OG-205 baseline and acceptance

- Read the complete revision-2 execution plan and all six full Linear descriptions. Issues are Todo in M5; existing historical tracker discrepancies are not reimplementation instructions. The mounted Linear connector has no mutation tools; preserve pending synchronization rather than inventing updates.
- Initial checkout: clean `fix/v0.1.1-adversarial-corrections`, HEAD `02555dd`. PR #1 is merged at `83a9e42940190d88ed065c5804be331d3b40d48e`; annotated `v0.1.1` points there. Fetched current main `e3da375218206354f79dac539e252f7821c1c399`; no newer dossier work. Created assigned feature branch from main. Other worktrees, including operator main, remain untouched.
- Repository root confirmed; origin `https://github.com/TomaszGonczar/company-bi-research-agent.git`. Authenticated GitHub viewer permission ADMIN; no credential changes or permission bypass. `uv 0.12.3`, CPython 3.12.13. Initial package 0.1.1/schema 0.1. Poppler `pdftoppm 26.10.0` available. Fontconfig returns Verdana for DejaVu, so use the specified upstream archive, not an unlicensed substitute.
- Protected inventory: 122 existing tracked code/test/fixture/docs files and SHA-256 values in `examples/dossier/baseline-sha256.json`. All source except CLI protected; all old tests, examples and docs protected. Allowed edits: CLI isolation, package/lock, CI additive smoke, README/reviewer guide, new dossier files/resources/tests/examples/docs. No Holdout B first-execution runner invoked.
- Actual baseline commands: `uv sync --frozen --python 3.12`; `uv run --frozen pytest -q` (**740 passed**, 30 pre-existing lxml warnings); `ruff check .` PASS; `ruff format --check src tests scripts` PASS (56 files); `mypy src` PASS (19 source files); `python scripts/review_offline.py --output-dir .work/v0.2/baseline-review` PASS (zero external calls). Full command output available in the execution transcript.
- Frozen [contract and two labelled mockups](V0_2_DOSSIER_CONTRACT.md) cover final-only projection, exact interfaces/files/exits, source retention, manifest-last semantics, fixed layout/questions and release gates. Mockups validated against M5; actual rendered visual proof remains pending OG-207/209.

## OG-206 projection acceptance

- Added final-profile-only immutable view, stable source numbering, exact financial formatting, registry/research count separation, state/reason-only gaps and at most three fixed questions. No candidates or retained page bodies reach the view.
- New validated recipe builder generated rich, zero-finance, stress and failed-run inputs. Actual `verify_run`: rich/zero/stress **complete**, eight supported research fields each; failed **not_published**. Stress has 40 separately evidenced services but counts as one products/services field.
- **11 targeted tests passed**; Ruff and mypy passed; actual rich projection smoke printed 25 employees (2026-09-30), `-0.7500` and `12.5000` PLN millions with exact interval/scope. Optional wrong employee/event dates clear; uncertain/wrong-amount/group/range candidates do not become observations.
- Integration finding: the existing gate omits ordinary uncited run sources from the **final** profile; registry/quarantined sources survive. The adapter preserves every final source, not additional raw-run material. The new uncited-source test uses a quarantined source that the real gate retains. No semantic-core change.

## OG-207 PDF acceptance

- ReportLab **4.5.1** runtime; pypdf **6.20.0** development-only inspection; Pillow 12.3.0 is ReportLab's new transitive dependency. No unrelated dependency upgrade. Narrow untyped ReportLab imports; mypy remains strict.
- DejaVu Sans **2.37**, regular/bold and full upstream LICENSE packaged unmodified. Archive: `https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip`; SHA-256 `7576310b219e04159d35ff61dd4a4ec4cdba4f35c00e002a136f00e96a908b0a`. Original redistribution/license notices retained.
- A4, 16 mm margins, body 10.5/14 pt; invariant PDF metadata; safe escaped text and HTTP(S) links. Full supported values/citations, all final sources and gaps flow through appendix; main previews are explicitly abbreviated.
- **17 targeted tests passed**, Ruff/mypy passed. Actual sparse/rich/stress rendering in `.work/v0.2/pdf-smoke-02`: **3/5/24 total pages**, **1/1/2 main pages**. Every same-environment repeat had identical bytes. Full values, citations, source metadata, Polish/markup text and embedded regular/bold fonts checked through pypdf.
- First inspection found an orphan main heading and a misleading “3 shown” label when the preview shortened an item. Repaired heading lookahead and honest list preview wording; event dates now stay visible beside a shortened title. Grouped source metadata avoids a one-line trailing source page. A text-test failure was page-footer interleaving across a split citation, not lost evidence; extraction now geometrically excludes footer furniture. Removed a brittle wrapped-wording assertion.
- Inspected repaired stress main pages 1–2, full legal identity page 3 and long-URL final page 24, rich evidence page 2 and sparse source/gap page 3. Correct glyphs/wrapping; no clipping or overlap observed there. Full final-example all-page inspection remains OG-209's gate.

## OG-208 CLI and bundle acceptance

- Added isolated lazy dossier dispatch; existing commands unchanged. Input buffer is read once, hashed and validated, followed by one existing `verify_run`. Successful six-file bundle and failed diagnostic-only three-file bundle use existing profile/verification serializers.
- Actual CLI smoke: `.work/v0.2/cli-supported-01` exit **0**, partial, six files; `.work/v0.2/cli-failed-01` exit **1**, diagnostics only; invalid identity exit **2**, bounded message and no output; repaired rich path `.work/v0.2/cli-rich-02` exit **0**, complete.
- **27 CLI/file-safety tests passed**, mypy PASS for 20 source modules. Existing autouse guards block sockets/DNS/registry/model/Tavily/Scrapling during these real in-process CLI calls.
- POSIX safe publication uses no-follow directory descriptors, exclusive directory/artifact creation, owned inode checks, and completion manifest last. Existing destinations, dangling symlinks, input/output hardlinks/aliases, symlink parents, traversal, reservation races, render/copy/manifest failures and hash tampering are refused without overwriting old data. Fresh repeat bundles are byte-identical in this environment.
- Reproduced three additional failures before repair: mutation after manifest creation returned success; replacing the parent returned success; cleanup failure left a completed manifest while reporting failure. Fixed final parent/artifact rechecks and moved successful staging cleanup inside the publication transaction. All three regressions now pass. Replaced-directory cleanup preserves the external replacement and retains staging with a bounded diagnostic. No directory-atomicity or crash-atomicity claim.
- Safe writer currently requires POSIX directory-descriptor/no-follow primitives (tested macOS; hosted Linux pending). Native Windows refuses safely rather than claiming equivalent collision guarantees.

## Release limitations

This is a presentation/usability change, not expanded publication language, better real researched yield or production accuracy. Registry facts do not count as researched BI. Synthetic classification is a caller-provided label; input hashes are not source authentication. No employer/client material sent; OG-201 untouched.
