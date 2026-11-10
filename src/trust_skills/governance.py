"""Structured AI inventory, local risk prioritization, model cards and evaluations."""

import math
import re
from datetime import date

from .core import InputError, finding, records, report, required, unique


def risk_register(data):
    rows = records(data, "risks")
    unique(rows)
    out, scored = [], []
    for row in rows:
        required(
            row,
            ("id", "system_id", "scenario", "harm", "owner", "treatment", "status", "review_date"),
            "risk",
        )
        if row["status"] not in {"open", "mitigating", "accepted", "closed"}:
            raise InputError("Risk status must be open, mitigating, accepted, or closed")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["review_date"]):
            raise InputError("review_date must use YYYY-MM-DD")
        try:
            date.fromisoformat(row["review_date"])
        except ValueError as exc:
            raise InputError("review_date must be an ISO calendar date") from exc
        for field in ("likelihood", "impact"):
            if type(row.get(field)) is not int or not 1 <= row[field] <= 5:
                raise InputError(f"{field} must be an integer from 1 to 5")
        score = row["likelihood"] * row["impact"]
        result = dict(
            row, score=score, priority="high" if score >= 15 else "medium" if score >= 6 else "low"
        )
        residual = (row.get("residual_likelihood"), row.get("residual_impact"))
        if any(x is not None for x in residual):
            if any(type(x) is not int or not 1 <= x <= 5 for x in residual):
                raise InputError("Supply both residual ratings as integers from 1 to 5")
            result["residual_score"] = residual[0] * residual[1]
        approval = row.get("approval_evidence")
        if approval is not None and not isinstance(approval, str):
            raise InputError("approval_evidence must be text")
        if row["status"] in {"accepted", "closed"} and not (approval or "").strip():
            out.append(
                finding(
                    "RISK_APPROVAL_GAP",
                    row["id"],
                    "Acceptance or closure lacks accountable approval evidence.",
                    "ai-rmf",
                )
            )
        scored.append(result)
    scored.sort(key=lambda r: (-r["score"], r["id"]))
    return report(
        "ai-risk-register",
        out,
        {
            "risks": scored,
            "scoring_policy": "Local ordinal 1–5 likelihood × impact; high ≥15, medium ≥6; not prescribed by NIST.",
        },
        [
            "Scores are prioritization aids, not probabilities or legal risk classifications.",
            "Owners must review affected groups, harms, uncertainty, residual risk, and approvals.",
        ],
    )


def inventory(data):
    systems = records(data, "systems")
    unique(systems)
    out = []
    for item in systems:
        required(
            item,
            (
                "id",
                "name",
                "owner",
                "purpose",
                "model",
                "lifecycle",
                "data_classification",
                "oversight",
            ),
            "system",
        )
        if item["lifecycle"] not in {"proposed", "development", "deployed", "retired"}:
            raise InputError("Unknown lifecycle state")
        monitoring = item.get("monitoring")
        if monitoring is not None and not isinstance(monitoring, str):
            raise InputError("monitoring must be text")
        groups = item.get("affected_groups", [])
        if not isinstance(groups, list) or not all(
            isinstance(x, str) and x.strip() for x in groups
        ):
            raise InputError("affected_groups must be an array of nonempty text")
        if item["lifecycle"] == "deployed" and not (monitoring or "").strip():
            out.append(
                finding(
                    "INVENTORY_MONITORING",
                    item["id"],
                    "Deployed system has no monitoring evidence.",
                    "ai-rmf",
                )
            )
        if not item.get("affected_groups"):
            out.append(
                finding(
                    "INVENTORY_STAKEHOLDERS",
                    item["id"],
                    "Record affected stakeholder groups and consultation needs.",
                    "ai-rmf",
                )
            )
    return report(
        "ai-system-inventory",
        out,
        {"systems": sorted(systems, key=lambda x: x["id"]), "system_count": len(systems)},
    )


def model_card(data):
    required(
        data,
        (
            "name",
            "version",
            "owner",
            "intended_use",
            "out_of_scope",
            "training_data",
            "limitations",
        ),
        "model card",
    )
    evaluations = records(data, "evaluations")
    out = []
    for i, row in enumerate(evaluations):
        required(row, ("metric", "dataset", "result", "method"), f"evaluation {i}")
        if not row.get("slice"):
            out.append(
                finding(
                    "MODEL_CARD_SLICES",
                    f"evaluation:{i + 1}",
                    "No population or condition slice recorded; review disaggregated performance.",
                    "model-cards",
                )
            )
    return report(
        "ai-model-card-generator",
        out,
        {"model_card": data},
        [
            "User-supplied claims are not independently verified; missing evidence must remain explicit.",
            "No performance, fairness, or suitability guarantee is inferred.",
        ],
    )


def evaluation_plan(data):
    required(data, ("system_id", "owner", "decision"), "evaluation plan")
    rows = records(data, "metrics")
    unique(rows)
    out, gates = [], []
    for row in rows:
        required(row, ("id", "metric", "dataset", "slice", "method"), "metric")
        if row.get("direction") not in ("at_least", "at_most"):
            raise InputError("direction must be at_least or at_most")
        if type(row.get("threshold")) not in {int, float} or (
            isinstance(row["threshold"], float) and not math.isfinite(row["threshold"])
        ):
            raise InputError("threshold must be finite numeric data")
        observed = row.get("observed")
        state = "not_run"
        if observed is not None:
            if type(observed) not in {int, float} or (
                isinstance(observed, float) and not math.isfinite(observed)
            ):
                raise InputError("observed must be finite numeric data")
            passed = (
                observed >= row["threshold"]
                if row["direction"] == "at_least"
                else observed <= row["threshold"]
            )
            state = "threshold_met" if passed else "threshold_missed"
            if not passed:
                out.append(
                    finding(
                        "EVAL_THRESHOLD",
                        row["id"],
                        "Observed result misses the supplied local threshold.",
                        "ai-rmf",
                    )
                )
        gates.append(dict(row, state=state))
    return report(
        "ai-evaluation-planner",
        out,
        {"system_id": data["system_id"], "decision": data["decision"], "gates": gates},
        [
            "No model is invoked and no evaluation is run; observations are supplied evidence.",
            "Thresholds are locally chosen; statistical uncertainty, representativeness, leakage, and human release approval require review.",
        ],
    )
