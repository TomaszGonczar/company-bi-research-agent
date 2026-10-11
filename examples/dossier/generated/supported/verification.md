# Offline verification — Example sp. z o.o.

- Status: **verified**
- NIP: 5220003782
- Profile status: partial
- Research generated: 2026-10-05T12:00:00\+00:00
- Input: supported.json (SHA-256 `1585df7207b6bd9717387a1538d6674f56fc83fa04aa182023f93100a78e1ec8`)
- Decisions: accepted 1, preserved 6

> This checks the supplied retained source ledger and publication gate; it does not authenticate edited input or prove publisher truth.

> Candidate states are agent assertions. Only final supported facts passed this gate; preserved uncertain/unknown facts remain unverified.

## products\_services

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    [
      "cloud services"
    ]

  - Evidence (candidate / unverified):
    - [page](https://company.example/): Example sp. z o.o. offers "cloud services".

**Final:** supported

Value:

    [
      "cloud services"
    ]

  - Evidence (supporting final publication):
    - [page](https://company.example/): Example sp. z o.o. offers "cloud services".

## business\_description

**Decision: PRESERVED**

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

## employees

**Decision: PRESERVED**

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example

Context:

    {
      "as_of": null
    }

  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example

Context:

    {
      "as_of": null
    }

  - Evidence: none

## financials\[0\]

**Decision: PRESERVED**

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example

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

  - Fact reason: Not established in this synthetic offline example

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

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example

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

  - Fact reason: Not established in this synthetic offline example

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

## industries

**Decision: PRESERVED**

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

## markets

**Decision: PRESERVED**

**Reason:** Not established in this synthetic offline example

**Candidate:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

**Final:** unknown

Value:

    null

  - Fact reason: Not established in this synthetic offline example
  - Evidence: none

## Candidate limitations
- Synthetic strict-contract probe; no live-company research

## Final limitations
- Synthetic strict-contract probe; no live-company research

## Retained source metadata
### Candidate
- [registry](https://registry.example/) — registry; Synthetic MF-shaped registry record; retrieved 2026-10-05T12:00:00\+00:00
- [page](https://company.example/) — full\_page; Synthetic complete assertion unit; retrieved 2026-10-05T12:00:00\+00:00
### Final
- [page](https://company.example/) — full\_page; Synthetic complete assertion unit; retrieved 2026-10-05T12:00:00\+00:00
- [registry](https://registry.example/) — registry; Synthetic MF-shaped registry record; retrieved 2026-10-05T12:00:00\+00:00

Retained research diagnostics (from the input; no calls made by verification):

    {
      "model": "offline-synthetic-fixture",
      "status": "completed",
      "stop_reason": null,
      "failure_code": null,
      "failures": [],
      "validated_progress_retained": false,
      "model_requests": 0,
      "searches": 0,
      "page_reads": 1,
      "dynamic_reads": 0,
      "output_retries": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "duration_seconds": 0.0,
      "cost_usd": null
    }
