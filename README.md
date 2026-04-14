# ProofSAR AI 🛡️
### Explainable Suspicious Activity Report (SAR) Generation System

> **From 5-hour SAR drafting → 5-minute regulator-ready explainable reports using AI**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.34-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 What It Does

ProofSAR AI automates the entire AML compliance workflow:

| Without ProofSAR AI | With ProofSAR AI |
|---------------------|-----------------|
| 5–6 hours per SAR | ~5 minutes |
| Black-box decisions | SHAP explainability |
| Manual rule checking | C++ OOP engine |
| No audit trail | SHA-256 hash chain |
| Email drafts | Regulator-ready PDF |

---

## 🏗️ Architecture

```
CSV/API Input
    │
    ▼
Data Preprocessor (Faker synthetic + real)
    │
    ├──► ML Model (RF + XGBoost + LR + SMOTE)
    │         │
    │         ▼
    │    SHAP Explainer → Human-readable reasons
    │
    ├──► C++ Detection Engine
    │    ├── Structuring  (near ₹10L threshold)
    │    ├── Layering     (offshore wire transfers)
    │    └── Smurfing     (small rapid transactions)
    │
    ▼
Guilt Engine (60% ML + 40% Rules fusion)
    │
    ▼
Gemini LLM → SAR Narrative + Legal Mapping (PMLA/RBI)
    │
    ├──► SHA-256 Audit Chain
    ├──► Gmail SMTP Alerts
    ├──► PDF Report (ReportLab)
    └──► FastAPI Backend ← Streamlit Frontend
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.11+
pip install -r requirements.txt

# (Optional) g++ for C++ detection engine
# Windows: Install MinGW or Visual Studio Build Tools
# Linux/Mac: sudo apt install g++ / xcode-select --install
```

### 2. Environment Variables

```bash
# Copy and fill .env
cp .env .env.local

# Required for AI SAR generation:
GEMINI_API_KEY=your_key_from_aistudio.google.com

# Required for email alerts:
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_16_char_app_password  # Gmail App Password, NOT account password

# JWT settings (change in production!):
JWT_SECRET=proofsar_super_secret_jwt_key_change_in_production_2026
```

### 3. Launch (All-in-one)

```bash
python run_app.py
```

This will:
1. Generate synthetic AML dataset (DATA/)
2. Train ML models → save best as ML/model.pkl
3. Compile C++ detection engine (if g++ available)
4. Start FastAPI backend on http://localhost:8000
5. Start Streamlit frontend on http://localhost:8501

### 4. Individual Commands

```bash
# Generate data only
python run_app.py data

# Train ML model only
python run_app.py train

# Backend only
python run_app.py backend

# Frontend only
python run_app.py frontend

# Run all tests
python run_app.py test
```

---

## 🔑 Default Credentials

| Role | Username | Password | Access |
|------|----------|----------|--------|
| Admin | `admin` | `Admin@2026` | Full system access |
| Analyst | `analyst` | `Analyst@2026` | Read + Generate SAR |

> ⚠️ Change these in production via `/auth/register`

---

## 📡 API Reference

Base URL: `http://localhost:8000`
Interactive Docs: `http://localhost:8000/docs`

### Authentication
```
POST /auth/login          — Login, get JWT token
POST /auth/register       — Register user (Admin only)
GET  /auth/me             — Get current user info
```

### Analysis
```
POST /analyze             — Analyze single transaction
POST /analyze/batch       — Batch CSV analysis
```

### SAR
```
POST /generate-sar        — Generate SAR narrative (Gemini or template)
```

### Audit
```
GET  /audit/verify        — Verify SHA-256 chain integrity
GET  /audit/events        — Get recent audit events
GET  /audit/{event_id}    — Get specific event
```

### Alerts & Metrics
```
GET  /alerts              — Recent alerts
GET  /metrics             — System KPIs
GET  /health              — Health check
```

### Example: Analyze Transaction

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@2026"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Analyze
curl -X POST http://localhost:8000/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-2024-001",
    "account_id": "ACC-78432",
    "amount": 950000.0,
    "location": "Cayman Islands",
    "channel": "Wire Transfer",
    "currency": "USD",
    "hour": 2,
    "is_weekend": 1,
    "is_high_risk_location": 1,
    "is_high_risk_channel": 1,
    "is_international": 1,
    "amount_log": 13.76,
    "near_threshold": 1,
    "acc_mean_amount": 50000.0,
    "acc_std_amount": 15000.0,
    "acc_txn_count": 10,
    "acc_max_amount": 1000000.0,
    "amount_vs_mean": 19.0,
    "amount_zscore": 60.0
  }'
```

---

## 🧪 Running Tests

```bash
# All tests
pytest TESTS/ -v

# API tests only
pytest TESTS/test_api.py -v

# Full flow tests
pytest TESTS/test_full_flow.py -v

# With coverage
pytest TESTS/ --cov=. --cov-report=term-missing
```

---

## 📁 Project Structure

```
ProofSAR-AI/
├── ANTIGRAVITY_OS/       # Project management docs
│   ├── PROJECT.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   └── ISSUES.md
│
├── AUTH/                 # JWT + bcrypt authentication
│   ├── auth.py
│   ├── jwt_handler.py
│   └── password_utils.py
│
├── DATA/                 # Transaction data
│   ├── generate_data.py  # Faker synthetic generator
│   ├── transactions.csv  # (generated)
│   └── transactions_test.csv
│
├── ML/                   # Machine learning
│   ├── train_model.py    # RF + XGBoost + LR training
│   ├── explainability.py # SHAP analysis
│   ├── model.pkl         # (generated)
│   └── metrics.json      # (generated)
│
├── DETECTION/            # C++ OOP rule engine
│   ├── structuring.cpp   # All 3 rules + main
│   └── cpp_runner.py     # Python wrapper + fallback
│
├── REASONING/            # Verdict fusion
│   └── guilt_engine.py   # ML + rule score combiner
│
├── AI/                   # LLM integration
│   ├── gemini_client.py  # Gemini 1.5 Flash
│   └── local_llm.py      # Template fallback
│
├── AUDIT/                # Tamper-proof logging
│   └── hash_chain.py     # SHA-256 chain
│
├── ALERTS/               # Email notifications
│   └── gmail_service.py  # Gmail SMTP
│
├── BACKEND/              # FastAPI server
│   ├── main.py
│   ├── routes.py
│   └── config.py
│
├── FRONTEND/             # Streamlit UI
│   ├── app.py
│   ├── styles.css
│   └── components/
│       └── sidebar.py
│
├── REPORTS/              # PDF output
│   └── pdf_generator.py
│
├── TESTS/                # Test suite
│   ├── test_api.py
│   └── test_full_flow.py
│
├── run_app.py            # Unified launcher
├── requirements.txt
└── .env                  # Environment variables
```

---

## 🔒 Security Notes

- **Never commit** `.env` with real credentials
- JWT tokens expire in 24h (configurable)
- Passwords hashed with bcrypt (12 rounds)
- Gmail requires App Password, not account password
- All actions logged to tamper-proof audit chain

---

## 🌐 Deployment

### Backend → Railway

```bash
# railway.json is auto-detected
# Set env vars in Railway dashboard
# Start command: uvicorn BACKEND.main:app --host 0.0.0.0 --port $PORT
```

### Frontend → Streamlit Cloud

```bash
# 1. Push to GitHub
# 2. Connect to streamlit.io/cloud
# 3. Main file: FRONTEND/app.py
# 4. Set BACKEND_URL in Streamlit secrets:
#    BACKEND_URL = "https://your-railway-app.up.railway.app"
```

---

## 🏦 Legal & Compliance

ProofSAR AI maps detected patterns to:
- **PMLA 2002** (Prevention of Money Laundering Act)
  - Section 3 & 4 (Layering offences)
  - Section 12 & 12A (STR filing obligation)
- **RBI AML/CFT Guidelines**
  - Master Direction on KYC 2016
  - Circular RBI/2019-20/88
- **FATF Recommendations** 20, 26
- **FEMA 1999** (Foreign Exchange)

> ⚠️ This system is an AI-assisted tool. All SAR reports must be reviewed by a qualified AML Compliance Officer before submission to FIU-IND.

---

## 📊 ML Model Performance

| Model | AUC | Precision | Recall | F1 |
|-------|-----|-----------|--------|-----|
| XGBoost | ~0.96 | ~0.89 | ~0.82 | ~0.85 |
| Random Forest | ~0.94 | ~0.85 | ~0.78 | ~0.81 |
| Logistic Regression | ~0.88 | ~0.76 | ~0.71 | ~0.73 |

*Metrics on synthetic dataset; results vary with real data*

---

## 📄 License

MIT License — See [LICENSE](LICENSE)

---

**Built with ❤️ by Antigravity OS**
