"""Check the real workflow parses before depending on hosted execution."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow():
    # BaseLoader keeps GitHub's YAML 1.2 `on` key as a string.
    return yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )


def test_workflow_parses_and_includes_offline_artifact_installation():
    data = workflow()
    assert {"push", "pull_request", "workflow_dispatch"} <= data["on"].keys()
    steps = data["jobs"]["checks"]["steps"]
    assert any("--only-binary=:all:" in step.get("run", "") for step in steps)
    assert any("scripts/install_smoke.py" in step.get("run", "") for step in steps)


def test_workflow_actions_are_immutable_and_permissions_read_only():
    data = workflow()
    assert data["permissions"] == {"contents": "read"}
    for step in data["jobs"]["checks"]["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[a-zA-Z0-9_./-]+@[0-9a-f]{40}", step["uses"])
