"""
TESTS/test_full_flow.py
End-to-end integration tests — data → ML → detection → guilt → SAR → audit → PDF
Run: pytest TESTS/test_full_flow.py -v
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import pytest
import pandas as pd


# ─── Fixtures ─────────────────────────────────────────────────────────────────
HIGH_RISK_TXN = {
    "transaction_id": "E2E-001",
    "account_id":     "ACC-E2E",
    "amount":         970000.0,
    "timestamp":      "2024-06-15T02:30:00",
    "location":       "Cayman Islands",
    "channel":        "Wire Transfer",
    "currency":       "USD",
    "hour":           2,
    "is_weekend":     1,
    "is_high_risk_location": 1,
    "is_high_risk_channel":  1,
    "is_international": 1,
    "amount_log":     13.78,
    "near_threshold": 1,
    "acc_mean_amount": 30000.0,
    "acc_std_amount":  8000.0,
    "acc_txn_count":   5,
    "acc_max_amount":  970000.0,
    "amount_vs_mean":  32.33,
    "amount_zscore":   118.75,
}

LOW_RISK_TXN = {
    "transaction_id": "E2E-002",
    "account_id":     "ACC-NORMAL",
    "amount":         1500.0,
    "timestamp":      "2024-06-15T10:00:00",
    "location":       "Mumbai",
    "channel":        "Online",
    "currency":       "INR",
    "hour":           10,
    "is_weekend":     0,
    "is_high_risk_location": 0,
    "is_high_risk_channel":  0,
    "is_international": 0,
    "amount_log":     7.31,
    "near_threshold": 0,
    "acc_mean_amount": 2000.0,
    "acc_std_amount":  500.0,
    "acc_txn_count":   50,
    "acc_max_amount":  5000.0,
    "amount_vs_mean":  0.75,
    "amount_zscore":   -1.0,
}


# ─── 1. Data Layer ────────────────────────────────────────────────────────────
class TestDataGeneration:
    def test_generate_dataset(self):
        from DATA.generate_data import generate_dataset, add_features
        df = generate_dataset(n_accounts=50, fraud_ratio=0.05)
        assert len(df) > 100
        assert "is_suspicious" in df.columns
        assert df["is_suspicious"].sum() > 0

    def test_add_features(self):
        from DATA.generate_data import generate_dataset, add_features
        df = generate_dataset(n_accounts=30, fraud_ratio=0.05)
        df_feat = add_features(df)
        assert "near_threshold" in df_feat.columns
        assert "amount_zscore"  in df_feat.columns
        assert "amount_log"     in df_feat.columns


# ─── 2. ML Layer ─────────────────────────────────────────────────────────────
class TestMLModel:
    def test_predict_returns_required_fields(self):
        from ML.train_model import predict_transaction
        result = predict_transaction(HIGH_RISK_TXN)
        assert "is_suspicious" in result
        assert "risk_score"    in result
        assert "risk_level"    in result
        assert 0 <= result["risk_score"] <= 1

    def test_high_risk_txn_score_higher(self):
        from ML.train_model import predict_transaction
        high = predict_transaction(HIGH_RISK_TXN)
        low  = predict_transaction(LOW_RISK_TXN)
        assert high["risk_score"] >= low["risk_score"]

    def test_risk_levels_valid(self):
        from ML.train_model import predict_transaction
        r = predict_transaction(HIGH_RISK_TXN)
        assert r["risk_level"] in ("HIGH","MEDIUM","LOW")


# ─── 3. Detection Layer ───────────────────────────────────────────────────────
class TestDetectionEngine:
    def test_structuring_detected(self):
        from DETECTION.cpp_runner import _python_structuring
        txn = {"amount": 950000.0}
        result = _python_structuring(txn)
        assert result is not None
        assert result["rule"] == "STRUCTURING"
        assert result["score"] >= 0.65

    def test_layering_detected(self):
        from DETECTION.cpp_runner import _python_layering
        txn = {"amount": 800000, "location": "Cayman Islands",
               "channel": "Wire Transfer", "currency": "USD"}
        result = _python_layering(txn)
        assert result is not None
        assert result["rule"] == "LAYERING"

    def test_smurfing_detected(self):
        from DETECTION.cpp_runner import _python_smurfing
        txn = {"amount": 15000, "hour": 2, "is_weekend": 0}
        result = _python_smurfing(txn)
        assert result is not None
        assert result["rule"] == "SMURFING"

    def test_normal_txn_no_flags(self):
        from DETECTION.cpp_runner import _python_structuring, _python_layering, _python_smurfing
        txn = {"amount": 5000, "location": "Mumbai", "channel": "Online",
               "currency": "INR", "hour": 14, "is_weekend": 0}
        assert _python_structuring(txn) is None
        assert _python_layering(txn)    is None
        assert _python_smurfing(txn)    is None

    def test_run_detection_api(self):
        from DETECTION.cpp_runner import run_detection
        r = run_detection(HIGH_RISK_TXN)
        assert "is_flagged"      in r
        assert "risk_score"      in r
        assert "triggered_rules" in r
        assert r["is_flagged"] is True


# ─── 4. Reasoning Layer ───────────────────────────────────────────────────────
class TestGuiltEngine:
    def test_compute_guilt_high_risk(self):
        from REASONING.guilt_engine import compute_guilt
        from ML.train_model import predict_transaction
        from DETECTION.cpp_runner import run_detection
        ml   = predict_transaction(HIGH_RISK_TXN)
        rule = run_detection(HIGH_RISK_TXN)
        v    = compute_guilt(HIGH_RISK_TXN, ml, rule)
        assert v.risk_level in ("HIGH","MEDIUM","LOW")
        assert 0 <= v.risk_score <= 1
        assert isinstance(v.recommendation, str)
        assert len(v.recommendation) > 10

    def test_fusion_logic(self):
        from REASONING.guilt_engine import _fuse_scores
        assert _fuse_scores(0.9, 0.9) >= 0.85
        assert _fuse_scores(0.1, 0.1) <= 0.2
        # High rule score should boost fused score
        fused_boost = _fuse_scores(0.5, 0.9)
        fused_no    = _fuse_scores(0.5, 0.5)
        assert fused_boost > fused_no


# ─── 5. SAR Layer ─────────────────────────────────────────────────────────────
class TestSARGeneration:
    def _build_verdict(self):
        from ML.train_model import predict_transaction
        from DETECTION.cpp_runner import run_detection
        from REASONING.guilt_engine import compute_guilt
        ml   = predict_transaction(HIGH_RISK_TXN)
        rule = run_detection(HIGH_RISK_TXN)
        v    = compute_guilt(HIGH_RISK_TXN, ml, rule)
        return v.to_dict()

    def test_template_sar_generated(self):
        from AI.local_llm import generate_sar_template
        v = self._build_verdict()
        r = generate_sar_template(v)
        assert "sar_text" in r
        assert len(r["sar_text"]) > 200
        assert "SUSPICIOUS ACTIVITY REPORT" in r["sar_text"]
        assert "PMLA" in r["sar_text"]

    def test_sar_contains_txn_id(self):
        from AI.local_llm import generate_sar_template
        v = self._build_verdict()
        r = generate_sar_template(v)
        assert "E2E-001" in r["sar_text"]


# ─── 6. Audit Layer ──────────────────────────────────────────────────────────
class TestAuditChain:
    def test_append_and_verify(self):
        from AUDIT.hash_chain import append_event, verify_chain
        append_event("TEST_EVENT", {"key":"value","test":True}, actor="pytest")
        result = verify_chain()
        assert result["valid"] is True
        assert result["total_events"] >= 1

    def test_genesis_hash(self):
        from AUDIT.hash_chain import GENESIS_HASH
        assert len(GENESIS_HASH) == 64
        assert all(c == "0" for c in GENESIS_HASH)

    def test_hash_is_deterministic(self):
        import hashlib
        data = "test_payload_123"
        h1 = hashlib.sha256(data.encode()).hexdigest()
        h2 = hashlib.sha256(data.encode()).hexdigest()
        assert h1 == h2

    def test_recent_events_returns_list(self):
        from AUDIT.hash_chain import get_recent_events
        events = get_recent_events(5)
        assert isinstance(events, list)


# ─── 7. Password Utils ────────────────────────────────────────────────────────
class TestPasswordUtils:
    def test_hash_and_verify(self):
        from AUTH.password_utils import hash_password, verify_password
        pw   = "TestPassword@123"
        h    = hash_password(pw)
        assert verify_password(pw, h) is True
        assert verify_password("wrongpass", h) is False

    def test_hashes_are_unique(self):
        from AUTH.password_utils import hash_password
        h1 = hash_password("SamePwd@1")
        h2 = hash_password("SamePwd@1")
        assert h1 != h2   # bcrypt salt randomness

    def test_short_password_rejected(self):
        from AUTH.password_utils import hash_password
        with pytest.raises(ValueError):
            hash_password("abc")

    def test_strength_validator(self):
        from AUTH.password_utils import validate_password_strength
        assert validate_password_strength("Strong@123")["is_valid"] is True
        assert validate_password_strength("weak")["is_valid"]       is False


# ─── 8. PDF Generation ────────────────────────────────────────────────────────
class TestPDFGeneration:
    def test_pdf_bytes_generated(self):
        from REPORTS.pdf_generator import generate_pdf
        verdict = {
            "transaction_id": "PDF-001",
            "account_id":     "ACC-999",
            "risk_score":     0.87,
            "risk_level":     "HIGH",
            "triggered_rules":["STRUCTURING"],
            "legal_violations": [],
            "top_reasons":    [],
            "recommendation": "File SAR immediately",
            "metadata":       {"amount":950000,"channel":"Wire Transfer","location":"Cayman Islands"}
        }
        pdf = generate_pdf(verdict, "Sample SAR narrative text for testing.", "abc123hash")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000
        assert pdf[:4] == b"%PDF"   # Valid PDF header


# ─── 9. Async Batch Flow ──────────────────────────────────────────────────────
class TestAsyncBatchFlow:
    def test_full_async_pipeline(self):
        """
        Tests the async pipeline via component calls.
        Note: Real E2E via API requires a running worker or eager mode.
        """
        from BACKEND.celery_app import celery_app
        from BACKEND.tasks import process_batch_transactions
        from AUDIT.hash_chain import get_recent_events
        
        # Force eager mode for this test so it runs synchronously
        celery_app.conf.task_always_eager = True
        
        txns = [
            {"transaction_id": "ASYNC-1", "amount": 500, "location": "Local"},
            {"transaction_id": "ASYNC-2", "amount": 990000, "location": "Panama"}
        ]
        
        # Trigger task
        result = process_batch_transactions.apply(args=[txns]).get()
        
        assert result["status"] == "completed"
        assert result["total_processed"] == 2
        assert result["flagged_count"] >= 1
        
        # Verify it hit the audit chain
        events = get_recent_events(5)
        batch_events = [e for e in events if e["event_type"] == "BATCH_ANALYSIS_ASYNC_COMPLETED"]
        assert len(batch_events) > 0
        assert batch_events[0]["data"]["total_processed"] == 2
