"""Explicit skill routing; inputs remain data and are never interpreted as instructions."""

from .core import InputError, object_input
from .governance import evaluation_plan, inventory, model_card, risk_register
from .html_review import review as html_review
from .planning import accessibility_report, audit_plan, control_map, design_system
from .sbom import review as sbom_review
from .security import api_review, code_review, llm_review, secrets, threat_model

TEXT_SKILLS = {
    "accessible-html-review",
    "aria-pattern-review",
    "keyboard-navigation-test",
    "accessible-forms-review",
    "secure-code-review",
    "secrets-exposure-audit",
}
JSON_HANDLERS = {
    "wcag-audit-planner": audit_plan,
    "accessible-design-system": design_system,
    "accessibility-report-generator": accessibility_report,
    "threat-model-generator": threat_model,
    "dependency-sbom-review": sbom_review,
    "api-security-review": api_review,
    "ai-system-inventory": inventory,
    "ai-risk-register": risk_register,
    "ai-model-card-generator": model_card,
    "ai-evaluation-planner": evaluation_plan,
    "llm-application-security-review": llm_review,
}
MAPPING_SKILLS = {
    "nist-csf-control-mapper",
    "secure-development-lifecycle",
    "ai-governance-controls-mapper",
}
SKILLS = tuple(sorted(TEXT_SKILLS | JSON_HANDLERS.keys() | MAPPING_SKILLS))


def run(skill, data):
    if skill not in SKILLS:
        raise InputError("Unknown skill")
    if skill in TEXT_SKILLS:
        if not isinstance(data, str):
            raise InputError("This skill needs UTF-8 text input")
        if skill == "secure-code-review":
            return code_review(data)
        if skill == "secrets-exposure-audit":
            return secrets(data)
        return html_review(data, skill)
    object_input(data)
    if skill in MAPPING_SKILLS:
        return control_map(data, skill)
    return JSON_HANDLERS[skill](data)
