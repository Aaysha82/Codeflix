"""
AUDIT/hash_chain.py
SHA-256 tamper-proof audit log chain.
Each event is hashed with the previous hash, forming an immutable chain.
"""
from __future__ import annotations
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from loguru import logger

AUDIT_FILE = "AUDIT/audit_chain.json"
GENESIS_HASH = "0" * 64   # genesis / null previous hash


# ─── Internal helpers ─────────────────────────────────────────────────────────
def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _load_chain() -> list[dict]:
    if not os.path.exists(AUDIT_FILE):
        os.makedirs("AUDIT", exist_ok=True)
        return []
    with open(AUDIT_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.error("Audit chain corrupted — returning empty chain")
            return []


def _save_chain(chain: list[dict]) -> None:
    with open(AUDIT_FILE, "w") as f:
        json.dump(chain, f, indent=2, default=str)


# ─── Public API ───────────────────────────────────────────────────────────────
def append_event(event_type: str, event_data: dict, actor: str = "system") -> dict:
    """
    Append a new event to the audit chain.

    Returns the new audit record (with hashes).
    """
    chain = _load_chain()
    prev_hash = chain[-1]["current_hash"] if chain else GENESIS_HASH

    block = {
        "event_id":    str(uuid.uuid4()),
        "seq":         len(chain) + 1,
        "event_type":  event_type,
        "actor":       actor,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "event_data":  event_data,
        "prev_hash":   prev_hash,
    }

    block_payload = json.dumps(
        {k: v for k, v in block.items() if k != "current_hash"},
        sort_keys=True, default=str
    )
    block["current_hash"] = _sha256(block_payload)

    chain.append(block)
    _save_chain(chain)
    logger.info(f"Audit [{block['seq']}] {event_type} by {actor} → {block['current_hash'][:12]}…")
    return block


def verify_chain() -> dict:
    """
    Verify the integrity of the entire audit chain.
    Returns {valid: bool, broken_at: int|None, total_events: int}.
    """
    chain = _load_chain()
    if not chain:
        return {"valid": True, "broken_at": None, "total_events": 0, "message": "Empty chain"}

    expected_prev = GENESIS_HASH
    for i, block in enumerate(chain):
        # Check prev_hash linkage
        if block["prev_hash"] != expected_prev:
            return {
                "valid": False,
                "broken_at": i + 1,
                "total_events": len(chain),
                "message": f"Chain broken at event #{i + 1} — prev_hash mismatch"
            }
        # Recompute current_hash
        payload = json.dumps(
            {k: v for k, v in block.items() if k != "current_hash"},
            sort_keys=True, default=str
        )
        expected_hash = _sha256(payload)
        if block["current_hash"] != expected_hash:
            return {
                "valid": False,
                "broken_at": i + 1,
                "total_events": len(chain),
                "message": f"Block #{i + 1} hash mismatch — data may have been tampered"
            }
        expected_prev = block["current_hash"]

    return {
        "valid": True,
        "broken_at": None,
        "total_events": len(chain),
        "message": f"Chain intact — {len(chain)} events verified"
    }


def get_event(event_id: str) -> dict | None:
    """Fetch a single event by its UUID."""
    for block in _load_chain():
        if block["event_id"] == event_id:
            return block
    return None


def get_recent_events(limit: int = 50) -> list[dict]:
    """Return most recent N audit events (newest first)."""
    chain = _load_chain()
    return list(reversed(chain[-limit:]))


def get_full_chain() -> list[dict]:
    """Return the full audit chain."""
    return _load_chain()


# ─── Convenience wrappers ─────────────────────────────────────────────────────
def log_login(username: str, role: str, success: bool) -> dict:
    return append_event("AUTH_LOGIN", {
        "username": username, "role": role, "success": success
    }, actor=username)


def log_analysis(txn_id: str, risk_score: float, risk_level: str, actor: str, extra_data: dict = None) -> dict:
    data = {
        "transaction_id": txn_id,
        "risk_score": risk_score,
        "risk_level": risk_level
    }
    if extra_data:
        data.update(extra_data)
    return append_event("TRANSACTION_ANALYZED", data, actor=actor)


def log_sar_generated(txn_id: str, account_id: str, sar_text: str, actor: str) -> dict:
    return append_event("SAR_GENERATED", {
        "transaction_id": txn_id,
        "account_id": account_id,
        "sar_content_hash": hashlib.sha256(sar_text.encode()).hexdigest(),
        "sar_preview": sar_text[:200] + "..."
    }, actor=actor)



def log_alert_sent(txn_id: str, recipient: str, alert_type: str) -> dict:
    return append_event("ALERT_SENT", {
        "transaction_id": txn_id, "recipient": recipient, "alert_type": alert_type
    }, actor="system")
