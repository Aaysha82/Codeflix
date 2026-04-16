"""
run_app.py
ProofSAR AI -- Single launcher script
Starts both FastAPI backend and Streamlit frontend.
"""
import sys, os, time, subprocess, threading, signal, platform

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

# Use python -m to avoid PATH issues
BACKEND_CMD  = [sys.executable, "-m", "uvicorn", "BACKEND.main:app",
                "--host", "0.0.0.0", "--port", "8000"]
FRONTEND_CMD = [sys.executable, "-m", "streamlit", "run", "FRONTEND/app.py",
                "--server.port", "8501", "--server.headless", "true"]
CELERY_CMD  = [sys.executable, "-m", "celery", "-A", "BACKEND.celery_app", "worker",
                "--loglevel", "info", "-P", "solo"] # -P solo for Windows stability

BANNER = """
+--------------------------------------------------------------+
|                                                              |
|   ProofSAR AI -- AML & SAR Automation System                 |
|                                                              |
|   Backend  -> http://localhost:8000                           |
|   API Docs -> http://localhost:8000/docs                      |
|   Frontend -> http://localhost:8501                           |
|   Worker   -> Celery (Active)                                 |
|                                                              |
|   Default Login:                                             |
|     admin   / Admin@2026   (full access)                     |
|     analyst / Analyst@2026 (read + generate SAR)             |
|                                                              |
+--------------------------------------------------------------+
"""

def run_cmd(cmd: list, name: str) -> subprocess.Popen:
    print(f"[{name}] Starting...")
    return subprocess.Popen(cmd)

def ensure_data():
    if not os.path.exists("DATA/transactions.csv"):
        print("[Setup] Generating dataset...")
        subprocess.run([sys.executable, "DATA/generate_data.py"])

def ensure_model():
    if not os.path.exists("ML/model.pkl"):
        print("[Setup] Training model...")
        subprocess.run([sys.executable, "ML/train_model.py"])

def compile_cpp():
    src = "DETECTION/structuring.cpp"
    out = "DETECTION/detector.exe" if platform.system() == "Windows" else "DETECTION/detector"
    inc = "-IDETECTION/include"
    
    # Try C++17, fallback to C++14 if needed (for GCC < 7)
    for std in ["-std=c++17", "-std=c++14"]:
        try:
            res = subprocess.run(["g++", "-o", out, src, std, inc], capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[Setup] C++ engine ready ({std}).")
                return
        except Exception:
            continue
    print("[Setup] Using Python fallback for detection.")

def clean_project():
    """Remove all generated files, caches, and build artifacts."""
    import shutil
    print("[Clean] Starting cleanup...")
    
    targets = [
        "DATA/transactions.csv",
        "DATA/transactions_test.csv",
        "DATA/proofsar.db",
        "ML/model.pkl",
        "ML/scaler.pkl",
        "ML/metrics.json",
        "AUDIT/audit_chain.json",
        "DETECTION/detector.exe",
        "DETECTION/detector",
        "BACKEND/app.log",
    ]
    
    # Remove specific files
    for t in targets:
        if os.path.exists(t):
            try:
                os.remove(t)
                print(f"  - Removed: {t}")
            except Exception as e:
                print(f"  - Failed to remove {t}: {e}")

    # Remove directories
    dirs = [
        "ML/mlruns",
        "REPORTS",   # Added REPORTS to clean
        "__pycache__",
        "BACKEND/__pycache__",
        "FRONTEND/__pycache__",
        "ML/__pycache__",
        "DETECTION/__pycache__",
        "AUTH/__pycache__",
        "AUDIT/__pycache__",
        "REASONING/__pycache__",
        "DATA/__pycache__",
        "AI/__pycache__",
        "ALERTS/__pycache__",
    ]
    
    for d in dirs:
        if os.path.exists(d):
            # For REPORTS, we probably just want to clear content or ensure it exists
            if d == "REPORTS":
                 shutil.rmtree(d)
                 os.makedirs(d, exist_ok=True)
                 print(f"  - Cleared directory: {d}")
                 continue
                 
            try:
                shutil.rmtree(d)
                print(f"  - Removed directory: {d}")
            except Exception as e:
                print(f"  - Failed to remove dir {d}: {e}")

    print("[Clean] Done.")

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    
    if mode == "clean":
        clean_project()
        return

    print(BANNER)
    
    os.makedirs("DATA", exist_ok=True)
    os.makedirs("ML",   exist_ok=True)
    os.makedirs("AUDIT", exist_ok=True)
    
    if mode == "train":
        ensure_data()
        ensure_model()
        return

    ensure_data()
    ensure_model()
    compile_cpp()

    procs = []
    if mode in ("backend", "both"):
        procs.append(run_cmd(BACKEND_CMD, "Backend"))
        procs.append(run_cmd(CELERY_CMD,  "Worker"))
    if mode in ("frontend", "both"):
        procs.append(run_cmd(FRONTEND_CMD, "Frontend"))

    print("\nProofSAR AI is running. Press Ctrl+C to stop.\n")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        for p in procs: p.terminate()

def test_pipeline():
    """Run a full end-to-end test of the ProofSAR AI pipeline."""
    from BACKEND.routes import TransactionInput
    from ML.train_model import predict_transaction
    from DETECTION.cpp_runner import run_detection
    from REASONING.guilt_engine import compute_guilt
    from AI.gemini_client import generate_sar_with_gemini
    from AUDIT.hash_chain import verify_chain, get_recent_events
    import json

    print("\n" + "="*60)
    print("   ProofSAR AI — END-TO-END PIPELINE TEST")
    print("="*60)

    # 1. Generate Transaction
    txn = {
        "transaction_id": "TEST_TXN_999",
        "account_id":     "TEST_ACC_888",
        "amount":         950000.0,  # Near 10L threshold
        "location":       "Panama",  # High risk
        "channel":        "Wire Transfer",
        "currency":       "INR",
        "hour":           3,
        "is_weekend":     1
    }
    print("=== TRANSACTION ===")
    print(json.dumps(txn, indent=2))

    # 2. Risk detection
    print("\n=== RISK ANALYSIS ===")
    ml_res = predict_transaction(txn)
    rule_res = run_detection(txn)
    print(f"ML Score  : {ml_res['risk_score']:.4f}")
    print(f"Rule Score: {rule_res['risk_score']:.4f}")
    print(f"Rules Hit : {rule_res['triggered_rules']}")

    # 3. Reasoning & Legal Mapping
    print("\n=== LEGAL MAPPING & EXPLANATION ===")
    verdict = compute_guilt(txn, ml_res, rule_res)
    for v in verdict.legal_violations:
        print(f"• {v['act']} ({v['section']}): {v['description']}")
    
    # 4. SAR Report
    print("\n=== SAR REPORT ===")
    sar = generate_sar_with_gemini(verdict.to_dict())
    try:
        print(sar["sar_text"][:500] + "...")
    except UnicodeEncodeError:
        print(sar["sar_text"][:500].encode('ascii', 'ignore').decode('ascii') + "...")


    # 5. Audit Hash
    print("\n=== AUDIT HASH ===")
    from AUDIT.hash_chain import log_analysis, log_sar_generated
    analysis_rec = log_analysis(txn["transaction_id"], verdict.risk_score, verdict.risk_level, "tester")
    sar_rec = log_sar_generated(txn["transaction_id"], txn["account_id"], sar["sar_text"], "tester")
    print(f"Analysis Hash: {analysis_rec['current_hash']}")
    print(f"SAR Hash     : {sar_rec['current_hash']}")
    
    status = verify_chain()
    print(f"Chain Integrity: {'VALID' if status['valid'] else 'BROKEN'}")
    print("="*60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_pipeline()
    else:
        main()

