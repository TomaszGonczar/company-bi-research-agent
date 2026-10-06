from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from company_bi.verification import write_verification

FIXTURE = Path(__file__).parents[1] / "examples/strict_contract/supported.json"
OUTPUTS = ("profile.json", "profile.md", "verification.json", "verification.md")


def input_copy(tmp_path: Path) -> Path:
    path = tmp_path / "input.json"
    shutil.copyfile(FIXTURE, path)
    return path


def test_independent_verification_outputs_are_written_and_usable(tmp_path: Path) -> None:
    source = input_copy(tmp_path)
    output = tmp_path / "out"

    write_verification(source, output)

    assert all((output / name).is_file() for name in OUTPUTS)
    profile = json.loads((output / "profile.json").read_text())
    verification = json.loads((output / "verification.json").read_text())
    assert profile["identity"]["legal_name"]["value"] == "Example sp. z o.o."
    assert profile["products_services"]["value"] == ["cloud services"]
    assert verification["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert "## Identity" in (output / "profile.md").read_text()
    assert "Offline verification" in (output / "verification.md").read_text()


def test_verification_markdown_flattens_external_inline_newlines(tmp_path: Path) -> None:
    source = input_copy(tmp_path)
    data = json.loads(source.read_text())
    data["sources"][1]["source"]["title"] = "Company page\r\n# Injected heading"
    data["draft"]["products_services"]["evidence"][0]["excerpt"] = (
        "Cloud services\r\n- Injected list item"
    )
    source.write_text(json.dumps(data))
    output = tmp_path / "out"

    write_verification(source, output)

    markdown = (output / "verification.md").read_text()
    assert "# Injected heading" not in markdown.splitlines()
    assert "- Injected list item" not in markdown.splitlines()
    assert r"Company page \# Injected heading" in markdown
    assert "Cloud services - Injected list item" in markdown


def test_profile_symlink_to_verification_destination_rejects_before_writes(tmp_path: Path) -> None:
    source = input_copy(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    (output / "profile.json").symlink_to("verification.json")
    (output / "verification.md").write_bytes(b"sentinel verification markdown")
    input_before = source.read_bytes()
    other_before = (output / "verification.md").read_bytes()

    with pytest.raises(ValueError, match="destinations must be distinct"):
        write_verification(source, output)

    assert source.read_bytes() == input_before
    assert (output / "verification.md").read_bytes() == other_before
    assert not (output / "profile.md").exists()
    assert not (output / "verification.json").exists()


def test_hardlinked_destinations_reject_before_writes(tmp_path: Path) -> None:
    source = input_copy(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    shared = output / "shared"
    shared.write_bytes(b"shared sentinel")
    (output / "profile.json").hardlink_to(shared)
    (output / "verification.json").hardlink_to(shared)
    input_before = source.read_bytes()
    shared_before = shared.read_bytes()

    with pytest.raises(ValueError, match="destinations must be distinct"):
        write_verification(source, output)

    assert source.read_bytes() == input_before
    assert shared.read_bytes() == shared_before
    assert not (output / "profile.md").exists()
    assert not (output / "verification.md").exists()


def test_input_symlink_destination_still_rejects_without_modification(tmp_path: Path) -> None:
    source = input_copy(tmp_path)
    output = tmp_path / "out"
    output.mkdir()
    (output / "profile.json").symlink_to(source)
    (output / "verification.md").write_bytes(b"sentinel")
    input_before = source.read_bytes()
    other_before = (output / "verification.md").read_bytes()

    with pytest.raises(ValueError, match="must not overwrite the input"):
        write_verification(source, output)

    assert source.read_bytes() == input_before
    assert (output / "verification.md").read_bytes() == other_before
    assert not (output / "profile.md").exists()
    assert not (output / "verification.json").exists()
