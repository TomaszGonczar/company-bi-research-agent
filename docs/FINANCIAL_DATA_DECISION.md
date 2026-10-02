# Financial data decision — Company BI v0.1

[OG-160](https://linear.app/tpg96/issue/OG-160) · **Decision frozen: official issuer HTML/text (linked CSV when present) is the primary route; UNKNOWN is the fallback.** No universal financial-document parser or financial-data provider integration is required to proceed.

## Time-box and scope

Hard ceiling: **120 minutes**. Live investigation: **2026-10-02 19:07:16–19:17:28 UTC (10.2 minutes)**. Closed early once structured registry access, readable issuer sources and public document discovery had been exercised for two real companies. This was a focused route spike, not a claim of broad market coverage or a two-hour completed implementation.

Test companies, confirmed through public KRS JSON rather than an LLM name match:

| Legal entity | NIP | KRS | Evidence |
| --- | --- | --- | --- |
| ASSECO POLAND SPÓŁKA AKCYJNA | `5220003782` | `0000033391` | [KRS record](https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000033391?format=json&rejestr=P), [issuer contact / NIP](https://pl.asseco.com/en/contact) |
| LPP SPÓŁKA AKCYJNA | `5831014898` | `0000000778` | [KRS record](https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/0000000778?format=json&rejestr=P) |

The spike used known KRS numbers to check these two anchors. It did **not** implement the future NIP-to-registry resolver.

## What was actually exercised

### 1. Registry / public structured data

- Read the [official open KRS API documentation](https://prs.ms.gov.pl/krs/openApi), then successfully retrieved and parsed both current-record JSON responses.
- The documented API covers current/full registry records and change bulletins. The tested records contain identity and filed-report metadata, not a ready-made revenue/net-result table. Share capital is not revenue; report filing is not evidence of an amount.
- Asseco's consolidated filing metadata explicitly says `OD 01.01.2025 DO 31.12.2025`, filed `30.06.2026`.
- LPP's consolidated filing metadata explicitly says `OD 01.02.2025 DO 31.01.2026`, filed `01.09.2026`. **A “2025” label must not be silently converted to calendar 2025.**
- Tested the public [RDF browser](https://rdf-przegladarka.ms.gov.pl/wyszukaj-podmiot) with Chromium. The legacy `ekrs.ms.gov.pl/rdf/pd` reader path hit a redirect loop; browser navigation reached the replacement portal. Asseco search returned its legal name and a document table with **96 entries**, including 2025 annual filings.
- A second search changed the entity heading to LPP while the captured document table still showed the preceding calendar-year rows; that mixed snapshot was not used as LPP evidence. API JSON supplied the reliable LPP period. This observation rules out treating an early asynchronous browser snapshot as a trusted company/document association.
- No undocumented RDF API, CAPTCHA bypass, bulk download or registry crawler was introduced. Registry discovery is useful, but RDF document ingestion is not the primary amount route.

### 2. Readily extractable issuer HTML/text and CSV

**Asseco:** [Financial highlights HTML](https://inwestor.asseco.com/en/financial-information/financial-highlights/) identifies the table as **consolidated** and gives `[mPLN]`. Its [linked CSV](https://inwestor.asseco.com/en/financial-information/financial-highlights/csv/) was retrieved and parsed with Python's standard `csv` module and `Decimal`, without a financial parser dependency.

Observed output, in **millions of PLN**, not legal-entity-only sales:

| Reporting year label | Consolidated revenue | Profit row actually named by the source |
| --- | ---: | ---: |
| 2025 | 16,779.8 | 1,138.7 |
| 2024 | 15,020.1 | 519.9 |
| 2023 | 14,743.9 | 482.7 |

The profit label is **“Net profit attributable to Shareholders of Asseco Poland S.A.”** Those values are not automatically the total group `net_result`. v0.1 refuses to substitute attributable profit, operating profit, EBITDA or pre-tax profit for total net result. With only this table, revenue is a candidate; the requested net result is unavailable unless a separate eligible source supplies total net profit. The CSV alone omits scope; retain the companion HTML heading as scope evidence.

**LPP:** retrieved the [issuer's 26 March 2026 results release](https://www.lpp.com/en/press-releases/lpp-has-delivered-on-its-2025-plan-record-profits-at-every-level-and-investments-in-technology-and-logistics-as-the-foundations-for-the-groups-further-growth/). A throwaway text extraction found **“net profit stood at PLN 2.4 bn”** in LPP Group context. Preserve the reported value `2.4`, unit `billions`, currency `PLN` and group scope; do not invent extra precision.

The same page says revenue **“exceeded PLN 23 bn”**. A bound is not an exact monetary value, and its rounded headline does not resolve that distinction. Do not publish an exact revenue of `23` billion as supported. Fiscal-period association must be supported by retrieved reporting context, including the explicit non-calendar interval; publication date is not reporting period.

These outputs prove readable public routes exist. They are **spike observations/candidates**, not final gate-verified company profiles. No financial amount was published into the synthetic profile examples from these live sources.

### 3. Public financial-document discovery

- Located and inspected Asseco's [selected standalone financial data PDF for 2025](https://inwestor.asseco.com/files/investor/uploads/Selected_financial_data_of_Asseco_Poland_2025.pdf) using the assistant's document reader. It contains standalone operating revenue **1,703.4 million PLN** and net profit **432.7 million PLN**, for the year ended 31 December 2025—very different from the consolidated table. This demonstrates the scope risk, **not** an implemented PDF extraction route.
- LPP's [2025 consolidated annual-report page](https://www.lpp.com/en/reports/consolidated-annual-report-of-lpp-sa-group-for-2025/) exposes a downloadable **PDF and ZIP**. The [report index](https://www.lpp.com/en/investor-relations/reports/financial-reports/) also exposes interim PDFs.
- Finding a link is not retrieving its contents and cannot support a financial amount. Easy discovery does not justify universal PDF/XML/XBRL/ESEF parsing. No such code or dependency was added.

## Frozen v0.1 implementation contract

### One primary route

Within the ordinary per-company research limits, search for the resolved company's official/investor-relations results pages. Read selected HTML/text with static extraction first. An explicitly linked CSV may be read as a structured companion using standard-library CSV/decimal handling; this is the same issuer source route, not another provider interface. Retain original headers, unit labels, scope labels, period evidence and source IDs with the candidate.

Prefer directly stated totals for the identified legal entity. Clearly attributed group data may be included **only with explicit group scope and group name**. Never relabel group data as that NIP's standalone accounts. Extract up to three most recent available reporting intervals actually found, without inventing periods or combining interim and annual amounts. The existing search/read/deadline ceilings apply; finance does not receive a separate unbounded budget.

### One fallback: UNKNOWN

If no eligible amount with complete context was retrieved, emit the requested metric with `state: unknown`, `value: null`, empty evidence and an explicit reason such as “Only an unsupported PDF was found” or “No total net result with identifiable reporting context was obtained.” Do not set zero, make up a number, or stop the rest of the company profile/batch.

If candidate evidence exists but conflicts or is ambiguous, retain `uncertain`, no selected amount where unsafe, its candidate references and the reason. This is an evidence-state outcome, not a second acquisition route. The fallback does not erase conflicts.

### Hard fields versus best-effort values

| Hard v0.1 contract | Best-effort / no coverage guarantee |
| --- | --- |
| Both metric slots (`revenue`, `net_result`) are represented, even when unknown. | Obtaining either numerical amount. |
| Every asserted amount has metric, explicit reporting start/end, currency, reported unit, entity/group scope and retrieved evidence. Group amounts name the group. | Finding one, two or three eligible recent intervals; the maximum is three, not a required count. |
| Finite decimal values; preserve published precision and units (`units`, `thousands`, `millions`, `billions`), losses and genuine stated zeroes. No FX conversion. | Standalone legal-entity financials; group results must remain labelled group. |
| Source/period/scope ambiguity never becomes supported. Do not substitute net-profit variants, headline bounds or growth percentages for an amount. | Financial disclosure availability outside publicly listed companies. |

A year-only caption is insufficient to invent fiscal start/end. Use explicit, matching reporting context from retrieved sources; otherwise no asserted amount. A successfully parsed number alone does not satisfy this contract. Schema currency validation checks a three-letter code's shape; source verification must establish the actual currency.

### Unsupported amount formats

**No PDF parsing, OCR/scanned tables, image charts, arbitrary XML/XBRL/ESEF, ZIP financial bundles, macro-enabled spreadsheets, or universal spreadsheet financial ingestion in v0.1.** This restriction does not remove the planned XLSX **NIP input** support. Public document links may be retained as discovery/gap context, but unfetched/unsupported documents never become supporting `Source` entries or amount evidence.

A company's accessible ordinary HTML/text remains eligible; adding document parsers, a paid provider, or deeper registry scraping would require an explicitly assigned issue, not another research cycle before implementation.

## Remaining risks, accepted rather than blocking

- Two public issuers are a best-case sample, not evidence of broad private-company financial coverage. Many profiles will be partial.
- Publisher layouts/links can change, source text can be unavailable, and filing metadata may lag results. Failure means unknown, not a silent alternative integration.
- Fiscal years, consolidated versus standalone scope, minority-interest qualifiers, discontinued operations and rounded/bounded figures can be misinterpreted. Preserve the source's meaning or refuse the assertion; do not construct adjusted/comparable metrics.
- The later evidence gate must check actual retrieval, excerpt presence and identity/context. Schema acceptance and quote matching alone do not prove semantic correctness.
- Scrapling extraction quality and bounded-agent behavior were not tested here; they belong to the assigned research/extraction stages. No universal improvement percentage is claimed.

**Exit condition met:** one primary route, one UNKNOWN fallback, concrete hard/best-effort fields and unsupported formats are frozen. Financial coverage is not a prerequisite for starting the later implementation issues.
