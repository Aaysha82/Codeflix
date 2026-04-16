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
    You are a senior AML Compliance Officer and official SAR/STR writer at a leading bank in India.
    Generate a professional, regulator-ready Suspicious Transaction Report (STR) narrative (Form 102) 
    for submission to FIU-IND based on the following automated assessment.

    --- STR DATA INPUTS ---
    Reference ID     : {txn_id}
    Account Number   : {account}
    Amount           : INR {float(amount):,.2f}
    Channel/Method   : {channel}
    Branch Location  : {location}
    Detection Date   : {datetime.now().strftime('%Y-%m-%d')}
    
    --- RISK DETECTION RESULTS ---
    Calculated Risk  : {float(risk):.2%} ({risk_lvl} Severity)
    AML Rules Hit    : {rules}
    Top SHAP Insights:
    {reasons if reasons else '  - Non-typical transaction behavior for account profile'}

    --- REGULATORY GROUNDS ---
    {legal_str if legal_str else '  - Suspicion under PMLA 2002 Section 12(1)'}
    
    --- STR NARRATIVE STRUCTURE (REQUIRED) ---
    Your report MUST use the following formal sections:
    1. GROUNDS FOR SUSPICION: Provide a concise technical justification for why this transaction is flagged. 
       Highlight specific anomalies (e.g., structuring, layering, or smurfing) relative to PMLA 2002 guidelines.
    2. ACCOUNT PROFILE DEVIATION: Describe how this transaction differs from the account's historical behavior 
       (mentioning the {float(amount):,.2f} INR value specifically).
    3. DETAILED NARRATIVE: Provide a 1-2 paragraph description of the activity suitable for FIU-IND audit. 
       Avoid technical jargon where possible, focus on the suspicious logic.
    4. CONCLUSION & RECOMMENDATION: Final sign-off by Compliance.

    Tone: Formal, objective, authoritative, and strictly professional.
    Language: Standard English (Indian Banking dialect).
    Length: 200-400 words.
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
