import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from trust_skills.cli import main
from trust_skills.core import InputError, render
from trust_skills.engine import run
from trust_skills.security import api_review, code_review, secrets


def codes(result):
    return {x["code"] for x in result["findings"]}


@pytest.mark.parametrize(
    "security,anonymous", [(None, False), ([], True), ([{}], True), ([{"bearer": []}, {}], True)]
)
def test_api_security_inheritance_and_overrides(security, anonymous):
    operation = {} if security is None else {"security": security}
    data = {
        "openapi": "3.1.1",
        "security": [{"bearer": []}],
        "components": {"securitySchemes": {"bearer": {"type": "http", "scheme": "bearer"}}},
        "paths": {"/widgets": {"get": operation}},
    }
    result = api_review(data)
    assert ("API_ANONYMOUS" in codes(result)) == anonymous


def test_api_unknown_scheme_and_refs():
    result = api_review(
        {"openapi": "3.0.3", "paths": {"/widgets": {"get": {"security": [{"missing": []}]}}}}
    )
    assert "API_UNKNOWN_SCHEME" in codes(result)


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"openapi": "2.0", "paths": {}},
        {"openapi": "3.1.1", "paths": {"/": {"get": {"security": {}}}}},
    ],
)
def test_api_invalid_inputs(data):
    with pytest.raises(InputError):
        api_review(data)


def test_ast_aliases_and_non_executable_strings():
    assert "CODE_DANGEROUS_CALL" in codes(
        code_review("from pickle import loads as unpack\nunpack(payload)")
    )
    assert not code_review("example = 'eval(user_input)'\n# exec(user_input)")["findings"]


def test_redaction_all_output_formats():
    sentinel = "SYNTHETIC_VALUE_MUST_NOT_ESCAPE"
    text = f'password = "{sentinel}"\n-----BEGIN PRIVATE KEY-----\n{sentinel}\n-----END PRIVATE KEY-----'
    result = secrets(text)
    assert len(result["findings"]) == 2
    for format_ in ("json", "markdown"):
        assert sentinel not in render(result, format_)
    report = {"skill": "demo", "artifacts": {"api_key": sentinel, "nested": [f"token={sentinel}"]}}
    assert sentinel not in render(report, "json")


def test_markdown_does_not_render_untrusted_html_or_links():
    rendered = render(
        {
            "artifacts": {
                "evidence": "<script>bad()</script> [open](https://example.invalid)\n# forged"
            }
        },
        "markdown",
    )
    assert "<script>" not in rendered
    assert "[open](" not in rendered
    assert "\n# forged" not in rendered


def test_cli_stdout_is_utf8_under_legacy_pipe_encoding():
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "trust_skills",
            "run",
            "ai-risk-register",
            "--input",
            str(root / "skills/ai-risk-register/examples/input.json"),
        ],
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "ascii", "PYTHONPATH": str(root / "src")},
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8")
    assert json.loads(completed.stdout.decode("utf-8"))["artifacts"]["risks"][0]["score"] == 15


def test_cli_exit_codes_and_output_no_overwrite(tmp_path, capsys):
    source = tmp_path / "input.html"
    source.write_text('<html><img src="demo.png"></html>', encoding="utf-8")
    assert (
        main(["run", "accessible-html-review", "--input", str(source), "--fail-on-findings"]) == 1
    )
    assert json.loads(capsys.readouterr().out)["findings"]
    output = tmp_path / "report.json"
    assert (
        main(["run", "accessible-html-review", "--input", str(source), "--output", str(output)])
        == 0
    )
    original = output.read_bytes()
    assert (
        main(["run", "accessible-html-review", "--input", str(source), "--output", str(output)])
        == 2
    )
    assert output.read_bytes() == original


def test_cli_errors_never_echo_input(tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_text('{"password": "SYNTHETIC_PRIVATE_VALUE", invalid}', encoding="utf-8")
    assert main(["run", "ai-risk-register", "--input", str(source)]) == 2
    output = capsys.readouterr()
    assert "SYNTHETIC_PRIVATE_VALUE" not in output.err + output.out


@pytest.mark.parametrize(
    "content", ['{"threshold": 1e999}', '{"threshold": NaN}', '{"threshold": 1, "threshold": 2}']
)
def test_cli_rejects_nonfinite_and_ambiguous_json(tmp_path, capsys, content):
    source = tmp_path / "input.json"
    source.write_text(content, encoding="utf-8")
    assert main(["run", "ai-evaluation-planner", "--input", str(source)]) == 2
    assert "Traceback" not in capsys.readouterr().err


@pytest.mark.parametrize(
    "name",
    [
        "ai-system-inventory",
        "ai-risk-register",
        "ai-model-card-generator",
        "ai-evaluation-planner",
        "nist-csf-control-mapper",
        "threat-model-generator",
        "accessible-design-system",
        "accessibility-report-generator",
    ],
)
def test_missing_required_records_rejected(name):
    with pytest.raises(InputError):
        run(name, {})
