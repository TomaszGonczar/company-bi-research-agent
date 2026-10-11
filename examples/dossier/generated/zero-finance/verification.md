# Offline verification — Przykładowa Firma Żółć sp. z o.o.

- Status: **verified**
- NIP: 5220003782
- Profile status: complete
- Research generated: 2026-10-05T12:00:00\+00:00
- Input: zero-finance.json (SHA-256 `f4fbc06fb68396560d87c26c52165a69f164db14a71a3a221e930911074fc7b8`)
- Decisions: accepted 8

> This checks the supplied retained source ledger and publication gate; it does not authenticate edited input or prove publisher truth.

> Candidate states are agent assertions. Only final supported facts passed this gate; preserved uncertain/unknown facts remain unverified.

## business\_description

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    "dostawca rozwiązań pomiarowych"

  - Evidence (candidate / unverified):
    - [business\\\_description](https://business_description.example/): Przykładowa Firma Żółć sp. z o.o. działa jako "dostawca rozwiązań pomiarowych".

**Final:** supported

Value:

    "dostawca rozwiązań pomiarowych"

  - Evidence (supporting final publication):
    - [business\\\_description](https://business_description.example/): Przykładowa Firma Żółć sp. z o.o. działa jako "dostawca rozwiązań pomiarowych".

## employees

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    {
      "count": 25,
      "kind": "exact"
    }


Context:

    {
      "as_of": "2026-09-30"
    }

  - Evidence (candidate / unverified):
    - [employees](https://employees.example/): Przykładowa Firma Żółć sp. z o.o. zatrudnia 25 pracowników na dzień 2026-09-30.

**Final:** supported

Value:

    {
      "count": 25,
      "kind": "exact"
    }


Context:

    {
      "as_of": "2026-09-30"
    }

  - Evidence (supporting final publication):
    - [employees](https://employees.example/): Przykładowa Firma Żółć sp. z o.o. zatrudnia 25 pracowników na dzień 2026-09-30.

## financials\[0\]

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    "0.0000"


Context:

    {
      "currency": "PLN",
      "group_name": null,
      "metric": "revenue",
      "period": {
        "end": "2025-12-31",
        "start": "2025-01-01"
      },
      "scope": "legal_entity",
      "unit": "millions"
    }

  - Evidence (candidate / unverified):
    - [revenue](https://revenue.example/): Przykładowa Firma Żółć sp. z o.o. reported standalone revenue of PLN 0.0000 million for 2025-01-01 to 2025-12-31.

**Final:** supported

Value:

    "0.0000"


Context:

    {
      "currency": "PLN",
      "group_name": null,
      "metric": "revenue",
      "period": {
        "end": "2025-12-31",
        "start": "2025-01-01"
      },
      "scope": "legal_entity",
      "unit": "millions"
    }

  - Evidence (supporting final publication):
    - [revenue](https://revenue.example/): Przykładowa Firma Żółć sp. z o.o. reported standalone revenue of PLN 0.0000 million for 2025-01-01 to 2025-12-31.

## financials\[1\]

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    "-0.7500"


Context:

    {
      "currency": "PLN",
      "group_name": null,
      "metric": "net_result",
      "period": {
        "end": "2025-12-31",
        "start": "2025-01-01"
      },
      "scope": "legal_entity",
      "unit": "millions"
    }

  - Evidence (candidate / unverified):
    - [net\\\_result](https://net_result.example/): Przykładowa Firma Żółć sp. z o.o. reported standalone net loss of PLN 0.7500 million for 2025-01-01 to 2025-12-31.

**Final:** supported

Value:

    "-0.7500"


Context:

    {
      "currency": "PLN",
      "group_name": null,
      "metric": "net_result",
      "period": {
        "end": "2025-12-31",
        "start": "2025-01-01"
      },
      "scope": "legal_entity",
      "unit": "millions"
    }

  - Evidence (supporting final publication):
    - [net\\\_result](https://net_result.example/): Przykładowa Firma Żółć sp. z o.o. reported standalone net loss of PLN 0.7500 million for 2025-01-01 to 2025-12-31.

## industries

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    [
      "aparatura pomiarowa"
    ]

  - Evidence (candidate / unverified):
    - [industries](https://industries.example/): Przykładowa Firma Żółć sp. z o.o. działa w branży "aparatura pomiarowa".

**Final:** supported

Value:

    [
      "aparatura pomiarowa"
    ]

  - Evidence (supporting final publication):
    - [industries](https://industries.example/): Przykładowa Firma Żółć sp. z o.o. działa w branży "aparatura pomiarowa".

## markets

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    [
      "Polska"
    ]

  - Evidence (candidate / unverified):
    - [markets](https://markets.example/): Przykładowa Firma Żółć sp. z o.o. działa na rynku "Polska".

**Final:** supported

Value:

    [
      "Polska"
    ]

  - Evidence (supporting final publication):
    - [markets](https://markets.example/): Przykładowa Firma Żółć sp. z o.o. działa na rynku "Polska".

## products\_services

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    [
      "systemy pomiarowe"
    ]

  - Evidence (candidate / unverified):
    - [products\\\_services](https://products_services.example/): Przykładowa Firma Żółć sp. z o.o. oferuje "systemy pomiarowe".

**Final:** supported

Value:

    [
      "systemy pomiarowe"
    ]

  - Evidence (supporting final publication):
    - [products\\\_services](https://products_services.example/): Przykładowa Firma Żółć sp. z o.o. oferuje "systemy pomiarowe".

## recent\_developments\[0\]

**Decision: ACCEPTED**

**Reason:** The publication gate retained this supported fact.

**Candidate:** supported

Value:

    {
      "occurred_on": "2026-09-18",
      "published_on": "2026-09-20",
      "summary": "Przykładowa Firma Żółć sp. z o.o. otworzyła \"centrum badawcze\" w dniu 2026-09-18.",
      "title": "centrum badawcze"
    }

  - Evidence (candidate / unverified):
    - [event](https://event.example/): Przykładowa Firma Żółć sp. z o.o. otworzyła "centrum badawcze" w dniu 2026-09-18.

**Final:** supported

Value:

    {
      "occurred_on": "2026-09-18",
      "published_on": "2026-09-20",
      "summary": "Przykładowa Firma Żółć sp. z o.o. otworzyła \"centrum badawcze\" w dniu 2026-09-18.",
      "title": "centrum badawcze"
    }

  - Evidence (supporting final publication):
    - [event](https://event.example/): Przykładowa Firma Żółć sp. z o.o. otworzyła "centrum badawcze" w dniu 2026-09-18.

## Candidate limitations
- None recorded.

## Final limitations
- None recorded.

## Retained source metadata
### Candidate
- [registry](https://registry.example/) — registry; Syntetyczny rekord w strukturze MF; retrieved 2026-10-05T12:00:00\+00:00
- [business\\\_description](https://business_description.example/) — full\_page; Syntetyczna pełna asercja: business\_description; retrieved 2026-10-05T12:00:00\+00:00
- [products\\\_services](https://products_services.example/) — full\_page; Syntetyczna pełna asercja: products\_services; retrieved 2026-10-05T12:00:00\+00:00
- [industries](https://industries.example/) — full\_page; Syntetyczna pełna asercja: industries; retrieved 2026-10-05T12:00:00\+00:00
- [markets](https://markets.example/) — full\_page; Syntetyczna pełna asercja: markets; retrieved 2026-10-05T12:00:00\+00:00
- [employees](https://employees.example/) — full\_page; Syntetyczna pełna asercja: employees; retrieved 2026-10-05T12:00:00\+00:00
- [revenue](https://revenue.example/) — full\_page; Syntetyczna pełna asercja: revenue; retrieved 2026-10-05T12:00:00\+00:00
- [net\\\_result](https://net_result.example/) — full\_page; Syntetyczna pełna asercja: net\_result; retrieved 2026-10-05T12:00:00\+00:00
- [event](https://event.example/) — full\_page; Syntetyczna pełna asercja: event; retrieved 2026-10-05T12:00:00\+00:00
### Final
- [business\\\_description](https://business_description.example/) — full\_page; Syntetyczna pełna asercja: business\_description; retrieved 2026-10-05T12:00:00\+00:00
- [employees](https://employees.example/) — full\_page; Syntetyczna pełna asercja: employees; retrieved 2026-10-05T12:00:00\+00:00
- [event](https://event.example/) — full\_page; Syntetyczna pełna asercja: event; retrieved 2026-10-05T12:00:00\+00:00
- [industries](https://industries.example/) — full\_page; Syntetyczna pełna asercja: industries; retrieved 2026-10-05T12:00:00\+00:00
- [markets](https://markets.example/) — full\_page; Syntetyczna pełna asercja: markets; retrieved 2026-10-05T12:00:00\+00:00
- [net\\\_result](https://net_result.example/) — full\_page; Syntetyczna pełna asercja: net\_result; retrieved 2026-10-05T12:00:00\+00:00
- [products\\\_services](https://products_services.example/) — full\_page; Syntetyczna pełna asercja: products\_services; retrieved 2026-10-05T12:00:00\+00:00
- [registry](https://registry.example/) — registry; Syntetyczny rekord w strukturze MF; retrieved 2026-10-05T12:00:00\+00:00
- [revenue](https://revenue.example/) — full\_page; Syntetyczna pełna asercja: revenue; retrieved 2026-10-05T12:00:00\+00:00

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
      "page_reads": 8,
      "dynamic_reads": 0,
      "output_retries": 0,
      "input_tokens": 0,
      "output_tokens": 0,
      "duration_seconds": 0.0,
      "cost_usd": null
    }
