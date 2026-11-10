"""Offline security review helpers. Never execute input code or call target APIs."""

import ast
import re

from .core import (
    SECRET_PATTERNS,
    InputError,
    finding,
    object_input,
    records,
    report,
    required,
    unique,
)


def secrets(text):
    out = []
    for index, pattern in enumerate(SECRET_PATTERNS):
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            out.append(
                finding(
                    f"SECRET_PATTERN_{index + 1}",
                    f"line:{line}",
                    "Potential credential material [REDACTED]; verify privately, revoke if live, and remove through approved history cleanup.",
                    "ssdf11",
                    "high",
                )
            )
    return report(
        "secrets-exposure-audit",
        out,
        {"lines_reviewed": len(text.splitlines())},
        [
            "Patterns are incomplete and produce false positives, including synthetic examples.",
            "No raw values, snippets, hashes, file paths, Git history, or environment variables are emitted; no credential validity is tested.",
        ],
    )


def code_review(text):
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise InputError(
            f"Python syntax error at line {exc.lineno}; source is not echoed"
        ) from None
    aliases, out = {}, []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                aliases[name.asname or name.name] = name.name
        if isinstance(node, ast.ImportFrom) and node.module:
            for name in node.names:
                aliases[name.asname or name.name] = f"{node.module}.{name.name}"

    def symbol(node):
        if isinstance(node, ast.Name):
            return aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            return f"{symbol(node.value)}.{node.attr}"
        return ""

    dangerous = {
        "eval",
        "exec",
        "builtins.eval",
        "builtins.exec",
        "pickle.loads",
        "pickle.load",
        "os.system",
        "yaml.load",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = symbol(node.func)
        if name in dangerous:
            out.append(
                finding(
                    "CODE_DANGEROUS_CALL",
                    f"line:{node.lineno}",
                    f"Review {name} for untrusted input and safer alternatives.",
                    "owasp-asvs",
                    "high",
                )
            )
        if name.startswith("subprocess.") and any(
            k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True
            for k in node.keywords
        ):
            out.append(
                finding(
                    "CODE_SHELL",
                    f"line:{node.lineno}",
                    "shell=True needs injection review; prefer an argument array without a shell.",
                    "owasp-asvs",
                    "high",
                )
            )
    return report(
        "secure-code-review",
        out,
        {
            "language": "python",
            "manual_checks": [
                "Trace untrusted sources to sensitive sinks",
                "Review authorization at resource boundaries",
                "Verify error handling and dependency assumptions",
            ],
        },
        [
            "Python AST heuristics only; no taint analysis, execution, or interprocedural resolution.",
            "Named call findings require human context review; other languages require manual review.",
        ],
    )


def api_review(data):
    version = str(data.get("openapi", ""))
    if not (version.startswith("3.0.") or version.startswith("3.1.")):
        raise InputError("Supported input: OpenAPI 3.0.x or 3.1.x JSON objects")
    paths = object_input(data.get("paths"), "paths")
    schemes = object_input(
        object_input(data.get("components", {}), "components").get("securitySchemes", {}),
        "securitySchemes",
    )
    out, operations = [], []
    servers = data.get("servers", [])
    if not isinstance(servers, list):
        raise InputError("servers must be an array")
    for server in servers:
        object_input(server, "server")
        url = server.get("url", "")
        if not isinstance(url, str):
            raise InputError("server URL must be text")
        if url.startswith("http://"):
            out.append(
                finding(
                    "API_HTTP",
                    "servers",
                    "Plain HTTP server declaration; verify TLS termination and deployment configuration.",
                    "owasp-api2023:API8",
                )
            )
    for path, item in sorted(paths.items()):
        object_input(item, "path item")
        if "$ref" in item:
            out.append(
                finding(
                    "API_UNRESOLVED_REF",
                    path,
                    "Path reference is not resolved; supply a bundled document.",
                    "openapi31",
                )
            )
        for method in ("get", "post", "put", "patch", "delete", "options", "head", "trace"):
            if method not in item:
                continue
            op = object_input(item[method], "operation")
            loc = f"{method.upper()} {path}"
            security = op.get("security", data.get("security", []))
            if not isinstance(security, list) or not all(isinstance(x, dict) for x in security):
                raise InputError("security must be an array of requirement objects")
            anonymous = not security or any(not entry for entry in security)
            if anonymous:
                out.append(
                    finding(
                        "API_ANONYMOUS",
                        loc,
                        "Operation permits anonymous access in its declaration; confirm this is intentional.",
                        "owasp-api2023:API2",
                    )
                )
            for entry in security:
                for name, scopes in entry.items():
                    if not isinstance(scopes, list) or not all(isinstance(s, str) for s in scopes):
                        raise InputError("Security scopes must be arrays of strings")
                    if name not in schemes:
                        out.append(
                            finding(
                                "API_UNKNOWN_SCHEME",
                                loc,
                                "Security requirement names an undefined scheme.",
                                "openapi31",
                            )
                        )
                    elif "$ref" in object_input(schemes[name], "security scheme"):
                        out.append(
                            finding(
                                "API_UNRESOLVED_REF",
                                loc,
                                "Security scheme reference requires bundling and review.",
                                "openapi31",
                            )
                        )
            if re.search(r"\{[^}]+\}", path):
                out.append(
                    finding(
                        "API_OBJECT_AUTH_REVIEW",
                        loc,
                        "Resource identifier needs cross-user and cross-tenant authorization tests; declaration alone is not evidence.",
                        "owasp-api2023:API1",
                    )
                )
            operations.append({"operation": loc, "anonymous_declared": anonymous})
    if not operations:
        out.append(
            finding(
                "API_NO_OPERATIONS",
                "paths",
                "No operations inspected; resolve references and confirm scope.",
                "openapi31",
            )
        )
    return report(
        "api-security-review",
        out,
        {
            "operations": operations,
            "manual_checks": [
                "Test object and function authorization using synthetic tenants",
                "Review request limits, SSRF protections, and schema validation",
                "Compare deployed inventory to this declaration",
            ],
        },
        [
            "No requests are sent; no runtime authorization or exploitability is established.",
            "OpenAPI subset review only; references, webhooks, callbacks, and per-operation server overrides are not expanded.",
        ],
    )


def threat_model(data):
    assets, flows = records(data, "assets"), records(data, "flows")
    unique(assets)
    unique(flows)
    ids = {a["id"] for a in assets}
    for asset in assets:
        required(asset, ("id", "name", "boundary", "classification"), "asset")
    boundaries = {a["id"]: a["boundary"] for a in assets}
    threats = []
    for flow in flows:
        required(flow, ("id", "source", "target", "data"), "flow")
        if flow["source"] not in ids or flow["target"] not in ids:
            raise InputError("Flow endpoints must reference asset IDs")
        cross = boundaries[flow["source"]] != boundaries[flow["target"]]
        scenarios = [
            ("tampering", "Validate message integrity and reject malformed input"),
            ("disclosure", "Minimize data, encrypt transport, and enforce recipient authorization"),
        ]
        if cross:
            scenarios += [
                ("spoofing", "Authenticate peers and bind identity to authorization"),
                ("denial-of-service", "Bound request size, concurrency, and resource budgets"),
            ]
        for category, mitigation in scenarios:
            threats.append(
                {
                    "id": f"{flow['id']}:{category}",
                    "flow": flow["id"],
                    "category": category,
                    "crosses_boundary": cross,
                    "mitigation_candidate": mitigation,
                    "status": "hypothesis-needs-review",
                }
            )
    return report(
        "threat-model-generator",
        artifacts={"assets": assets, "flows": flows, "threats": threats},
        limitations=[
            "Generated scenarios are hypotheses, not confirmed vulnerabilities or a complete STRIDE analysis.",
            "Review trust boundaries, business abuse, privilege escalation, repudiation, owners, and residual risks with system experts.",
        ],
    )


def llm_review(data):
    required(data, ("system_id", "owner"), "LLM application")
    controls = object_input(data.get("controls"), "controls")
    checks = {
        "untrusted_input_isolation": (
            "LLM01:2025",
            "Keep retrieved content and user input outside authority-bearing instructions",
        ),
        "sensitive_data_filtering": (
            "LLM02:2025",
            "Minimize sensitive context and enforce access outside the model",
        ),
        "dependency_provenance": (
            "LLM03:2025",
            "Review model, plugin, and retrieval-source provenance",
        ),
        "data_integrity": (
            "LLM04:2025",
            "Protect training and retrieval corpora from unauthorized modification",
        ),
        "output_validation": ("LLM05:2025", "Validate model output before rendering or execution"),
        "tool_least_privilege": (
            "LLM06:2025",
            "Enforce scoped tool permissions and approval for consequential actions",
        ),
        "prompt_secret_exclusion": (
            "LLM07:2025",
            "Keep secrets and authorization decisions out of system prompts",
        ),
        "retrieval_access_control": (
            "LLM08:2025",
            "Apply tenant and document access checks during retrieval",
        ),
        "grounding_review": (
            "LLM09:2025",
            "Evaluate factual grounding and communicate uncertainty",
        ),
        "resource_limits": ("LLM10:2025", "Set token, tool-call, concurrency, and cost limits"),
    }
    unknown = set(controls) - set(checks)
    if unknown:
        raise InputError("Unknown LLM control keys; consult the documented input contract")
    out, evidence = [], []
    for key, (risk, action) in checks.items():
        value = controls.get(key)
        if value is not None and not isinstance(value, str):
            raise InputError("Control evidence must be text")
        if not value or not value.strip():
            out.append(
                finding(
                    "LLM_EVIDENCE_GAP",
                    key,
                    action + "; no evidence supplied.",
                    f"owasp-llm2025:{risk}",
                )
            )
        else:
            evidence.append(
                {"control": key, "risk": risk, "evidence": value, "status": "unverified"}
            )
    return report(
        "llm-application-security-review",
        out,
        {"system_id": data["system_id"], "evidence": evidence},
        [
            "Evidence presence is not proof of control effectiveness; no adversarial prompts or live attacks are executed.",
            "Human review must cover indirect injection, tool authority, retrieval boundaries, and approval bypass.",
        ],
    )
