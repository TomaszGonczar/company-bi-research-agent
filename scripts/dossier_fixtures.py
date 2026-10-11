"""Reproducible synthetic retained runs; never modifies frozen strict evidence."""

import json
from pathlib import Path
from typing import Any

from company_bi.models import CompanyResearchRun
from company_bi.verification import verify_run

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-10-05T12:00:00Z"
NAME = "Przykładowa Firma Żółć sp. z o.o."


def make_run(kind: str = "rich") -> CompanyResearchRun:
    data = json.loads((ROOT / "examples/strict_contract/supported.json").read_bytes())
    name = NAME if kind != "stress" else "Przykładowa " + "Żółć Pomiarowa " * 28 + "sp. z o.o."
    identity = data["identity"]
    identity["legal_name"]["value"] = name
    identity["legal_name"]["evidence"][0]["excerpt"] = name
    address = "ul. Przykładowa 1, 00-001 Warszawa"
    identity["registered_address"] = {
        "state": "supported",
        "value": address,
        "evidence": [{"source_id": "registry", "excerpt": address}],
    }
    for field in ("krs", "regon", "registered_city", "website"):
        identity[field] = {"state": "unknown", "reason": "Brak danych w syntetycznym przykładzie."}
    registry = data["sources"][0]
    registry["content"] = json.dumps(
        {
            "result": {
                "subject": {
                    "nip": identity["nip"],
                    "name": name,
                    "workingAddress": address,
                }
            }
        },
        ensure_ascii=False,
    )
    registry["source"]["title"] = "Syntetyczny rekord w strukturze MF"
    sources = [registry]

    def supported(source_id: str, assertion: str, value: Any, **context: Any) -> dict[str, Any]:
        source = {
            "source_id": source_id,
            "url": f"https://{source_id}.example/",
            "title": f"Syntetyczna pełna asercja: {source_id}",
            "retrieved_at": STAMP,
        }
        if source_id == "event":
            source["published_on"] = "2026-09-20"
        sources.append(
            {"source": source, "kind": "full_page", "content": assertion, "fetch_mode": "static"}
        )
        return {
            "state": "supported",
            "value": value,
            "evidence": [{"source_id": source_id, "excerpt": assertion}],
            **context,
        }

    draft = data["draft"]
    for field, label, predicate in (
        ("business_description", "dostawca rozwiązań pomiarowych", "działa jako"),
        ("products_services", "systemy pomiarowe", "oferuje"),
        ("industries", "aparatura pomiarowa", "działa w branży"),
        ("markets", "Polska", "działa na rynku"),
    ):
        draft[field] = supported(
            field,
            f'{name} {predicate} "{label}".',
            label if field == "business_description" else [label],
        )
    draft["employees"] = supported(
        "employees",
        f"{name} zatrudnia 25 pracowników na dzień 2026-09-30.",
        {"kind": "exact", "count": 25},
        as_of="2026-09-30",
    )
    draft["financials"] = []
    for metric, predicate, amount, value in (
        (
            "revenue",
            "revenue",
            "0.0000" if kind == "zero-finance" else "12.5000",
            "0.0000" if kind == "zero-finance" else "12.5000",
        ),
        ("net_result", "net loss", "0.7500", "-0.7500"),
    ):
        assertion = (
            f"{name} reported standalone {predicate} of PLN {amount} million "
            "for 2025-01-01 to 2025-12-31."
        )
        draft["financials"].append(
            supported(
                metric,
                assertion,
                value,
                metric=metric,
                currency="PLN",
                unit="millions",
                scope="legal_entity",
                group_name=None,
                period={"start": "2025-01-01", "end": "2025-12-31"},
            )
        )
    assertion = f'{name} otworzyła "centrum badawcze" w dniu 2026-09-18.'
    draft["recent_developments"] = [
        supported(
            "event",
            assertion,
            {
                "title": "centrum badawcze",
                "summary": assertion,
                "published_on": "2026-09-20",
                "occurred_on": "2026-09-18",
            },
        )
    ]
    draft["limitations"] = []
    if kind == "stress":
        sources[:] = [s for s in sources if s["source"]["source_id"] != "products_services"]
        values, evidence = [], []
        for number in range(1, 41):
            label = f"Usługa {number:02d}: " + 'Żółć & <pomiar> "precyzyjny" ' * 4
            label = label.strip()
            item = supported(
                f"service{number:02d}",
                f"{name} oferuje {json.dumps(label, ensure_ascii=False)}.",
                [label],
            )
            values.append(label)
            evidence.extend(item["evidence"])
        draft["products_services"] = {"state": "supported", "value": values, "evidence": evidence}
        sources[-1]["source"]["url"] += "pomiar" * 180
        sources[-1]["source"]["title"] += " — Długi tytuł źródła Żółć" * 24
        identity["website"]["reason"] += " Nie ustalono witryny w tym kontrolowanym materiale." * 60
    data["sources"] = sources
    data["diagnostics"]["page_reads"] = len(sources) - 1
    if kind == "failed-run":
        data["diagnostics"].update(
            status="failed",
            failure_code="MODEL_FAILURE",
            stop_reason="Syntetyczna awaria modelu; brak publikacji.",
        )
    run = CompanyResearchRun.model_validate(data)
    # Revalidation, not unchecked copies, is required even for fixture construction.
    return CompanyResearchRun.model_validate_json(run.model_dump_json())


def main() -> None:
    output = ROOT / "examples/dossier"
    output.mkdir(exist_ok=True)
    for kind in ("rich", "failed-run", "zero-finance", "stress"):
        run = make_run(kind)
        profile, report = verify_run(
            run, input_sha256="fixture-preflight", input_name=f"{kind}.json"
        )
        if kind == "failed-run":
            assert profile is None and report.status == "not_published"
        else:
            assert profile is not None and profile.status == "complete"
            assert profile.products_services.state == "supported"
        (output / f"{kind}.json").write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(kind, report.status, profile.status if profile else None)


if __name__ == "__main__":
    main()
