"""
ML/mlflow_tracker.py
MLflow integration for ProofSAR AI monitoring
"""
import os
import mlflow
import mlflow.sklearn
from datetime import datetime
from loguru import logger

# Configure MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "file:./ML/mlruns")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("ProofSAR_AI_AML")

def start_run(run_name: str = None):
    """Start and return an MLflow run."""
    if not run_name:
        run_name = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return mlflow.start_run(run_name=run_name)

def log_metrics(metrics: dict):
    """Log simple dictionary of metrics."""
    mlflow.log_metrics(metrics)

def log_params(params: dict):
    """Log simple dictionary of parameters."""
    mlflow.log_params(params)

def log_model(model, artifact_path="model"):
    """Log the trained model artifact."""
    mlflow.sklearn.log_model(model, artifact_path)
    logger.info(f"Model logged to MLflow artifacts: {artifact_path}")

def check_drift(reference_df, current_df, threshold=0.1):
    """
    Very basic drift detection using mean differences.
    In production, use EvidentlyAI or similar.
    """
    drift_detected = False
    details = {}
    
    for col in reference_df.columns:
        if col in current_df.columns and reference_df[col].dtype in ['int64', 'float64']:
            ref_mean = reference_df[col].mean()
            cur_mean = current_df[col].mean()
            diff = abs(ref_mean - cur_mean) / (ref_mean + 1e-9)
            
            if diff > threshold:
                drift_detected = True
                details[col] = {"ref_mean": ref_mean, "cur_mean": cur_mean, "diff_pct": diff * 100}
    
    if drift_detected:
        logger.warning(f"Drift detected in features: {list(details.keys())}")
        mlflow.log_dict(details, "drift_analysis.json")
    
    return drift_detected, details
