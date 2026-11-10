import pytest

from trust_skills.core import InputError
from trust_skills.governance import risk_register
from trust_skills.html_review import review
from trust_skills.sbom import review as sbom_review


def test_html_defects_and_line_evidence():
    result = review('<html>\n<img src="synthetic.png"><button></button></html>')
    assert {x["code"] for x in result["findings"]} >= {
        "HTML_LANG",
        "HTML_TITLE",
        "IMAGE_ALT",
        "CONTROL_NAME",
    }
    assert next(x for x in result["findings"] if x["code"] == "IMAGE_ALT")["location"] == "line:2"


def test_html_decorative_alt_and_labelled_button():
    result = review(
        '<html lang="en"><title>Demo</title><img alt=""><button aria-label="Save"></button></html>'
    )
    assert not result["findings"]


@pytest.mark.parametrize("edition", ["1.5", "1.6", "1.7"])
def test_cyclonedx_quality(edition):
    result = sbom_review(
        {
            "bomFormat": "CycloneDX",
            "specVersion": edition,
            "components": [
                {
                    "name": "synthetic-widget",
                    "version": "1.0",
                    "bom-ref": "a",
                    "licenses": [{"license": {"id": "Apache-2.0"}}],
                }
            ],
        }
    )
    assert not result["findings"]
    assert len(result["artifacts"]["components"]) == 1


def test_spdx_missing_version_and_license():
    result = sbom_review(
        {
            "spdxVersion": "SPDX-2.3",
            "packages": [{"name": "synthetic-widget", "SPDXID": "SPDXRef-widget"}],
        }
    )
    assert len(result["findings"]) == 2


def test_sbom_unsupported_and_bad_shapes():
    for data in (
        {"spdxVersion": "SPDX-3.0"},
        {"bomFormat": "CycloneDX", "specVersion": "1.7", "components": {}},
    ):
        with pytest.raises(InputError):
            sbom_review(data)


def risk(**changes):
    return dict(
        id="R1",
        system_id="S1",
        scenario="Synthetic ranking error",
        harm="Unequal access",
        owner="Risk team",
        treatment="Review outcomes",
        status="open",
        review_date="2026-12-01",
        likelihood=3,
        impact=5,
        **changes,
    )


def test_risk_scoring_and_approval():
    row = risk()
    row.update(status="accepted", residual_likelihood=2, residual_impact=3)
    result = risk_register({"risks": [row]})
    assert result["artifacts"]["risks"][0]["score"] == 15
    assert result["artifacts"]["risks"][0]["residual_score"] == 6
    assert result["findings"][0]["code"] == "RISK_APPROVAL_GAP"


@pytest.mark.parametrize("value", [True, 0, 6, "3", 2.5])
def test_invalid_risk_rating(value):
    row = risk()
    row["likelihood"] = value
    with pytest.raises(InputError):
        risk_register({"risks": [row]})
