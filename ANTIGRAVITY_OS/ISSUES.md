# ISSUES.md — Known Issues & Resolutions

## ISSUE-001: SHAP Slow on Large Datasets
- **Status**: RESOLVED
- **Description**: SHAP TreeExplainer slow for 10k+ rows
- **Resolution**: Sample 200 rows for SHAP; full dataset for prediction

## ISSUE-002: C++ Compilation on Windows
- **Status**: RESOLVED
- **Description**: g++ not always available on Windows
- **Resolution**: Auto-detect compiler; fallback to Python rule engine if g++ missing

## ISSUE-003: Gemini API Rate Limits
- **Status**: RESOLVED
- **Description**: Free tier has RPM limits
- **Resolution**: Template-based fallback SAR if API call fails

## ISSUE-004: SMTP Authentication
- **Status**: DOCUMENTED
- **Description**: Gmail requires App Password (not account password)
- **Resolution**: Documented in README; system falls back gracefully if SMTP fails

## ISSUE-005: SMOTE Requires Minority Samples
- **Status**: RESOLVED
- **Description**: SMOTE fails if minority class < k_neighbors
- **Resolution**: Auto-adjust k_neighbors based on sample count

## ISSUE-006: JWT Secret Must Be Strong
- **Status**: DOCUMENTED
- **Description**: Weak JWT_SECRET allows token forgery
- **Resolution**: Auto-generate 256-bit secret if not set; warn in logs

## ISSUE-007: Streamlit Re-runs on Widget Change
- **Status**: DOCUMENTED
- **Description**: Streamlit re-runs entire script on interaction
- **Resolution**: Use st.session_state for all stateful data

## ISSUE-008: C++ JSON Output Parsing
- **Status**: RESOLVED
- **Description**: C++ stdout must be valid JSON
- **Resolution**: Added try/except with fallback Python rules

## ISSUE-009: Model Not Found on Fresh Start
- **Status**: RESOLVED
- **Description**: model.pkl missing if train not run
- **Resolution**: Auto-trigger training if model.pkl is absent

## ISSUE-010: PDF Unicode Characters
- **Status**: RESOLVED
- **Description**: ReportLab default font lacks unicode
- **Resolution**: Use Helvetica with ASCII-safe encoding for special chars
