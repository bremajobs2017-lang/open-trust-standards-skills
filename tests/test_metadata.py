from pathlib import Path

import pytest

from trust_skills.core import InputError
from trust_skills.engine import SKILLS
from trust_skills.metadata import SECTIONS, load_yaml, validate_library, validate_skill

ROOT = Path(__file__).resolve().parents[1]


def test_complete_library():
    assert validate_library(ROOT, SKILLS)["skills_validated"] == 20


@pytest.mark.parametrize("name", SKILLS)
def test_frontmatter_and_official_reference_links(name):
    front = validate_skill(ROOT / "skills" / name)
    assert front["name"] == name
    assert front["license"] == "Apache-2.0"
    assert front["metadata"]["standards"]


@pytest.mark.parametrize(
    "front",
    [
        "name: wrong-name\ndescription: Review things",
        'name: demo\ndescription: ""',
        "name: demo\ndescription: 12",
        "name: demo\ndescription: Review\nmetadata:\n  version: 1",
        "name: demo\nname: demo\ndescription: Review",
        "name: demo\ndescription: Review\nunknown: value",
    ],
)
def test_invalid_frontmatter(tmp_path, front):
    path = tmp_path / "demo"
    path.mkdir()
    body = "\n".join(f"## {section}\nConcrete guidance." for section in SECTIONS)
    (path / "SKILL.md").write_text(f"---\n{front}\n---\n# Demo\n{body}\n", encoding="utf-8")
    with pytest.raises(InputError):
        validate_skill(path)


def test_yaml_rejects_unsafe_tags_and_duplicates():
    for value in ('!!python/object/apply:os.system ["unused"]', "id: a\nid: b"):
        with pytest.raises(InputError):
            load_yaml(value)
