
from BACKEND.database import AuditEvent, SessionLocal
from datetime import datetime, timezone
import json

def debug_audit():
    db = SessionLocal()
    events = db.query(AuditEvent).order_by(AuditEvent.seq.asc()).all()
    for ev in events:
        print(f"Seq: {ev.seq}")
        print(f"  Type: {ev.event_type}")
        print(f"  DB Timestamp (repr): {repr(ev.timestamp)}")
        print(f"  DB ISO format      : {ev.timestamp.isoformat()}")
        
        # Reconstruct payload like verify_chain does
        payload_dict = {
            "event_id": ev.event_id,
            "seq": ev.seq,
            "event_type": ev.event_type,
            "actor": ev.actor,
            "timestamp": ev.timestamp.isoformat(),
            "event_data": ev.event_data,
            "prev_hash": ev.prev_hash
        }
        payload_json = json.dumps(payload_dict, sort_keys=True, default=str)
        import hashlib
        calc_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        print(f"  Stored Hash: {ev.current_hash}")
        print(f"  Calc Hash  : {calc_hash}")
        print(f"  Match      : {calc_hash == ev.current_hash}")
    db.close()

if __name__ == "__main__":
    debug_audit()
