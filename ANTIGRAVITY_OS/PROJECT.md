# ProofSAR AI — Project Documentation

## Project Title
**ProofSAR AI — Explainable Suspicious Activity Report (SAR) Generation System**

## Subtitle
From 5-hour SAR drafting → 5-minute regulator-ready explainable reports using AI

## Version
1.0.0 — Production Release

## Date Created
2026-04-14

## Architect
Antigravity OS — Senior AI Engineer + AML Analyst + Full-Stack Developer

---

## Problem Statement
Banks and financial institutions:
- Spend 5–6 hours per SAR
- Face high false positives from legacy systems
- Use black-box ML systems (no explainability)
- Struggle with audit-proof, regulator-compliant workflows

## Solution
ProofSAR AI provides:
1. Automated transaction ingestion (CSV + API)
2. ML-based fraud detection (RF + XGBoost + LR)
3. Explainable AI via SHAP values
4. C++ OOP rule-based detection engine
5. SAR narrative generation via Gemini LLM
6. Legal violation mapping (PMLA / RBI guidelines)
7. SHA-256 tamper-proof audit log chain
8. Gmail SMTP alerting system
9. JWT-based auth with Admin/Analyst roles
10. Streamlit dashboard with PDF export

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python) |
| Frontend | Streamlit |
| ML | scikit-learn, XGBoost, SHAP |
| Detection Engine | C++ with OOP |
| Auth | JWT + bcrypt |
| AI/LLM | Google Gemini API |
| Audit | SHA-256 hash chain (Python) |
| Alerts | Gmail SMTP |
| PDF | ReportLab |
| DB | SQLite (in-memory + file) |

## Architecture
```
[CSV/API Input] → [Data Preprocessor] → [ML Model] → [C++ Rule Engine]
                                               ↓                ↓
                                    [SHAP Explainer] ← [Risk Scorer]
                                               ↓
                                    [Gemini SAR Generator]
                                               ↓
                            [Audit Log] ← [FastAPI Backend] → [Alert Service]
                                               ↓
                                    [Streamlit Frontend]
                                               ↓
                                    [PDF Report Export]
```

## Compliance Mapping
- PMLA (Prevention of Money Laundering Act)
- RBI Guidelines on AML/CFT
- FinCEN SAR Filing Requirements
- FATF Recommendations

## Status
✅ Phase 1: Project Structure
✅ Phase 2: Data Generation
✅ Phase 3: ML Model
✅ Phase 4: C++ Detection Engine
✅ Phase 5: Explainability Engine
✅ Phase 6: AI SAR Generation
✅ Phase 7: Audit Log System
✅ Phase 8: Alert System
✅ Phase 9: Authentication
✅ Phase 10: FastAPI Backend
✅ Phase 11: Streamlit Frontend
✅ Phase 12: PDF Reports
✅ Phase 13: Antigravity Files
✅ Phase 14: Testing
✅ Phase 15: Deployment Ready
