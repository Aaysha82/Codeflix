"""
AI/gemini_client.py
Google Gemini API client for SAR narrative generation.
Falls back to local template if API key missing or quota exceeded.
"""
from __future__ import annotations
import os
import textwrap
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
_gemini_model = None


def _init_gemini():
    """Lazy-initialize Gemini client."""
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY not set — SAR will use template fallback")
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        logger.success("Gemini 1.5 Flash initialized")
        return _gemini_model
    except Exception as e:
        logger.error(f"Gemini init failed: {e}")
        return None


def _build_sar_prompt(verdict: dict) -> str:
    """Build a structured prompt for Gemini to generate a SAR narrative."""
    txn_id    = verdict.get("transaction_id", "N/A")
    account   = verdict.get("account_id",     "N/A")
    amount    = verdict.get("metadata", {}).get("amount",   0)
    channel   = verdict.get("metadata", {}).get("channel",  "N/A")
    location  = verdict.get("metadata", {}).get("location", "N/A")
    risk      = verdict.get("risk_score",  0)
    risk_lvl  = verdict.get("risk_level",  "N/A")
    rules     = ", ".join(verdict.get("triggered_rules", [])) or "None"
    reasons   = "\n".join(f"  - {r['reason']}" for r in verdict.get("top_reasons", [])[:4])
    violations= verdict.get("legal_violations", [])
    legal_str = ""
    for v in violations:
        legal_str += f"  • {v['act']} {v['section']}: {v['description']}\n"

    return textwrap.dedent(f"""
    You are a senior AML Compliance Officer and expert SAR writer at a major Indian bank.
    Generate a professional, regulator-ready Suspicious Activity Report (SAR) narrative 
    based on the following transaction assessment. Write in formal banking compliance language.

    --- TRANSACTION DETAILS ---
    Transaction ID : {txn_id}
    Account ID     : {account}
    Amount         : INR {float(amount):,.2f}
    Channel/Method : {channel}
    Jurisdiction   : {location}
    
    --- RISK DETECTION RESULTS ---
    Risk Score     : {float(risk):.2%} ({risk_lvl} Risk)
    Rules Triggered: {rules}
    Primary Risk Factors:
    {reasons if reasons else '  - Anomalous activity deviating from profile'}

    --- LEGAL GROUNDS ---
    {legal_str if legal_str else '  - Suspicion under PMLA Section 12A'}
    
    --- NARRATIVE REQUIREMENTS ---
    Your report MUST cover:
    1. SUMMARY OF SUSPICION: Why is this being reported? (Focus on {rules if rules != 'None' else 'anomaly'})
    2. PATTERN ANALYSIS: How does this amount/method fit money laundering patterns like Structuring or Layering?
    3. LEGAL JUSTIFICATION: Explicitly mention the relevant sections of PMLA 2002.
    4. CONCLUSION: Final compliance recommendation.

    Maintain a serious, professional, and objective tone. Keep it under 350 words.
    """).strip()



def generate_sar_with_gemini(verdict: dict) -> dict:
    """
    Generate SAR using Gemini API.
    Returns {"sar_text": str, "source": str, "model": str}
    """
    model = _init_gemini()

    if model is None:
        return _fallback_sar(verdict)

    try:
        prompt   = _build_sar_prompt(verdict)
        response = model.generate_content(prompt)
        sar_text = response.text.strip()
        logger.success(f"SAR generated via Gemini ({len(sar_text)} chars)")
        return {
            "sar_text": sar_text,
            "source":   "gemini-1.5-flash",
            "model":    "google/gemini-1.5-flash",
            "prompt_tokens": len(prompt.split())
        }
    except Exception as e:
        logger.error(f"Gemini SAR generation failed: {e}")
        return _fallback_sar(verdict)


def _fallback_sar(verdict: dict) -> dict:
    """Template-based SAR fallback (no API key needed)."""
    from AI.local_llm import generate_sar_template
    return generate_sar_template(verdict)
