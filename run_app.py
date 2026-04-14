"""
run_app.py
ProofSAR AI — Single launcher script
Starts both FastAPI backend and Streamlit frontend.

Usage:
  python run_app.py          # starts both
  python run_app.py backend  # backend only
  python run_app.py frontend # frontend only
  python run_app.py train    # train ML model only
  python run_app.py data     # generate data only
  python run_app.py test     # run all tests
"""
from __future__ import annotations
import sys, os, time, subprocess, threading, signal, platform

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

BACKEND_CMD  = [sys.executable, "-m", "uvicorn", "BACKEND.main:app",
                "--host", "0.0.0.0", "--port", "8000", "--reload"]
FRONTEND_CMD = [sys.executable, "-m", "streamlit", "run", "FRONTEND/app.py",
                "--server.port", "8501", "--server.headless", "true",
                "--server.fileWatcherType", "none"]

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🛡️  ProofSAR AI — AML & SAR Automation System             ║
║                                                              ║
║   Backend  → http://localhost:8000                           ║
║   API Docs → http://localhost:8000/docs                      ║
║   Frontend → http://localhost:8501                           ║
║                                                              ║
║   Default Login:                                             ║
║     admin   / Admin@2026   (full access)                     ║
║     analyst / Analyst@2026 (read + generate SAR)             ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_cmd(cmd: list, name: str) -> subprocess.Popen:
    print(f"[{name}] Starting: {' '.join(cmd)}")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, universal_newlines=True
    )
    def stream():
        for line in proc.stdout:
            print(f"[{name}] {line}", end="")
    t = threading.Thread(target=stream, daemon=True)
    t.start()
    return proc


def ensure_data():
    """Generate data if not present."""
    if not os.path.exists("DATA/transactions.csv"):
        print("[Setup] Generating synthetic AML dataset…")
        subprocess.run([sys.executable, "DATA/generate_data.py"], check=False)
    else:
        print("[Setup] Dataset found ✓")


def ensure_model():
    """Train model if not present."""
    if not os.path.exists("ML/model.pkl"):
        print("[Setup] Training ML model…")
        subprocess.run([sys.executable, "ML/train_model.py"], check=False)
    else:
        print("[Setup] Model found ✓")


def ensure_dirs():
    """Create required directories."""
    for d in ["DATA","ML","AUDIT","REPORTS","AUTH","BACKEND","FRONTEND",
              "DETECTION","REASONING","AI","ALERTS","TESTS","ANTIGRAVITY_OS"]:
        os.makedirs(d, exist_ok=True)


def compile_cpp():
    """Attempt to compile C++ detection engine."""
    src = "DETECTION/structuring.cpp"
    out = "DETECTION/detector.exe" if platform.system() == "Windows" else "DETECTION/detector"
    if os.path.exists(out):
        print("[Setup] C++ engine binary found ✓")
        return
    try:
        r = subprocess.run(["g++", "-o", out, src, "-std=c++17"],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            print("[Setup] C++ engine compiled ✓")
        else:
            print(f"[Setup] C++ compile failed (Python fallback will be used):\n{r.stderr[:200]}")
    except FileNotFoundError:
        print("[Setup] g++ not found — Python rule fallback will be used")


def run_tests():
    print("[Tests] Running full test suite…")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "TESTS/", "-v", "--tb=short"],
        cwd=ROOT
    )
    sys.exit(result.returncode)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    print(BANNER)

    if mode == "data":
        ensure_dirs()
        subprocess.run([sys.executable, "DATA/generate_data.py"])
        return

    if mode == "train":
        ensure_dirs()
        ensure_data()
        subprocess.run([sys.executable, "ML/train_model.py"])
        return

    if mode == "test":
        ensure_dirs()
        ensure_data()
        ensure_model()
        run_tests()
        return

    # Common setup for backend / frontend / both
    ensure_dirs()
    print("[Setup] Checking prerequisites…")
    ensure_data()
    ensure_model()
    compile_cpp()
    print("[Setup] All prerequisites ready ✓\n")

    procs = []

    if mode in ("backend", "both"):
        procs.append(run_cmd(BACKEND_CMD, "Backend"))
        time.sleep(3)   # Let backend start

    if mode in ("frontend", "both"):
        procs.append(run_cmd(FRONTEND_CMD, "Frontend"))

    if not procs:
        print(f"Unknown mode: {mode}. Use: both | backend | frontend | train | data | test")
        sys.exit(1)

    print("\n[Launch] ProofSAR AI is running! Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\n[Shutdown] Stopping all processes…")
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while all(p.poll() is None for p in procs):
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
