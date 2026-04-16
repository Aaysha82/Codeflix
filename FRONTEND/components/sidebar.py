"""
FRONTEND/components/sidebar.py
Streamlit sidebar component — navigation, user info, system status
"""
import streamlit as st
import requests
from datetime import datetime

BACKEND = st.secrets.get("BACKEND_URL", "http://localhost:8000") if hasattr(st, "secrets") else "http://localhost:8000"

def render_sidebar():
    with st.sidebar:
        # Logo + Branding
        st.markdown("""
        <div style="text-align:center;padding:12px 0 8px 0">
          <div style="font-size:32px">🛡️</div>
          <div style="font-size:18px;font-weight:700;color:#1a237e;letter-spacing:1px">ProofSAR AI</div>
          <div style="font-size:10px;color:#888;margin-top:2px">AML Detection & SAR Platform</div>
        </div>
        <hr style="border:none;border-top:1px solid #e0e0e0;margin:8px 0"/>
        """, unsafe_allow_html=True)

        # User info
        user = st.session_state.get("user", {})
        if user:
            role_color = "#1a237e" if user.get("role") == "admin" else "#1565c0"
            st.markdown(f"""
            <div style="background:#f0f4ff;border-radius:8px;padding:10px 12px;margin-bottom:12px">
              <div style="font-size:12px;color:#666">Logged in as</div>
              <div style="font-weight:700;color:#1a237e;font-size:14px">{user.get('username','')}</div>
              <span style="background:{role_color};color:#fff;font-size:10px;
                           padding:2px 8px;border-radius:10px;font-weight:600">
                {user.get('role','').upper()}
              </span>
            </div>
            """, unsafe_allow_html=True)

        # Navigation
        st.markdown("**Navigate**")
        pages = {
            "📊 Dashboard":        "dashboard",
            "🔍 Analyze Transaction": "analyze",
            "📁 Batch Upload":      "batch",
            "📄 Generate SAR":      "sar",
            "🔗 Audit Log":         "audit",
            "⚠️ Alerts":            "alerts",
        }
        if user.get("role") == "admin":
            pages["👥 User Management"] = "users"

        for label, page_key in pages.items():
            active = st.session_state.get("active_page") == page_key
            btn_style = "primary" if active else "secondary"
            if st.button(label, key=f"nav_{page_key}", use_container_width=True, type=btn_style):
                st.session_state.active_page = page_key
                st.rerun()

        st.markdown("---")

        # Backend status
        try:
            r = requests.get(f"{BACKEND}/health", timeout=3)
            if r.status_code == 200:
                st.markdown("🟢 **Backend** Online")
            else:
                st.markdown("🔴 **Backend** Error")
        except Exception:
            st.markdown("🔴 **Backend** Offline")

        st.markdown(f"<div style='font-size:10px;color:#aaa;margin-top:4px'>{datetime.now().strftime('%H:%M:%S')}</div>",
                    unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
