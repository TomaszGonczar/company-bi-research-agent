import hashlib
import json
import os
from pathlib import Path

import pytest

from company_bi import dossier
from company_bi.cli import main
from company_bi.models import CompanyProfile

INPUT = Path("examples/strict_contract/supported.json")


def check_bundle(path):
    manifest = json.loads((path / "dossier-manifest.json").read_bytes())
    assert manifest["bundle_status"] == "complete"
    assert set(p.name for p in path.iterdir()) == {*manifest["artifacts"], "dossier-manifest.json"}
    for name, digest in manifest["artifacts"].items():
        assert hashlib.sha256((path / name).read_bytes()).hexdigest() == digest
    return manifest


@pytest.mark.parametrize(
    "case,exit_code,status",
    [
        ("examples/strict_contract/supported.json", 0, "partial"),
        ("examples/strict_contract/out_of_contract.json", 0, "partial"),
        ("examples/strict_contract/unsafe.json", 0, "partial"),
        ("examples/dossier/rich.json", 0, "complete"),
        ("examples/dossier/failed-run.json", 1, None),
    ],
)
def test_real_offline_cli_bundle_states(tmp_path, case, exit_code, status):
    output = tmp_path / "bundle"
    original = Path(case).read_bytes()
    assert main(["dossier", case, "--output-dir", str(output), "--synthetic"]) == exit_code
    manifest = check_bundle(output)
    assert manifest["input_sha256"] == hashlib.sha256(original).hexdigest()
    assert manifest["profile_status"] == status
    assert manifest["synthetic"] is True
    assert Path(case).read_bytes() == original
    if status:
        profile = CompanyProfile.model_validate_json((output / "profile.json").read_bytes())
        assert profile.status == status
        assert manifest["profile_schema_version"] == "0.1"
        assert (output / f"{profile.identity.nip}.dossier.pdf").read_bytes().startswith(b"%PDF-")
    else:
        assert manifest["publication_status"] == "not_published"
        assert set(manifest["artifacts"]) == {"verification.json", "verification.md"}
        assert manifest["profile_schema_version"] is None


@pytest.mark.parametrize("invalid", ["identity", "json", "profile"])
def test_invalid_input_cannot_publish(tmp_path, capsys, invalid):
    path = tmp_path / "invalid.json"
    if invalid == "identity":
        path.write_bytes(Path("examples/strict_contract/identity_invalid.json").read_bytes())
    elif invalid == "json":
        path.write_text('{"secret":"DO_NOT_LOG"')
    else:
        path.write_text('{"schema_version":"0.1"}')
    output = tmp_path / "bundle"
    assert main(["dossier", str(path), "--output-dir", str(output)]) == 2
    assert not output.exists()
    error = capsys.readouterr().err
    assert error.startswith("DOSSIER_ERROR:") and len(error) < 600
    assert "DO_NOT_LOG" not in error


@pytest.mark.parametrize("collision", ["directory", "dangling", "symlink", "hardlink", "input"])
def test_destinations_are_never_overwritten(tmp_path, collision):
    path = tmp_path / "input.json"
    path.write_bytes(INPUT.read_bytes())
    original = path.read_bytes()
    output = tmp_path / "bundle"
    if collision == "directory":
        output.mkdir()
        (output / "operator.txt").write_text("preserve")
    elif collision == "dangling":
        output.symlink_to(tmp_path / "absent")
    elif collision == "symlink":
        output.symlink_to(path)
    elif collision == "hardlink":
        os.link(path, output)
    else:
        output = path
    assert main(["dossier", str(path), "--output-dir", str(output)]) == 2
    assert path.read_bytes() == original
    assert os.path.lexists(output)
    if collision == "directory":
        assert (output / "operator.txt").read_text() == "preserve"


@pytest.mark.parametrize("alias", ["symlink", "hardlink", "parent", "traversal"])
def test_alias_inputs_and_parent_paths_are_refused(tmp_path, alias):
    original = tmp_path / "original.json"
    original.write_bytes(INPUT.read_bytes())
    path, output = original, tmp_path / "bundle"
    if alias in {"symlink", "hardlink"}:
        path = tmp_path / "input.json"
        if alias == "symlink":
            path.symlink_to(original)
        else:
            os.link(original, path)
    elif alias == "parent":
        parent = tmp_path / "linked-parent"
        parent.symlink_to(tmp_path, target_is_directory=True)
        output = parent / "bundle"
    else:
        output = tmp_path / "unused" / ".." / "bundle"
    assert main(["dossier", str(path), "--output-dir", str(output)]) == 2
    assert original.read_bytes() == INPUT.read_bytes()
    assert not (tmp_path / "bundle").exists()


def test_collision_immediately_before_reservation(tmp_path, monkeypatch):
    reserve = dossier._reserve_directory
    output = tmp_path / "bundle"

    def collide(parent_fd, name):
        output.mkdir()
        (output / "operator.txt").write_text("external winner")
        return reserve(parent_fd, name)

    monkeypatch.setattr(dossier, "_reserve_directory", collide)
    with pytest.raises(FileExistsError):
        dossier.write_dossier(INPUT, output)
    assert (output / "operator.txt").read_text() == "external winner"
    assert not (output / "dossier-manifest.json").exists()
    assert not list(tmp_path.glob(".dossier-*"))


@pytest.mark.parametrize("failure", ["render", "copy", "manifest", "tamper"])
def test_failed_publication_has_no_success_bundle(tmp_path, monkeypatch, failure):
    output = tmp_path / "bundle"
    original = INPUT.read_bytes()
    if failure == "render":

        def fail_render(view, path):
            path.write_bytes(b"%PDF-partial")
            raise RuntimeError("SECRET_SOURCE_CONTENT")

        monkeypatch.setattr(dossier, "render_dossier_pdf", fail_render)
    else:
        write = dossier._exclusive_write

        def fail_write(fd, name, data, owned):
            write(fd, name, data, owned)
            if failure == "copy" and name == "profile.json":
                raise OSError("controlled mid-copy failure")
            if failure == "manifest" and name == "dossier-manifest.json":
                raise OSError("controlled manifest failure")
            if failure == "tamper" and name == "verification.md":
                (output / "profile.json").write_bytes(b"altered")

        monkeypatch.setattr(dossier, "_exclusive_write", fail_write)
    assert main(["dossier", str(INPUT), "--output-dir", str(output)]) == 2
    assert not output.exists()
    assert INPUT.read_bytes() == original
    assert not list(tmp_path.glob(".dossier-*"))


def test_replaced_directory_survives_failed_publication(tmp_path, monkeypatch, capsys):
    output, moved = tmp_path / "bundle", tmp_path / "moved-operation"
    write = dossier._exclusive_write
    replaced = False

    def replace_directory(fd, name, data, owned):
        nonlocal replaced
        write(fd, name, data, owned)
        if not replaced:
            replaced = True
            output.rename(moved)
            output.mkdir()
            (output / "operator.txt").write_text("preserve replacement")

    monkeypatch.setattr(dossier, "_exclusive_write", replace_directory)
    assert main(["dossier", str(INPUT), "--output-dir", str(output)]) == 2
    assert (output / "operator.txt").read_text() == "preserve replacement"
    assert not (output / "dossier-manifest.json").exists()
    assert not (moved / "dossier-manifest.json").exists()
    assert len(list(tmp_path.glob(".dossier-*"))) == 1  # Recovery evidence intentionally retained.
    assert "staging retained" in capsys.readouterr().err


def test_repeat_never_overwrites_and_fresh_bundle_is_identical(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    dossier.write_dossier(INPUT, first, synthetic=True)
    before = {p.name: p.read_bytes() for p in first.iterdir()}
    with pytest.raises(ValueError):
        dossier.write_dossier(INPUT, first, synthetic=True)
    dossier.write_dossier(INPUT, second, synthetic=True)
    assert before == {p.name: p.read_bytes() for p in first.iterdir()}
    assert before == {p.name: p.read_bytes() for p in second.iterdir()}


@pytest.mark.parametrize("late_failure", ["manifest_tamper", "parent_replaced", "stage_cleanup"])
def test_completion_cannot_outlive_late_failure(tmp_path, monkeypatch, late_failure):
    parent = tmp_path / "parent"
    parent.mkdir()
    output = parent / "bundle"
    moved = tmp_path / "moved-parent"
    write = dossier._exclusive_write

    def late_write(fd, name, data, owned):
        write(fd, name, data, owned)
        if name == "dossier-manifest.json":
            if late_failure == "manifest_tamper":
                (output / "profile.json").write_text("external mutation")
            elif late_failure == "parent_replaced":
                parent.rename(moved)
                parent.mkdir()
                (parent / "operator.txt").write_text("preserve")

    def fail_cleanup(*args, **kwargs):
        raise OSError("controlled cleanup failure")

    monkeypatch.setattr(dossier, "_exclusive_write", late_write)
    if late_failure == "stage_cleanup":
        monkeypatch.setattr(dossier.shutil, "rmtree", fail_cleanup)
    assert main(["dossier", str(INPUT), "--output-dir", str(output)]) == 2
    assert not (output / "dossier-manifest.json").exists()
    assert not (moved / "bundle" / "dossier-manifest.json").exists()
    if late_failure == "parent_replaced":
        assert (parent / "operator.txt").read_text() == "preserve"
