import io
import tarfile
import zipfile

import pytest

from scripts.install_smoke import clean_environment, inspect_artifacts


def test_smoke_drops_inherited_install_targets_and_import_paths(tmp_path):
    inherited = {
        "PATH": "synthetic-path",
        "PIP_TARGET": "unrelated-target",
        "PIP_INDEX_URL": "https://example.invalid",
        "PYTHONPATH": "unrelated-source",
        "PYTHONHOME": "unrelated-python",
        "VIRTUAL_ENV": "unrelated-venv",
        "PIP_USER": "1",
    }
    env = clean_environment(inherited, tmp_path)
    assert (
        not {"PIP_TARGET", "PIP_INDEX_URL", "PIP_USER", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
        & env.keys()
    )
    assert env["PIP_NO_INDEX"] == env["PIP_NO_CACHE_DIR"] == "1"
    assert env["PIP_FIND_LINKS"] == str(tmp_path)
    assert inherited["PIP_TARGET"] == "unrelated-target"


def test_install_smoke_rejects_archive_traversal_before_extraction(tmp_path):
    sdist = tmp_path / "bad.tar.gz"
    with tarfile.open(sdist, "w:gz") as archive:
        entry = tarfile.TarInfo("../synthetic-outside.txt")
        entry.size = 1
        archive.addfile(entry, io.BytesIO(b"x"))
    with pytest.raises(ValueError, match="unsafe"):
        inspect_artifacts(sdist, tmp_path / "unused.whl")
    assert not (tmp_path.parent / "synthetic-outside.txt").exists()


def test_install_smoke_checks_source_and_wheel_contract(tmp_path):
    sdist, wheel = tmp_path / "fixture.tar.gz", tmp_path / "fixture.whl"
    with tarfile.open(sdist, "w:gz") as archive:
        for name in [
            *(f"root/skills/skill-{i}/SKILL.md" for i in range(20)),
            "root/standards/registry.yaml",
            "root/scripts/install_smoke.py",
            "root/tests/fixtures/manifest.json",
        ]:
            entry = tarfile.TarInfo(name)
            archive.addfile(entry, io.BytesIO(b""))
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("trust_skills/cli.py", "")
    assert inspect_artifacts(sdist, wheel) == "root"
    with zipfile.ZipFile(wheel, "a") as archive:
        archive.writestr("skills/unexpected/SKILL.md", "")
    with pytest.raises(ValueError, match="CLI-only"):
        inspect_artifacts(sdist, wheel)
