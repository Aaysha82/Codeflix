"""
FRONTEND/app.py
ProofSAR AI — Complete Streamlit Frontend
Run: streamlit run FRONTEND/app.py
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json, time, io
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests

# ─── Page config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="ProofSAR AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Inject CSS ───────────────────────────────────────────────────────────────
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def api(method: str, path: str, **kwargs) -> dict | None:
    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = getattr(requests, method)(f"{BACKEND}{path}", headers=headers,
                                      timeout=30, **kwargs)
        if r.status_code in (200, 201):
            return r.json()
        st.error(f"API Error {r.status_code}: {r.json().get('detail', r.text)}")
        return None
    except requests.ConnectionError:
        st.error("❌ Cannot connect to backend. Is it running?")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def risk_badge(level: str) -> str:
    # High contrast colors for visibility
    colors = {"HIGH": "#b71c1c", "MEDIUM": "#bf360c", "LOW": "#1b5e20"}
    bg     = {"HIGH": "#ffebee", "MEDIUM": "#fff3e0", "LOW": "#e8f5e9"}
    c = colors.get(level, "#1e293b")
    b = bg.get(level, "#f8fafc")
    return f'<span class="badge" style="background:{b};color:{c};border:1px solid {c}">{level}</span>'


def risk_bar(score: float, level: str) -> str:
    colors = {"HIGH": "#c62828", "MEDIUM": "#e65100", "LOW": "#2e7d32"}
    c = colors.get(level, "#1976d2")
    pct = int(score * 100)
    return f"""<div class="risk-bar-container">
      <div class="risk-bar-fill" style="width:{pct}%;background:{c}"></div>
    </div><div style="font-size:11px;color:{c};font-weight:600">{score:.2%} risk</div>"""


def page_header(icon: str, title: str, subtitle: str):
    st.markdown(f"""
    <div class="page-header">
      <h1>{icon} {title}</h1>
      <p>{subtitle}</p>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def page_login():
    # Centre the login card
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:40px 0 16px">
          <h2 style="font-size:24px;font-weight:700;color:#1a237e;margin:8px 0 4px">ProofSAR AI</h2>
          <p style="color:#475569;font-size:14px;font-weight:500">Explainable AML & SAR Generation Platform</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="admin or analyst")
            password = st.text_input("🔒 Password", type="password", placeholder="Your password")
            submitted = st.form_submit_button("Login →", use_container_width=True, type="primary")

        if submitted:
            with st.spinner("Authenticating…"):
                resp = api("post", "/auth/login",
                           json={"username": username, "password": password})
            if resp:
                st.session_state.update({
                    "token":       resp["access_token"],
                    "user":        {"username": username, "role": resp["role"],
                                    "permissions": resp.get("permissions", [])},
                    "active_page": "dashboard"
                })
                st.success(f"Welcome, {username}! 🎉")
                time.sleep(0.5)
                st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:16px;font-size:12px;color:#475569;font-weight:500">
          Default credentials: <code>admin / Admin@2026</code> | <code>analyst / Analyst@2026</code>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
def page_dashboard():
    page_header("📊", "Dashboard", "Real-time AML detection metrics and system overview")
    metrics = api("get", "/metrics") or {}

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        (c1, "🔍", "Analyses",      metrics.get("total_analyses", 0), "transactions"),
        (c2, "📄", "SARs Filed",    metrics.get("total_sars",     0), "reports"),
        (c3, "🔔", "Alerts Sent",   metrics.get("total_alerts",   0), "notifications"),
        (c4, "🔗", "Audit Events",  metrics.get("total_events",   0), "events"),
        (c5, "✅", "Chain Intact",
             "Yes" if metrics.get("chain_integrity", True) else "⚠️ Broken", ""),
    ]
    for col, icon, label, val, unit in kpis:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="icon">{icon}</div>
              <div class="label">{label}</div>
              <div class="value">{val}</div>
              <div class="delta">{unit}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="card"><div class="card-title">📈 Risk Distribution (Demo)</div>', unsafe_allow_html=True)
        demo_data = {
            "Low Risk (<40%)":    65,
            "Medium Risk (40–70%)": 23,
            "High Risk (>70%)":   12
        }
        fig = go.Figure(go.Pie(
            labels=list(demo_data.keys()),
            values=list(demo_data.values()),
            hole=0.55,
            marker_colors=["#2e7d32", "#e65100", "#c62828"],
            textinfo="label+percent",
            textfont_size=12,
        ))
        fig.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=240,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="card-title">🏷️ AML Pattern Breakdown</div>', unsafe_allow_html=True)
        patterns = {"Structuring": 38, "Layering": 29, "Smurfing": 21, "Other": 12}
        fig2 = go.Figure(go.Bar(
            x=list(patterns.values()),
            y=list(patterns.keys()),
            orientation="h",
            marker_color=["#1976d2", "#283593", "#0d47a1", "#5c6bc0"],
            text=[f"{v}%" for v in patterns.values()],
            textposition="outside"
        ))
        fig2.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(tickfont=dict(size=12)),
            margin=dict(l=10, r=40, t=10, b=10),
            height=240,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Recent audit events
    st.markdown("---")
    st.markdown("#### 🔗 Recent Audit Events")
    events = api("get", "/audit/events?limit=8") or []
    if events:
        for ev in events[:6]:
            et = ev.get("event_type","")
            ts = ev.get("timestamp","")[:19].replace("T"," ")
            actor = ev.get("actor","system")
            h = ev.get("current_hash","")[:16]
            st.markdown(f"""
            <div class="audit-row">
              <div class="audit-dot"></div>
              <div>
                <b style="color:var(--navy)">{et}</b> · <span style="color:var(--text)">{actor}</span>
                <div style="color:var(--text-muted);font-size:11px;font-weight:500">{ts}</div>
                <div class="audit-hash">Hash: {h}…</div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No audit events yet. Run your first analysis!")


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYZE TRANSACTION
# ═══════════════════════════════════════════════════════════════════════════════
def page_analyze():
    page_header("🔍", "Analyze Transaction", "Run ML + rule-based AML detection on a single transaction")

    with st.form("analyze_form"):
        st.markdown("#### Transaction Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            txn_id   = st.text_input("Transaction ID", value="TXN-2024-001")
            account  = st.text_input("Account ID",     value="ACC-78432")
            amount   = st.number_input("Amount (INR ₹)", min_value=1.0, value=950000.0, step=1000.0)
        with c2:
            location = st.selectbox("Location", [
                "Mumbai","Delhi","Bangalore","Hyderabad","Chennai","Kolkata",
                "Cayman Islands","Panama","Switzerland","Dubai","Pune","Jaipur"
            ])
            channel  = st.selectbox("Channel", [
                "Online","ATM","Branch","Mobile","Wire Transfer","RTGS","NEFT","UPI"
            ])
            currency = st.selectbox("Currency", ["INR","USD","EUR","CHF","AED","GBP","SGD"])
        with c3:
            hour     = st.slider("Hour of Day", 0, 23, 2)
            is_wknd  = st.selectbox("Weekend?", [0, 1], format_func=lambda x: "Yes" if x else "No")
            acc_mean = st.number_input("Account Avg Amount", value=50000.0)

        submitted = st.form_submit_button("🚀 Run Analysis", use_container_width=True, type="primary")

    if submitted:
        HIGH_RISK_LOC = {"Cayman Islands","Panama","Switzerland","Dubai","British Virgin Islands"}
        HIGH_RISK_CH  = {"Wire Transfer","RTGS","SWIFT"}
        import math
        amt_log = math.log1p(amount)

        payload = {
            "transaction_id": txn_id, "account_id": account,
            "amount": amount, "location": location, "channel": channel,
            "currency": currency, "hour": hour, "is_weekend": is_wknd,
            "is_high_risk_location": int(location in HIGH_RISK_LOC),
            "is_high_risk_channel":  int(channel  in HIGH_RISK_CH),
            "is_international":      int(currency != "INR"),
            "amount_log":  amt_log,
            "near_threshold": int(850000 <= amount < 1000000),
            "acc_mean_amount": acc_mean,
            "acc_std_amount":  acc_mean * 0.3,
            "acc_txn_count":   20,
            "acc_max_amount":  amount * 1.2,
            "amount_vs_mean":  amount / max(acc_mean, 1),
            "amount_zscore":   (amount - acc_mean) / max(acc_mean * 0.3, 1),
        }

        with st.spinner("🔄 Running ML model, C++ rules & SHAP analysis…"):
            result = api("post", "/analyze", json=payload)

        if result:
            st.session_state["last_verdict"] = {**payload, **result}
            _render_result(result, payload)


def _render_result(result: dict, payload: dict):
    lvl   = result.get("risk_level", "LOW")
    score = result.get("risk_score", 0)
    alert_map = {"HIGH": "alert-high", "MEDIUM": "alert-medium", "LOW": "alert-low"}
    icon_map  = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "✅"}

    st.markdown("---")
    st.markdown("### 📊 Analysis Results")

    # Top summary
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Risk Level</div>
          {risk_badge(lvl)}
          <br><br>
          {risk_bar(score, lvl)}
        </div>""", unsafe_allow_html=True)
    with c2:
        rules = result.get("triggered_rules", [])
        rules_html = "".join(f'<span class="reason-pill">⚡ {r}</span>' for r in rules) or \
                     '<span class="reason-pill">None triggered</span>'
        st.markdown(f"""
        <div class="card">
          <div class="card-title">AML Rules Triggered</div>
          {rules_html}
          <br><br>
          <div style="font-size:11px;color:#6b7280;margin-top:8px">
            SAR Required: <b style="color:{'#c62828' if result.get('sar_required') else '#2e7d32'}">
            {'YES' if result.get('sar_required') else 'NO'}</b>
          </div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="card">
          <div class="card-title">Recommendation</div>
          <div class="{alert_map.get(lvl,'alert-low')}">
            {icon_map.get(lvl,'')} {result.get('recommendation','—')}
          </div>
          <div style="font-size:10px;color:#aaa;margin-top:8px;font-family:monospace">
            Audit: {result.get('audit_hash','')[:20]}…
          </div>
        </div>""", unsafe_allow_html=True)

    # SHAP reasons
    reasons = result.get("top_reasons", [])
    if reasons:
        st.markdown("#### 🧠 Top Risk Indicators (SHAP)")
        fig = go.Figure()
        sorted_r = sorted(reasons, key=lambda x: x.get("importance",0))
        vals  = [r.get("shap_value", 0) for r in sorted_r]
        names = [r.get("description", r.get("feature","")) for r in sorted_r]
        colors_bar = ["#c62828" if v > 0 else "#1976d2" for v in vals]
        fig.add_trace(go.Bar(
            x=vals, y=names, orientation="h",
            marker_color=colors_bar, opacity=0.85,
            text=[f"{v:+.4f}" for v in vals], textposition="outside"
        ))
        fig.update_layout(
            xaxis_title="SHAP Value (Impact on Risk Score)",
            margin=dict(l=10, r=60, t=10, b=10),
            height=max(220, len(reasons)*45),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(zeroline=True, zerolinecolor="#999", zerolinewidth=1.5, gridcolor="#f0f0f0"),
            yaxis=dict(tickfont=dict(size=11))
        )
        st.plotly_chart(fig, use_container_width=True)

    # Full narrative
    with st.expander("📋 Full Risk Narrative"):
        st.code(result.get("narrative", "No narrative available"), language=None)

    # Go to SAR
    if lvl in ("HIGH", "MEDIUM"):
        st.markdown("---")
        if st.button("📄 Generate SAR Report", type="primary"):
            st.session_state.active_page = "sar"
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH UPLOAD
# ═══════════════════════════════════════════════════════════════════════════════
def page_batch():
    page_header("📁", "Batch Analysis", "Upload a CSV to run AML detection on multiple transactions")

    st.info("📋 Required columns: `transaction_id`, `account_id`, `amount`, `location`, `channel`")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        st.markdown(f"**Preview** — {len(df):,} rows loaded")
        st.dataframe(df.head(5), use_container_width=True)

        if st.button("🚀 Run Batch Detection", type="primary"):
            with st.spinner(f"Analysing {len(df):,} transactions…"):
                uploaded.seek(0)
                files = {"file": (uploaded.name, uploaded, "text/csv")}
                token = st.session_state.get("token","")
                try:
                    r = requests.post(f"{BACKEND}/analyze/batch",
                                      headers={"Authorization": f"Bearer {token}"},
                                      files=files, timeout=120)
                    if r.status_code == 200:
                        data = r.json()
                        _render_batch_results(data)
                    else:
                        st.error(f"Batch error: {r.json().get('detail', r.text)}")
                except Exception as e:
                    st.error(f"Batch request failed: {e}")


def _render_batch_results(data: dict):
    total   = data.get("total",   0)
    flagged = data.get("flagged", 0)
    pct     = data.get("flagged_pct", 0)
    results = data.get("results", [])

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Analyzed", f"{total:,}")
    with c2: st.metric("Flagged",         f"{flagged:,}", delta=f"{pct}%")
    with c3: st.metric("Clean",           f"{total-flagged:,}")

    if results:
        df = pd.DataFrame(results)
        show_cols = [c for c in ["transaction_id","account_id","amount","location",
                                  "channel","is_flagged","risk_score","triggered_rules"]
                     if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True, height=300)

        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Results CSV", csv_bytes, "proofsar_results.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE SAR
# ═══════════════════════════════════════════════════════════════════════════════
def page_sar():
    page_header("📄", "Generate SAR", "Create a regulator-ready Suspicious Activity Report")

    verdict = st.session_state.get("last_verdict")

    if not verdict:
        st.warning("⚠️ No transaction analysed yet. Please run an analysis first.")
        if st.button("← Go to Analysis", type="primary"):
            st.session_state.active_page = "analyze"
            st.rerun()
        return

    # Summary card
    lvl = verdict.get("risk_level", "N/A")
    st.markdown(f"""
    <div class="card">
      <div class="card-title">📌 Transaction Summary</div>
      <table style="width:100%;font-size:13px;border-collapse:collapse">
        <tr><td style="color:#6b7280;padding:4px 8px;width:160px">Transaction ID</td>
            <td style="font-weight:600;padding:4px 8px;font-family:monospace">{verdict.get('transaction_id','N/A')}</td>
            <td style="color:#6b7280;padding:4px 8px;width:140px">Account ID</td>
            <td style="font-weight:600;padding:4px 8px">{verdict.get('account_id','N/A')}</td></tr>
        <tr><td style="color:#6b7280;padding:4px 8px">Amount</td>
            <td style="padding:4px 8px">₹{float(verdict.get('amount',0)):,.2f}</td>
            <td style="color:#6b7280;padding:4px 8px">Risk Level</td>
            <td style="padding:4px 8px">{risk_badge(lvl)}</td></tr>
      </table>
    </div>""", unsafe_allow_html=True)

    if st.button("⚡ Generate SAR with AI", type="primary", use_container_width=True):
        with st.spinner("🤖 Generating SAR narrative…"):
            resp = api("post", "/generate-sar", json={"verdict": verdict})

        if resp:
            st.session_state["last_sar"] = resp
            sar_text = resp.get("sar_text", "")

            st.markdown("#### 📋 SAR Narrative")
            st.markdown(f'<div class="sar-box">{sar_text}</div>', unsafe_allow_html=True)

            st.success(f"✅ SAR generated via **{resp.get('source','template')}** · "
                       f"ID: `{resp.get('sar_id','N/A')}`")

            # PDF download
            st.markdown("---")
            if st.button("📥 Generate & Download PDF"):
                _download_pdf(verdict, sar_text, resp.get("audit_hash",""))

    elif "last_sar" in st.session_state:
        sar_text = st.session_state["last_sar"].get("sar_text", "")
        st.markdown("#### 📋 SAR Narrative (Last Generated)")
        st.markdown(f'<div class="sar-box">{sar_text}</div>', unsafe_allow_html=True)
        if st.button("📥 Download PDF"):
            _download_pdf(verdict, sar_text,
                          st.session_state["last_sar"].get("audit_hash",""))


def _download_pdf(verdict: dict, sar_text: str, audit_hash: str):
    try:
        from REPORTS.pdf_generator import generate_pdf
        with st.spinner("Generating PDF…"):
            pdf_bytes = generate_pdf(verdict, sar_text, audit_hash)
        txn_id = verdict.get("transaction_id","sar")
        st.download_button(
            "⬇️ Download SAR PDF",
            data     = pdf_bytes,
            file_name= f"SAR_{txn_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime     = "application/pdf",
            type     = "primary"
        )
    except Exception as e:
        st.error(f"PDF generation failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOG
# ═══════════════════════════════════════════════════════════════════════════════
def page_audit():
    page_header("🔗", "Audit Log", "Tamper-proof SHA-256 blockchain audit trail")

    # Chain verification
    integrity = api("get", "/audit/verify") or {}
    if integrity.get("valid"):
        st.success(f"✅ Audit chain INTACT — {integrity.get('total_events',0)} events verified")
    else:
        st.error(f"❌ Chain BROKEN at event #{integrity.get('broken_at')} — {integrity.get('message')}")

    # Events
    limit = st.slider("Events to show", 10, 200, 50)
    events = api("get", f"/audit/events?limit={limit}") or []

    if events:
        rows = []
        for e in events:
            rows.append({
                "Seq":        e.get("seq"),
                "Event Type": e.get("event_type"),
                "Actor":      e.get("actor"),
                "Timestamp":  e.get("timestamp","")[:19].replace("T"," "),
                "Hash (16)":  e.get("current_hash","")[:16]+"…",
                "Prev Hash":  e.get("prev_hash","")[:16]+"…",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=400)
        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Export Audit Log CSV", csv, "audit_log.csv","text/csv")
    else:
        st.info("No audit events recorded yet.")


# ═══════════════════════════════════════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════════════════════════════════════
def page_alerts():
    page_header("⚠️", "Alerts", "High-risk transaction and SAR filing notifications")
    alerts = api("get", "/alerts") or []

    if not alerts:
        st.info("No alerts recorded yet.")
        return

    for a in alerts:
        et   = a.get("event_type","")
        data = a.get("event_data",{})
        ts   = a.get("timestamp","")[:19].replace("T"," ")
        icon = "🚨" if "ALERT" in et else "📄"
        st.markdown(f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <span style="font-size:18px">{icon}</span>
              <b style="font-size:13px;margin-left:8px">{et}</b>
              <div style="color:#6b7280;font-size:11px;margin-top:4px">{ts}</div>
            </div>
            <div style="font-size:11px;text-align:right;color:#6b7280">
              TXN: {data.get('transaction_id','N/A')[:16]}…
            </div>
          </div>
          <div style="margin-top:8px;font-size:12px;color:#444">
            {json.dumps(data, indent=2)[:200]}…
          </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT (Admin only)
# ═══════════════════════════════════════════════════════════════════════════════
def page_users():
    page_header("👥", "User Management", "Manage analyst and admin accounts")
    users = api("get", "/auth/users") or []

    if users:
        df = pd.DataFrame(users)
        st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.markdown("#### ➕ Register New User")
    with st.form("register_form"):
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("Username")
            new_email    = st.text_input("Email")
        with c2:
            new_password = st.text_input("Password", type="password")
            new_role     = st.selectbox("Role", ["analyst","admin"])
        if st.form_submit_button("Register User", type="primary"):
            resp = api("post", "/auth/register", json={
                "username": new_username, "password": new_password,
                "email": new_email, "role": new_role
            })
            if resp:
                st.success(f"✅ User '{new_username}' registered as {new_role}")


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:16px 0 10px">
          <div style="font-size:36px">🛡️</div>
          <div style="font-size:16px;font-weight:700;color:#1a237e">ProofSAR AI</div>
          <div style="font-size:10px;color:#888">AML Detection Platform</div>
        </div>
        <hr style="border:none;border-top:1px solid #e0e7ff;margin:8px 0"/>
        """, unsafe_allow_html=True)

        user = st.session_state.get("user", {})
        role_color = "#1a237e" if user.get("role") == "admin" else "#1565c0"
        st.markdown(f"""
        <div style="background:#f0f4ff;border-radius:8px;padding:10px;margin-bottom:12px">
          <div style="font-size:11px;color:#666">Logged in as</div>
          <div style="font-weight:700;color:#1a237e">{user.get('username','')}</div>
          <span style="background:{role_color};color:#fff;font-size:10px;
                       padding:2px 8px;border-radius:10px">{user.get('role','').upper()}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("**Navigation**")
        pages = [
            ("📊 Dashboard",             "dashboard"),
            ("🔍 Analyze Transaction",    "analyze"),
            ("📁 Batch Upload",           "batch"),
            ("📄 Generate SAR",           "sar"),
            ("🔗 Audit Log",              "audit"),
            ("⚠️ Alerts",                 "alerts"),
        ]
        if user.get("role") == "admin":
            pages.append(("👥 User Management", "users"))

        for label, page_key in pages:
            is_active = st.session_state.get("active_page") == page_key
            if st.button(label, key=f"nav_{page_key}", use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.active_page = page_key
                st.rerun()

        st.markdown("---")
        try:
            r = requests.get(f"{BACKEND}/health", timeout=2)
            status = "🟢 Online" if r.status_code == 200 else "🔴 Error"
        except Exception:
            status = "🔴 Offline"
        st.markdown(f"**Backend:** {status}")
        st.markdown(f"<div style='font-size:10px;color:#aaa'>{datetime.now().strftime('%H:%M:%S')}</div>",
                    unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    if "token" not in st.session_state:
        page_login()
        return

    render_sidebar()

    page = st.session_state.get("active_page", "dashboard")
    dispatch = {
        "dashboard": page_dashboard,
        "analyze":   page_analyze,
        "batch":     page_batch,
        "sar":       page_sar,
        "audit":     page_audit,
        "alerts":    page_alerts,
        "users":     page_users,
    }
    dispatch.get(page, page_dashboard)()


if __name__ == "__main__":
    main()
