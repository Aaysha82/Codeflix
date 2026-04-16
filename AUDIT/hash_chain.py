"""
AUDIT/hash_chain.py
Tamper-proof audit chain with SQLAlchemy persistence
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger
from BACKEND.database import AuditEvent, SessionLocal

GENESIS_HASH = "0" * 64

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def append_event(event_type: str, event_data: dict, actor: str = "system") -> dict:
    """Append a new event block to the database-backed hash chain."""
    db = SessionLocal()
    try:
        # Get latest event for prev_hash
        last_event = db.query(AuditEvent).order_by(AuditEvent.seq.desc()).first()
        prev_hash = last_event.current_hash if last_event else GENESIS_HASH
        seq = (last_event.seq + 1) if last_event else 1
        
        block_id = str(uuid.uuid4())
        timestamp_str = datetime.now(timezone.utc).isoformat()
        
        # Prepare payload for hashing (exclude current_hash itself)
        payload_dict = {
            "event_id": block_id,
            "seq": seq,
            "event_type": event_type,
            "actor": actor,
            "timestamp": timestamp_str,
            "event_data": event_data,
            "prev_hash": prev_hash
        }
        payload_json = json.dumps(payload_dict, sort_keys=True, default=str)
        current_hash = _sha256(payload_json)
        
        event = AuditEvent(
            event_id=block_id,
            seq=seq,
            event_type=event_type,
            actor=actor,
            timestamp=timestamp_str,
            event_data=event_data,
            prev_hash=prev_hash,
            current_hash=current_hash
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Audit [{seq}] {event_type} logged → {current_hash[:12]}")
        
        return {
            "event_id": event.event_id,
            "seq": event.seq,
            "event_type": event.event_type,
            "actor": event.actor,
            "timestamp": event.timestamp,  # Already a string
            "current_hash": event.current_hash
        }
    finally:
        db.close()

def verify_chain() -> dict:
    """Full cryptographic verification of the audit chain."""
    db = SessionLocal()
    try:
        events = db.query(AuditEvent).order_by(AuditEvent.seq.asc()).all()
        if not events:
            return {"valid": True, "total_events": 0}
            
        expected_prev = GENESIS_HASH
        for i, ev in enumerate(events):
            if ev.prev_hash != expected_prev:
                return {"valid": False, "broken_at": ev.seq, "reason": "Chain linkage broken"}
            
            payload_dict = {
                "event_id": ev.event_id,
                "seq": ev.seq,
                "event_type": ev.event_type,
                "actor": ev.actor,
                "timestamp": ev.timestamp,  # Now a string directly
                "event_data": ev.event_data,
                "prev_hash": ev.prev_hash
            }
            payload_json = json.dumps(payload_dict, sort_keys=True, default=str)
            if _sha256(payload_json) != ev.current_hash:
                return {"valid": False, "broken_at": ev.seq, "reason": "Hash mismatch/Tampering detected"}
            
            expected_prev = ev.current_hash
            
        return {"valid": True, "total_events": len(events)}
    finally:
        db.close()

def get_recent_events(limit: int = 50) -> List[dict]:
    db = SessionLocal()
    try:
        events = db.query(AuditEvent).order_by(AuditEvent.seq.desc()).limit(limit).all()
        return [
            {
                "seq": e.seq,
                "event_type": e.event_type,
                "actor": e.actor,
                "timestamp": e.timestamp,  # Already a string
                "current_hash": e.current_hash,
                "event_data": e.event_data
            } for e in events
        ]
    finally:
        db.close()

def get_event(event_id: str) -> Optional[dict]:
    db = SessionLocal()
    try:
        e = db.query(AuditEvent).filter(AuditEvent.event_id == event_id).first()
        if not e: return None
        return {
            "event_id": e.event_id,
            "seq": e.seq,
            "event_type": e.event_type,
            "actor": e.actor,
            "timestamp": e.timestamp,  # Already a string
            "event_data": e.event_data,
            "current_hash": e.current_hash
        }
    finally:
        db.close()

# ─── Logic Wrappers ───────────────────────────────────────────────────────────
def log_login(username: str, role: str, success: bool) -> dict:
    return append_event("AUTH_LOGIN", {"username": username, "role": role, "success": success}, actor=username)

def log_analysis(txn_id: str, risk_score: float, risk_level: str, actor: str, extra_data: dict = None) -> dict:
    data = {"transaction_id": txn_id, "risk_score": risk_score, "risk_level": risk_level}
    if extra_data: data.update(extra_data)
    return append_event("TRANSACTION_ANALYZED", data, actor=actor)

def log_sar_generated(txn_id: str, account_id: str, sar_text: str, actor: str) -> dict:
    return append_event("SAR_GENERATED", {
        "transaction_id": txn_id,
        "account_id": account_id,
        "content_hash": hashlib.sha256(sar_text.encode()).hexdigest(),
        "preview": sar_text[:150] + "..."
    }, actor=actor)

def log_alert_sent(txn_id: str, recipient: str, alert_type: str) -> dict:
    return append_event("ALERT_SENT", {
        "transaction_id": txn_id, "recipient": recipient, "alert_type": alert_type
    }, actor="system")
