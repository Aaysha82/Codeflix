# DECISIONS.md — Architectural Decisions

## ADR-001: Framework Choice
- **Decision**: FastAPI for backend
- **Reason**: Async support, auto OpenAPI docs, type safety with Pydantic
- **Alternative Considered**: Flask (rejected — no async, no auto validation)

## ADR-002: ML Strategy
- **Decision**: Ensemble of RF + XGBoost + LR with voting
- **Reason**: XGBoost best performance; RF for stability; LR for interpretability baseline
- **Best Model Selection**: Cross-validated AUC score determines final model.pkl

## ADR-003: Explainability
- **Decision**: SHAP (TreeExplainer for RF/XGBoost)
- **Reason**: Model-agnostic, produces feature-level contribution scores
- **Alternative**: LIME (rejected — slower, less stable)

## ADR-004: C++ Integration
- **Decision**: Compile C++ → executable, call via Python subprocess
- **Reason**: Avoids ctypes complexity; JSON I/O between Python and C++
- **Alternative**: pybind11 (future enhancement)

## ADR-005: Auth Strategy
- **Decision**: JWT HS256 with 24h expiry
- **Reason**: Stateless, scalable; no session store needed
- **Alternative**: OAuth2 (overkill for internal tool)

## ADR-006: LLM Strategy
- **Decision**: Gemini 1.5 Flash as primary, template fallback if API unavailable
- **Reason**: Gemini free tier; cost-effective; fast inference
- **Alternative**: OpenAI GPT-4 (paid; swappable)

## ADR-007: Audit Chain
- **Decision**: SHA-256 chained hash stored in JSON file
- **Reason**: Simple, portable, tamper-evident without blockchain overhead
- **Alternative**: Blockchain (future enhancement)

## ADR-008: PDF Generation
- **Decision**: ReportLab for PDF
- **Reason**: Full layout control, tables, styles; production-grade
- **Alternative**: WeasyPrint (requires GTK on Windows — complex)

## ADR-009: Data Imbalance
- **Decision**: SMOTE oversampling during training
- **Reason**: Real AML data is severely imbalanced (1-5% fraud)
- **Alternative**: Class weights (less effective for tree models)

## ADR-010: Frontend
- **Decision**: Streamlit with custom CSS injection
- **Reason**: Rapid ML-focused UI; no React overhead
- **Alternative**: React/Next.js (future web app enhancement)
