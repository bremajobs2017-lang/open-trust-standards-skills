"""Bounded planning, control-evidence mapping, contrast, and reporting helpers."""

import re

from .core import InputError, finding, records, report, required, unique

CSF = {
    "GV": "Govern",
    "ID": "Identify",
    "PR": "Protect",
    "DE": "Detect",
    "RS": "Respond",
    "RC": "Recover",
}
AI_RMF = {"GOVERN": "Govern", "MAP": "Map", "MEASURE": "Measure", "MANAGE": "Manage"}
SSDF = {
    "PO": "Prepare the Organization",
    "PS": "Protect the Software",
    "PW": "Produce Well-Secured Software",
    "RV": "Respond to Vulnerabilities",
}


def control_map(data, skill):
    allowed, key, ref = {
        "nist-csf-control-mapper": (CSF, "function", "nist-csf20"),
        "ai-governance-controls-mapper": (AI_RMF, "function", "ai-rmf"),
        "secure-development-lifecycle": (SSDF, "practice_group", "ssdf11"),
    }[skill]
    rows = records(data, "controls")
    unique(rows)
    out, mapped, covered = [], [], set()
    for row in rows:
        required(row, ("id", key, "owner", "description"), "control")
        target = row[key]
        if target not in allowed:
            raise InputError(
                f"{key} must be one of {', '.join(allowed)}; detailed clauses are not mapped by this tool"
            )
        evidence = row.get("evidence")
        if evidence is not None and not isinstance(evidence, str):
            raise InputError("evidence must be text")
        if not evidence or not evidence.strip():
            out.append(
                finding(
                    "CONTROL_EVIDENCE_GAP",
                    row["id"],
                    "Control has no evidence; assign collection and review tasks.",
                    ref,
                )
            )
        else:
            covered.add(target)
        mapped.append(dict(row, mapping_status="candidate-human-review"))
    for target in allowed:
        if target not in covered:
            out.append(
                finding(
                    "FRAMEWORK_AREA_GAP",
                    target,
                    "No evidence supplied for this framework area; determine applicability.",
                    ref,
                )
            )
    return report(
        skill,
        out,
        {"mappings": mapped, "areas_with_evidence": sorted(covered), "framework_areas": allowed},
        [
            "Mappings are user-selected candidates at function/practice-group level only; not a full subcategory crosswalk.",
            "Evidence presence does not establish implementation, effectiveness, compliance, or maturity.",
        ],
    )


def audit_plan(data):
    required(data, ("scope", "owner"), "audit plan")
    if data.get("level") not in ("A", "AA", "AAA"):
        raise InputError("level must be A, AA, or AAA")
    pages = records(data, "pages")
    unique(pages)
    for page in pages:
        required(page, ("id", "type", "journey"), "page")
    # Representative sampling is a planning proposal, never a statistically complete assessment.
    selected, groups = [], set()
    for page in pages:
        group = (page["type"], page["journey"])
        if group not in groups or page.get("critical") is True:
            selected.append(page)
            groups.add(group)
    return report(
        "wcag-audit-planner",
        artifacts={
            "scope": data["scope"],
            "target": f"WCAG 2.2 {data['level']}",
            "sample": selected,
            "sample_policy": "First page per declared page-type/journey plus every declared critical page; reviewer must expand complete processes.",
            "test_tracks": [
                "Static automated checks",
                "Keyboard and focus",
                "Screen reader semantics",
                "Contrast, reflow, zoom, and target size",
                "Forms, errors, authentication, and complete processes",
            ],
            "evidence_fields": [
                "page/state",
                "criterion and level",
                "steps",
                "expected",
                "actual",
                "environment",
                "reviewer",
                "retest",
            ],
        },
        limitations=[
            "Does not enumerate or assess every success criterion; reviewer must obtain the full target-level checklist.",
            "Sampling proposal requires human review for complete processes, third-party content, responsive states, and WCAG conformance requirements.",
        ],
    )


def luminance(hex_):
    if not isinstance(hex_, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", hex_):
        raise InputError("Colors must be opaque six-digit hex strings, e.g. #112233")
    channels = [int(hex_[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(v * weight for v, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def design_system(data):
    pairs = records(data, "color_pairs")
    unique(pairs)
    out, results = [], []
    for pair in pairs:
        required(pair, ("id", "foreground", "background", "usage"), "color pair")
        if pair["usage"] not in {"normal_text", "large_text", "non_text"}:
            raise InputError("usage must be normal_text, large_text, or non_text")
        a, b = luminance(pair["foreground"]), luminance(pair["background"])
        ratio = (max(a, b) + 0.05) / (min(a, b) + 0.05)
        threshold = 4.5 if pair["usage"] == "normal_text" else 3.0
        if ratio < threshold:
            out.append(
                finding(
                    "CONTRAST_RATIO",
                    pair["id"],
                    f"Declared color pair is below the local AA screening threshold of {threshold}:1.",
                    "wcag22:1.4.3" if pair["usage"] != "non_text" else "wcag22:1.4.11",
                )
            )
        results.append(
            dict(pair, ratio=round(ratio, 4), threshold=threshold, threshold_met=ratio >= threshold)
        )
    return report(
        "accessible-design-system",
        out,
        {
            "color_pairs": results,
            "manual_checks": [
                "Confirm large text meets WCAG size and weight definitions",
                "Review component focus, disabled/error/hover states, and forced colors",
                "Check target size and non-color affordances in rendered components",
            ],
        },
        [
            "Opaque sRGB pairs only; no alpha, gradients, rendered text, or applicability exceptions.",
            "Ratios use unrounded values for decisions; this is not a design-system accessibility certification.",
        ],
    )


def accessibility_report(data):
    rows = records(data, "findings")
    unique(rows)
    allowed = {
        "1.1.1",
        "1.3.1",
        "1.4.3",
        "1.4.10",
        "1.4.11",
        "2.1.1",
        "2.1.2",
        "2.4.2",
        "2.4.3",
        "2.4.7",
        "2.4.11",
        "2.5.8",
        "3.1.1",
        "3.3.1",
        "3.3.2",
        "4.1.2",
    }
    severity = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    counts = dict.fromkeys(severity, 0)
    for row in rows:
        required(
            row,
            (
                "id",
                "criterion",
                "severity",
                "location",
                "evidence",
                "recommendation",
                "status",
                "method",
            ),
            "accessibility finding",
        )
        if row["criterion"] not in allowed:
            raise InputError(
                "Criterion is outside this tool's verified WCAG 2.2 subset; use a manual report for other criteria"
            )
        if (
            row["severity"] not in severity
            or row["method"] not in {"automated", "human"}
            or row["status"] not in {"open", "fixed", "needs-review"}
        ):
            raise InputError("Invalid severity, method, or finding status")
        if row["method"] == "human" and not row.get("reviewer"):
            raise InputError("Human findings must identify a reviewer role or pseudonymous ID")
        counts[row["severity"]] += 1
    ordered = sorted(rows, key=lambda x: (severity[x["severity"]], x["id"]))
    return report(
        "accessibility-report-generator",
        artifacts={
            "severity_counts": counts,
            "findings": ordered,
            "open_count": sum(x["status"] == "open" for x in rows),
        },
        limitations=[
            "Aggregates supplied evidence only; a fixed status requires independent retesting.",
            "Subset criterion identifiers are validated, but findings and compliance conclusions are not independently assessed.",
        ],
    )
