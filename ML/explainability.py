"""
ML/explainability.py
SHAP-based explainability engine — converts ML decisions into human-readable reasons
"""
import os
import numpy as np
import pandas as pd
import shap
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from loguru import logger
from ML.train_model import FEATURE_COLS, MODEL_PATH, SCALER_PATH

FEATURE_DESCRIPTIONS = {
    "amount": "Transaction amount",
    "amount_log": "Log-scaled transaction amount",
    "hour": "Hour of day transaction occurred",
    "day_of_week": "Day of the week",
    "is_weekend": "Transaction on weekend",
    "is_high_risk_location": "High-risk jurisdiction (offshore/tax haven)",
    "is_high_risk_channel": "High-risk channel (wire transfer/RTGS)",
    "is_international": "International currency transaction",
    "near_threshold": "Amount near reporting threshold (₹8.5L–₹10L)",
    "acc_mean_amount": "Account average transaction amount",
    "acc_std_amount": "Account transaction volatility",
    "acc_txn_count": "Total account transaction count",
    "acc_max_amount": "Account maximum single transaction",
    "amount_vs_mean": "Amount relative to account average",
    "amount_zscore": "Amount standard deviations from mean"
}

REASON_TEMPLATES = {
    "amount": "Unusually high transaction amount (₹{val:,.0f})",
    "near_threshold": "Amount structured near ₹10 lakh reporting threshold",
    "is_high_risk_location": "Transaction routed through high-risk jurisdiction",
    "is_high_risk_channel": "High-risk channel (wire/RTGS) used",
    "is_international": "International currency transfer detected",
    "amount_vs_mean": "Amount {val:.1f}x higher than account average",
    "amount_zscore": "Amount {val:.1f} standard deviations above normal",
    "is_weekend": "Transaction conducted outside business hours (weekend)",
    "hour": "Transaction at unusual hour ({val:.0f}:00)",
    "acc_txn_count": "High transaction frequency ({val:.0f} transactions)",
    "acc_std_amount": "High transaction amount variability detected"
}


def load_model_for_shap():
    """Load model artifact and scaler."""
    if not os.path.exists(MODEL_PATH):
        logger.warning("Model not found — triggering training...")
        from ML.train_model import main
        main()
    artifact = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return artifact, scaler


def compute_shap_values(transactions: list[dict], max_samples: int = 200) -> dict:
    """
    Compute SHAP values for a list of transaction dicts.
    Returns SHAP values, feature names, and base value.
    """
    artifact, scaler = load_model_for_shap()
    model = artifact["model"]
    imputer = artifact["imputer"]
    feature_cols = artifact["feature_cols"]

    df = pd.DataFrame(transactions)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    X = df[feature_cols].values
    X_imp = imputer.transform(X)
    X_sc = scaler.transform(X_imp)

    # Sample if large
    if len(X_sc) > max_samples:
        idx = np.random.choice(len(X_sc), max_samples, replace=False)
        X_sc = X_sc[idx]

    model_name = artifact["model_name"]
    if model_name in ["RandomForest", "XGBoost"]:
        explainer = shap.TreeExplainer(model)
        shap_values_raw = explainer.shap_values(X_sc)
        # For binary classification, take class-1 SHAP values
        if isinstance(shap_values_raw, list):
            shap_vals = shap_values_raw[1]
        else:
            shap_vals = shap_values_raw
        base_value = float(explainer.expected_value[1]) if isinstance(
            explainer.expected_value, (list, np.ndarray)) else float(explainer.expected_value)
    else:
        explainer = shap.LinearExplainer(model, X_sc)
        shap_vals = explainer.shap_values(X_sc)
        base_value = float(explainer.expected_value)

    return {
        "shap_values": shap_vals,
        "feature_names": feature_cols,
        "base_value": base_value,
        "X_transformed": X_sc,
        "model_name": model_name
    }


def get_top_reasons(transaction: dict, top_k: int = 5) -> list[dict]:
    """
    Get top-k explanatory reasons for a single transaction.
    Returns list of {feature, importance, direction, reason} dicts.
    """
    result = compute_shap_values([transaction])
    shap_vals = result["shap_values"][0]
    feature_names = result["feature_names"]

    # Map feature values from original transaction
    feature_values = {}
    for col in feature_names:
        feature_values[col] = transaction.get(col, 0)

    reasons = []
    for feat, shap_val, val in zip(feature_names, shap_vals, [feature_values.get(f, 0) for f in feature_names]):
        desc = FEATURE_DESCRIPTIONS.get(feat, feat.replace("_", " ").title())
        template = REASON_TEMPLATES.get(feat)
        if template:
            try:
                reason_text = template.format(val=val)
            except Exception:
                reason_text = desc
        else:
            direction = "increases" if shap_val > 0 else "decreases"
            reason_text = f"{desc} {direction} suspicion risk"

        reasons.append({
            "feature": feat,
            "shap_value": float(shap_val),
            "feature_value": float(val) if isinstance(val, (int, float)) else val,
            "importance": abs(float(shap_val)),
            "direction": "risk_increasing" if shap_val > 0 else "risk_decreasing",
            "description": desc,
            "reason": reason_text
        })

    # Sort by absolute SHAP value
    reasons.sort(key=lambda x: x["importance"], reverse=True)
    return reasons[:top_k]


def generate_narrative(transaction: dict, risk_score: float, reasons: list[dict]) -> str:
    """Generate human-readable AML explanation narrative."""
    top_reasons = [r["reason"] for r in reasons[:3]]
    risk_label = "HIGH" if risk_score >= 0.7 else "MEDIUM" if risk_score >= 0.4 else "LOW"
    amount = transaction.get("amount", 0)
    account = transaction.get("account_id", "N/A")
    channel = transaction.get("channel", "N/A")
    location = transaction.get("location", "N/A")

    narrative = f"""RISK ASSESSMENT: {risk_label} (Score: {risk_score:.2%})

Transaction of ₹{amount:,.2f} from account {account} via {channel} ({location}) 
has been flagged by the ProofSAR AI detection engine.

PRIMARY RISK INDICATORS:
"""
    for i, r in enumerate(top_reasons, 1):
        narrative += f"  {i}. {r}\n"

    if risk_score >= 0.7:
        narrative += "\nACTION REQUIRED: Immediate SAR filing recommended under PMLA Section 12."
    elif risk_score >= 0.4:
        narrative += "\nACTION RECOMMENDED: Enhanced due diligence and monitoring advised."
    else:
        narrative += "\nSTATUS: Low risk — continue standard monitoring."

    return narrative


def plot_shap_waterfall(transaction: dict, output_path: str = None) -> str:
    """Generate SHAP waterfall chart. Returns path to saved image."""
    result = compute_shap_values([transaction])
    shap_vals = result["shap_values"][0]
    feature_names = result["feature_names"]
    base_value = result["base_value"]

    fig, ax = plt.subplots(figsize=(10, 6))
    sorted_idx = np.argsort(np.abs(shap_vals))[::-1][:10]
    top_features = [feature_names[i] for i in sorted_idx]
    top_shap = [shap_vals[i] for i in sorted_idx]

    colors = ["#d32f2f" if v > 0 else "#1976d2" for v in top_shap]
    bars = ax.barh(top_features[::-1], top_shap[::-1], color=colors[::-1], alpha=0.85)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("SHAP Value (Impact on Risk Score)", fontsize=11)
    ax.set_title("ProofSAR AI — Feature Impact on Suspicion Score", fontsize=13, fontweight="bold")
    ax.tick_params(labelsize=9)

    for bar, val in zip(bars, top_shap[::-1]):
        ax.text(
            bar.get_width() + (0.002 if val > 0 else -0.002),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.3f}",
            va="center", ha="left" if val > 0 else "right", fontsize=8
        )

    plt.tight_layout()
    os.makedirs("REPORTS", exist_ok=True)
    if output_path is None:
        output_path = "REPORTS/shap_chart.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path
