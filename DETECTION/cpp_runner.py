"""
DETECTION/cpp_runner.py
Python wrapper that compiles and runs the C++ AML detection engine.
Falls back to pure-Python rules if g++ is unavailable.
"""
import os
import sys
import json
import subprocess
import platform
from loguru import logger

CPP_SOURCE = "DETECTION/structuring.cpp"
CPP_BINARY = "DETECTION/detector.exe" if platform.system() == "Windows" else "DETECTION/detector"

HIGH_RISK_LOCATIONS = {"Cayman Islands", "Panama", "Switzerland", "Dubai",
                        "British Virgin Islands", "Malta", "Isle of Man"}
HIGH_RISK_CHANNELS  = {"Wire Transfer", "RTGS", "SWIFT"}
FOREIGN_CURRENCIES  = {"USD", "EUR", "CHF", "AED", "GBP", "SGD"}
THRESHOLD = 1_000_000  # INR 10 lakh


# ─── Compile C++ binary ───────────────────────────────────────────────────────
def compile_cpp() -> bool:
    """Compile the C++ detection engine. Returns True on success."""
    if os.path.exists(CPP_BINARY):
        return True
    try:
        result = subprocess.run(
            ["g++", "-o", CPP_BINARY, CPP_SOURCE, "-std=c++17"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            logger.success("C++ detection engine compiled successfully")
            return True
        logger.warning(f"C++ compile failed:\n{result.stderr}")
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning(f"g++ not available ({e}); using Python fallback rules")
        return False


# ─── Python fallback rules ────────────────────────────────────────────────────
def _python_structuring(txn: dict) -> dict | None:
    amt = float(txn.get("amount", 0))
    if THRESHOLD * 0.80 <= amt <= THRESHOLD * 0.99:
        score = 0.65 + (amt / THRESHOLD - 0.80) / 0.20 * 0.30
        return {
            "rule": "STRUCTURING",
            "score": round(score, 4),
            "explanation": (
                f"Amount ₹{amt:,.0f} is {amt/THRESHOLD*100:.1f}% of the "
                f"₹10L reporting threshold — classic structuring pattern"
            )
        }
    return None


def _python_layering(txn: dict) -> dict | None:
    amt     = float(txn.get("amount",   0))
    loc     = txn.get("location",  "")
    ch      = txn.get("channel",   "")
    cur     = txn.get("currency",  "INR")
    flags   = sum([
        amt >= 500_000,
        loc in HIGH_RISK_LOCATIONS,
        ch  in HIGH_RISK_CHANNELS,
        cur in FOREIGN_CURRENCIES,
    ])
    if flags >= 2:
        score = min(0.95, 0.55 + flags * 0.10)
        return {
            "rule": "LAYERING",
            "score": round(score, 4),
            "explanation": (
                f"High-value {cur} transfer of ₹{amt:,.0f} via {ch} to {loc} — "
                "matches international layering pattern"
            )
        }
    return None


def _python_smurfing(txn: dict) -> dict | None:
    amt     = float(txn.get("amount",     0))
    hour    = int(txn.get("hour",         12))
    weekend = int(txn.get("is_weekend",   0))
    if 1_000 <= amt <= 50_000 and (hour <= 5 or weekend == 1):
        score = 0.60 + (0.10 if hour <= 5 else 0) + (0.05 if weekend else 0)
        return {
            "rule": "SMURFING",
            "score": round(score, 4),
            "explanation": (
                f"Small amount ₹{amt:,.0f} transacted at hour {hour:02d}:00 "
                "— consistent with smurfing activity"
            )
        }
    return None


def _run_python_rules(txn: dict) -> dict:
    """Pure-Python fallback for all three AML rules."""
    triggered, explanations, max_score = [], [], 0.0
    for fn in [_python_structuring, _python_layering, _python_smurfing]:
        hit = fn(txn)
        if hit:
            triggered.append(hit["rule"])
            explanations.append(hit["explanation"])
            max_score = max(max_score, hit["score"])
    return {
        "is_flagged":      len(triggered) > 0,
        "risk_score":      round(max_score, 4),
        "triggered_rules": triggered,
        "explanations":    explanations,
        "engine":          "python_fallback"
    }


# ─── C++ runner ───────────────────────────────────────────────────────────────
def _run_cpp_engine(txn: dict) -> dict:
    """Call compiled C++ binary with JSON input."""
    payload = json.dumps({
        "transaction_id": txn.get("transaction_id", ""),
        "account_id":     txn.get("account_id",     ""),
        "amount":         float(txn.get("amount",    0)),
        "location":       txn.get("location",        ""),
        "channel":        txn.get("channel",         ""),
        "currency":       txn.get("currency",        "INR"),
        "hour":           int(txn.get("hour",        0)),
        "is_weekend":     int(txn.get("is_weekend",  0))
    })
    result = subprocess.run(
        [CPP_BINARY, payload],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(f"C++ engine error: {result.stderr}")
    output = json.loads(result.stdout.strip())
    output["engine"] = "cpp"
    return output


# ─── Public API ───────────────────────────────────────────────────────────────
_cpp_available: bool | None = None   # lazy compile flag


def run_detection(txn: dict) -> dict:
    """
    Run AML rule detection on a single transaction dict.
    Returns:
        {
            is_flagged: bool,
            risk_score: float,
            triggered_rules: list[str],
            explanations: list[str],
            engine: str
        }
    """
    global _cpp_available
    if _cpp_available is None:
        _cpp_available = compile_cpp()

    if _cpp_available:
        try:
            return _run_cpp_engine(txn)
        except Exception as e:
            logger.warning(f"C++ engine failed ({e}); falling back to Python rules")
            return _run_python_rules(txn)
    return _run_python_rules(txn)


def run_batch_detection(transactions: list[dict]) -> list[dict]:
    """Run detection on a list of transactions."""
    results = []
    for txn in transactions:
        det = run_detection(txn)
        results.append({**txn, **det})
    return results
