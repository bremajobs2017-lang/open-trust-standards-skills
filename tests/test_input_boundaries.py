import json
from pathlib import Path

import pytest
from test_examples import example

from trust_skills.core import InputError
from trust_skills.engine import run
from trust_skills.metadata import SECTIONS, validate_skill
from trust_skills.sbom import review


@pytest.mark.parametrize("value", [[], {}, None, True, 7])
@pytest.mark.parametrize(
    "skill,key", [("wcag-audit-planner", "level"), ("dependency-sbom-review", "specVersion")]
)
def test_malformed_enum_types_fail_cleanly(skill, key, value):
    data = example(skill)
    data[key] = value
    with pytest.raises(InputError):
        run(skill, data)


def test_spdx_patch_documentation_version_is_not_a_version_marker():
    with pytest.raises(InputError):
        review({"spdxVersion": "SPDX-2.3.1", "packages": []})


def test_complete_spdx_fixture():
    path = (
        Path(__file__).resolve().parents[1]
        / "skills/dependency-sbom-review/examples/input-spdx.json"
    )
    result = review(json.loads(path.read_text(encoding="utf-8")))
    assert result["artifacts"]["format"] == "SPDX"
    assert not result["findings"]


def test_valid_frontmatter_can_contain_dashes(tmp_path):
    skill = tmp_path / "demo"
    skill.mkdir()
    body = "\n".join(f"## {section}\nSpecific instructions." for section in SECTIONS)
    (skill / "SKILL.md").write_text(
        '---\nname: demo\ndescription: "Review a literal---separator safely"\n---\n' + body,
        encoding="utf-8",
    )
    assert validate_skill(skill)["name"] == "demo"


def test_whitespace_approval_is_still_a_gap():
    data = example("ai-risk-register")
    data["risks"][0]["approval_evidence"] = "   "
    assert run("ai-risk-register", data)["findings"][0]["code"] == "RISK_APPROVAL_GAP"


def test_basic_iso_date_format_is_rejected():
    data = example("ai-risk-register")
    data["risks"][0]["review_date"] = "20261201"
    with pytest.raises(InputError):
        run("ai-risk-register", data)
