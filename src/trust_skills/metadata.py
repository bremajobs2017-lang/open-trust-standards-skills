"""Agent Skills format checks plus this library's stricter content contract."""

import re
from pathlib import Path

import yaml

from .core import InputError, read_text

NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SECTIONS = (
    "Activation criteria",
    "Inputs",
    "Procedure",
    "Outputs",
    "Examples",
    "Validation",
    "Limitations",
    "Official references",
)


class UniqueLoader(yaml.SafeLoader):
    """Safe YAML with duplicate mapping keys rejected."""


def mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise InputError("YAML keys must be unique strings")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def load_yaml(text):
    try:
        return yaml.load(text, Loader=UniqueLoader)
    except yaml.YAMLError as exc:
        raise InputError("Invalid YAML; check syntax and supported safe types") from exc


def validate_skill(path: Path):
    text = read_text(path / "SKILL.md")
    match = re.fullmatch(r"---\n(.*?)\n---(?:\n|$)(.*)", text, re.DOTALL)
    if not match:
        raise InputError("SKILL.md must begin with YAML frontmatter delimited by ---")
    front = load_yaml(match[1])
    body = match[2]
    if not isinstance(front, dict) or set(front) - FIELDS:
        raise InputError("Frontmatter contains unsupported fields")
    name, description = front.get("name"), front.get("description")
    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 64
        or not NAME.fullmatch(name)
        or name != path.name
    ):
        raise InputError(
            "Skill name must match directory and use 1–64 lowercase letters/digits with single hyphens"
        )
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise InputError("description must be nonempty text of at most 1024 characters")
    for field in ("license", "compatibility", "allowed-tools"):
        if field in front and (not isinstance(front[field], str) or not front[field].strip()):
            raise InputError(f"{field} must be nonempty text")
    if len(front.get("compatibility", "")) > 500:
        raise InputError("compatibility is limited to 500 characters")
    if "metadata" in front:
        metadata = front["metadata"]
        if not isinstance(metadata, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
        ):
            raise InputError("metadata must map strings to strings")
    for section in SECTIONS:
        if not re.search(rf"^## {re.escape(section)}\s*$", body, re.MULTILINE):
            raise InputError(f"Missing library-required section: {section}")
    if len(body.split()) > 5000:
        raise InputError("Library entrypoints should stay below 5000 words")
    return front


def validate_library(root: Path, expected):
    skills = root / "skills"
    if not skills.is_dir() or not (root / "standards/registry.yaml").is_file():
        raise InputError(
            "Source validation requires a checkout or extracted source distribution containing skills/ and standards/"
        )
    actual = {p.name for p in skills.iterdir() if p.is_dir()}
    if actual != set(expected):
        raise InputError("Skill directories do not match the 20-skill CLI catalog")
    registry = load_yaml(read_text(root / "standards" / "registry.yaml"))
    if not isinstance(registry, dict) or not isinstance(registry.get("sources"), list):
        raise InputError("Standards registry must contain sources")
    ids = set()
    for source in registry["sources"]:
        if not isinstance(source, dict):
            raise InputError("Registry source must be an object")
        for key in (
            "id",
            "title",
            "edition",
            "official_url",
            "verification_status",
            "verified_on",
            "verification_scope",
        ):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise InputError(f"Registry requires text field {key}")
        if source["id"] in ids or not source["official_url"].startswith("https://"):
            raise InputError("Registry IDs must be unique and URLs must use HTTPS")
        ids.add(source["id"])
    for name in sorted(actual):
        if not (skills / name).resolve().is_relative_to(skills.resolve()):
            raise InputError("Skill directory escapes the source library")
        front = validate_skill(skills / name)
        refs = front.get("metadata", {}).get("standards", "").split(",")
        if not refs or any(ref not in ids for ref in refs):
            raise InputError(f"Unknown standards registry ID in {name}")
        if not any((skills / name / "examples").glob("input.*")):
            raise InputError(f"Missing executable example for {name}")
    return {"skills_validated": len(actual), "sources_registered": len(ids)}
