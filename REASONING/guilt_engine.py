"""
REASONING/guilt_engine.py
Composite risk scorer that fuses ML probability + C++ rule scores
into a single guilt verdict with detailed legal mapping.
"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass, field, asdict
from typing import Any
from loguru import logger


# ─── Legal violation catalogue ────────────────────────────────────────────────
def _load_legal_map() -> dict:
    path = os.path.join(os.path.dirname(__file__), "legal_map.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load legal_map.json: {e}")
    return {}

LEGAL_VIOLATIONS = _load_legal_map()

RISK_BAND = {
    "HIGH":   (0.70, 1.01),
    "MEDIUM": (0.40, 0.70),
    "LOW":    (0.00, 0.40),
}


@dataclass
class GuiltVerdict:
    transaction_id: str
    account_id:     str
    risk_score:     float
    risk_level:     str
    is_guilty:      bool
    ml_score:       float
    rule_score:     float
    triggered_rules: list[str]
    legal_violations: list[dict]
    explanations:   list[str]
    top_reasons:    list[dict]
    recommendation: str
    sar_required:   bool
    narrative:      str
    audit_hash:     str = ""
    metadata:       dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ─── Fusion logic ─────────────────────────────────────────────────────────────
def _fuse_scores(ml_score: float, rule_score: float) -> float:
    """
    Weighted fusion:  60% ML probability + 40% rule-based score.
    If rule score > 0.75, boost final score by 10%.
    """
    fused = 0.60 * ml_score + 0.40 * rule_score
    if rule_score >= 0.75:
        fused = min(fused + 0.10, 1.0)
    return round(fused, 4)


def _get_risk_level(score: float) -> str:
    for level, (lo, hi) in RISK_BAND.items():
        if lo <= score < hi:
            return level
    return "LOW"


def _get_legal_violations(triggered_rules: list[str], ml_result: dict) -> list[dict]:
    violations = []
    # Add rule-based violations
    for r in triggered_rules:
        if r in LEGAL_VIOLATIONS:
            violations.append(LEGAL_VIOLATIONS[r])
    
    # Add ML-based high value indicator if rule doesn't catch it
    if ml_result.get("risk_score", 0) > 0.8 and "HIGH_VALUE" in LEGAL_VIOLATIONS:
        if not any(v.get("act") == LEGAL_VIOLATIONS["HIGH_VALUE"].get("act") for v in violations):
            violations.append(LEGAL_VIOLATIONS["HIGH_VALUE"])
            
    return violations


def _build_recommendation(risk_level: str, triggered_rules: list[str]) -> str:
    if risk_level == "HIGH":
        return (
            "IMMEDIATE ACTION REQUIRED: File Suspicious Activity Report (SAR) within 7 days "
            "per PMLA Section 12A. Freeze account pending investigation. Notify FIU-IND."
        )
    elif risk_level == "MEDIUM":
        return (
            "Enhanced Due Diligence (EDD) recommended. Monitor account for 30 days. "
            "Collect supporting KYC documentation. Escalate to Compliance Officer."
        )
    return (
        "Standard monitoring continued. Flag for quarterly review. "
        "No immediate action required."
    )


def _build_narrative(
    txn: dict, risk_score: float, risk_level: str,
    triggered_rules: list[str], top_reasons: list[dict],
    violations: list[dict]
) -> str:
    acc     = txn.get("account_id", "N/A")
    amt     = txn.get("amount",     0)
    loc     = txn.get("location",   "N/A")
    ch      = txn.get("channel",    "N/A")
    reasons = "\n".join(f"  • {r['reason']}" for r in top_reasons[:3]) if top_reasons else "  • No specific indicators"
    rules   = ", ".join(triggered_rules) if triggered_rules else "None"
    
    legal_justification = ""
    for v in violations[:2]:
        legal_justification += f"\n  - {v['act']} ({v['section']}): {v['description']}"

    return (
        f"PROOFSAR AI — SUSPICION ASSESSMENT REPORT\n"
        f"{'─'*50}\n"
        f"Account:        {acc}\n"
        f"Transaction:    ₹{float(amt):,.2f} via {ch} ({loc})\n"
        f"Risk Score:     {risk_score:.2%}  [{risk_level}]\n"
        f"Rules Triggered: {rules}\n"
        f"Legal Basis:    {legal_justification if legal_justification else 'Under Review'}\n\n"
        f"PRIMARY INDICATORS:\n{reasons}\n\n"
        f"ASSESSMENT:\n"
        f"Based on ML model probability ({txn.get('_ml_score', 0):.2%}) fused with "
        f"rule-based detection score ({txn.get('_rule_score', 0):.2%}), this transaction "
        f"exhibits characteristics consistent with {'financial crime' if risk_level != 'LOW' else 'normal activity'}."
    )


# ─── Main entry point ─────────────────────────────────────────────────────────
def compute_guilt(
    txn: dict,
    ml_result: dict,
    rule_result: dict,
    shap_reasons: list[dict] | None = None
) -> GuiltVerdict:
    """
    Fuse ML + rule results into a final GuiltVerdict.
    """
    ml_score   = float(ml_result.get("risk_score",  0.0))
    rule_score = float(rule_result.get("risk_score", 0.0))
    fused      = _fuse_scores(ml_score, rule_score)
    risk_level = _get_risk_level(fused)

    triggered  = rule_result.get("triggered_rules", [])
    violations = _get_legal_violations(triggered, ml_result)
    top_reasons = shap_reasons or []

    # Annotate txn for narrative
    txn["_ml_score"]   = ml_score
    txn["_rule_score"] = rule_score

    recommendation = _build_recommendation(risk_level, triggered)
    narrative      = _build_narrative(txn, fused, risk_level, triggered, top_reasons, violations)

    return GuiltVerdict(
        transaction_id   = txn.get("transaction_id", ""),
        account_id       = txn.get("account_id", ""),
        risk_score       = fused,
        risk_level       = risk_level,
        is_guilty        = fused >= 0.40,
        ml_score         = ml_score,
        rule_score       = rule_score,
        triggered_rules  = triggered,
        legal_violations = violations,
        explanations     = rule_result.get("explanations", []),
        top_reasons      = top_reasons,
        recommendation   = recommendation,
        sar_required     = risk_level == "HIGH",
        narrative        = narrative,
        metadata         = {
            "engine_used": rule_result.get("engine", "unknown"),
            "model_used":  ml_result.get("model_used", "unknown"),
            "amount":      txn.get("amount"),
            "channel":     txn.get("channel"),
            "location":    txn.get("location"),
        }
    )

