"""
TESTS/test_api.py
FastAPI backend unit & integration tests
Run: pytest TESTS/test_api.py -v
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from BACKEND.main import app

client = TestClient(app)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_token(username="admin", password="Admin@2026"):
    resp = client.post("/auth/login", json={"username": username, "password": password})
    if resp.status_code == 200:
        return resp.json()["access_token"]
    return None


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


SAMPLE_TXN = {
    "transaction_id": "TEST-001",
    "account_id":     "ACC-TEST",
    "amount":         950000.0,
    "location":       "Cayman Islands",
    "channel":        "Wire Transfer",
    "currency":       "USD",
    "hour":           2,
    "is_weekend":     1,
    "is_high_risk_location": 1,
    "is_high_risk_channel":  1,
    "is_international": 1,
    "amount_log":     13.76,
    "near_threshold": 1,
    "acc_mean_amount": 50000.0,
    "acc_std_amount":  15000.0,
    "acc_txn_count":   10,
    "acc_max_amount":  1000000.0,
    "amount_vs_mean":  19.0,
    "amount_zscore":   60.0,
}


# ─── Health ───────────────────────────────────────────────────────────────────
class TestHealth:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "ProofSAR AI"

    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ─── Auth ─────────────────────────────────────────────────────────────────────
class TestAuth:
    def test_login_admin_success(self):
        r = client.post("/auth/login", json={"username":"admin","password":"Admin@2026"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_analyst_success(self):
        r = client.post("/auth/login", json={"username":"analyst","password":"Analyst@2026"})
        assert r.status_code == 200
        assert r.json()["role"] == "analyst"

    def test_login_wrong_password(self):
        r = client.post("/auth/login", json={"username":"admin","password":"wrongpass"})
        assert r.status_code == 401

    def test_login_unknown_user(self):
        r = client.post("/auth/login", json={"username":"nobody","password":"pass"})
        assert r.status_code == 401

    def test_me_with_token(self):
        token = get_token()
        assert token is not None
        r = client.get("/auth/me", headers=auth_headers(token))
        assert r.status_code == 200
        assert r.json()["username"] == "admin"

    def test_me_without_token(self):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_invalid_token(self):
        r = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401


# ─── Analysis ─────────────────────────────────────────────────────────────────
class TestAnalysis:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = get_token()
        self.headers = auth_headers(self.token)

    def test_analyze_high_risk(self):
        r = client.post("/analyze", json=SAMPLE_TXN, headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "risk_score"    in data
        assert "risk_level"    in data
        assert "is_suspicious" in data
        assert "audit_hash"    in data
        assert data["risk_level"] in ("HIGH","MEDIUM","LOW")

    def test_analyze_low_risk(self):
        low_txn = {**SAMPLE_TXN,
                   "amount": 5000.0,
                   "location": "Mumbai",
                   "channel":  "Online",
                   "currency": "INR",
                   "is_high_risk_location": 0,
                   "is_high_risk_channel":  0,
                   "is_international": 0,
                   "near_threshold": 0,
                   "amount_vs_mean": 0.1,
                   "amount_zscore": -0.5}
        r = client.post("/analyze", json=low_txn, headers=self.headers)
        assert r.status_code == 200

    def test_analyze_requires_auth(self):
        r = client.post("/analyze", json=SAMPLE_TXN)
        assert r.status_code == 401

    def test_analyze_invalid_amount(self):
        bad = {**SAMPLE_TXN, "amount": -100}
        r = client.post("/analyze", json=bad, headers=self.headers)
        assert r.status_code == 422


# ─── SAR Generation ───────────────────────────────────────────────────────────
class TestSAR:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token   = get_token()
        self.headers = auth_headers(self.token)

    def test_generate_sar(self):
        verdict = {
            "transaction_id": "TEST-SAR-001",
            "account_id":     "ACC-999",
            "risk_score":     0.87,
            "risk_level":     "HIGH",
            "triggered_rules":["STRUCTURING","LAYERING"],
            "legal_violations": [],
            "top_reasons":    [],
            "recommendation": "File SAR immediately",
            "metadata":       {"amount":950000,"channel":"Wire Transfer","location":"Cayman Islands"}
        }
        r = client.post("/generate-sar", json={"verdict": verdict}, headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "sar_text" in data
        assert len(data["sar_text"]) > 100

    def test_generate_sar_requires_auth(self):
        r = client.post("/generate-sar", json={"verdict":{}})
        assert r.status_code == 401


# ─── Audit ────────────────────────────────────────────────────────────────────
class TestAudit:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.token   = get_token()
        self.headers = auth_headers(self.token)

    def test_verify_chain(self):
        r = client.get("/audit/verify", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "valid"        in data
        assert "total_events" in data

    def test_get_events(self):
        r = client.get("/audit/events?limit=10", headers=self.headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_metrics(self):
        r = client.get("/metrics", headers=self.headers)
        assert r.status_code == 200
        data = r.json()
        assert "total_analyses" in data
        assert "chain_integrity" in data
