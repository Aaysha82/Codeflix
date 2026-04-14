"""
BACKEND/routes.py
All FastAPI route handlers — analysis, SAR, audit, alerts, auth
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone
from typing import Optional, Annotated
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import pandas as pd
import io

from AUTH.auth        import register_user, login_user, get_current_user, list_users
from AUTH.jwt_handler import has_permission
from ML.train_model   import predict_transaction, load_model
from ML.explainability import get_top_reasons, generate_narrative
from DETECTION.cpp_runner  import run_detection, run_batch_detection
from REASONING.guilt_engine import compute_guilt
from AUDIT.hash_chain  import (
    append_event, verify_chain, get_event,
    get_recent_events, log_login, log_analysis,
    log_sar_generated, log_alert_sent
)
from AI.gemini_client  import generate_sar_with_gemini
from ALERTS.gmail_service import send_high_risk_alert, send_sar_generated_alert
from loguru import logger

router = APIRouter()
bearer = HTTPBearer(auto_error=False)


# ─── Auth helpers ─────────────────────────────────────────────────────────────
def get_token(creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)]) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return creds.credentials


def current_user(token: str = Depends(get_token)) -> dict:
    user = get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_permission(permission: str):
    def checker(user: dict = Depends(current_user)):
        if not has_permission(user["role"], permission):
            raise HTTPException(status_code=403, detail=f"Permission denied: {permission}")
        return user
    return checker


# ─── Pydantic schemas ─────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    email:    str
    role:     str = "analyst"


class LoginRequest(BaseModel):
    username: str
    password: str


class TransactionInput(BaseModel):
    transaction_id:      str   = "txn_000"
    account_id:          str   = "acc_000"
    amount:              float = Field(gt=0)
    timestamp:           str   = ""
    location:            str   = "Mumbai"
    channel:             str   = "Online"
    currency:            str   = "INR"
    hour:                int   = 12
    is_weekend:          int   = 0
    is_high_risk_location: int = 0
    is_high_risk_channel:  int = 0
    is_international:    int   = 0
    amount_log:          float = 0
    near_threshold:      int   = 0
    acc_mean_amount:     float = 0
    acc_std_amount:      float = 0
    acc_txn_count:       int   = 1
    acc_max_amount:      float = 0
    amount_vs_mean:      float = 1
    amount_zscore:       float = 0


class AnalyzeResponse(BaseModel):
    transaction_id: str
    is_suspicious:  bool
    risk_score:     float
    risk_level:     str
    triggered_rules: list
    explanations:   list
    top_reasons:    list
    recommendation: str
    sar_required:   bool
    narrative:      str
    audit_hash:     str


class SARRequest(BaseModel):
    verdict: dict


# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────
@router.post("/auth/register", tags=["Auth"], status_code=201)
def register(req: RegisterRequest,
             _user: dict = Depends(require_permission("manage_users"))):
    try:
        result = register_user(req.username, req.password, req.email, req.role)
        append_event("USER_REGISTERED", {"username": req.username, "role": req.role},
                     actor=_user["username"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", tags=["Auth"])
def login(req: LoginRequest):
    try:
        result = login_user(req.username, req.password)
        log_login(req.username, result["role"], True)
        return result
    except ValueError as e:
        log_login(req.username, "unknown", False)
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/auth/me", tags=["Auth"])
def me(user: dict = Depends(current_user)):
    return user


@router.get("/auth/users", tags=["Auth"])
def users(_: dict = Depends(require_permission("manage_users"))):
    return list_users()


# ─── ANALYSIS ROUTES ──────────────────────────────────────────────────────────
@router.post("/analyze", tags=["Analysis"], response_model=AnalyzeResponse)
def analyze(txn: TransactionInput, user: dict = Depends(current_user)):
    """Full AML analysis pipeline: ML + C++ rules + SHAP + guilt verdict."""
    try:
        txn_dict = txn.model_dump()

        # ML prediction
        ml_result  = predict_transaction(txn_dict)

        # C++ rule detection
        rule_result = run_detection(txn_dict)

        # SHAP explanations
        try:
            shap_reasons = get_top_reasons(txn_dict, top_k=5)
        except Exception as e:
            logger.warning(f"SHAP failed: {e}")
            shap_reasons = []

        # Guilt verdict
        verdict = compute_guilt(txn_dict, ml_result, rule_result, shap_reasons)

        # Audit log
        audit_rec = log_analysis(
            txn.transaction_id, verdict.risk_score,
            verdict.risk_level, user["username"]
        )

        # Auto-alert if HIGH risk
        if verdict.risk_level == "HIGH" and os.getenv("EMAIL_USER"):
            send_high_risk_alert(
                to_email        = os.getenv("EMAIL_USER", ""),
                txn_id          = txn.transaction_id,
                account         = txn.account_id,
                amount          = txn.amount,
                risk_score      = verdict.risk_score,
                risk_level      = verdict.risk_level,
                triggered_rules = verdict.triggered_rules
            )
            log_alert_sent(txn.transaction_id, os.getenv("EMAIL_USER",""), "HIGH_RISK")

        return AnalyzeResponse(
            transaction_id  = verdict.transaction_id,
            is_suspicious   = verdict.is_guilty,
            risk_score      = verdict.risk_score,
            risk_level      = verdict.risk_level,
            triggered_rules = verdict.triggered_rules,
            explanations    = verdict.explanations,
            top_reasons     = verdict.top_reasons,
            recommendation  = verdict.recommendation,
            sar_required    = verdict.sar_required,
            narrative       = verdict.narrative,
            audit_hash      = audit_rec["current_hash"]
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/batch", tags=["Analysis"])
async def analyze_batch(
    file: UploadFile = File(...),
    user: dict = Depends(current_user)
):
    """Batch analysis from uploaded CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        required = ["transaction_id","account_id","amount"]
        missing  = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing columns: {missing}")

        results = run_batch_detection(df.to_dict("records"))
        flagged = [r for r in results if r.get("is_flagged")]
        append_event("BATCH_ANALYSIS", {
            "total": len(results), "flagged": len(flagged),
            "filename": file.filename
        }, actor=user["username"])
        return {
            "total": len(results),
            "flagged": len(flagged),
            "flagged_pct": round(len(flagged)/max(len(results),1)*100, 2),
            "results": results[:100]   # cap response size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── SAR ROUTES ───────────────────────────────────────────────────────────────
@router.post("/generate-sar", tags=["SAR"])
def generate_sar(req: SARRequest,
                 user: dict = Depends(require_permission("generate_sar"))):
    """Generate SAR narrative using Gemini or template fallback."""
    try:
        verdict  = req.verdict
        sar_resp = generate_sar_with_gemini(verdict)
        sar_id   = sar_resp.get("sar_id", f"SAR-{datetime.now().strftime('%Y%m%d%H%M%S')}")

        audit_rec = log_sar_generated(
            verdict.get("transaction_id", "N/A"),
            verdict.get("account_id",     "N/A"),
            actor = user["username"]
        )

        # Alert compliance email
        email = os.getenv("EMAIL_USER", "")
        if email:
            send_sar_generated_alert(
                to_email   = email,
                sar_id     = sar_id,
                txn_id     = verdict.get("transaction_id", "N/A"),
                account    = verdict.get("account_id",     "N/A"),
                risk_level = verdict.get("risk_level",     "N/A")
            )
            log_alert_sent(verdict.get("transaction_id","N/A"), email, "SAR_GENERATED")

        return {
            **sar_resp,
            "sar_id":     sar_id,
            "generated_by": user["username"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audit_hash": audit_rec["current_hash"]
        }
    except Exception as e:
        logger.error(f"SAR generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── AUDIT ROUTES ─────────────────────────────────────────────────────────────
@router.get("/audit/verify", tags=["Audit"])
def verify_audit(_: dict = Depends(require_permission("view_audit"))):
    """Verify the integrity of the full audit chain."""
    return verify_chain()


@router.get("/audit/events", tags=["Audit"])
def audit_events(
    limit: int = 50,
    _: dict = Depends(require_permission("view_audit"))
):
    """Get most recent audit events."""
    return get_recent_events(limit)


@router.get("/audit/{event_id}", tags=["Audit"])
def audit_event(
    event_id: str,
    _: dict = Depends(require_permission("view_audit"))
):
    """Get a specific audit event by ID."""
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return event


# ─── ALERTS ROUTE ─────────────────────────────────────────────────────────────
@router.get("/alerts", tags=["Alerts"])
def alerts(_: dict = Depends(current_user)):
    """Return recent alert events from audit chain."""
    events = get_recent_events(100)
    return [e for e in events if e.get("event_type") in ("ALERT_SENT", "SAR_GENERATED")]


# ─── HEALTH & METRICS ─────────────────────────────────────────────────────────
@router.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "ProofSAR AI", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/metrics", tags=["System"])
def metrics(_: dict = Depends(current_user)):
    """High-level system metrics."""
    events = get_recent_events(1000)
    return {
        "total_analyses":  sum(1 for e in events if e["event_type"] == "TRANSACTION_ANALYZED"),
        "total_sars":      sum(1 for e in events if e["event_type"] == "SAR_GENERATED"),
        "total_alerts":    sum(1 for e in events if e["event_type"] == "ALERT_SENT"),
        "chain_integrity": verify_chain()["valid"],
        "total_events":    len(events)
    }
