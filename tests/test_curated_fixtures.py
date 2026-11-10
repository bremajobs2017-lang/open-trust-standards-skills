import json
from pathlib import Path

import pytest

from trust_skills.engine import TEXT_SKILLS, run

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = json.loads((FIXTURES / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", MANIFEST["cases"], ids=lambda c: c["file"])
def test_separately_curated_expectations(case):
    text = (FIXTURES / case["file"]).read_text(encoding="utf-8")
    data = text if case["skill"] in TEXT_SKILLS else json.loads(text)
    result = run(case["skill"], data)
    assert {f["code"] for f in result["findings"]} == set(case["expected_codes"])
    assert len(result["findings"]) == case["finding_count"]
    if "expected_risk_order" in case:
        assert [r["id"] for r in result["artifacts"]["risks"]] == case["expected_risk_order"]
    assert "known_false_positives" in case and case["known_false_negatives"]


def test_injection_fixture_is_data_not_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    report = run(
        "accessible-html-review", (FIXTURES / "adversarial.html").read_text(encoding="utf-8")
    )
    assert not (tmp_path / "PWNED.txt").exists()
    assert "HOST_INJECTION_EXECUTED" not in json.dumps(report)
