import json
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError

import pytest
from openpyxl import Workbook
from pydantic import TypeAdapter, ValidationError

from company_bi.cli import main
from company_bi.ingest import InputFileError, read_input, resolve_file
from company_bi.models import BatchResult, CompanyProfile
from company_bi.nip import InvalidNIP, validate_nip

RegistryStub = Callable[[dict[str, dict[str, Any] | bytes | Exception]], None]


@pytest.mark.parametrize("nip", ["5220003782", "5831014898"])
def test_known_valid_nip_checksums(nip: str) -> None:
    assert validate_nip(nip) == nip


@pytest.mark.parametrize(
    "value",
    [None, "", "123", "52200037822", "522000378X", "５２２０００３７８２", True, 5220003782.0],
)
def test_empty_malformed_and_wrong_length_nips_are_rejected(value: object) -> None:
    with pytest.raises(InvalidNIP):
        validate_nip(value)


@pytest.mark.parametrize("nip", ["5220003783", "1234567890"])
def test_invalid_checksum_including_modulo_ten_is_rejected(nip: str) -> None:
    with pytest.raises(InvalidNIP):
        validate_nip(nip)


def test_permitted_prefix_whitespace_and_hyphens_preserve_the_nip() -> None:
    assert validate_nip(" pl\u00a0522-000-37-82 ") == "5220003782"


def test_invalid_rows_do_not_attempt_registry_lookup(tmp_path: Path) -> None:
    path = tmp_path / "invalid.csv"
    path.write_text("nip\n123\n5220003783\n\n", encoding="utf-8")
    results = resolve_file(path)  # Any HTTP attempt is blocked by the autouse fixture.
    assert [
        (result.row_number, result.status, result.nip, result.error_code) for result in results
    ] == [
        (2, "invalid_input", None, "INVALID_NIP"),
        (3, "invalid_input", None, "INVALID_NIP"),
        (4, "invalid_input", None, "INVALID_NIP"),
    ]


def test_registry_identity_preserves_identifiers_address_and_name(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "input.csv"
    path.write_text("nip\n5220003782\n", encoding="utf-8")
    result = resolve_file(path)[0]
    assert result.status == "resolved"
    identity = result.identity
    assert identity is not None
    assert (identity.nip, identity.legal_name.value, identity.regon.value, identity.krs.value) == (
        "5220003782",
        '"ASSECO POLAND" SPÓŁKA AKCYJNA',
        "010334578",
        "0000033391",
    )
    assert identity.registered_address.value == "OLCHOWA 14, 35-322 RZESZÓW"
    assert (identity.registered_city.state, identity.registered_city.value) == ("unknown", None)
    assert (identity.website.state, identity.website.value) == ("unknown", None)
    assert (result.json_path, result.markdown_path) == (None, None)


def test_valid_nip_with_explicit_null_subject_is_unresolved(
    tmp_path: Path,
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"1234563218": {"result": {"subject": None}}})
    path = tmp_path / "missing.csv"
    path.write_text("nip\n1234563218\n", encoding="utf-8")
    result = resolve_file(path)[0]
    assert (result.status, result.nip, result.identity, result.error_code) == (
        "unresolved",
        "1234563218",
        None,
        "COMPANY_NOT_FOUND",
    )


def test_mixed_batch_continues_and_persists_all_row_outcomes(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject, "1234563218": {"result": {"subject": None}}})
    path = tmp_path / "mixed.csv"
    path.write_text("nip\nPL 522-000-37-82\n123\n1234563218\n", encoding="utf-8")
    output = tmp_path / "identity.json"
    assert main(["resolve", str(path), "--output", str(output)]) == 0
    results = TypeAdapter(list[BatchResult]).validate_json(output.read_bytes())
    assert [
        (row.row_number, row.input_nip, row.nip, row.status, row.error_code) for row in results
    ] == [
        (2, "PL 522-000-37-82", "5220003782", "resolved", None),
        (3, "123", None, "invalid_input", "INVALID_NIP"),
        (4, "1234563218", "1234563218", "unresolved", "COMPANY_NOT_FOUND"),
    ]


@pytest.mark.parametrize(
    ("failure", "error_code"),
    [
        (URLError("network unavailable"), "REGISTRY_NETWORK_ERROR"),
        (TimeoutError("registry timed out"), "REGISTRY_NETWORK_ERROR"),
        (
            HTTPError("https://wl-api.mf.gov.pl/", 503, "unavailable", None, None),
            "REGISTRY_HTTP_ERROR",
        ),
        (
            HTTPError("https://wl-api.mf.gov.pl/", 404, "not found", None, None),
            "REGISTRY_HTTP_ERROR",
        ),
        ({"result": {}}, "REGISTRY_INVALID_RESPONSE"),
        (b"<html>maintenance</html>", "REGISTRY_INVALID_RESPONSE"),
    ],
)
def test_registry_failures_are_not_company_not_found_and_do_not_abort_other_rows(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
    failure: dict[str, Any] | bytes | Exception,
    error_code: str,
) -> None:
    mock_registry({"5831014898": failure, "5220003782": registry_subject})
    path = tmp_path / "failure.csv"
    path.write_text("nip\n5831014898\n5220003782\n", encoding="utf-8")
    results = resolve_file(path)
    assert [(row.status, row.error_code) for row in results] == [
        ("failed", error_code),
        ("resolved", None),
    ]
    assert results[0].identity is None
    assert results[0].nip == "5831014898"


def test_returned_nip_mismatch_never_selects_another_company(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    registry_subject["result"]["subject"]["nip"] = "5831014898"
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "mismatch.csv"
    path.write_text("nip\n5220003782\n", encoding="utf-8")
    result = resolve_file(path)[0]
    assert (result.status, result.error_code, result.nip, result.identity) == (
        "failed",
        "REGISTRY_IDENTITY_MISMATCH",
        "5220003782",
        None,
    )


def test_missing_optional_registry_fields_stay_unknown_not_guessed(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    for key in ("regon", "krs", "workingAddress"):
        del registry_subject["result"]["subject"][key]
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "optional.csv"
    path.write_text("nip\n5220003782\n", encoding="utf-8")
    result = resolve_file(path)[0]
    assert result.status == "resolved"
    identity = result.identity
    assert identity is not None
    for fact in (identity.regon, identity.krs, identity.registered_address, identity.website):
        assert (fact.state, fact.value) == ("unknown", None)


def test_malformed_registry_identifier_is_not_padded_or_repaired(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    registry_subject["result"]["subject"]["krs"] = "33391"
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "identifier.csv"
    path.write_text("nip\n5220003782\n", encoding="utf-8")
    result = resolve_file(path)[0]
    assert (result.status, result.error_code, result.identity) == (
        "failed",
        "REGISTRY_INVALID_RESPONSE",
        None,
    )


def test_duplicate_formatted_nips_share_one_identity_snapshot(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "duplicates.csv"
    path.write_text("nip\n5220003782\nPL 522-000-37-82\n", encoding="utf-8")
    results = resolve_file(path)
    assert [row.status for row in results] == ["resolved", "resolved"]
    assert results[0].sources[0].source_id == results[1].sources[0].source_id
    assert [row.row_number for row in results] == [2, 3]


def test_xlsx_exact_integer_blank_and_formula_rows_do_not_abort_the_batch(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "input.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(["NIP", "ignored"])
    sheet.append([5220003782, None])
    sheet.append([None, "blank NIP"])
    sheet.append(["=5220003782", None])
    workbook.save(path)
    workbook.close()
    results = resolve_file(path)
    assert [(row.row_number, row.nip, row.status) for row in results] == [
        (2, "5220003782", "resolved"),
        (3, None, "invalid_input"),
        (4, None, "invalid_input"),
    ]


@pytest.mark.parametrize("headers", ["name", "nip,NIP", ""])
def test_missing_or_ambiguous_nip_header_is_a_file_error(tmp_path: Path, headers: str) -> None:
    path = tmp_path / "headers.csv"
    path.write_text(f"{headers}\n5220003782\n", encoding="utf-8")
    with pytest.raises(InputFileError):
        read_input(path)


def test_utf8_bom_and_ignored_columns_do_not_change_nip_selection(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "bom.csv"
    path.write_text("note, NIP \nexample,5220003782\n", encoding="utf-8-sig")
    result = resolve_file(path)[0]
    assert (result.nip, result.status) == ("5220003782", "resolved")


def test_cli_never_overwrites_its_input_file(tmp_path: Path) -> None:
    path = tmp_path / "same.csv"
    original = "nip\n5220003782\n"
    path.write_text(original, encoding="utf-8")
    assert main(["resolve", str(path), "--output", str(path)]) == 2
    assert path.read_text(encoding="utf-8") == original


def test_resolved_outcome_cannot_claim_unretrieved_identity_or_bi_reports(
    tmp_path: Path,
    registry_subject: dict[str, Any],
    mock_registry: RegistryStub,
) -> None:
    mock_registry({"5220003782": registry_subject})
    path = tmp_path / "row.csv"
    path.write_text("nip\n5220003782\n", encoding="utf-8")
    payload = resolve_file(path)[0].model_dump(mode="json")
    without_sources = {**payload, "sources": []}
    with pytest.raises(ValidationError):
        BatchResult.model_validate_json(json.dumps(without_sources))
    with_reports = {
        **payload,
        "json_path": "outputs/company.json",
        "markdown_path": "outputs/company.md",
    }
    with pytest.raises(ValidationError):
        BatchResult.model_validate_json(json.dumps(with_reports))


def test_complete_profile_requires_supported_city_or_address() -> None:
    path = Path(__file__).parents[1] / "examples/profiles/complete.json"
    payload = json.loads(path.read_text())
    payload["identity"]["registered_city"] = deepcopy(payload["identity"]["registered_address"])
    with pytest.raises(ValidationError):
        CompanyProfile.model_validate_json(json.dumps(payload))
