# ProofSAR AI: Detailed Technical Solution Architecture

## Executive Summary

This document provides a comprehensive technical blueprint for ProofSAR AI's implementation, including detailed architecture patterns, module specifications, data flows, and implementation roadmap. It serves as the definitive guide for developers, architects, and stakeholders.

---

## Table of Contents

1. [Detailed System Architecture](#detailed-system-architecture)
2. [Core Module Specifications](#core-module-specifications)
3. [Data Flow & Processing Pipeline](#data-flow--processing-pipeline)
4. [API Architecture](#api-architecture)
5. [Database Schema](#database-schema)
6. [Security Architecture](#security-architecture)
7. [ML Pipeline Architecture](#ml-pipeline-architecture)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Performance Optimization](#performance-optimization)
10. [Deployment Architecture](#deployment-architecture)

---

## 1. Detailed System Architecture

### 1.1 Microservices Architecture

ProofSAR AI follows a modular microservices-inspired architecture where components operate as independent services with clear interfaces:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                              │
├─────────────────────────────────────────────────────────────────────────┤
│  Streamlit Frontend (Port 8501)                                          │
│  ├── Dashboard                                                            │
│  ├── Case Management UI                                                   │
│  ├── SAR Editor                                                           │
│  └── Analytics & Reporting                                               │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ HTTP/HTTPS
┌──────────────────────────▼──────────────────────────────────────────────┐
│                          API GATEWAY LAYER                               │
├──────────────────────────────────────────────────────────────────────────┤
│  FastAPI (Port 8000)                                                     │
│  ├── Request routing & load balancing                                    │
│  ├── JWT token validation                                                │
│  ├── Rate limiting & throttling                                          │
│  ├── CORS handling                                                       │
│  └── OpenAPI/Swagger documentation                                       │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬─────────────────┐
        │                  │                  │                 │
┌───────▼───────┐  ┌──────▼──────┐  ┌───────▼──────┐  ┌────────▼──────┐
│   AUTH        │  │   ANALYSIS  │  │   SAR        │  │   AUDIT       │
│   SERVICE     │  │   SERVICE   │  │   SERVICE    │  │   SERVICE     │
├───────────────┤  ├─────────────┤  ├──────────────┤  ├───────────────┤
│ • Login       │  │ • CSV Parse │  │ • Generate   │  │ • Hash Chain  │
│ • Register    │  │ • ML Score  │  │ • Narrative  │  │ • Verify      │
│ • Token Gen   │  │ • C++ Rules │  │ • Export PDF │  │ • Event Log   │
│ • User Mgmt   │  │ • SHAP      │  │ • Version    │  │ • Immutable   │
└───────────────┘  └─────────────┘  └──────────────┘  └───────────────┘
        │                  │                  │                 │
        └──────────────────┼──────────────────┴─────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────────┐
│                      SERVICE ORCHESTRATION LAYER                         │
├──────────────────────────────────────────────────────────────────────────┤
│  Celery Task Queue + Redis Cache                                         │
│  ├── Async job scheduling                                                │
│  ├── Task distribution                                                   │
│  ├── Result caching                                                      │
│  └── Model loading cache                                                 │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
┌───▼────────────┐  ┌──────▼──────┐  ┌──────────▼──┐
│ ML PIPELINE    │  │ C++ ENGINE  │  │ ALERT       │
│ SERVICE        │  │ SERVICE     │  │ SERVICE     │
├────────────────┤  ├─────────────┤  ├─────────────┤
│ • RF Model     │  │ • Structuring│  │ • Gmail     │
│ • XGBoost      │  │ • Smurfing  │  │ • Queue     │
│ • LR Model     │  │ • Layering  │  │ • Retry     │
│ • SHAP Explainer│  │ • Placement │  │ • Logging   │
└────────────────┘  └─────────────┘  └─────────────┘
    │                  │                  │
    └──────────────────┼──────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────────────┐
│                        DATA & STATE LAYER                                │
├──────────────────────────────────────────────────────────────────────────┤
│  ├─ SQLite Database (audit_chain.json, session.db)                       │
│  ├─ JSON Files (legal_map.json, model metadata)                          │
│  ├─ CSV Files (transaction data, training datasets)                      │
│  ├─ Pickle Files (ML models: model.pkl)                                  │
│  ├─ Redis Cache (active sessions, model cache)                           │
│  └─ File System (generated PDFs, reports)                                │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Layer-by-Layer Breakdown

#### **Presentation Layer (Frontend)**
- **Technology**: Streamlit 1.34+
- **Port**: 8501
- **Responsibilities**:
  - User authentication interface
  - Dashboard with KPI metrics
  - Case management UI (create, list, view, edit)
  - SAR editor with real-time preview
  - CSV upload interface
  - Analytics and visualization
  - Report export functionality

#### **API Gateway Layer (Backend)**
- **Technology**: FastAPI 0.111+ with Uvicorn ASGI server
- **Port**: 8000
- **Responsibilities**:
  - JWT token validation
  - Request routing to service layer
  - Rate limiting and throttling
  - CORS headers and validation
  - OpenAPI schema generation
  - Error handling and response standardization
  - Logging and monitoring

#### **Service Layer**
Each service implements a specific domain:

**AUTH Service** (`AUTH/`)
- User registration and login
- Password hashing (bcrypt)
- JWT token generation/validation
- Role-based access control enforcement
- Session management

**ANALYSIS Service** (`BACKEND/`, `ML/`, `DETECTION/`)
- Transaction data ingestion
- Feature engineering
- ML model inference
- C++ rule engine execution
- Risk aggregation
- Explainability computation

**SAR Service** (`BACKEND/routes.py`, `AI/`)
- SAR narrative generation (Gemini or template)
- Legal mapping
- PDF/DOCX export
- Version management
- Approval workflow

**AUDIT Service** (`AUDIT/`, `BACKEND/`)
- Hash chain generation and verification
- Event logging
- Immutability verification
- Compliance reporting

#### **Task Orchestration Layer**
- **Technology**: Celery + Redis
- **Responsibilities**:
  - Async task scheduling
  - Model caching and preloading
  - Background email sending
  - Batch processing
  - Job retry logic

#### **Data & State Layer**
- **SQLite**: Session state, user data, case metadata
- **JSON**: Audit chains, legal mappings, configuration
- **CSV**: Transaction data, training datasets
- **Pickle**: Trained ML models
- **Redis**: Active session cache, model cache
- **File System**: Generated PDFs, exports

---

## 2. Core Module Specifications

### 2.1 Authentication Module (`AUTH/`)

**Files**:
- `auth.py` - Main authentication logic
- `jwt_handler.py` - JWT token operations
- `password_utils.py` - Password hashing/verification
- `users.json` - User database (production: replace with DB)

**Key Functions**:

```python
# auth.py
def register_user(username: str, password: str, role: str) -> User
    """
    Register new user with bcrypt password hashing
    Args:
        username: Unique username
        password: Plain text password (min 8 chars)
        role: "admin" | "analyst" | "viewer"
    Returns:
        User object with hashed password
    """

def login(username: str, password: str) -> LoginResponse
    """
    Authenticate user and issue JWT token
    Args:
        username: Registered username
        password: Plain text password
    Returns:
        JWT access_token, expiration time
    """

def verify_token(token: str) -> User
    """
    Validate JWT token and extract user info
    Args:
        token: Bearer token from Authorization header
    Returns:
        User object or raise InvalidTokenError
    """

def check_permission(user: User, resource: str, action: str) -> bool
    """
    Verify role-based access to resource
    Args:
        user: Authenticated User
        resource: "case" | "sar" | "audit" | "system"
        action: "read" | "create" | "edit" | "approve"
    Returns:
        True if permitted, False otherwise
    """
```

**Role Matrix**:
| Resource | Admin | Analyst | Viewer |
|----------|-------|---------|--------|
| Create Case | ✅ | ✅ | ❌ |
| Generate SAR | ✅ | ✅ | ❌ |
| Edit SAR | ✅ | ✅ | ❌ |
| Approve SAR | ✅ | ❌ | ❌ |
| View Audit Log | ✅ | ✅ | ✅ |
| Manage Users | ✅ | ❌ | ❌ |
| Export Report | ✅ | ✅ | ✅ |

---

### 2.2 Analysis Engine (`BACKEND/`, `ML/`, `DETECTION/`)

#### **Data Flow**:
```
CSV Input
  │
  ▼
[PREPROCESSING]
  ├── Validate format
  ├── Handle missing values
  ├── Engineer features
  └── Normalize values
  │
  ▼
[PARALLEL PROCESSING]
  ├─→ [ML MODEL]
  │    ├── Random Forest
  │    ├── XGBoost
  │    └── Logistic Regression
  │    └─→ Ensemble Vote (60%)
  │
  ├─→ [C++ DETECTION]
  │    ├── Structuring patterns
  │    ├── Smurfing detection
  │    ├── Layering analysis
  │    └── Placement scoring
  │    └─→ Rule Score (40%)
  │
  └─→ [SHAP EXPLAINER]
       └── Feature importance per model
  │
  ▼
[RISK AGGREGATION]
  ├── Guilt Score = 0.6 * ML_Score + 0.4 * Rule_Score
  ├── Confidence = ensemble_std_dev
  └── Red Flags = SHAP top features
  │
  ▼
[OUTPUT]
  ├── Risk Classification (Low/Medium/High/Critical)
  ├── Guilt Score (0-100)
  ├── Confidence (0-1)
  ├── Red Flags (list)
  └── Evidence (SHAP values)
```

**Key Components**:

```python
# ML/train_model.py
class MLPipeline:
    def __init__(self):
        self.rf_model = RandomForestClassifier(n_estimators=100)
        self.xgb_model = XGBClassifier(n_estimators=100)
        self.lr_model = LogisticRegression()
        self.scaler = StandardScaler()
        self.smote = SMOTE(random_state=42)
        self.shap_explainer = None
    
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train ensemble with SMOTE balancing
        """
        X_balanced, y_balanced = self.smote.fit_resample(X, y)
        X_scaled = self.scaler.fit_transform(X_balanced)
        
        self.rf_model.fit(X_scaled, y_balanced)
        self.xgb_model.fit(X_scaled, y_balanced)
        self.lr_model.fit(X_scaled, y_balanced)
        
        self.shap_explainer = shap.TreeExplainer(self.xgb_model)
        
        return {
            'rf_score': self.rf_model.score(X_scaled, y_balanced),
            'xgb_score': self.xgb_model.score(X_scaled, y_balanced),
            'lr_score': self.lr_model.score(X_scaled, y_balanced),
        }
    
    def predict_ensemble(self, X: pd.DataFrame) -> Dict:
        """
        Get predictions from all models and compute ensemble
        """
        X_scaled = self.scaler.transform(X)
        
        rf_pred = self.rf_model.predict_proba(X_scaled)[:, 1]
        xgb_pred = self.xgb_model.predict_proba(X_scaled)[:, 1]
        lr_pred = self.lr_model.predict_proba(X_scaled)[:, 1]
        
        # Ensemble: average with weights
        ensemble_pred = (rf_pred + xgb_pred + lr_pred) / 3
        
        # SHAP explanations
        shap_values = self.shap_explainer.shap_values(X_scaled)
        
        return {
            'risk_score': ensemble_pred,
            'confidence': np.std([rf_pred, xgb_pred, lr_pred]),
            'shap_values': shap_values,
            'feature_importance': self._get_top_features(shap_values)
        }

# DETECTION/cpp_runner.py
class CppDetectionEngine:
    def __init__(self):
        self.binary_path = compile_cpp_if_needed()
        self.compiled = self.binary_path is not None
    
    def detect_patterns(self, transactions: pd.DataFrame) -> Dict:
        """
        Call C++ engine for rule-based detection
        """
        if not self.compiled:
            return {'structuring': 0, 'smurfing': 0, 'layering': 0}
        
        # Write transactions to temp file
        input_file = write_temp_csv(transactions)
        output_file = tempfile.NamedTemporaryFile(delete=False)
        
        # Call C++ binary
        subprocess.run([
            self.binary_path,
            input_file,
            output_file.name
        ])
        
        # Parse results
        results = parse_cpp_output(output_file.name)
        return results
```

#### **Feature Engineering**:

```python
def engineer_features(transaction_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create advanced features for ML models
    """
    features = transaction_df.copy()
    
    # Temporal features
    features['hour'] = pd.to_datetime(features['timestamp']).dt.hour
    features['day_of_week'] = pd.to_datetime(features['timestamp']).dt.dayofweek
    features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
    
    # Amount-based features
    features['amount_log'] = np.log1p(features['amount'])
    features['near_threshold'] = (features['amount'] > 900000).astype(int)
    
    # Account-based features (aggregations)
    acc_stats = features.groupby('account_id')['amount'].agg(['mean', 'std', 'count', 'max'])
    features['acc_mean_amount'] = features['account_id'].map(acc_stats['mean'])
    features['acc_std_amount'] = features['account_id'].map(acc_stats['std'])
    features['acc_txn_count'] = features['account_id'].map(acc_stats['count'])
    features['acc_max_amount'] = features['account_id'].map(acc_stats['max'])
    
    # Deviation features
    features['amount_vs_mean'] = features['amount'] / features['acc_mean_amount']
    features['amount_zscore'] = (features['amount'] - features['acc_mean_amount']) / features['acc_std_amount']
    
    # Risk location & channel
    high_risk_locations = ['Cayman Islands', 'Panama', 'Bahamas']
    features['is_high_risk_location'] = features['location'].isin(high_risk_locations).astype(int)
    
    high_risk_channels = ['Wire Transfer', 'Crypto', 'Hawala']
    features['is_high_risk_channel'] = features['channel'].isin(high_risk_channels).astype(int)
    
    # International flag
    features['is_international'] = (features['location'] != 'India').astype(int)
    
    return features
```

---

### 2.3 SAR Generation Engine (`AI/`, `REASONING/`)

#### **SAR Template Structure**:

```python
SAR_TEMPLATE = """
═══════════════════════════════════════════════════════════════
        SUSPICIOUS ACTIVITY REPORT (SAR)
             FIU-IND Filing Format
═══════════════════════════════════════════════════════════════

REPORT ID: {report_id}
DATE FILED: {filing_date}
REPORTING INSTITUTION: {institution_name}

───────────────────────────────────────────────────────────────
1. EXECUTIVE SUMMARY
───────────────────────────────────────────────────────────────
{executive_summary}

Risk Level: {risk_level} | Guilt Score: {guilt_score}% | Confidence: {confidence}%

───────────────────────────────────────────────────────────────
2. CUSTOMER INFORMATION
───────────────────────────────────────────────────────────────
Name: {customer_name}
Account ID: {account_id}
Customer Category: {customer_category}
KYC Status: {kyc_status}
Risk Profile: {risk_profile}
Account Age: {account_age_days} days

───────────────────────────────────────────────────────────────
3. TRANSACTION ANALYSIS
───────────────────────────────────────────────────────────────
Total Transactions: {total_txns}
Date Range: {date_range}
Total Amount: ₹{total_amount:,.2f}

Transaction Details:
{transaction_table}

───────────────────────────────────────────────────────────────
4. SUSPICIOUS ACTIVITY DESCRIPTION
───────────────────────────────────────────────────────────────
{suspicious_description}

Red Flags Identified:
{red_flags_list}

Statistical Evidence:
{statistical_evidence}

───────────────────────────────────────────────────────────────
5. LEGAL BASIS & COMPLIANCE
───────────────────────────────────────────────────────────────
Suspected Offense:
  • {suspected_offense}

Relevant PMLA Sections:
{pmla_citations}

RBI Guidelines Violated:
{rbi_citations}

───────────────────────────────────────────────────────────────
6. RECOMMENDATION
───────────────────────────────────────────────────────────────
Recommended Action: {recommendation}
Further Investigation: {investigation_needed}

───────────────────────────────────────────────────────────────
7. AUDIT & CERTIFICATION
───────────────────────────────────────────────────────────────
Generated By: ProofSAR AI v1.0
Analysis Timestamp: {analysis_timestamp}
SHA-256 Hash: {document_hash}

Authorized Reporting Officer (ARO):
_______________________
Signature: ________________    Date: ______________
"""
```

#### **SAR Generation Algorithm**:

```python
class SARGenerator:
    def __init__(self, gemini_api_key: str = None):
        self.gemini_api_key = gemini_api_key
        self.template_engine = TemplateEngine()
        self.legal_mapper = LegalMapper()
    
    def generate_sar(self, case: Case, use_gemini: bool = True) -> SAR:
        """
        Generate complete SAR with narrative
        """
        # Extract case data
        transactions = case.transactions
        analysis = case.analysis_result
        red_flags = analysis['red_flags']
        
        # Build evidence block
        evidence = self._build_evidence_block(transactions, analysis)
        
        if use_gemini and self.gemini_api_key:
            # AI-powered narrative
            narrative = self._generate_narrative_gemini(
                customer=case.customer,
                transactions=transactions,
                red_flags=red_flags,
                evidence=evidence
            )
        else:
            # Template-based fallback
            narrative = self._generate_narrative_template(
                red_flags=red_flags,
                evidence=evidence
            )
        
        # Map legal violations
        pmla_sections, rbi_guidelines = self.legal_mapper.map_violations(
            red_flags=red_flags,
            analysis=analysis
        )
        
        # Create SAR object
        sar = SAR(
            report_id=generate_report_id(),
            case_id=case.id,
            executive_summary=narrative['summary'],
            suspicious_description=narrative['description'],
            red_flags=red_flags,
            pmla_sections=pmla_sections,
            rbi_guidelines=rbi_guidelines,
            recommendation=analysis['recommendation'],
            guilt_score=analysis['guilt_score'],
            confidence=analysis['confidence']
        )
        
        return sar
    
    def _generate_narrative_gemini(self, customer, transactions, 
                                   red_flags, evidence) -> Dict:
        """
        Use Google Gemini to generate human-readable narrative
        """
        prompt = self._build_gemini_prompt(
            customer, transactions, red_flags, evidence
        )
        
        response = generate_content_gemini(
            model="gemini-pro",
            prompt=prompt,
            temperature=0.3,  # Low temperature for consistency
            max_output_tokens=1500
        )
        
        # Parse structured response
        return parse_gemini_response(response)
    
    def _generate_narrative_template(self, red_flags, evidence) -> Dict:
        """
        Template-based narrative for offline environments
        """
        summary_parts = []
        for flag in red_flags:
            summary_parts.append(
                NARRATIVE_TEMPLATES[flag['type']].format(**flag)
            )
        
        return {
            'summary': " ".join(summary_parts[:2]),
            'description': "\n".join(summary_parts)
        }
```

#### **Legal Mapping Engine** (`REASONING/legal_map.json`):

```json
{
  "structuring": {
    "pmla_sections": ["Section 5 - Proceeds of crime"],
    "rbi_guidelines": ["KYC Guidelines - Section 3 - Red Flag Indicators"],
    "description": "Pattern consistent with structuring/smurfing to avoid CTR threshold"
  },
  "layering": {
    "pmla_sections": ["Section 5 - Proceeds of crime", "Section 3 - Money laundering"],
    "rbi_guidelines": ["CFT Guidelines - Section 2 - Beneficial Ownership"],
    "description": "Complex offshore movements indicative of money laundering"
  },
  "placement": {
    "pmla_sections": ["Section 3 - Money laundering"],
    "rbi_guidelines": ["KYC Guidelines - Section 5 - High Risk Customers"],
    "description": "Use of high-risk channels for fund transfer"
  }
}
```

---

### 2.4 Audit Trail Engine (`AUDIT/`)

#### **SHA-256 Hash Chain Implementation**:

```python
class AuditChain:
    def __init__(self, chain_file: str = "AUDIT/audit_chain.json"):
        self.chain_file = chain_file
        self.chain = self._load_chain()
    
    def add_event(self, event_type: str, actor: str, 
                  resource: str, action: str, details: Dict) -> str:
        """
        Add event to immutable hash chain
        
        Event format:
        {
            "sequence": 1001,
            "timestamp": "2026-04-16T10:30:45Z",
            "event_id": "evt_random_uuid",
            "event_type": "SAR_GENERATED",
            "actor": "analyst@company.com",
            "resource": "sar_20260416_001",
            "action": "create",
            "details": {...},
            "previous_hash": "abc123...",
            "event_hash": "def456...",
            "chain_valid": true
        }
        """
        
        # Get previous hash
        if len(self.chain) > 0:
            previous_hash = self.chain[-1]['event_hash']
        else:
            previous_hash = "GENESIS"
        
        # Create event object
        event = {
            'sequence': len(self.chain) + 1,
            'timestamp': datetime.utcnow().isoformat() + "Z",
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'actor': actor,
            'resource': resource,
            'action': action,
            'details': details,
            'previous_hash': previous_hash
        }
        
        # Calculate hash
        event_string = json.dumps(event, sort_keys=True)
        event_hash = hashlib.sha256(event_string.encode()).hexdigest()
        event['event_hash'] = event_hash
        
        # Verify chain
        event['chain_valid'] = self._verify_chain_integrity()
        
        # Persist
        self.chain.append(event)
        self._persist_chain()
        
        return event['event_id']
    
    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify entire chain integrity
        
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Check hash linkage
            if current['previous_hash'] != previous['event_hash']:
                violations.append(
                    f"Event {current['event_id']}: Broken link from previous event"
                )
            
            # Verify event hash
            event_copy = current.copy()
            event_copy.pop('event_hash')
            event_copy.pop('chain_valid', None)
            
            recalculated_hash = hashlib.sha256(
                json.dumps(event_copy, sort_keys=True).encode()
            ).hexdigest()
            
            if recalculated_hash != current['event_hash']:
                violations.append(
                    f"Event {current['event_id']}: Hash mismatch (tampering detected)"
                )
            
            # Check sequence
            if current['sequence'] != previous['sequence'] + 1:
                violations.append(
                    f"Event {current['event_id']}: Sequence break"
                )
        
        return len(violations) == 0, violations
    
    def get_event_history(self, resource_id: str = None, 
                         start_date: str = None, 
                         end_date: str = None) -> List[Dict]:
        """
        Query audit events with optional filtering
        """
        results = self.chain
        
        if resource_id:
            results = [e for e in results if e['resource'] == resource_id]
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            results = [e for e in results 
                      if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            results = [e for e in results 
                      if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) <= end_dt]
        
        return results
```

**Audit Event Types**:
- `USER_REGISTERED` - New user created
- `USER_LOGIN` - User authenticated
- `CASE_CREATED` - Investigation case opened
- `CSV_UPLOADED` - Transaction data imported
- `ANALYSIS_STARTED` - ML analysis initiated
- `ANALYSIS_COMPLETED` - Analysis finished with results
- `SAR_GENERATED` - SAR narrative created
- `SAR_EDITED` - SAR modified by analyst
- `SAR_APPROVED` - SAR approved by ARO
- `SAR_FILED` - SAR submitted to FIU-IND
- `AUDIT_VERIFIED` - Chain integrity verified

---

### 2.5 Alert Service (`ALERTS/`)

#### **Email Alert Architecture**:

```python
class AlertService:
    def __init__(self, email_user: str, email_pass: str):
        self.email_user = email_user
        self.email_pass = email_pass
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_alert(self, alert: Alert) -> AlertResult:
        """
        Send alert with retry logic
        
        Alert types:
        - HIGH_RISK: Case guilt score > 75%
        - PENDING: SAR awaiting approval
        - APPROVED: SAR approved, ready to file
        - REJECTED: SAR rejected, needs rework
        - ERROR: System error or exception
        """
        
        recipients = self._get_recipients_for_alert(alert)
        subject = self._build_subject(alert)
        body = self._build_body(alert)
        
        try:
            message = MIMEMultipart()
            message['From'] = self.email_user
            message['To'] = ", ".join(recipients)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'html'))
            
            # Attempt send with retries
            for attempt in range(3):
                try:
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls()
                        server.login(self.email_user, self.email_pass)
                        server.send_message(message)
                    
                    return AlertResult(
                        success=True,
                        alert_id=alert.id,
                        recipients=recipients
                    )
                except Exception as e:
                    if attempt < 2:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    raise
        
        except Exception as e:
            log_error(f"Alert send failed: {e}")
            # Schedule retry via Celery
            send_alert_retry.apply_async(
                args=[alert.id],
                countdown=300  # Retry in 5 minutes
            )
            return AlertResult(
                success=False,
                alert_id=alert.id,
                error=str(e)
            )
    
    def _build_body(self, alert: Alert) -> str:
        """Generate HTML email body"""
        
        template = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>ProofSAR AI Alert: {alert.alert_type}</h2>
                
                <p><strong>Alert ID:</strong> {alert.id}</p>
                <p><strong>Timestamp:</strong> {alert.timestamp}</p>
                <p><strong>Severity:</strong> 
                    <span style="color: {'red' if alert.severity == 'HIGH' else 'orange'};">
                        {alert.severity}
                    </span>
                </p>
                
                <h3>Details</h3>
                <p>{alert.message}</p>
                
                <h3>Action Required</h3>
                <p>
                    <a href="{alert.action_url}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        {alert.action_text}
                    </a>
                </p>
                
                <hr>
                <p style="font-size: 0.9em; color: #666;">
                    This is an automated alert from ProofSAR AI. 
                    Do not reply to this email.
                </p>
            </body>
        </html>
        """
        
        return template
```

---

## 3. Data Flow & Processing Pipeline

### 3.1 Complete Transaction Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: DATA INGESTION                                         │
├─────────────────────────────────────────────────────────────────┤
│  Input: CSV file or API stream                                  │
│  - Validate CSV schema                                          │
│  - Check encoding (UTF-8)                                       │
│  - Detect missing values                                        │
│  Output: Validated DataFrame (pandas)                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  STEP 2: DATA CLEANING                                          │
├─────────────────────────────────────────────────────────────────┤
│  - Fill missing categorical values: mode                        │
│  - Fill missing numeric values: median                          │
│  - Remove duplicate transactions                                │
│  - Handle outliers: IQR method                                  │
│  Output: Clean, deduplicated data                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  STEP 3: FEATURE ENGINEERING                                    │
├─────────────────────────────────────────────────────────────────┤
│  - Temporal: hour, day_of_week, is_weekend                      │
│  - Amount-based: amount_log, near_threshold                     │
│  - Account aggregations: mean, std, count, max                  │
│  - Deviation: z-scores, vs_mean ratio                           │
│  - Risk indicators: location, channel, international            │
│  Output: 25+ engineered features                                │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│  STEP 4: NORMALIZATION & SCALING                                │
├─────────────────────────────────────────────────────────────────┤
│  - StandardScaler: μ=0, σ=1                                     │
│  - One-hot encoding: categorical variables                      │
│  Output: Scaled feature matrix [N x 50]                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
        ┌────────┴────────┬─────────────┐
        │                 │             │
┌───────▼───────┐  ┌──────▼──────┐  ┌──▼──────────┐
│ ML PREDICTION │  │ C++ RULES   │  │ SHAP        │
│               │  │ ENGINE      │  │ EXPLAINER   │
└───────┬───────┘  └──────┬──────┘  └──┬──────────┘
        │ ML_Score        │ Rules_Score │ Features
        │ (0-1)           │ (0-1)       │
        └────────┬────────┴─────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│  STEP 5: RISK AGGREGATION                                        │
├──────────────────────────────────────────────────────────────────┤
│  Guilt_Score = 0.6 * ML_Score + 0.4 * Rules_Score              │
│  Confidence = 1 - StdDev([RF_score, XGB_score, LR_score])      │
│  Red_Flags = Top-5 SHAP features with violations                │
│  Risk_Level = Classify_By_Score(Guilt_Score)                   │
│  Output: Comprehensive risk assessment                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│  STEP 6: SAR GENERATION                                          │
├──────────────────────────────────────────────────────────────────┤
│  - Extract customer KYC data                                     │
│  - Build transaction narrative                                  │
│  - Generate AI narrative (Gemini or template)                    │
│  - Map legal violations (PMLA, RBI)                              │
│  - Create PDF/DOCX export                                        │
│  Output: Complete SAR document                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│  STEP 7: AUDIT LOGGING                                           │
├──────────────────────────────────────────────────────────────────┤
│  - Create audit event                                            │
│  - Add to SHA-256 hash chain                                     │
│  - Verify chain integrity                                        │
│  - Persist to audit_chain.json                                   │
│  Output: Immutable audit trail                                   │
└────────────────┬────────────────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│  STEP 8: ALERTING & NOTIFICATION                                 │
├──────────────────────────────────────────────────────────────────┤
│  If Risk_Level = HIGH or CRITICAL:                               │
│  - Queue Gmail alert via Celery                                  │
│  - Send to Analysts & ARO                                        │
│  - Log alert attempt to audit chain                              │
│  Output: Escalation notification sent                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Case Lifecycle

```
┌─────────────────┐
│  1. CREATED     │  ← User creates case from CSV or manual entry
│  status='draft' │
└────────┬────────┘
         │
┌────────▼─────────┐
│  2. ANALYZING    │  ← ML + C++ analysis running
│  status='active' │
└────────┬────────┘
         │
┌────────▼──────────────┐
│  3. RESULTS_READY    │  ← Analysis complete, SAR can be generated
│  status='analysis_ok'│
└────────┬──────────────┘
         │
┌────────▼─────────────────┐
│  4. SAR_GENERATED       │  ← SAR narrative created
│  status='sar_generated' │
└────────┬─────────────────┘
         │
┌────────▼─────────────────┐
│  5. UNDER_REVIEW        │  ← Analyst reviewing, may edit
│  status='review'        │
└────────┬─────────────────┘
         │
     ┌───┴───┐
     │ Edit? │
     └───┬───┘
         │
     ┌───┴──────────┐
     │              │
┌────▼──────┐  ┌───▼────────┐
│  YES: 5   │  │  NO: 6     │
│  (loop)   │  │            │
└───────────┘  └───┬────────┘
                  │
          ┌───────▼────────┐
          │  6. READY_TO   │
          │     APPROVE    │
          │ status='ready' │
          └───────┬────────┘
                  │
          ┌───────▼────────────┐
          │  7. APPROVED       │
          │ status='approved'  │
          └───────┬────────────┘
                  │
          ┌───────▼──────────┐
          │  8. FILED        │
          │ status='filed'   │ ← Submitted to FIU-IND
          └──────────────────┘
```

---

## 4. API Architecture

### 4.1 Complete API Endpoints

```
BASE URL: http://localhost:8000

┌─────────────────────────────────────────────────────────────────┐
│ AUTHENTICATION ENDPOINTS                                        │
├─────────────────────────────────────────────────────────────────┤
POST   /auth/register           Register new user
POST   /auth/login              Login & get JWT token
GET    /auth/me                 Get current user info
POST   /auth/logout             Invalidate token
POST   /auth/refresh-token      Refresh expired token
```

**POST /auth/login**
```json
{
  "username": "analyst",
  "password": "Analyst@2026"
}
```

**Response (200)**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_001",
    "username": "analyst",
    "role": "analyst",
    "email": "analyst@company.com"
  }
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ CASE MANAGEMENT ENDPOINTS                                       │
├─────────────────────────────────────────────────────────────────┤
POST   /cases                   Create new case
GET    /cases                   List all cases (paginated)
GET    /cases/{case_id}         Get case details
PATCH  /cases/{case_id}         Update case
DELETE /cases/{case_id}         Delete case (draft only)
```

**POST /cases**
```json
{
  "title": "Customer XYZ - High Risk Activity",
  "description": "Multiple large transactions in 24 hours",
  "customer_id": "cust_123",
  "case_type": "transaction_monitoring"
}
```

**Response (201)**
```json
{
  "case_id": "case_20260416_001",
  "title": "Customer XYZ - High Risk Activity",
  "status": "draft",
  "created_at": "2026-04-16T10:30:45Z",
  "created_by": "analyst@company.com"
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ ANALYSIS ENDPOINTS                                              │
├─────────────────────────────────────────────────────────────────┤
POST   /analyze                 Analyze single transaction
POST   /analyze/batch           Batch CSV analysis
GET    /analyze/status/{job_id} Check async job status
```

**POST /analyze/batch**
```json
{
  "case_id": "case_20260416_001",
  "csv_file": "<base64_encoded_csv>",
  "use_gemini": true
}
```

**Response (202 - Async)**
```json
{
  "job_id": "job_abc123xyz",
  "status": "queued",
  "message": "Analysis job created, check back with job_id",
  "status_url": "/analyze/status/job_abc123xyz"
}
```

**GET /analyze/status/job_abc123xyz**
```json
{
  "job_id": "job_abc123xyz",
  "status": "completed",
  "results": {
    "transactions_analyzed": 1500,
    "high_risk_count": 45,
    "analysis_summary": {
      "ml_score": 0.82,
      "rules_score": 0.78,
      "guilt_score": 80.5,
      "confidence": 0.92,
      "risk_level": "HIGH",
      "red_flags": [
        "Structuring pattern detected",
        "Amount significantly above account average",
        "International transfers to high-risk jurisdiction"
      ]
    },
    "completed_at": "2026-04-16T10:32:15Z"
  }
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ SAR GENERATION ENDPOINTS                                        │
├─────────────────────────────────────────────────────────────────┤
POST   /generate-sar            Generate SAR narrative
GET    /sar/{sar_id}            Get SAR document
PATCH  /sar/{sar_id}            Edit SAR narrative
POST   /sar/{sar_id}/approve    Approve SAR (ARO only)
POST   /sar/{sar_id}/reject     Reject SAR (ARO only)
POST   /sar/{sar_id}/file       File SAR to FIU-IND
POST   /sar/{sar_id}/export-pdf Export as PDF
```

**POST /generate-sar**
```json
{
  "case_id": "case_20260416_001",
  "use_gemini": true
}
```

**Response (201)**
```json
{
  "sar_id": "sar_20260416_001",
  "case_id": "case_20260416_001",
  "status": "draft",
  "executive_summary": "Customer engaged in structured deposits...",
  "guilt_score": 80.5,
  "red_flags": [...],
  "created_at": "2026-04-16T10:33:22Z",
  "version": 1
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ AUDIT & COMPLIANCE ENDPOINTS                                    │
├─────────────────────────────────────────────────────────────────┤
GET    /audit/verify            Verify hash chain integrity
GET    /audit/events            Get audit events (paginated)
GET    /audit/events/{event_id} Get specific event details
GET    /audit/report/{case_id}  Generate compliance audit report
```

**GET /audit/verify**
```json
{
  "is_valid": true,
  "total_events": 2547,
  "violations": [],
  "verification_timestamp": "2026-04-16T10:34:10Z",
  "chain_hash": "abc123def456..."
}
```

**GET /audit/events?limit=50&offset=0**
```json
{
  "total": 2547,
  "limit": 50,
  "offset": 0,
  "events": [
    {
      "event_id": "evt_xyz789",
      "sequence": 2547,
      "timestamp": "2026-04-16T10:33:22Z",
      "event_type": "SAR_GENERATED",
      "actor": "analyst@company.com",
      "resource": "sar_20260416_001",
      "action": "create",
      "details": {...},
      "event_hash": "def456abc123..."
    }
  ]
}
```

---

```
┌─────────────────────────────────────────────────────────────────┐
│ DASHBOARD & METRICS ENDPOINTS                                   │
├─────────────────────────────────────────────────────────────────┤
GET    /metrics                 System KPIs and statistics
GET    /metrics/dashboard       Dashboard data (cases, alerts, etc)
GET    /health                  System health check
```

**GET /metrics**
```json
{
  "total_cases": 1523,
  "active_cases": 87,
  "sars_generated": 1204,
  "sars_filed": 1187,
  "high_risk_alerts": 234,
  "false_positive_rate": 0.18,
  "avg_processing_time_seconds": 124,
  "uptime_percent": 99.98,
  "last_analysis": "2026-04-16T10:33:22Z"
}
```

---

### 4.2 Error Handling & Status Codes

```python
# Standard HTTP responses
200 OK                  # Successful GET/POST
201 Created             # Successful POST (new resource)
202 Accepted            # Async job accepted
204 No Content          # Successful DELETE
400 Bad Request         # Invalid parameters
401 Unauthorized        # Missing/invalid authentication
403 Forbidden           # Insufficient permissions
404 Not Found           # Resource not found
409 Conflict            # Invalid state transition
422 Unprocessable       # Validation error
429 Too Many Requests   # Rate limited
500 Internal Error      # Server error
503 Service Unavailable # System overloaded
```

**Error Response Format**:
```json
{
  "error": {
    "code": "AUTH_001",
    "message": "Invalid JWT token",
    "details": "Token expired at 2026-04-16T11:30:00Z",
    "timestamp": "2026-04-16T10:34:45Z",
    "request_id": "req_abc123"
  }
}
```

---

## 5. Database Schema

### 5.1 SQLite Schema

```sql
-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- bcrypt hash
    role TEXT NOT NULL,           -- 'admin', 'analyst', 'viewer'
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role)
);

-- Cases table
CREATE TABLE cases (
    case_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    customer_id TEXT NOT NULL,
    customer_name TEXT,
    case_type TEXT NOT NULL,      -- 'transaction_monitoring', 'investigation', 'onboarding'
    status TEXT DEFAULT 'draft',  -- 'draft', 'analyzing', 'analysis_ok', 'sar_generated', 'review', 'approved', 'filed'
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority TEXT DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    INDEX idx_status (status),
    INDEX idx_customer_id (customer_id),
    INDEX idx_created_at (created_at)
);

-- Analysis results table
CREATE TABLE analysis_results (
    result_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    ml_score REAL NOT NULL,       -- 0.0 - 1.0
    rules_score REAL NOT NULL,    -- 0.0 - 1.0
    guilt_score REAL NOT NULL,    -- 0.0 - 100.0
    confidence REAL NOT NULL,     -- 0.0 - 1.0
    risk_level TEXT NOT NULL,     -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    red_flags JSON NOT NULL,      -- Array of red flag objects
    analysis_summary JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    INDEX idx_case_id (case_id),
    INDEX idx_guilt_score (guilt_score)
);

-- SARs table
CREATE TABLE sars (
    sar_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    version INT DEFAULT 1,
    status TEXT DEFAULT 'draft', -- 'draft', 'review', 'approved', 'filed', 'rejected'
    executive_summary TEXT NOT NULL,
    suspicious_description TEXT NOT NULL,
    recommendation TEXT,
    pmla_sections JSON NOT NULL,
    rbi_guidelines JSON NOT NULL,
    guilt_score REAL NOT NULL,
    red_flags JSON NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by TEXT,
    approved_at TIMESTAMP,
    filed_at TIMESTAMP,
    document_hash TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id),
    INDEX idx_case_id (case_id),
    INDEX idx_status (status),
    INDEX idx_filed_at (filed_at)
);

-- Transactions table
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    account_id TEXT NOT NULL,
    customer_id TEXT,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    timestamp TIMESTAMP NOT NULL,
    location TEXT,
    channel TEXT,            -- 'Wire Transfer', 'Crypto', 'Hawala', 'Cash', etc.
    counterparty TEXT,
    description TEXT,
    transaction_data JSON,  -- Full raw transaction object
    FOREIGN KEY (case_id) REFERENCES cases(case_id),
    INDEX idx_case_id (case_id),
    INDEX idx_account_id (account_id),
    INDEX idx_timestamp (timestamp)
);

-- Audit trail table (JSON chain stored separately, this is for indexing)
CREATE TABLE audit_index (
    event_id TEXT PRIMARY KEY,
    sequence INT UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    resource TEXT NOT NULL,
    action TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    chain_valid BOOLEAN NOT NULL,
    UNIQUE INDEX idx_sequence (sequence),
    INDEX idx_timestamp (timestamp),
    INDEX idx_event_type (event_type),
    INDEX idx_resource (resource)
);

-- Alerts table
CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    case_id TEXT,
    sar_id TEXT,
    alert_type TEXT NOT NULL,     -- 'HIGH_RISK', 'PENDING', 'APPROVED', 'REJECTED', 'ERROR'
    severity TEXT NOT NULL,       -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    message TEXT NOT NULL,
    recipients JSON NOT NULL,
    sent_at TIMESTAMP,
    status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    retry_count INT DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_case_id (case_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization Flow

```
┌──────────────┐
│  USER LOGIN  │
└──────┬───────┘
       │ (username, password)
       ▼
┌──────────────────────────────┐
│  BCRYPT PASSWORD VERIFICATION │
├──────────────────────────────┤
│  1. Hash provided password   │
│  2. Compare with stored hash │
│  3. Rate limit: 5 attempts   │
└──────┬───────────────────────┘
       │ Success
       ▼
┌──────────────────────────────┐
│  JWT TOKEN GENERATION        │
├──────────────────────────────┤
│ Header:                      │
│   {                          │
│     "alg": "HS256",          │
│     "typ": "JWT"             │
│   }                          │
│                              │
│ Payload:                     │
│   {                          │
│     "user_id": "usr_001",    │
│     "username": "analyst",   │
│     "role": "analyst",       │
│     "iat": 1713265445,       │
│     "exp": 1713269045        │ (1 hour)
│   }                          │
│                              │
│ Signature:                   │
│   HMACSHA256(                │
│     base64(header) + '.' +   │
│     base64(payload),         │
│     JWT_SECRET               │
│   )                          │
└──────┬───────────────────────┘
       │ Token issued
       ▼
┌──────────────────────────────┐
│  API REQUEST WITH TOKEN      │
├──────────────────────────────┤
│ Header:                      │
│   Authorization: Bearer ...  │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  TOKEN VALIDATION            │
├──────────────────────────────┤
│ 1. Extract from header      │
│ 2. Verify signature         │
│ 3. Check expiration         │
│ 4. Extract user info        │
└──────┬───────────────────────┘
       │ Valid
       ▼
┌──────────────────────────────┐
│  PERMISSION CHECK            │
├──────────────────────────────┤
│ Check role vs. resource      │
│ • Admin: all actions        │
│ • Analyst: read+create      │
│ • Viewer: read-only         │
└──────┬───────────────────────┘
       │ Authorized
       ▼
┌──────────────────────────────┐
│  EXECUTE ENDPOINT            │
└──────────────────────────────┘
```

### 6.2 Data Encryption Strategy

```python
# Sensitive data encryption using Fernet (symmetric)
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_customer_pii(self, customer_data: Dict) -> str:
        """
        Encrypt personally identifiable information
        Sensitive fields: name, email, phone, account_number, SSN/PAN
        """
        json_str = json.dumps(customer_data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return encrypted.decode()
    
    def decrypt_customer_pii(self, encrypted_str: str) -> Dict:
        """Decrypt PII for display/processing"""
        decrypted = self.cipher.decrypt(encrypted_str.encode())
        return json.loads(decrypted.decode())
```

### 6.3 API Rate Limiting

```python
# Rate limiting per user/IP
limiter = RateLimiter(
    key_func=get_user_id,  # Per user
    rates=["100/hour", "10/minute"]
)

@app.post("/analyze/batch")
@limiter.limit("1/minute")  # 1 batch job per minute
async def batch_analyze(request: Request, case: AnalyzeRequest):
    """Prevent resource exhaustion"""
    return await process_analysis(case)
```

---

## 7. ML Pipeline Architecture

### 7.1 Model Training Pipeline

```
┌────────────────────────────────────────────────────────────┐
│ STEP 1: DATA PREPARATION                                  │
├────────────────────────────────────────────────────────────┤
│ • Load raw transactions (transactions_test.csv)            │
│ • Generate synthetic data (Faker)                          │
│ • Combine and label (suspicious=1, normal=0)              │
│ • Train/test split: 80/20                                 │
│ Output: balanced dataset with labels                       │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 2: FEATURE ENGINEERING                               │
├────────────────────────────────────────────────────────────┤
│ • Extract 25+ features from raw data                       │
│ • Temporal, amount-based, account, deviation, risk         │
│ Output: [N x 25] feature matrix                            │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 3: CLASS BALANCING (SMOTE)                            │
├────────────────────────────────────────────────────────────┤
│ • Oversample minority class (suspicious)                   │
│ • Create synthetic examples via interpolation              │
│ • Balanced dataset: 50% / 50%                              │
│ Output: [N' x 25] balanced feature matrix                  │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 4: NORMALIZATION (StandardScaler)                     │
├────────────────────────────────────────────────────────────┤
│ • Scale each feature: (x - μ) / σ                          │
│ • Fit on training set, apply to test                       │
│ Output: [N' x 25] scaled feature matrix                    │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 5: MODEL TRAINING (Parallel)                          │
├────────────────────────────────────────────────────────────┤
│ Model 1: Random Forest                                     │
│   - 100 trees, depth=15, min_samples_leaf=5               │
│   - Class weights: balanced                                │
│                                                             │
│ Model 2: XGBoost                                           │
│   - 100 rounds, learning_rate=0.1, max_depth=6            │
│   - Scale_pos_weight for imbalance                          │
│                                                             │
│ Model 3: Logistic Regression                               │
│   - L2 regularization, max_iter=1000                       │
│   - Class weights: balanced                                │
│                                                             │
│ Output: 3 trained model objects                            │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 6: MODEL EVALUATION                                   │
├────────────────────────────────────────────────────────────┤
│ Metrics per model:                                         │
│   • Accuracy: (TP + TN) / Total                            │
│   • Precision: TP / (TP + FP) - false alarm rate           │
│   • Recall: TP / (TP + FN) - detection rate                │
│   • F1-Score: harmonic mean of precision & recall          │
│   • ROC-AUC: area under ROC curve                          │
│   • Confusion Matrix: TP, FP, TN, FN                       │
│                                                             │
│ Output: Performance metrics for model selection            │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 7: SHAP EXPLAINABILITY                                │
├────────────────────────────────────────────────────────────┤
│ • Initialize TreeExplainer for XGBoost                     │
│ • Compute SHAP values for test set                         │
│ • Generate feature importance                              │
│ • Identify top contributing features                       │
│                                                             │
│ Output: SHAP values for interpretation                     │
└────────────┬───────────────────────────────────────────────┘
             │
┌────────────▼───────────────────────────────────────────────┐
│ STEP 8: MODEL PERSISTENCE                                  │
├────────────────────────────────────────────────────────────┤
│ • Pickle all 3 models + scaler                             │
│ • Save to ML/model.pkl                                     │
│ • Store hyperparameters to ML/model_meta.json              │
│ • Version control: model_20260416_v1.pkl                   │
│                                                             │
│ Output: Production-ready model artifact                    │
└────────────────────────────────────────────────────────────┘
```

### 7.2 Model Inference Pipeline

```python
class ModelInference:
    def __init__(self, model_path: str = "ML/model.pkl"):
        # Load cached models
        self.models = pickle.load(open(model_path, 'rb'))
        self.rf_model = self.models['rf']
        self.xgb_model = self.models['xgb']
        self.lr_model = self.models['lr']
        self.scaler = self.models['scaler']
        self.shap_explainer = shap.TreeExplainer(self.xgb_model)
    
    def predict(self, X: pd.DataFrame) -> Dict:
        """
        Predict on new data and explain predictions
        """
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from each model
        rf_pred_proba = self.rf_model.predict_proba(X_scaled)[:, 1]
        xgb_pred_proba = self.xgb_model.predict_proba(X_scaled)[:, 1]
        lr_pred_proba = self.lr_model.predict_proba(X_scaled)[:, 1]
        
        # Ensemble prediction (simple average)
        ensemble_pred = np.mean([rf_pred_proba, xgb_pred_proba, lr_pred_proba], axis=0)
        
        # Get SHAP explanations
        shap_values = self.shap_explainer.shap_values(X_scaled)
        
        # Identify top contributing features
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        top_features_idx = np.argsort(mean_abs_shap)[-5:]
        top_features = [X.columns[i] for i in top_features_idx]
        
        return {
            'probability': float(ensemble_pred[0]),
            'risk_score': float(ensemble_pred[0] * 100),
            'confidence': float(1 - np.std([rf_pred_proba, xgb_pred_proba, lr_pred_proba])),
            'top_features': top_features,
            'shap_values': shap_values.tolist()
        }
```

---

## 8. Implementation Roadmap

### Phase-wise Breakdown

```
PHASE 1: Foundation (Week 1-2)
├── Project structure & Git setup
├── Environment configuration (.env)
├── Database schema creation
├── FastAPI base structure
└── Streamlit UI skeleton

PHASE 2: Authentication (Week 3-4)
├── User registration/login endpoints
├── JWT token implementation
├── Password hashing (bcrypt)
├── Role-based access control
└── Auth middleware integration

PHASE 3: Data Pipeline (Week 5-6)
├── CSV upload functionality
├── Data validation & cleaning
├── Feature engineering
├── Synthetic data generation (Faker)
└── Batch processing via Celery

PHASE 4: ML Models (Week 7-8)
├── Random Forest training
├── XGBoost implementation
├── Logistic Regression
├── SMOTE balancing
├── Model persistence (pickle)
└── Model versioning

PHASE 5: Analysis Engine (Week 9-10)
├── ML inference pipeline
├── C++ detection engine compilation
├── Rule-based scoring
├── Risk aggregation
└── SHAP explainability

PHASE 6: SAR Generation (Week 11-12)
├── SAR template structure
├── Gemini LLM integration
├── Local template fallback
├── Legal mapping (PMLA/RBI)
├── PDF export (ReportLab)
└── DOCX export (python-docx)

PHASE 7: Audit Trail (Week 13-14)
├── SHA-256 hash chain implementation
├── Event logging
├── Chain integrity verification
├── Immutability enforcement
└── Audit query endpoints

PHASE 8: Alert System (Week 15-16)
├── Gmail SMTP integration
├── Alert types & thresholds
├── Recipient management
├── Retry logic
└── Alert history tracking

PHASE 9: Frontend (Week 17-18)
├── Dashboard with KPIs
├── Case management UI
├── SAR editor
├── CSV upload interface
├── Analytics & visualizations
└── Report export

PHASE 10: API Complete (Week 19-20)
├── All remaining endpoints
├── Error handling
├── Rate limiting
├── CORS configuration
├── OpenAPI documentation
└── Request/response logging

PHASE 11: Testing (Week 21-22)
├── Unit tests (95%+ coverage)
├── Integration tests
├── API tests
├── ML model validation
├── Performance benchmarking
└── Security testing

PHASE 12: Deployment (Week 23-24)
├── Docker containerization
├── docker-compose orchestration
├── Environment configs
├── CI/CD pipeline
├── Load testing
└── Production readiness

TOTAL: ~6 months (24 weeks) for full production deployment
```

---

## 9. Performance Optimization

### 9.1 Caching Strategy

```python
# Redis caching for hot data
cache = Redis(host='localhost', port=6379, db=0)

@app.get("/cases/{case_id}", )
async def get_case(case_id: str):
    # Try cache first
    cached = cache.get(f"case:{case_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from DB
    case = db.query(Case).filter_by(id=case_id).first()
    
    # Store in cache (1 hour TTL)
    cache.setex(f"case:{case_id}", 3600, json.dumps(case.to_dict()))
    
    return case

# Model caching
ML_MODELS = None

def get_models():
    global ML_MODELS
    if ML_MODELS is None:
        ML_MODELS = pickle.load(open("ML/model.pkl"))
    return ML_MODELS
```

### 9.2 Query Optimization

```sql
-- Index frequently queried columns
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_customer_id ON cases(customer_id);
CREATE INDEX idx_sars_case_id ON sars(case_id);
CREATE INDEX idx_audit_resource ON audit_index(resource);

-- Optimize audit queries with covering index
CREATE INDEX idx_audit_covering 
ON audit_index(timestamp, event_type, resource) 
INCLUDE (event_id, actor);

-- Partition large tables by date if needed
CREATE TABLE transactions_2026_q1 PARTITION OF transactions
  FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
```

### 9.3 Async Processing

```python
# Long-running operations via Celery
@celery.task
def async_batch_analysis(case_id: str, csv_path: str):
    """Process large CSV files asynchronously"""
    try:
        # Process in chunks
        for chunk in pd.read_csv(csv_path, chunksize=1000):
            analyze_chunk(chunk)
        
        # Update status
        db.update_case_status(case_id, 'completed')
    except Exception as e:
        db.update_case_status(case_id, 'failed', error=str(e))

# Trigger async job
job = async_batch_analysis.delay(case_id, csv_path)
```

---

## 10. Deployment Architecture

### 10.1 Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: proofsar
      POSTGRES_USER: proofsar
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  fastapi:
    build: .
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://proofsar:${DB_PASSWORD}@postgres:5432/proofsar
      REDIS_URL: redis://redis:6379/0
      GEMINI_API_KEY: ${GEMINI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./:/app
  
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    command: streamlit run FRONTEND/app.py
    ports:
      - "8501:8501"
    environment:
      API_URL: http://fastapi:8000
    depends_on:
      - fastapi
  
  celery:
    build: .
    command: celery -A BACKEND.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://proofsar:${DB_PASSWORD}@postgres:5432/proofsar
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis

volumes:
  postgres_data:
```

### 10.2 Cloud Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────────────┐
│                      AWS DEPLOYMENT                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ CloudFront CDN                                       │  │
│  │ (Static assets, PDF caching)                         │  │
│  └──────────┬───────────────────────────────────────────┘  │
│             │                                               │
│  ┌──────────▼───────────────────────────────────────────┐  │
│  │ Application Load Balancer (ALB)                      │  │
│  │ ├── HTTPS termination                                │  │
│  │ ├── Path-based routing                               │  │
│  │ └── Health checks                                    │  │
│  └────────────┬──────────────────────────────────────────┘ │
│               │                                             │
│  ┌────────────┼──────────────────────────────────────────┐ │
│  │ ECS Cluster                                          │  │
│  │ ├── FastAPI Task (2-5 replicas)                      │  │
│  │ ├── Streamlit Task (1-2 replicas)                    │  │
│  │ └── Celery Worker Task (2-10 replicas)               │  │
│  └────────────┬──────────────────────────────────────────┘ │
│               │                                             │
│  ┌────────────┼──────────────────────────────────────────┐ │
│  │ Data & Services                                      │  │
│  │ ├── RDS PostgreSQL (Multi-AZ)                        │  │
│  │ ├── ElastiCache Redis                                │  │
│  │ ├── S3 (PDFs, logs, exports)                         │  │
│  │ ├── CloudWatch (Monitoring)                          │  │
│  │ └── Secrets Manager (API keys, creds)                │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This detailed architecture provides:

✅ **Complete technical blueprint** for implementation  
✅ **Module specifications** with code examples  
✅ **Data flow diagrams** showing processing pipelines  
✅ **API reference** with all endpoints  
✅ **Database schema** for SQL implementation  
✅ **Security architecture** for enterprise compliance  
✅ **ML pipeline** for model training & inference  
✅ **Implementation roadmap** for 24-week rollout  
✅ **Performance optimization** strategies  
✅ **Deployment architecture** for production  

This document serves as the definitive guide for ProofSAR AI development and deployment.
