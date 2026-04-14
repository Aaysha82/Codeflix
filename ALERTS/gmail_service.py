"""
ALERTS/gmail_service.py
Gmail SMTP alert service for high-risk AML events.
Uses App Password (not account password) for authentication.
"""
from __future__ import annotations
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
SMTP_HOST  = "smtp.gmail.com"
SMTP_PORT  = 587


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Core SMTP send function. Returns True on success."""
    if not EMAIL_USER or not EMAIL_PASS:
        logger.warning("Email credentials not configured — alert skipped")
        return False
    if EMAIL_PASS in ("your_16_char_app_password", ""):
        logger.warning("EMAIL_PASS is placeholder — skipping SMTP")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"ProofSAR AI <{EMAIL_USER}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html_body, "html"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        logger.success(f"Alert sent to {to_email}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check EMAIL_PASS (App Password)")
        return False
    except Exception as e:
        logger.error(f"Alert send failed: {e}")
        return False


# ─── HTML templates ───────────────────────────────────────────────────────────
def _high_risk_template(txn_id: str, account: str, amount: float,
                          risk_score: float, risk_level: str, rules: list) -> str:
    rules_html = "".join(f"<li>{r}</li>" for r in rules) or "<li>Anomalous Pattern</li>"
    color = {"HIGH": "#d32f2f", "MEDIUM": "#f57c00", "LOW": "#388e3c"}.get(risk_level, "#555")
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px">
      <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
                  box-shadow:0 2px 8px rgba(0,0,0,0.12);overflow:hidden">
        <div style="background:linear-gradient(135deg,#1a237e,#283593);padding:24px;color:#fff">
          <h2 style="margin:0">🚨 ProofSAR AI — High-Risk Alert</h2>
          <p style="margin:6px 0 0;opacity:.85">Automated AML Detection System</p>
        </div>
        <div style="padding:24px">
          <table style="width:100%;border-collapse:collapse">
            <tr><td style="padding:8px;color:#666;width:160px">Transaction ID</td>
                <td style="padding:8px;font-weight:bold">{txn_id}</td></tr>
            <tr style="background:#f9f9f9">
                <td style="padding:8px;color:#666">Account</td>
                <td style="padding:8px">{account}</td></tr>
            <tr><td style="padding:8px;color:#666">Amount</td>
                <td style="padding:8px">₹{amount:,.2f}</td></tr>
            <tr style="background:#f9f9f9">
                <td style="padding:8px;color:#666">Risk Score</td>
                <td style="padding:8px;font-weight:bold;color:{color}">{risk_score:.2%}</td></tr>
            <tr><td style="padding:8px;color:#666">Risk Level</td>
                <td style="padding:8px">
                  <span style="background:{color};color:#fff;padding:3px 10px;
                               border-radius:12px;font-size:12px">{risk_level}</span>
                </td></tr>
          </table>
          <div style="margin-top:16px">
            <h4 style="color:#333;margin-bottom:8px">AML Patterns Detected</h4>
            <ul style="color:#555;padding-left:20px">{rules_html}</ul>
          </div>
          <div style="margin-top:20px;background:#fff3e0;border-left:4px solid #f57c00;
                      padding:12px;border-radius:4px">
            <strong>Action Required:</strong> Review and file SAR within 7 days per PMLA Section 12A.
          </div>
        </div>
        <div style="background:#f5f5f5;padding:16px;text-align:center;color:#999;font-size:12px">
          Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · ProofSAR AI · Confidential
        </div>
      </div>
    </body></html>"""


def _sar_generated_template(sar_id: str, txn_id: str, account: str, risk_level: str) -> str:
    color = {"HIGH": "#d32f2f", "MEDIUM": "#f57c00", "LOW": "#388e3c"}.get(risk_level, "#555")
    return f"""
    <html><body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px">
      <div style="max-width:600px;margin:auto;background:#fff;border-radius:8px;
                  box-shadow:0 2px 8px rgba(0,0,0,0.12);overflow:hidden">
        <div style="background:linear-gradient(135deg,#1b5e20,#2e7d32);padding:24px;color:#fff">
          <h2 style="margin:0">✅ SAR Generated — ProofSAR AI</h2>
          <p style="margin:6px 0 0;opacity:.85">Compliance Report Ready</p>
        </div>
        <div style="padding:24px">
          <p style="color:#555">A Suspicious Activity Report has been automatically generated
          and is ready for compliance officer review.</p>
          <table style="width:100%;border-collapse:collapse">
            <tr><td style="padding:8px;color:#666;width:160px">SAR ID</td>
                <td style="padding:8px;font-weight:bold;font-family:monospace">{sar_id}</td></tr>
            <tr style="background:#f9f9f9">
                <td style="padding:8px;color:#666">Transaction</td>
                <td style="padding:8px">{txn_id}</td></tr>
            <tr><td style="padding:8px;color:#666">Account</td>
                <td style="padding:8px">{account}</td></tr>
            <tr style="background:#f9f9f9">
                <td style="padding:8px;color:#666">Risk Level</td>
                <td style="padding:8px">
                  <span style="background:{color};color:#fff;padding:3px 10px;
                               border-radius:12px;font-size:12px">{risk_level}</span>
                </td></tr>
          </table>
          <div style="margin-top:20px;background:#e8f5e9;border-left:4px solid #2e7d32;
                      padding:12px;border-radius:4px">
            Please log in to ProofSAR AI dashboard to review, edit, and submit this SAR
            to FIU-IND (Financial Intelligence Unit — India).
          </div>
        </div>
        <div style="background:#f5f5f5;padding:16px;text-align:center;color:#999;font-size:12px">
          Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · ProofSAR AI · Confidential
        </div>
      </div>
    </body></html>"""


# ─── Public API ───────────────────────────────────────────────────────────────
def send_high_risk_alert(
    to_email: str,
    txn_id: str,
    account: str,
    amount: float,
    risk_score: float,
    risk_level: str,
    triggered_rules: list
) -> bool:
    subject  = f"🚨 [ProofSAR AI] HIGH-RISK Transaction Detected — {risk_level}"
    html     = _high_risk_template(txn_id, account, amount, risk_score, risk_level, triggered_rules)
    return _send_email(to_email, subject, html)


def send_sar_generated_alert(
    to_email: str,
    sar_id: str,
    txn_id: str,
    account: str,
    risk_level: str
) -> bool:
    subject = f"✅ [ProofSAR AI] SAR Generated — {sar_id}"
    html    = _sar_generated_template(sar_id, txn_id, account, risk_level)
    return _send_email(to_email, subject, html)


def test_connection() -> dict:
    """Test SMTP connection without sending an email."""
    if not EMAIL_USER or not EMAIL_PASS:
        return {"connected": False, "reason": "Credentials not configured"}
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(EMAIL_USER, EMAIL_PASS)
        return {"connected": True, "reason": "SMTP connection successful"}
    except Exception as e:
        return {"connected": False, "reason": str(e)}
