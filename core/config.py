# """
# config.py — All credentials are loaded from Streamlit Secrets.

# How to configure on Streamlit Cloud:
#   1. Go to your app → ⋮ → Settings → Secrets
#   2. Add your key-value pairs directly in the Secrets editor and save.

# For local development:
#   Create the file  .streamlit/secrets.toml  (in the project root) with your values.
#   This file is git-ignored and never committed.
# """

# import streamlit as st


# def _get(key: str, default=None):
#     """Safely fetch a key from st.secrets.
#     Handles UTF-8 BOM characters that Windows editors sometimes inject into
#     secrets.toml, which corrupts the first key name and causes 401 errors.
#     """
#     def _clean(v):
#         if isinstance(v, str):
#             return v.strip().lstrip('\ufeff').strip()
#         return v

#     # Direct lookup first
#     try:
#         val = st.secrets[key]
#         cleaned = _clean(val)
#         return cleaned if cleaned != "" else default
#     except (KeyError, AttributeError, Exception):
#         pass

#     # Fallback: iterate all secrets stripping BOM from key names
#     try:
#         for k, v in st.secrets.items():
#             if _clean(k) == key:
#                 cleaned = _clean(v)
#                 return cleaned if cleaned != "" else default
#     except Exception:
#         pass

#     return default


# # ── Groq LLM ──────────────────────────────────────────────────────────────────
# GROQ_API_KEY = _get("GROQ_API_KEY", "")
# GROQ_MODEL   = _get("GROQ_MODEL",   "llama-3.3-70b-versatile")

# # ── Email / SMTP ──────────────────────────────────────────────────────────────
# SMTP_HOST      = _get("SMTP_HOST",      "smtp.gmail.com")
# SMTP_PORT      = int(_get("SMTP_PORT",  587))
# SMTP_USER      = _get("SMTP_USER",      "")
# SMTP_PASSWORD  = _get("SMTP_PASSWORD",  "")
# SMTP_FROM_NAME = _get("SMTP_FROM_NAME", "MediCore AI")

# # ── Google Calendar / OAuth ───────────────────────────────────────────────────
# GOOGLE_CALENDAR_API_KEY    = _get("GOOGLE_CALENDAR_API_KEY",    "")
# GOOGLE_OAUTH_CLIENT_ID     = _get("GOOGLE_OAUTH_CLIENT_ID",     "")
# GOOGLE_OAUTH_CLIENT_SECRET = _get("GOOGLE_OAUTH_CLIENT_SECRET", "")
# GOOGLE_OAUTH_PROJECT_ID    = _get("GOOGLE_OAUTH_PROJECT_ID",    "")
# GOOGLE_AUTH_URI            = _get("GOOGLE_AUTH_URI",  "https://accounts.google.com/o/oauth2/auth")
# GOOGLE_TOKEN_URI           = _get("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
# GOOGLE_REDIRECT_URI        = _get("GOOGLE_REDIRECT_URI", "http://localhost:8501")
# GOOGLE_SCOPES              = _get("GOOGLE_SCOPES", "https://www.googleapis.com/auth/calendar.events")
# GOOGLE_CLIENT_ID           = GOOGLE_OAUTH_CLIENT_ID  # alias used by patient_auth_ui

# # ── App tunables ──────────────────────────────────────────────────────────────
# RISK_THRESHOLDS  = {"low": 30, "medium": 60, "high": 80}
# MAX_CHAT_HISTORY = 20
"""
config.py — All credentials are loaded from Streamlit Secrets.

IMPORTANT: Keys are prefixed with MEDICURE_ to avoid Streamlit Cloud's
built-in OAuth auto-detection which hijacks Google OAuth keys.
"""

import streamlit as st


def _get(key: str, default=None):
    """Safely fetch a key from st.secrets."""
    def _clean(v):
        if isinstance(v, str):
            return v.strip().lstrip('\ufeff').strip()
        return v

    try:
        val = st.secrets[key]
        cleaned = _clean(val)
        return cleaned if cleaned != "" else default
    except (KeyError, AttributeError, Exception):
        pass

    try:
        for k, v in st.secrets.items():
            if _clean(k) == key:
                cleaned = _clean(v)
                return cleaned if cleaned != "" else default
    except Exception:
        pass

    return default


# ── Groq LLM ──────────────────────────────────────────────────────────────────
GROQ_API_KEY = _get("GROQ_API_KEY", "")
GROQ_MODEL   = _get("GROQ_MODEL",   "llama-3.3-70b-versatile")

# ── Email / SMTP ──────────────────────────────────────────────────────────────
SMTP_HOST      = _get("SMTP_HOST",      "smtp.gmail.com")
SMTP_PORT      = int(_get("SMTP_PORT",  587))
SMTP_USER      = _get("SMTP_USER",      "")
SMTP_PASSWORD  = _get("SMTP_PASSWORD",  "")
SMTP_FROM_NAME = _get("SMTP_FROM_NAME", "MediCore AI")

# ── Google Calendar / OAuth ───────────────────────────────────────────────────
# Prefixed MEDICURE_ to prevent Streamlit Cloud auto-OAuth interception
GOOGLE_CALENDAR_API_KEY    = _get("MEDICURE_CALENDAR_API_KEY",    "")
GOOGLE_OAUTH_CLIENT_ID     = _get("MEDICURE_CLIENT_ID",           "")
GOOGLE_OAUTH_CLIENT_SECRET = _get("MEDICURE_CLIENT_SECRET",       "")
GOOGLE_OAUTH_PROJECT_ID    = _get("MEDICURE_PROJECT_ID",          "")
GOOGLE_AUTH_URI            = _get("MEDICURE_AUTH_URI",  "https://accounts.google.com/o/oauth2/auth")
GOOGLE_TOKEN_URI           = _get("MEDICURE_TOKEN_URI", "https://oauth2.googleapis.com/token")
GOOGLE_REDIRECT_URI        = _get("MEDICURE_REDIRECT_URI", "http://localhost:8501")
GOOGLE_SCOPES              = _get("MEDICURE_SCOPES", "https://www.googleapis.com/auth/calendar.events")
GOOGLE_CLIENT_ID           = GOOGLE_OAUTH_CLIENT_ID  # alias

# ── App tunables ──────────────────────────────────────────────────────────────
RISK_THRESHOLDS  = {"low": 30, "medium": 60, "high": 80}
MAX_CHAT_HISTORY = 20
