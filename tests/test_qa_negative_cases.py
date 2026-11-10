import json

import pytest
from test_examples import example

from scripts.install_smoke import safe_member
from trust_skills.cli import main
from trust_skills.core import InputError, render, sanitize
from trust_skills.engine import run


@pytest.mark.parametrize(
    "skill,collection",
    [
        ("ai-system-inventory", "systems"),
        ("ai-risk-register", "risks"),
        ("ai-evaluation-planner", "metrics"),
        ("threat-model-generator", "assets"),
        ("wcag-audit-planner", "pages"),
        ("accessibility-report-generator", "findings"),
        ("nist-csf-control-mapper", "controls"),
    ],
)
def test_duplicate_ids_across_record_tools(skill, collection):
    data = example(skill)
    data[collection].append(data[collection][0].copy())
    with pytest.raises(InputError):
        run(skill, data)


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff\xfe\xff",
        b"[1, 2]",
        b"null",
        b'{"risks": [null]}',
        b'{"risks": []}',
        b'{"risks": "not-a-list"}',
    ],
)
def test_cli_malformed_inputs_have_no_traceback(tmp_path, capsys, payload):
    path = tmp_path / "synthetic.json"
    path.write_bytes(payload)
    assert main(["run", "ai-risk-register", "--input", str(path)]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_unicode_roundtrip_and_terminal_controls_are_visible():
    text = "é e\u0301 日本語 👩🏽‍💻 \u202e \x1b[31m"
    data = example("ai-risk-register")
    data["risks"][0]["scenario"] = text
    result = run("ai-risk-register", data)
    assert "日本語 👩🏽‍💻" in result["artifacts"]["risks"][0]["scenario"]
    for format_ in ("json", "markdown"):
        output = render(result, format_)
        assert "\u202e" not in output and "\x1b" not in output
    assert "\\u202e" in sanitize(text)


@pytest.mark.parametrize(
    "material",
    [
        'api_key = "SYNTHETIC phrase with spaces"',
        "password = 'SYNTHETIC phrase with spaces'",
        "Bearer SYNTHETIC_ONLY_NOT_A_TOKEN",
        "https://synthetic:SYNTHETIC_ONLY@example.invalid/path",
        "-----BEGIN PRIVATE KEY-----\nSYNTHETIC ONLY\n-----END PRIVATE KEY-----",
    ],
)
def test_credential_material_never_survives_rendering(material):
    for format_ in ("json", "markdown"):
        result = {"skill": "synthetic", "artifacts": {"evidence": material}}
        output = render(result, format_)
        assert "SYNTHETIC" not in output
        assert "REDACTED" in output


def test_workspace_boundary_rejects_input_and_output_traversal(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "synthetic-outside.html"
    outside.write_text('<html lang="en"><title>Synthetic</title></html>', encoding="utf-8")
    inside = root / "input.html"
    inside.write_bytes(outside.read_bytes())
    traversal = root / ".." / outside.name
    assert (
        main(
            [
                "run",
                "accessible-html-review",
                "--input",
                str(traversal),
                "--workspace-root",
                str(root),
            ]
        )
        == 2
    )
    output = root / ".." / "should-not-exist.json"
    assert (
        main(
            [
                "run",
                "accessible-html-review",
                "--input",
                str(inside),
                "--output",
                str(output),
                "--workspace-root",
                str(root),
            ]
        )
        == 2
    )
    assert not output.exists()


def test_input_id_traversal_is_data_not_a_file_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = example("ai-risk-register")
    data["risks"][0]["id"] = "../../DO_NOT_CREATE.json"
    run("ai-risk-register", data)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "name", ["../../escape", "/absolute", "C:/absolute", "x\\..\\escape", "x/../escape"]
)
def test_archive_path_traversal_rejected(name):
    assert not safe_member(name)


def test_output_refuses_input_overwrite_and_existing_unicode_file(tmp_path):
    source = tmp_path / "入力.html"
    source.write_text('<img src="synthetic.png">', encoding="utf-8")
    initial = source.read_bytes()
    args = ["run", "accessible-html-review", "--input", str(source)]
    assert main([*args, "--output", str(source)]) == 2
    assert source.read_bytes() == initial
    output = tmp_path / "結果.json"
    assert main([*args, "--output", str(output)]) == 0
    before = output.read_bytes()
    assert main([*args, "--output", str(output)]) == 2
    assert output.read_bytes() == before


def test_registry_boundary_rejects_escape_before_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "trust_skills.cli.verify_registry", lambda *a, **k: pytest.fail("should not fetch")
    )
    assert (
        main(
            [
                "registry",
                "--registry",
                str(tmp_path / ".." / "outside.yaml"),
                "--workspace-root",
                str(tmp_path),
                "--live",
            ]
        )
        == 2
    )


def test_oversized_and_deep_inputs_fail_cleanly(tmp_path):
    path = tmp_path / "synthetic.json"
    with path.open("wb") as stream:
        stream.truncate(5_000_001)
    assert main(["run", "ai-risk-register", "--input", str(path)]) == 2
    path.write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
    assert main(["run", "ai-risk-register", "--input", str(path)]) == 2


def test_no_external_openapi_reference_is_read(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    secret = tmp_path / "SYNTHETIC_NOT_READ.json"
    secret.write_text(json.dumps({"marker": "DO_NOT_ECHO_MARKER"}), encoding="utf-8")
    result = run(
        "api-security-review", {"openapi": "3.1.1", "paths": {"/qa": {"$ref": str(secret)}}}
    )
    assert "DO_NOT_ECHO_MARKER" not in json.dumps(result)
    assert result["findings"][0]["code"] == "API_UNRESOLVED_REF"
