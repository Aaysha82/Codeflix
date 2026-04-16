"""
BACKEND/tasks.py
Asynchronous tasks for batch transaction analysis and report generation.
"""
import pandas as pd
import io
from typing import List, Dict
from loguru import logger
from BACKEND.celery_app import celery_app
from DETECTION.cpp_runner import run_detection
from ML.train_model import predict_transaction
from REASONING.guilt_engine import compute_guilt

@celery_app.task(bind=True, name="process_batch_transactions")
def process_batch_transactions(self, transactions: List[Dict]):
    """
    Process a list of transactions asynchronously.
    Updates task state with progress.
    """
    total = len(transactions)
    results = []
    
    for i, txn in enumerate(transactions):
        try:
            # 1. ML Prediction
            ml_res = predict_transaction(txn)
            
            # 2. Rule Detection
            rule_res = run_detection(txn)
            
            # 3. Guilt Reasoning
            verdict = compute_guilt(txn, ml_res, rule_res, [])
            
            results.append({
                "transaction_id": txn.get("transaction_id"),
                "risk_score": verdict.risk_score,
                "risk_level": verdict.risk_level,
                "is_guilty": verdict.is_guilty
            })
            
            # Update progress
            if i % 10 == 0 or i == total - 1:
                self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': total})
                
        except Exception as e:
            logger.error(f"Task error on txn {txn.get('transaction_id')}: {e}")
            
    return {
        "status": "completed",
        "total_processed": total,
        "flagged_count": sum(1 for r in results if r["is_guilty"]),
        "results": results[:500] # Limit result size in backend
    }
