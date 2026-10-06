# v0.1.1 independent Holdout B result

**PASS — sampled evidence for the frozen finite publication contract; not a release authorization.** The independent Holdout B was run against certified semantic commit `9f80eb7a7dcdb4c563a4bec897f22361cdbbae45`. This reports the supplied evidence; it does not claim general accuracy, publisher truth, exhaustive coverage, or real-world usefulness.

## Frozen inputs and runtime

- Runtime: Python **3.12.13**, Pydantic **2.13.5**.
- Corpus SHA-256: `ff490c5746249c6428361ab1d36dd44b50d69c83e0c766e6cc380eef58db9153`.
- Oracle SHA-256: `032f34d1f65d26b02ffecc25e4620f28cc10074dff16eeec6ea54f7bd840ece4`.
- Results archive: `company-bi-v011-holdout-b-results-9f80eb7.zip`, SHA-256 `1bb899f101bd76bc6a8de669a56b8dd2a54ce5af050044a824d0737931e2add1`.

## First-execution outcomes

One pass, **80 calls**, **70 semantic** and **10 boundary** probes; **zero reruns**. Populations are separate:

| Population | Result |
| --- | --- |
| Supported positives | 20/20 supported with components |
| True out of contract | 20/20 abstained |
| Unsafe | 30/30 received no support |
| Provenance-invalid | 5/5 model-rejected |
| Identity-invalid | 5/5 model-rejected |

All safety counters were zero; `failure_ids[]` was empty. These are finite, sampled contract probes, not an aggregate accuracy estimate or a claim about arbitrary publishers or text.

## Independent artifact audit and provenance

The parent’s independent evidence checker used only the Python standard library; it did **not** import or execute the production verifier or scorer and did not rerun Holdout B. Its verified record reports audit of **665** results-manifest payloads, **34** FREEZE entries, **80** exact run byte spans, **80** first-observation records, and **2** clean-worktree logs. The resulting record is `/Users/tomaszgonczar/Projects/company-bi-audits/v011-release-20261006T214033Z/evidence/verified-holdout.json`; the preserved results ZIP is `/Users/tomaszgonczar/Projects/company-bi-v011-holdout-b-results-9f80eb7.zip`. This independent artifact check establishes consistency of the supplied evidence artifacts, not semantic truth or an additional model execution.

## Limitations and release state

This evidence is for the frozen finite publication contract only. It does not demonstrate broad coverage, population-level precision, publisher truth, or real-world utility. Asseco and SONEL remain at **0 researched facts published**; the strict abstention is poor real-world yield, not useful BI output and not evidence those companies lack the activities. Historical measurements remain historical and unchanged. The original 70-case holdout remains a separately recorded failed fixture construction; prior external replay reports with missing corpora/runners have **not** been replayed by this result.

Current release preparation is post-holdout, metadata-only v0.1.1 hygiene: version metadata and CI formatting scope are aligned without semantic, parser, renderer, or authoring changes. Local release-preparation gates passed; hosted CI is pending authorization. This is not a hosted CI pass, and the commit is **not tagged, merged, pushed, or released**.

## Separate local release-preparation checks

Using the frozen lock on Python 3.12.13, with an allowlisted environment and OS network denial: **740 tests passed** (30 existing lxml deprecation warnings), Ruff passed, **56 files** passed formatting, and mypy passed for **19 source files**. The canonical CLI population passed **262/262**, including **97/97** contract positives; boundary/micro/IPv6/toolkit/component smoke results were **26/26**, **19/19**, **11/11**, **10/10**, and **5/5**. Offline reviewer execution made no external or paid/live provider calls and exercised one controlled local FunctionModel interruption. The separate historical replay recorded **160 correct and 14 unassessed** assertions, not 174 semantic successes. None of these checks reran Holdout B.

Local logs are preserved under `/Users/tomaszgonczar/Projects/company-bi-audits/v011-release-20261006T214033Z/checks/`. Check the final release-preparation commit SHA, its diff from the certified semantic commit, and exact-commit clean-clone logs in the external `company-bi-v011-release-candidate-review.zip`. Only release metadata, documentation and CI configuration may differ; production code, scripts, tests, fixtures, dependency versions and the normative publication contract must remain unchanged.
