"""Every skill gets a behavioral fixture assertion plus deterministic serialization checks."""

import json
from pathlib import Path

import pytest

from trust_skills.core import render
from trust_skills.engine import SKILLS, TEXT_SKILLS, run

ROOT = Path(__file__).resolve().parents[1]


def example(name):
    path = next((ROOT / "skills" / name / "examples").glob("input.*"))
    text = path.read_text(encoding="utf-8")
    return text if name in TEXT_SKILLS else json.loads(text)


@pytest.mark.parametrize("name", SKILLS)
def test_every_skill_example_is_deterministic(name):
    result = run(name, example(name))
    assert result == run(name, example(name))
    assert result["skill"] == name
    assert "human review required" in result["assessment"]
    assert result["summary"]["finding_count"] == len(result["findings"])
    assert json.loads(render(result, "json")) == result
    assert "Limitations" in render(result, "markdown")


# Expected outcomes represent the synthetic use cases, not scanner implementation details.
EXPECTED_CODES = {
    "accessible-html-review": {"HTML_LANG", "IMAGE_ALT", "CONTROL_NAME"},
    "aria-pattern-review": {"DIALOG_NAME", "ARIA_REFERENCE"},
    "keyboard-navigation-test": {"TABINDEX_POSITIVE", "CLICK_ONLY"},
    "accessible-forms-review": {"FORM_LABEL"},
    "accessible-design-system": {"CONTRAST_RATIO"},
    "secure-code-review": {"CODE_SHELL"},
    "secrets-exposure-audit": {"SECRET_PATTERN_1"},
    "api-security-review": {"API_HTTP", "API_ANONYMOUS", "API_OBJECT_AUTH_REVIEW"},
    "ai-system-inventory": {"INVENTORY_MONITORING"},
    "ai-risk-register": {"RISK_APPROVAL_GAP"},
    "ai-evaluation-planner": {"EVAL_THRESHOLD"},
    "nist-csf-control-mapper": {"FRAMEWORK_AREA_GAP"},
    "secure-development-lifecycle": {"FRAMEWORK_AREA_GAP"},
    "ai-governance-controls-mapper": {"FRAMEWORK_AREA_GAP"},
    "llm-application-security-review": {"LLM_EVIDENCE_GAP"},
}


@pytest.mark.parametrize("name,codes", EXPECTED_CODES.items())
def test_fixture_findings(name, codes):
    assert {x["code"] for x in run(name, example(name))["findings"]} == codes


def test_audit_plan_covers_critical_journey():
    artifact = run("wcag-audit-planner", example("wcag-audit-planner"))["artifacts"]
    assert artifact["target"] == "WCAG 2.2 AA"
    assert {x["id"] for x in artifact["sample"]} == {"home", "search"}


def test_report_counts_and_provenance():
    artifact = run("accessibility-report-generator", example("accessibility-report-generator"))[
        "artifacts"
    ]
    assert artifact["open_count"] == 1
    assert artifact["severity_counts"]["high"] == 1
    assert artifact["findings"][0]["method"] == "automated"


def test_threats_cross_boundary():
    threats = run("threat-model-generator", example("threat-model-generator"))["artifacts"][
        "threats"
    ]
    assert len(threats) == 4
    assert all(x["crosses_boundary"] and x["status"] == "hypothesis-needs-review" for x in threats)


def test_sbom_component_identity():
    result = run("dependency-sbom-review", example("dependency-sbom-review"))
    assert not result["findings"]
    assert result["artifacts"]["components"][0]["version"] == "1.0.0"


def test_model_card_preserves_evidence_without_inventing_measurements():
    result = run("ai-model-card-generator", example("ai-model-card-generator"))
    assert not result["findings"]
    assert "not a measured model" in result["artifacts"]["model_card"]["evaluations"][0]["result"]


def test_llm_evidence_stays_unverified():
    result = run("llm-application-security-review", example("llm-application-security-review"))
    assert len(result["findings"]) == 8
    assert len(result["artifacts"]["evidence"]) == 2
    assert all(x["status"] == "unverified" for x in result["artifacts"]["evidence"])


def test_evaluation_missing_observation_is_not_run():
    gates = run("ai-evaluation-planner", example("ai-evaluation-planner"))["artifacts"]["gates"]
    assert [x["state"] for x in gates] == ["threshold_missed", "not_run"]


@pytest.mark.parametrize(
    "name,count",
    [
        ("nist-csf-control-mapper", 5),
        ("secure-development-lifecycle", 3),
        ("ai-governance-controls-mapper", 3),
    ],
)
def test_mapping_missing_areas(name, count):
    result = run(name, example(name))
    assert len(result["findings"]) == count
    assert result["artifacts"]["mappings"][0]["mapping_status"] == "candidate-human-review"
