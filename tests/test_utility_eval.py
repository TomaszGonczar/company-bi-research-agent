import hashlib
import json
import runpy
from pathlib import Path

import pytest

from company_bi.models import CompanyResearchRun

ROOT = Path(__file__).parents[1]
_EVALUATOR = runpy.run_path(str(ROOT / "scripts/evaluate_utility.py"))
_assessment_map = _EVALUATOR["_assessment_map"]
credited_count = _EVALUATOR["credited_count"]
evaluate_company = _EVALUATOR["evaluate_company"]
gold_backed_matches = _EVALUATOR["gold_backed_matches"]
gold_credit = _EVALUATOR["gold_credit"]
observations_from_dump = _EVALUATOR["observations_from_dump"]
precision_counts = _EVALUATOR["precision_counts"]
ratio = _EVALUATOR["ratio"]
run_source_binding = _EVALUATOR["run_source_binding"]
stages = _EVALUATOR["stages"]
DATASET = json.loads((ROOT / "examples/utility_v011/dataset.json").read_text(encoding="utf-8"))
CASE = json.loads(
    (ROOT / "examples/utility_v011/cases/asseco-poland.json").read_text(encoding="utf-8")
)


def test_supported_uncertain_unknown_and_missing_use_all_gold_in_recall_denominator():
    claims = [
        {"id": "supported", "field": "business_description", "expected_value": "business activity"},
        {"id": "uncertain", "field": "products_services", "expected_value": "other product"},
        {"id": "unknown", "field": "industries", "expected_value": "power sector"},
        {"id": "missing", "field": "markets", "expected_value": "Asia"},
    ]
    facts = {
        "business_description": {"state": "supported", "value": "Current business activity"},
        "products_services": {"state": "uncertain", "value": ["other product"]},
        "industries": {"state": "unknown", "value": None},
        "markets": {"state": "supported", "value": ["Europe"]},
    }
    observations = observations_from_dump(facts)
    observed = stages(claims, observations, {field: fact["state"] for field, fact in facts.items()})
    assert [item["stage"] for item in observed] == ["supported", "uncertain", "unknown", "missing"]
    counts = {
        state: sum(item["stage"] == state for item in observed)
        for state in ("supported", "uncertain", "unknown", "missing")
    }
    assert counts == {"supported": 1, "uncertain": 1, "unknown": 1, "missing": 1}
    assert ratio(counts["supported"], len(claims)) == {
        "numerator": 1,
        "denominator": 4,
        "rate": 0.25,
    }


def test_unmatched_or_broader_supported_observation_stays_unassessed_not_perfect_precision():
    observations = [
        {"field": "products_services", "value": "unreviewed product", "state": "supported"},
        {"field": "products_services", "value": "calibration services", "state": "supported"},
        {
            "field": "business_description",
            "value": "leader in production of measuring instruments and accessories",
            "state": "supported",
        },
    ]
    claims = [
        {
            "id": "S1",
            "field": "business_description",
            "expected_value": "production of measuring instruments and accessories",
        },
        {"id": "S5", "field": "products_services", "expected_value": "calibration services"},
    ]
    assert stages(claims[:1], observations)[0]["stage"] == "supported"
    matched = gold_backed_matches(observations, claims)
    credits = gold_credit(claims, observations, matched, {})
    assert credits == {"S1": "unassessed_broader_support", "S5": "gold_backed"}
    assert credited_count(credits) == 1
    denied = gold_credit(
        claims,
        observations,
        matched,
        {
            (
                "business_description",
                "leader in production of measuring instruments and accessories",
            ): "unsupported",
        },
    )
    assert denied["S1"] == "externally_assessed_unsupported"
    approved = gold_credit(
        claims,
        observations,
        matched,
        {
            (
                "business_description",
                "leader in production of measuring instruments and accessories",
            ): "supported",
        },
    )
    assert approved["S1"] == "externally_assessed"
    counts = precision_counts(observations, matched, {})
    assert counts == {
        "supported_observations": 3,
        "gold_backed_support": 1,
        "externally_assessed_support": 0,
        "externally_assessed_unsupported": 0,
        "unassessed_support": 2,
    }
    assert ratio(counts["gold_backed_support"], counts["supported_observations"]) == {
        "numerator": 1,
        "denominator": 3,
        "rate": 1 / 3,
    }


def test_precision_observations_include_employees_financials_and_events():
    observations = observations_from_dump(
        {
            "employees": {
                "state": "supported",
                "value": {"kind": "exact", "count": 10},
                "as_of": "2025-12-31",
            },
            "financials": [
                {
                    "state": "supported",
                    "metric": "revenue",
                    "period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "value": "1200",
                    "currency": "PLN",
                    "unit": "thousand",
                }
            ],
            "recent_developments": [
                {
                    "state": "supported",
                    "value": {
                        "title": "New laboratory",
                        "description": "Company opened a laboratory",
                        "published_on": "2026-01-20",
                        "occurred_on": "2026-01-19",
                    },
                }
            ],
        }
    )
    assert {item["field"] for item in observations} == {
        "employees",
        "financials.revenue@2025-01-01:2025-12-31",
        "recent_developments@2026-01-20",
    }
    counts = precision_counts(observations, set(), {})
    assert counts["supported_observations"] == 3
    assert counts["unassessed_support"] == 3


def test_external_assessment_must_bind_exact_run_digest_and_observation(tmp_path: Path):
    exact_run = (ROOT / "examples/evals/retained/asseco-poland.json").read_bytes()
    digest = hashlib.sha256(exact_run).hexdigest()
    run = CompanyResearchRun.model_validate_json(exact_run)
    observations = observations_from_dump(run.draft.model_dump(mode="json"))
    observation = next(item for item in observations if item["state"] == "supported")
    path = tmp_path / "assessment.json"
    path.write_text(
        json.dumps(
            {
                "run_sha256": digest,
                "assessments": [
                    {
                        "field": observation["field"],
                        "value": observation["value"],
                        "judgment": "supported",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    expected = {
        (observation["field"], " ".join(observation["value"].split()).casefold()): "supported"
    }
    assert _assessment_map(path, digest, observations, set()) == expected
    with pytest.raises(ValueError, match="exact run SHA-256"):
        _assessment_map(path, "0" * 64, observations, set())
    with pytest.raises(ValueError, match="exact supported field/value"):
        _assessment_map(path, digest, [{**observation, "value": "different"}], set())


def test_wrong_nip_and_noncorpus_source_are_rejected(tmp_path: Path):
    raw = json.loads(
        (ROOT / "examples/evals/retained/asseco-poland.json").read_text(encoding="utf-8")
    )
    run = CompanyResearchRun.model_validate(raw)
    company = DATASET["cases"][0]
    run_path = tmp_path / "asseco-poland.json"
    output = tmp_path / "out"
    raw["identity"]["nip"] = "0000000000"
    run_path.write_text(json.dumps(raw), encoding="utf-8")
    rejected = evaluate_company(company, CASE, [], tmp_path, output, None)
    assert rejected["run_status"] == "rejected"
    assert "NIP" in rejected["error"]

    fixture_registry = next(source.source for source in run.sources if source.kind == "registry")
    case_for_run = {
        **CASE,
        "identity": run.identity.model_dump(mode="json"),
        "registry_source": fixture_registry.model_dump(mode="json"),
    }
    with pytest.raises(ValueError, match="URL/content hash is not in frozen corpus"):
        run_source_binding(run, case_for_run)

    tampered_identity = json.loads(json.dumps(case_for_run))
    tampered_identity["identity"]["registered_city"]["reason"] = "altered frozen identity"
    with pytest.raises(ValueError, match="identity does not match frozen case"):
        run_source_binding(run, tampered_identity)

    altered_sources = [
        source.model_copy(update={"content": source.content + " altered"})
        if source.kind == "registry"
        else source
        for source in run.sources
    ]
    tampered_registry_run = run.model_copy(update={"sources": altered_sources})
    with pytest.raises(ValueError, match="registry material does not match frozen"):
        run_source_binding(tampered_registry_run, case_for_run)
