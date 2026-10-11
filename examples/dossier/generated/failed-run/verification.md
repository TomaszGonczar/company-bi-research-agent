# Offline verification — Przykładowa Firma Żółć sp. z o.o.

- Status: **not_published**
- NIP: 5220003782
- Profile status: none
- Research generated: 2026-10-05T12:00:00\+00:00
- Input: failed-run.json (SHA-256 `73ade277c875a3d6e7b5e923dca899b4795343151e6c3f417381d790fbd4badc`)
- Decisions: none

> This checks the supplied retained source ledger and publication gate; it does not authenticate edited input or prove publisher truth.

> Candidate states are agent assertions. Only final supported facts passed this gate; preserved uncertain/unknown facts remain unverified.

**Not published:** Syntetyczna awaria modelu; brak publikacji.

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
- None.

Retained research diagnostics (from the input; no calls made by verification):

    {
      "model": "offline-synthetic-fixture",
      "status": "failed",
      "stop_reason": "Syntetyczna awaria modelu; brak publikacji.",
      "failure_code": "MODEL_FAILURE",
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
