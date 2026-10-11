# Dossier examples — v0.2.0

Presentation demonstrations, not production research accuracy. The exact final profiles, verification reports, artifact hashes and PDFs are under [`generated/`](generated/). [Machine-readable review summary](generated/review-summary.json); [contract](../../docs/V0_2_DOSSIER_CONTRACT.md); [release checks](../../docs/V0_2_RELEASE_CHECKS.md).

| Example | Classification | Final outcome | PDF |
| --- | --- | --- | --- |
| supported | synthetic | partial; one approved service; unknown sections stay unknown | [3 pages](generated/supported/5220003782.dossier.pdf) |
| out_of_contract | synthetic | partial; zero supported research fields; rejected value not printed as a fact | [3 pages](generated/out_of_contract/5220003782.dossier.pdf) |
| unsafe | synthetic | partial; zero supported research fields | [3 pages](generated/unsafe/5220003782.dossier.pdf) |
| rich | synthetic | complete; eight supported research fields/observations | [5 pages](generated/rich/5220003782.dossier.pdf) |
| zero-finance | synthetic | complete; supported `0.0000` revenue, `-0.7500` net result | [5 pages](generated/zero-finance/5220003782.dossier.pdf) |
| stress | synthetic | complete; long identity, 40 service labels, literal markup, long URL/title/reason | [24 pages](generated/stress/5220003782.dossier.pdf) |
| real-asseco | original public retained run | partial; **zero** supported researched fields; registry facts separate | [4 pages](generated/real-asseco/5220003782.dossier.pdf) |
| failed-run | synthetic valid failed run | diagnostics only, exit 1 | none |
| identity_invalid | synthetic invalid identity | refused, exit 2; no output directory | none |

All synthetic PDFs prominently say **DANE SYNTETYCZNE - demonstracja układu**. The synthetic inputs reuse a checksum-valid NIP only for shape; the rich/stress names, source assertions and MF-shaped registry response are fictional. They are not live registry findings about the company that owns that NIP. `--synthetic` is an explicit caller label, not a detector or authentication mechanism.

The real example is the unchanged [`../evals/retained/asseco-poland.json`](../evals/retained/asseco-poland.json), captured **2026-10-03T12:25:47.507942+00:00**. Its zero research support is an honest strict-contract result. It has not been refreshed or repaired into a positive. Ordinary final source metadata and quarantined references are preserved, but are not labelled as supporting research. An original reason may mention a rejected amount while explicitly explaining why it is unknown; that reason is not a published financial observation.

The `out_of_contract` and `unsafe` PDFs are intentionally byte-identical: the final publishable presentation is the same. Their companion verification reports retain the different original proposals and boundary reasons for forensic review. Do not use companion proposed values as final facts.

## Reproduce without keys or network

From the repository root, with Python 3.12 and `uv`:

```sh
uv sync --frozen --python 3.12
uv run --frozen python scripts/review_dossier.py --output-dir outputs/dossier-review
```

Use a fresh destination, not `generated/` (the command deliberately refuses existing paths). The subprocesses block network and model/provider entrypoints. The script verifies every expected exit, companion profile against the existing gate, full approved PDF values/citations/source metadata/reasons and completion-manifest hashes. It writes one deterministic summary; visual inspection is separately recorded, not inferred from text extraction.

To construct the new synthetic retained runs again using public models and real verification:

```sh
uv run --frozen python scripts/dossier_fixtures.py
```

This rewrites only the four new inputs in this directory, not the frozen strict fixtures or historical holdouts. Range employees and group financial candidates are abstention tests, not positive demos. `baseline-sha256.json` is the protected v0.1.1-era inventory, not a claim that current dossier outputs existed in that release.
