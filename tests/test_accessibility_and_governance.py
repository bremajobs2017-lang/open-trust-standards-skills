import copy

import pytest
from test_examples import example

from trust_skills.core import InputError
from trust_skills.engine import run
from trust_skills.html_review import review
from trust_skills.planning import luminance
from trust_skills.sbom import review as sbom_review


def test_wrapping_label_does_not_label_unrelated_field():
    result = review("<label>Name<input></label><input>", "accessible-forms-review")
    assert len(result["findings"]) == 1


def test_multiple_id_references_and_switch_mixed_state():
    result = review(
        '<span id="name">Demo</span><div role="switch" aria-checked="mixed" aria-labelledby="name missing"></div>',
        "aria-pattern-review",
    )
    assert {x["code"] for x in result["findings"]} == {"ARIA_STATE", "ARIA_REFERENCE"}


def test_duplicate_ids_reported_as_aria_issue_not_removed_wcag_parsing_criterion():
    result = review('<html lang="en"><title>Demo</title><b id="a"></b><i id="a"></i></html>')
    assert result["findings"][0]["code"] == "DUPLICATE_ID"
    assert result["findings"][0]["reference"] == "wai-aria12"


def test_empty_tabindex_is_a_finding():
    result = review("<div tabindex>Demo</div>", "keyboard-navigation-test")
    assert result["findings"][0]["code"] == "TABINDEX_INVALID"


def test_contrast_extremes_and_no_rounding_up():
    assert luminance("#000000") == 0
    assert luminance("#FFFFFF") == 1
    result = run("accessible-design-system", example("accessible-design-system"))
    pairs = result["artifacts"]["color_pairs"]
    assert pairs[0]["ratio"] < 4.5 and not pairs[0]["threshold_met"]
    assert pairs[1]["ratio"] == 21


def test_nested_sbom_graph_and_duplicates():
    data = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "metadata": {"component": {"bom-ref": "root"}},
        "components": [
            {
                "name": "a",
                "version": "1",
                "bom-ref": "a",
                "licenses": ["synthetic"],
                "components": [
                    {"name": "b", "version": "1", "bom-ref": "a", "licenses": ["synthetic"]}
                ],
            }
        ],
        "dependencies": [{"ref": "root", "dependsOn": ["a", "missing"]}],
    }
    result = sbom_review(data)
    assert len(result["artifacts"]["components"]) == 2
    assert {x["code"] for x in result["findings"]} == {"SBOM_DUPLICATE_ID", "SBOM_DANGLING_REF"}


def test_spdx_23_marker_against_231_docs_and_noassertion():
    result = sbom_review(
        {
            "spdxVersion": "SPDX-2.3",
            "packages": [
                {
                    "name": "demo",
                    "SPDXID": "SPDXRef-demo",
                    "versionInfo": "1.0",
                    "licenseConcluded": "NOASSERTION",
                }
            ],
        }
    )
    assert len(result["findings"]) == 1


@pytest.mark.parametrize("mutation", ["duplicate", "date", "residual"])
def test_risk_register_structural_errors(mutation):
    data = copy.deepcopy(example("ai-risk-register"))
    if mutation == "duplicate":
        data["risks"] *= 2
    elif mutation == "date":
        data["risks"][0]["review_date"] = "2026-02-30"
    else:
        del data["risks"][0]["residual_impact"]
    with pytest.raises(InputError):
        run("ai-risk-register", data)


def test_inventory_rejects_duplicates_and_invalid_lifecycle():
    data = example("ai-system-inventory")
    data["systems"][0]["lifecycle"] = "certified"
    with pytest.raises(InputError):
        run("ai-system-inventory", data)
    data["systems"][0]["lifecycle"] = "deployed"
    data["systems"] *= 2
    with pytest.raises(InputError):
        run("ai-system-inventory", data)


def test_report_human_method_requires_reviewer():
    data = example("accessibility-report-generator")
    data["findings"][0]["method"] = "human"
    with pytest.raises(InputError):
        run("accessibility-report-generator", data)


@pytest.mark.parametrize("value", [float("inf"), float("nan"), True])
def test_nonfinite_metrics_rejected(value):
    data = example("ai-evaluation-planner")
    data["metrics"][0]["threshold"] = value
    with pytest.raises(InputError):
        run("ai-evaluation-planner", data)


def test_local_metric_threshold_equality():
    data = example("ai-evaluation-planner")
    for row in data["metrics"]:
        row["observed"] = row["threshold"]
    assert all(
        g["state"] == "threshold_met"
        for g in run("ai-evaluation-planner", data)["artifacts"]["gates"]
    )
