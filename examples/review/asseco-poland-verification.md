# Offline verification — "ASSECO POLAND" SPÓŁKA AKCYJNA

- Status: **verified**
- NIP: 5220003782
- Profile status: partial
- Research generated: 2026-10-05T11:40:04.439573\+00:00
- Input: asseco-poland.json (SHA-256 `ad1a1487cab80ee3acb1fd6478eef62e51d11fd275ad5684d90e0aea35d5d1af`)
- Decisions: accepted 1, downgraded 3, preserved 3

> This checks the supplied retained source ledger and publication gate; it does not authenticate edited input or prove publisher truth.

> Candidate states are agent assertions. Only final supported facts passed this gate; preserved uncertain/unknown facts remain unverified.

## business\_description

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    "The activities of the Asseco Poland S.A focus on providing a wide range of proprietary IT solutions and services."

  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The activities of the Asseco Poland S.A focus on providing a wide range of proprietary IT solutions and services.

**Final:** supported

Value:

    "The activities of the Asseco Poland S.A focus on providing a wide range of proprietary IT solutions and services."

  - Evidence (supporting final publication):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The activities of the Asseco Poland S.A focus on providing a wide range of proprietary IT solutions and services.

## industries

**Decision: DOWNGRADED**

**Reason:** No exact full-page citation verifies the candidate value, entity, and required context
**Changed paths:** reason, state

**Candidate:** supported

Value:

    [
      "financial",
      "health",
      "corporate",
      "government"
    ]

  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): targeting the financial, health, corporate and government sectors, at home and abroad,

**Final:** uncertain

Value:

    [
      "financial",
      "health",
      "corporate",
      "government"
    ]

  - Fact reason: No exact full-page citation verifies the candidate value, entity, and required context
  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): targeting the financial, health, corporate and government sectors, at home and abroad,

## markets

**Decision: DOWNGRADED**

**Reason:** Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company
**Changed paths:** reason, state, value

**Candidate:** supported

Value:

    [
      "Poland",
      "abroad"
    ]

  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The strategy of organic growth of Asseco Poland S.A. is based on providing proprietary IT software and services to clients in Poland and abroad.

**Final:** uncertain

Value (cleared):

    null

  - Fact reason: Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company
  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The strategy of organic growth of Asseco Poland S.A. is based on providing proprietary IT software and services to clients in Poland and abroad.

## products\_services

**Decision: DOWNGRADED**

**Reason:** Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company
**Changed paths:** reason, state, value

**Candidate:** supported

Value:

    [
      "proprietary IT software and services",
      "software-based solutions",
      "SaaS-based solutions based on proprietary software"
    ]

  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The strategy of organic growth of Asseco Poland S.A. is based on providing proprietary IT software and services to clients in Poland and abroad.
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): building and delivering software-based solutions in the Company customers' business-critical areas
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): providing SaaS-based solutions based on proprietary software.

**Final:** uncertain

Value (cleared):

    null

  - Fact reason: Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company
  - Evidence (candidate / unverified):
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): The strategy of organic growth of Asseco Poland S.A. is based on providing proprietary IT software and services to clients in Poland and abroad.
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): building and delivering software-based solutions in the Company customers' business-critical areas
    - [S001](https://inwestor.asseco.com/en/about-asseco/strategy/): providing SaaS-based solutions based on proprietary software.

## employees

**Decision: PRESERVED**

**Reason:** No standalone employee count was established from the sources retrieved. Group headcount is not substituted for the legal entity.

**Candidate:** unknown

Value:

    null

  - Fact reason: No standalone employee count was established from the sources retrieved. Group headcount is not substituted for the legal entity.

Context:

    {
      "as_of": null
    }

  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: No standalone employee count was established from the sources retrieved. Group headcount is not substituted for the legal entity.

Context:

    {
      "as_of": null
    }

  - Evidence: none

## financials\[0\]

**Decision: PRESERVED**

**Reason:** No usable official HTML/text or linked CSV source with standalone-company revenue and explicit fiscal dates was retrieved.

**Candidate:** unknown

Value:

    null

  - Fact reason: No usable official HTML/text or linked CSV source with standalone-company revenue and explicit fiscal dates was retrieved.

Context:

    {
      "currency": null,
      "group_name": null,
      "metric": "revenue",
      "period": null,
      "scope": null,
      "unit": null
    }

  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: No usable official HTML/text or linked CSV source with standalone-company revenue and explicit fiscal dates was retrieved.

Context:

    {
      "currency": null,
      "group_name": null,
      "metric": "revenue",
      "period": null,
      "scope": null,
      "unit": null
    }

  - Evidence: none

## financials\[1\]

**Decision: PRESERVED**

**Reason:** No usable official HTML/text or linked CSV source with standalone-company total net result and explicit fiscal dates was retrieved; Group or other profit measures are not substituted.

**Candidate:** unknown

Value:

    null

  - Fact reason: No usable official HTML/text or linked CSV source with standalone-company total net result and explicit fiscal dates was retrieved; Group or other profit measures are not substituted.

Context:

    {
      "currency": null,
      "group_name": null,
      "metric": "net_result",
      "period": null,
      "scope": null,
      "unit": null
    }

  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: No usable official HTML/text or linked CSV source with standalone-company total net result and explicit fiscal dates was retrieved; Group or other profit measures are not substituted.

Context:

    {
      "currency": null,
      "group_name": null,
      "metric": "net_result",
      "period": null,
      "scope": null,
      "unit": null
    }

  - Evidence: none

## Candidate limitations
- Search results did not provide usable primary-source pages on employees, standalone financials, or recent developments. No developments are listed because none could be verified with full-page evidence and publication dates.

## Final limitations
- Search results did not provide usable primary-source pages on employees, standalone financials, or recent developments. No developments are listed because none could be verified with full-page evidence and publication dates.
- products/services: Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company
- industries: No exact full-page citation verifies the candidate value, entity, and required context
- markets: Cited page contains the candidate wording but not a recognized bounded affirmative relation for the resolved company

## Retained source metadata
### Candidate
- [mf-vat-5220003782-20261005T082944526457Z](https://wl-api.mf.gov.pl/api/search/nip/5220003782?date=2026-10-05) — registry; Ministerstwo Finansów — Wykaz podatników VAT; retrieved 2026-10-05T08:29:44.526457\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy) — search\_snippet; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:43.228981\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy) — search\_snippet; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:43.228981\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy) — search\_snippet; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:43.228981\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy) — search\_snippet; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:43.228981\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy) — search\_snippet; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:43.228981\+00:00
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy/) — full\_page; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:47.874936\+00:00; redirects: [https://inwestor.asseco.com/en/about-asseco/strategy](https://inwestor.asseco.com/en/about-asseco/strategy) → [https://inwestor.asseco.com/en/about-asseco/strategy/](https://inwestor.asseco.com/en/about-asseco/strategy/)
### Final
- [S001](https://inwestor.asseco.com/en/about-asseco/strategy/) — full\_page; Strategy - Asseco Poland S.A. - Centrum Relacji Inwestorskich; retrieved 2026-10-05T08:52:47.874936\+00:00; redirects: [https://inwestor.asseco.com/en/about-asseco/strategy](https://inwestor.asseco.com/en/about-asseco/strategy) → [https://inwestor.asseco.com/en/about-asseco/strategy/](https://inwestor.asseco.com/en/about-asseco/strategy/)
- [mf-vat-5220003782-20261005T082944526457Z](https://wl-api.mf.gov.pl/api/search/nip/5220003782?date=2026-10-05) — registry; Ministerstwo Finansów — Wykaz podatników VAT; retrieved 2026-10-05T08:29:44.526457\+00:00

Retained research diagnostics (from the input; no calls made by verification):

    {
      "model": "openai-codex:gpt-6-luna",
      "status": "completed",
      "stop_reason": null,
      "failure_code": null,
      "failures": [],
      "validated_progress_retained": false,
      "model_requests": 5,
      "searches": 5,
      "page_reads": 1,
      "dynamic_reads": 0,
      "output_retries": 0,
      "input_tokens": 23895,
      "output_tokens": 1111,
      "duration_seconds": 40.1280493340455,
      "cost_usd": null
    }
