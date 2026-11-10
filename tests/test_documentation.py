import re
from pathlib import Path

from trust_skills.metadata import load_yaml

ROOT = Path(__file__).resolve().parents[1]


def test_documentation_local_links_exist():
    paths = [*ROOT.glob("*.md"), *(ROOT / "docs").rglob("*.md"), *(ROOT / "skills").rglob("*.md")]
    for path in paths:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            assert (path.parent / target.split("#", 1)[0]).exists(), (path, target)


def test_every_skill_official_reference_matches_registry():
    registry = load_yaml((ROOT / "standards/registry.yaml").read_text(encoding="utf-8"))
    urls = {source["id"]: source["official_url"] for source in registry["sources"]}
    for path in (ROOT / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        front = load_yaml(text.split("---", 2)[1])
        for id_ in front["metadata"]["standards"].split(","):
            assert urls[id_] in text, (path, id_)
