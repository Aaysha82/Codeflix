"""
ML/train_model.py
Train and evaluate ML models for AML transaction detection
Run: python ML/train_model.py
"""
import os
import sys
import json
import joblib
import warnings
import numpy as np
import pandas as pd
from datetime import datetime
from loguru import logger

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, precision_score, recall_score, f1_score
)
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

warnings.filterwarnings("ignore")

FEATURE_COLS = [
    "amount", "amount_log", "hour", "day_of_week", "is_weekend",
    "is_high_risk_location", "is_high_risk_channel", "is_international",
    "near_threshold", "acc_mean_amount", "acc_std_amount", "acc_txn_count",
    "acc_max_amount", "amount_vs_mean", "amount_zscore"
]

MODEL_PATH = "ML/model.pkl"
SCALER_PATH = "ML/scaler.pkl"
METRICS_PATH = "ML/metrics.json"


def load_and_prepare_data(csv_path: str = "DATA/transactions.csv"):
    """Load dataset and prepare features."""
    if not os.path.exists(csv_path):
        logger.warning("Dataset not found. Generating synthetic data...")
        sys.path.insert(0, ".")
        from DATA.generate_data import generate_dataset, add_features
        df = generate_dataset(n_accounts=500, fraud_ratio=0.05)
        df = add_features(df)
        os.makedirs("DATA", exist_ok=True)
        df.to_csv(csv_path, index=False)
        df.to_csv("DATA/transactions_test.csv", index=False)
        logger.info(f"Generated dataset: {len(df)} rows")
    else:
        df = pd.read_csv(csv_path)

    # Ensure timestamp-derived features exist
    if "hour" not in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Fill missing engineered columns
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0

    X = df[FEATURE_COLS].copy()
    y = df["is_suspicious"].astype(int)
    logger.info(f"Dataset: {len(df)} rows | Fraud: {y.sum()} ({y.mean()*100:.2f}%)")
    return X, y, df


def build_models():
    """Build three candidate models."""
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=10,
        eval_metric="auc",
        random_state=42,
        verbosity=0
    )
    lr = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        C=0.5,
        random_state=42
    )
    return {"RandomForest": rf, "XGBoost": xgb, "LogisticRegression": lr}


def train_and_evaluate(X, y):
    """Train all models and select the best by AUC."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    imputer = SimpleImputer(strategy="median")

    X_train_imp = imputer.fit_transform(X_train)
    X_test_imp = imputer.transform(X_test)
    X_train_sc = scaler.fit_transform(X_train_imp)
    X_test_sc = scaler.transform(X_test_imp)

    # Apply SMOTE safely
    minority_count = y_train.sum()
    k_neighbors = min(5, minority_count - 1) if minority_count > 1 else 1
    if k_neighbors >= 1 and minority_count > k_neighbors:
        smote = SMOTE(k_neighbors=k_neighbors, random_state=42)
        X_res, y_res = smote.fit_resample(X_train_sc, y_train)
        logger.info(f"SMOTE applied: {len(y_res)} samples (k={k_neighbors})")
    else:
        X_res, y_res = X_train_sc, y_train
        logger.warning("Skipping SMOTE — insufficient minority samples")

    models = build_models()
    results = {}
    best_model = None
    best_auc = 0.0

    for name, model in models.items():
        logger.info(f"Training {name}...")
        if name == "XGBoost":
            model.fit(X_res, y_res)
        else:
            model.fit(X_res, y_res)

        y_prob = model.predict_proba(X_test_sc)[:, 1]
        y_pred = model.predict(X_test_sc)

        auc = roc_auc_score(y_test, y_prob)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)

        results[name] = {
            "auc": round(auc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
        }
        logger.info(f"{name}: AUC={auc:.4f} | P={prec:.4f} | R={rec:.4f} | F1={f1:.4f}")

        if auc > best_auc:
            best_auc = auc
            best_model = (name, model)

    logger.info(f"\nBest Model: {best_model[0]} with AUC={best_auc:.4f}")
    return best_model, scaler, imputer, results, X_test_sc, y_test


def save_artifacts(best_model, scaler, imputer, results):
    """Save model, scaler, imputer, and metrics."""
    os.makedirs("ML", exist_ok=True)
    model_artifact = {
        "model": best_model[1],
        "model_name": best_model[0],
        "feature_cols": FEATURE_COLS,
        "imputer": imputer,
        "trained_at": datetime.now().isoformat()
    }
    joblib.dump(model_artifact, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    metrics_output = {
        "best_model": best_model[0],
        "trained_at": datetime.now().isoformat(),
        "feature_cols": FEATURE_COLS,
        "model_results": results
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics_output, f, indent=2)
    logger.success(f"Saved model → {MODEL_PATH}")
    logger.success(f"Saved scaler → {SCALER_PATH}")
    logger.success(f"Saved metrics → {METRICS_PATH}")


def load_model():
    """Load trained model artifact. Auto-trains if missing."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        logger.warning("Model not found. Auto-training...")
        main()
    artifact = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    return artifact, scaler


def predict_transaction(transaction: dict) -> dict:
    """Run prediction on a single transaction dict."""
    artifact, scaler = load_model()
    model = artifact["model"]
    imputer = artifact["imputer"]
    feature_cols = artifact["feature_cols"]

    row = pd.DataFrame([transaction])
    for col in feature_cols:
        if col not in row.columns:
            row[col] = 0

    X = row[feature_cols].values
    X_imp = imputer.transform(X)
    X_sc = scaler.transform(X_imp)

    prob = model.predict_proba(X_sc)[0][1]
    pred = int(prob >= 0.5)
    risk_level = "HIGH" if prob >= 0.7 else "MEDIUM" if prob >= 0.4 else "LOW"

    return {
        "is_suspicious": pred,
        "risk_score": round(float(prob), 4),
        "risk_level": risk_level,
        "model_used": artifact["model_name"]
    }


def main():
    logger.info("=== ProofSAR AI — ML Training Pipeline ===")
    X, y, df = load_and_prepare_data()
    best_model, scaler, imputer, results, X_test, y_test = train_and_evaluate(X, y)
    save_artifacts(best_model, scaler, imputer, results)
    logger.info("\n=== Training Complete ===")
    for name, m in results.items():
        logger.info(f"{name}: AUC={m['auc']} | F1={m['f1']}")
    return best_model, scaler, results


if __name__ == "__main__":
    main()
