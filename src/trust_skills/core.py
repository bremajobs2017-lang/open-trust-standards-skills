"""Shared input validation, redaction, and report serialization."""

import json
import re
from pathlib import Path

MAX_BYTES = 5_000_000
SECRET_PATTERNS = (
    re.compile(
        r"""(?i)\b(?:password|passwd|api[_-]?key|secret|token)\b['"]?\s*[:=]\s*(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s'",;<>]+)"""
    ),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b"),
    re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?(?:-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|$)"
    ),
    re.compile(r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9._~+/-]+=*"),
)


class InputError(ValueError):
    """Invalid or unsupported local input."""


def read_text(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise InputError("Input must be a local file no larger than 5 MB")
    return path.read_text(encoding="utf-8-sig")


def within_root(path: Path, root: Path | None) -> Path:
    if root is not None and not path.resolve().is_relative_to(root.resolve()):
        raise InputError("Path escapes the explicitly selected workspace root")
    return path


def object_input(value, label="input") -> dict:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    return value


def records(data: dict, key: str) -> list[dict]:
    value = data.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(x, dict) for x in value):
        raise InputError(f"{key} must be a nonempty array of objects")
    return value


def required(item: dict, keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if not isinstance(item.get(key), str) or not item[key].strip()]
    if missing:
        raise InputError(f"{label}: required nonempty text fields: {', '.join(missing)}")


def unique(items: list[dict], key="id") -> None:
    ids = [x.get(key) for x in items]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(set(ids)) != len(ids):
        raise InputError(f"{key} values must be nonempty unique strings")


def redact(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    # URL credentials and common sensitive query parameters.
    text = re.sub(r"(?i)(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", text)
    return "".join(
        f"\\u{ord(c):04x}"
        if (ord(c) < 32 and c not in "\n\t")
        or ord(c) == 127
        or 0x202A <= ord(c) <= 0x202E
        or 0x2066 <= ord(c) <= 0x2069
        else c
        for c in text
    )


def sanitize(value):
    if isinstance(value, dict):
        return {
            redact(str(k)): "[REDACTED]"
            if re.fullmatch(r"(?i)(password|passwd|api[_-]?key|secret|token|authorization)", str(k))
            else sanitize(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return redact(value) if isinstance(value, str) else value


def finding(code, location, message, reference, severity="review") -> dict:
    return dict(
        code=code, location=location, message=message, reference=reference, severity=severity
    )


def report(skill, findings=None, artifacts=None, limitations=None) -> dict:
    findings = findings or []
    return sanitize(
        {
            "schema_version": "1.0",
            "skill": skill,
            "assessment": "automated-assistance; human review required",
            "summary": {"finding_count": len(findings)},
            "findings": findings,
            "artifacts": artifacts or {},
            "limitations": limitations
            or ["No certification or conformance conclusion is produced."],
        }
    )


def render(result: dict, format_: str) -> str:
    result = sanitize(result)
    if format_ == "json":
        return json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"

    def safe(value):
        # Render untrusted content as text, not active HTML, links, or Markdown headings.
        text = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", text).replace("\n", " ")

    lines = [f"# {safe(result.get('skill', 'Review'))}", "", safe(result.get("assessment", "")), ""]
    if result.get("findings"):
        lines += [
            "## Findings",
            "",
            "| Code | Severity | Location | Reference | Review action |",
            "| --- | --- | --- | --- | --- |",
        ]
        for item in result["findings"]:
            lines.append(
                "| "
                + " | ".join(
                    safe(item.get(k, ""))
                    for k in ("code", "severity", "location", "reference", "message")
                )
                + " |"
            )
    lines += ["", "## Artifacts", ""]
    for key, value in result.get("artifacts", {}).items():
        lines += [f"### {safe(key)}", ""]
        if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
            columns = list(dict.fromkeys(k for row in value for k in row))
            lines.append("| " + " | ".join(safe(k) for k in columns) + " |")
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
            lines += [
                "| " + " | ".join(safe(row.get(k, "")) for k in columns) + " |" for row in value
            ]
        elif isinstance(value, dict):
            lines += [f"- {safe(k)}: {safe(v)}" for k, v in value.items()]
        elif isinstance(value, list):
            lines += [f"- {safe(v)}" for v in value]
        else:
            lines += [safe(value)]
        lines.append("")
    lines += ["", "## Limitations", ""]
    lines += [f"- {safe(x)}" for x in result.get("limitations", [])]
    return "\n".join(lines) + "\n"
