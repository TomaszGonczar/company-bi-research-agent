from company_bi.evaluation import (
    EvalMetadata,
    EvalOutput,
    GoldClaim,
    _add_counts,
    _ratio,
    _raw_value_at,
    evaluate_case,
    evaluate_strict_case,
)


def claim(path, *, eligible=True, fields=None, states=("supported",), required=None):
    return GoldClaim(
        path=path,
        eligible=eligible,
        supported_fields=fields,
        allowed_states=list(states),
        required_fields=required or {},
        evidence=[{"source_id": "source-1", "excerpt": "Retained text"}],
        note="Manually annotated retained evidence.",
    )


def metadata(*claims):
    return EvalMetadata(
        provenance="controlled",
        categories=["regression"],
        expected_outcome="published",
        identity={},
        claims=list(claims),
    )


def test_supported_value_and_context_must_both_match_gold():
    gold = metadata(
        claim("financials.0", fields={"value": "10", "currency": "PLN", "metric": "revenue"})
    )
    candidate = EvalOutput(
        outcome="published",
        profile={
            "financials": [
                {"state": "supported", "value": "10", "currency": "EUR", "metric": "revenue"}
            ],
            "recent_developments": [],
            "identity": {
                "nip": "1234567890",
                "legal_name": {},
                "krs": {},
                "regon": {},
                "registered_city": {},
                "registered_address": {},
                "website": {},
            },
            "business_description": {},
            "products_services": {},
            "industries": {},
            "markets": {},
            "employees": {},
        },
    )
    result = evaluate_case(gold, candidate)
    assert result["counts"]["unsupported_as_supported"] == 1
    assert result["counts"].get("eligible_supported", 0) == 0


def test_missing_eligible_output_stays_in_recall_denominator():
    gold = metadata(claim("business_description", fields={"value": "Supported business"}))
    result = evaluate_case(gold, EvalOutput(outcome="rejected", error="gate rejected"))
    assert result["counts"]["eligible_researched"] == 1
    assert result["counts"]["eligible_missing"] == 1
    assert result["fields"][0]["state"] == "missing"


def test_precision_partitions_registry_and_researched_claims():
    claims = metadata(
        claim("identity.krs", fields={"value": "0000000001"}),
        claim("business_description", fields={"value": "Gold wording"}),
    )
    identity = {"nip": "1234567890", "krs": {"state": "supported", "value": "0000000002"}}
    profile = {
        "identity": {
            "nip": "1234567890",
            "legal_name": {},
            "krs": identity["krs"],
            "regon": {},
            "registered_city": {},
            "registered_address": {},
            "website": {},
        },
        "business_description": {"state": "supported", "value": "Gold wording"},
        "products_services": {},
        "industries": {},
        "markets": {},
        "employees": {},
        "financials": [],
        "recent_developments": [],
    }
    result = evaluate_case(
        claims, EvalOutput(outcome="published", identity=identity, profile=profile)
    )
    assert result["counts"]["supported_registry"] == 1
    assert result["counts"]["supported_researched"] == 1
    assert result["counts"].get("correct_supported_registry", 0) == 0
    assert result["counts"]["correct_supported_researched"] == 1


def test_uncertain_and_unknown_safety_have_distinct_constraints():
    gold = metadata(
        claim("employees", fields=None, states=("uncertain",), required={"value": None}),
        claim("business_description", fields=None, states=("unknown",), required={"value": None}),
    )
    profile = {
        "identity": {
            "nip": "1234567890",
            "legal_name": {},
            "krs": {},
            "regon": {},
            "registered_city": {},
            "registered_address": {},
            "website": {},
        },
        "employees": {"state": "uncertain", "value": None},
        "business_description": {"state": "unknown", "value": None},
        "products_services": {},
        "industries": {},
        "markets": {},
        "financials": [],
        "recent_developments": [],
    }
    score = evaluate_case(gold, EvalOutput(outcome="published", profile=profile))
    assert score["safety"]["uncertain"] == {"correct": 1, "total": 1}
    assert score["safety"]["unknown"] == {"correct": 1, "total": 1}
    profile["employees"]["value"] = {"kind": "exact", "count": 10}
    assert (
        evaluate_case(gold, EvalOutput(outcome="published", profile=profile))["safety"][
            "uncertain"
        ]["correct"]
        == 0
    )


def test_zero_denominator_is_unavailable_not_perfect():
    assert _ratio(0, 0) == {"numerator": 0, "denominator": 0, "rate": None}


def test_counts_aggregate_raw_claims_not_case_percentages():
    first = evaluate_case(
        metadata(claim("business_description", fields={"value": "yes"})),
        EvalOutput(
            outcome="published",
            profile={
                "business_description": {"state": "supported", "value": "yes"},
                "identity": {},
                "products_services": {},
                "industries": {},
                "markets": {},
                "employees": {},
                "financials": [],
                "recent_developments": [],
            },
        ),
    )
    second = evaluate_case(
        metadata(
            claim("business_description", fields={"value": "yes"}),
            claim("employees", fields={"value": 20}),
            claim("markets", fields={"value": ["local"]}),
        ),
        EvalOutput(outcome="rejected"),
    )
    counts = {}
    for values in (first["counts"], second["counts"]):
        _add_counts(counts, values)
    assert _ratio(counts.get("eligible_supported", 0), counts.get("eligible_researched", 0)) == {
        "numerator": 1,
        "denominator": 4,
        "rate": 0.25,
    }


def test_missing_with_no_required_constraints_is_not_a_safety_failure():
    gold = metadata(claim("business_description", fields=None, states=("supported",)))
    score = evaluate_case(gold, EvalOutput(outcome="rejected"))
    assert score["fields"][0]["required_fields_satisfied"] is True
    assert score["fields"][0]["safety_failure"] is False
    assert score["counts"]["eligible_missing"] == 1


def test_positive_eligible_downgrade_is_recall_loss_not_safety_failure():
    gold = metadata(claim("business_description", fields={"value": "Known"}, states=("supported",)))
    output = EvalOutput(
        outcome="published",
        profile={
            "business_description": {"state": "unknown", "value": None},
            "identity": {},
            "products_services": {},
            "industries": {},
            "markets": {},
            "employees": {},
            "financials": [],
            "recent_developments": [],
        },
    )
    score = evaluate_case(gold, output)
    assert score["fields"][0]["safety_failure"] is False
    assert score["counts"]["eligible_unknown"] == 1


def test_flexible_uncertainty_accepts_unknown_without_expanding_unknown_only_denominator():
    gold = metadata(
        claim("employees", fields=None, states=("uncertain", "unknown"), required={"value": None})
    )
    output = EvalOutput(
        outcome="published",
        profile={
            "employees": {"state": "unknown", "value": None},
            "identity": {},
            "business_description": {},
            "products_services": {},
            "industries": {},
            "markets": {},
            "financials": [],
            "recent_developments": [],
        },
    )
    score = evaluate_case(gold, output)
    assert score["safety"]["uncertain"] == {"correct": 1, "total": 1}
    assert "unknown" not in score["safety"]


def test_identity_null_expectations_are_compared():
    gold = metadata()
    gold.identity = {"nip": None, "krs": None}
    absent = evaluate_case(gold, EvalOutput(outcome="unresolved"))
    resolved = evaluate_case(gold, EvalOutput(outcome="published", identity={"nip": "1234567890"}))
    assert absent["counts"]["identity_fields_correct"] == 2
    assert absent["counts"].get("identity_cases_total", 0) == 0
    assert resolved["counts"]["identity_fields_correct"] == 1


def test_nested_required_context_preserves_null_occurrence_without_erasing_details():
    full_details = {
        "title": "Expansion",
        "summary": "Opened a new site",
        "published_on": "2025-01-10",
        "occurred_on": None,
    }
    gold = metadata(
        claim(
            "recent_developments.0",
            fields={"value": full_details},
            states=("supported", "uncertain"),
            required={"value": {"occurred_on": None}},
        )
    )

    def score_event(state, value):
        profile = {
            "identity": {},
            "business_description": {},
            "products_services": {},
            "industries": {},
            "markets": {},
            "employees": {},
            "financials": [],
            "recent_developments": [{"state": state, "value": value}],
        }
        return next(
            item
            for item in evaluate_case(gold, EvalOutput(outcome="published", profile=profile))[
                "fields"
            ]
            if item["path"] == "recent_developments.0"
        )

    assert score_event("supported", full_details)["required_fields_satisfied"] is True
    assert score_event("uncertain", None)["required_fields_satisfied"] is True
    wrong_day = {**full_details, "occurred_on": "2025-01-09"}
    assert score_event("uncertain", wrong_day)["required_fields_satisfied"] is False
    assert score_event("uncertain", wrong_day)["safety_failure"] is True


def test_published_identity_mismatch_cannot_hide_behind_correct_input_identity():
    gold = metadata()
    gold.identity = {"nip": "1111111111", "legal_name": "Expected company"}
    trusted_identity = {
        "nip": "1111111111",
        "legal_name": {"state": "supported", "value": "Expected company"},
    }
    score = evaluate_case(
        gold,
        EvalOutput(
            outcome="published",
            identity=trusted_identity,
            profile={"identity": {**trusted_identity, "nip": "2222222222"}},
        ),
    )
    assert score["counts"]["identity_fields_correct"] == 1
    assert score["counts"]["identity_cases_total"] == 1
    assert score["counts"].get("identity_cases_correct", 0) == 0


def test_strict_out_of_contract_true_is_not_an_eligible_miss():
    case = {
        "case_id": "true-outside-grammar",
        "classification": "OUT_OF_CONTRACT_TRUE",
        "path": "products_services",
        "expected": {"outcome": "published"},
        "rationale": "True but outside finite grammar.",
    }
    output = EvalOutput(
        outcome="published",
        profile={"products_services": {"state": "uncertain", "value": None}},
    )
    scored = evaluate_strict_case(case, output)
    assert scored["correct"] is True
    assert scored["eligible"] is False
    assert scored["classification"] == "OUT_OF_CONTRACT_TRUE"


def test_strict_contract_positive_requires_verified_support():
    case = {
        "case_id": "contract-positive",
        "classification": "SUPPORTED_CONTRACT_POSITIVE",
        "path": "products_services",
        "expected": {
            "outcome": "published",
            "supported_fields": {"value": ["cloud services"]},
        },
        "rationale": "Source-backed grammar positive.",
    }
    output = EvalOutput(
        outcome="published",
        profile={"products_services": {"state": "uncertain", "value": None}},
    )
    scored = evaluate_strict_case(case, output)
    assert scored["correct"] is False
    assert scored["eligible"] is True


def test_strict_positive_rejection_remains_in_eligible_denominator():
    case = {
        "case_id": "positive-rejected",
        "classification": "SUPPORTED_CONTRACT_POSITIVE",
        "path": "products_services",
        "expected": {"outcome": "published", "supported_fields": {"value": ["cloud"]}},
        "rationale": "Source-backed finite-language positive.",
    }
    scored = evaluate_strict_case(case, EvalOutput(outcome="rejected", error="GATE_REJECTED"))
    assert scored["eligible"] is True
    assert scored["correct"] is False
    assert scored["assessment"] == "failed"
    assert scored["semantic_execution"] == "unexercised"


def test_strict_positive_rejects_wrong_supported_context():
    case = {
        "case_id": "wrong-context",
        "classification": "SUPPORTED_CONTRACT_POSITIVE",
        "path": "products_services",
        "expected": {
            "outcome": "published",
            "supported_fields": {"value": ["Group services"]},
            "required_fields": {"scope": "legal_entity"},
        },
        "rationale": "Group evidence is not legal-entity support.",
    }
    output = EvalOutput(
        outcome="published",
        profile={
            "products_services": {
                "state": "supported",
                "value": ["Group services"],
                "scope": "group",
            }
        },
    )
    scored = evaluate_strict_case(case, output)
    assert scored["correct"] is False
    assert scored["assessment"] == "failed"


def test_strict_positive_allows_only_explicitly_adjudicated_optional_date_clearance():
    case = {
        "case_id": "optional-event-date-cleared",
        "classification": "SUPPORTED_CONTRACT_POSITIVE",
        "path": "recent_developments.0",
        "expected": {
            "outcome": "published",
            "supported_fields": {
                "value": {
                    "title": "New facility",
                    "summary": "Example sp. z o.o. opened a new facility.",
                    "published_on": "2026-09-01",
                }
            },
            "required_fields": {"value": {"occurred_on": None}},
        },
        "rationale": (
            "The source supports the event and publication date but not an optional occurrence day."
        ),
    }
    output = EvalOutput(
        outcome="published",
        profile={
            "recent_developments": [
                {
                    "state": "supported",
                    "value": {
                        "title": "New facility",
                        "summary": "Example sp. z o.o. opened a new facility.",
                        "published_on": "2026-09-01",
                        "occurred_on": None,
                    },
                }
            ]
        },
    )
    scored = evaluate_strict_case(case, output)
    assert scored["correct"] is True
    assert scored["semantic_execution"] == "executed"


def test_provenance_invalid_citation_can_be_withheld_in_published_identity_profile():
    case = {
        "case_id": "bad-citation-withheld",
        "classification": "PROVENANCE_INVALID",
        "path": "products_services",
        "expected": {
            "outcome": "published",
            "state": "uncertain",
            "required_fields": {"value": None},
        },
        "rationale": "Identity may publish while a fact with a rejected citation is withheld.",
    }
    output = EvalOutput(
        outcome="published",
        profile={
            "identity": {"legal_name": {"state": "supported", "value": "Example sp. z o.o."}},
            "products_services": {"state": "uncertain", "value": None},
        },
    )
    scored = evaluate_strict_case(case, output)
    assert scored["correct"] is True
    assert scored["semantic_execution"] == "not_applicable"


def test_raw_value_lookup_returns_none_for_missing_paths():
    assert _raw_value_at({"draft": {"employees": []}}, "employees.2") is None
    assert _raw_value_at({"draft": {"employees": []}}, "employees.not_an_index") is None
    assert _raw_value_at({"draft": {}}, "employees.0") is None
