# v0.2 dossier contract — OG-205–OG-210

Authoritative presentation contract for the assigned autonomous revision-2 package. The [strict publication contract](STRICT_PUBLICATION_CONTRACT.md) remains unchanged. Package 0.2.0, profile schema 0.1, template 0.2.0. No research-quality improvement is claimed.

## Boundary and interfaces

One new production module, `company_bi.dossier`, contains typed immutable presentation records and ordinary functions:

- `build_dossier_view(profile: CompanyProfile, *, synthetic: bool = False) -> DossierView`
- `render_dossier_pdf(view: DossierView, output_path: Path) -> None`
- `write_dossier(input_path: Path, output_dir: Path, *, synthetic: bool = False) -> DossierResult`

The CLI reads retained research bytes once, hashes and validates the same buffer, calls existing `verify_run` once, then projects only its returned final profile. No direct-profile CLI, candidate snapshots, network, model, browser, remote assets or second writer model. The PDF view contains only final identity, supported facts/citations, states/reasons, metadata, questions and synthetic classification. Companion verification files may contain explicitly identified original proposals. Hashes do not authenticate edited runs or publisher truth.

Protected surface: all baseline source modules except isolated CLI integration, every existing test, fixture and document under `docs/`. Their inventory is `examples/dossier/baseline-sha256.json`. Current JSON/Markdown, research, batch, identity, grammar and verification behavior remain unchanged. Historical Holdout B is not rerun as fresh certification.

## Command and persistence

`company-bi dossier RETAINED_RUN --output-dir FRESH_DIR [--synthetic]`

Published complete/partial: exit 0 and exactly `<canonical-nip>.dossier.pdf`, `profile.json`, `profile.md`, `verification.json`, `verification.md`, `dossier-manifest.json`. Reuse existing JSON/Markdown functions, not a new serialization convention. The verified canonical NIP, never display text, names the PDF.

Valid failed/not-published run: exit 1, only verification JSON/Markdown and completion manifest; no company profile/PDF. Invalid JSON/schema/identity/provenance, conflict or render/write failure: exit 2, bounded `DOSSIER_ERROR` on stderr, no completed bundle. Partial is successful, not equivalent to complete research. Unresolved upstream input is not fabricated into a run.

Read/validate and render in a private sibling staging directory. Validate profile/report round trips, PDF signature and artifact hashes before publication. Refuse existing destinations including dangling symlinks and aliases. Reserve a fresh destination by exclusive mkdir; create artifacts exclusively, validate hashes, write completion manifest last. Never overwrite by rename. Clean only operation-owned paths on failure; retain staging if cleanup cannot safely finish, reporting the incomplete location. Input and unrelated files remain untouched. This is **not directory-atomic**: readers accept only a complete manifest with matching artifact hashes. Parent paths must be real directories, not symlink traversals; reject `..` traversal. Do not change permissions of existing directories.

Safe publication requires POSIX directory descriptors and no-follow opens, tested locally on macOS; hosted Linux CI is a release gate. Native Windows fails with a bounded error instead of weakening the collision guarantee. Symlink input/parent paths and multiply linked input files are refused. In particular, macOS callers should use `/private/tmp` rather than symlink `/tmp`.

Manifest core keys: `manifest_version`, `bundle_status`, `publication_status`, `package_version`, `profile_schema_version`, `template_version`, `nip`, `profile_status`, `research_generated_at`, `synthetic`, `input_name`, `input_sha256`, `artifacts`. Versions 0.2.0 except schema 0.1; complete bundle; published/not_published; null profile status/schema for diagnostic-only output. `artifacts` maps every non-manifest filename to SHA-256 (including final profile). Stable JSON order, original timestamps, no self-hash or wall clock. `synthetic=false` is a caller label, not proof of authenticity.

## Content and ordering

1. Registry identity: full legal name/NIP, resolved timestamp, supported address/city/KRS/REGON/website only.
2. Business description, products/services, industries, markets.
3. Employees, exact original count and observation date (or explicitly unspecified).
4. Financials sorted by start/end/metric. Preserve exact Decimal/sign/zeros, currency, scale, full reporting interval, entity scope and group name when supported. No rounding, conversion, merging or charts.
5. Approved recent developments in canonical order (up to three); distinct publication/occurrence dates, unspecified occurrence stays unspecified.
6. Gaps, limitations and deterministic questions.
7. Appendix: every final source sorted by original source ID with stable numbers, every approved fact/citation/field name, full state/reason details and overflow.

Count supported research **fields/observations**, not list items or registry fields. Zero: “Nie ustalono faktów z researchu spełniających kontrakt publikacji”. Registry support never implies researched BI coverage.

States: supported = “Poparte przytoczonym źródłem”; uncertain = “Niepotwierdzone” plus final reason; unknown = “Nie ustalono” plus final reason; partial = “Dane częściowe”. Rejected proposals have no values in the PDF; final non-supported state/reason explains abstention. Empty events = “Nie ustalono zdarzeń spełniających kryteria”, not no events in reality. Financial metadata retained by the model is not displayed as a supported observation when its fact is non-supported. No candidate excerpt is promoted: appendix excerpts are only for supported facts; non-supported sources retain metadata and explicit usage labels.

Every final source preserves ID/kind/title/URL, retrieval/publication timestamps, redirects and publication-blocked reason. Label sources used for supported facts, non-supported references, uncited material and quarantine. Presence in the ledger is not verification.

Polish UI labels; original supported values, excerpts, reasons and timestamps are not translated/paraphrased. Synthetic flag prominently prints “DANE SYNTETYCZNE - demonstracja układu”. Original capture dates remain unchanged.

### Fixed questions

First three applicable, headed “Pytania do potwierdzenia”:

1. Missing business or products: “Jakie produkty i usługi firma obecnie oferuje?”
2. Missing supported employees: “Jaka jest aktualna liczba pracowników?”
3. No paired supported revenue/net result for the same interval: “Czy dostępne są jednostkowe wyniki finansowe za ostatni zamknięty okres?”
4. Missing supported markets: “Na jakich rynkach firma obecnie działa?”
5. Missing supported events: “Jakie istotne zmiany zaszły w firmie w ostatnich 12 miesiącach?”

These are prompts, not company-specific claims about growth, need or opportunity. Range employees/group finance are abstention cases under the unchanged strict gate, not fabricated positive demos.

## Layout and labelled mockups

ReportLab/Platypus invariant mode; A4 portrait, 16 mm margins, 10.5 pt body/14 pt leading, slate/blue hierarchy. Packaged DejaVu Sans 2.37 regular/bold and original license via package resources. No font/asset retrieval at runtime. Escape all profile strings before Paragraph markup; only safe HTTP(S) links clickable; preserve original strings. Long tokens wrap; long previews explicitly point to full appendix. Never shrink body text to force a page count. One sparse or at most two main pages; unlimited clearly labelled appendix. Every supported fact survives in full, even if main preview overflows.

### Sparse mockup — synthetic, zero approved research

```text
DANE SYNTETYCZNE - demonstracja układu
Example sp. z o.o. | NIP 5220003782
Dane częściowe | original research date
TOŻSAMOŚĆ Z REJESTRU: legal name [2]; missing identifiers not inferred

CO USTALONO
Nie ustalono faktów z researchu spełniających kontrakt publikacji
SKALA I FINANSE: Nie ustalono / Niepotwierdzone (by final state)
NAJWAŻNIEJSZE BRAKI: business, employees, financial coverage
PYTANIA DO POTWIERDZENIA: first three missing-section templates
Source-backed does not mean universal truth; full state/reasons in appendix
                                        Dossier • strona 1
--- ŹRÓDŁA I SZCZEGÓŁY / ANEKS ---
Full identity, states/reasons, source metadata and usage labels
No unsafe/OOC proposed service presented as an approved fact
```

### Rich mockup — synthetic, complete strict recipe

```text
DANE SYNTETYCZNE - demonstracja układu
Przykładowa Firma Żółć sp. z o.o. | NIP 5220003782
Kompletne pokrycie profilu | 2026-10-05T12:00:00Z
TOŻSAMOŚĆ Z REJESTRU: ul. Przykładowa 1, 00-001 Warszawa [registry]
CO USTALONO: dostawca rozwiązań pomiarowych; systemy pomiarowe
Branża: aparatura pomiarowa | Rynek: Polska [individual sources]
SKALA I FINANSE: 25 employees, 2026-09-30
Przychody: 12.5000 PLN millions; 2025-01-01–2025-12-31; legal_entity
Wynik netto: -0.7500 PLN millions; same interval; legal_entity
--- second main page only if needed ---
WYDARZENIA: centrum badawcze [source]
Publication 2026-09-20; occurrence 2026-09-18
Optional identifiers remain unknown; no question pretending they are facts
--- appendix ---
Full facts/field names/excerpts; all nine registry/research sources
```

Mockups checked against M5: identity/date, registry/research separation, visible gaps, faithful amounts, explicit sources and synthetic labels. They are layout specifications, not observed renders; actual page counts/visual findings belong in the release checks.

## Acceptance matrix and release authority

Required: existing supported/OOC/unsafe/invalid fixtures; valid failed run; rich recipe; zero/negative finance; non-supported context and optional-date clearing; range/group abstention; long names/Polish text/40 services/URLs/reasons; escaped markup and safe links; deterministic repeat; alias/symlink/hardlink/pre-existing/racing destination; render/copy failure; network/model-blocked CLI.

Run inherited pytest/Ruff/format/mypy/offline smoke plus dossier subprocess smoke, inspect **every** final page rasterized by Poppler, and install the wheel outside the source tree with packaged fonts/license. No runtime Poppler. Same locked environment must yield byte-identical PDFs; no cross-platform/version byte guarantee.

Complete the six assigned commits, then push one PR, require exact-head CI, normal permitted merge, post-merge main CI, annotated v0.2.0 and GitHub Release. Never bypass protection or move existing tags. Keep the continuation/evidence in [V0_2_RELEASE_CHECKS.md](V0_2_RELEASE_CHECKS.md). No OG-201 closure or employer/client outreach. Real demo is best effort from current-valid retained data, at most two already-configured live attempts; missing/zero-yield real data does not invalidate this presentation release.
