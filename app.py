import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.database import init_db
from ui.styles import PURPLE_THEME
from ui.auth_ui import render_hospital_auth
from ui.admin_ui import render_admin_portal
from ui.doctor_ui import render_doctor_dashboard
from ui.patient_ui import render_patient_dashboard, render_patient_login, _handle_google_oauth_callback
from ui.patient_auth_ui import render_patient_google_login
from ui.reception_ui import render_reception_dashboard

st.set_page_config(
    page_title="MediCore AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource(show_spinner=False)
def _init_db_once():
    init_db()
    return True

_init_db_once()

# Always inject CSS on every rerun — required so theme persists after refresh
st.markdown(PURPLE_THEME, unsafe_allow_html=True)

# ── Session persistence across page refresh via query params ──────────────────
import json as _json

_PERSIST_KEYS = [
    "mode", "patient_logged_in", "patient_id", "patient_google_authed",
    "hospital_data", "doctor_data", "admin_hospital_data",
    "google_access_token", "google_refresh_token",
]

def _save_session_to_params():
    """Encode key session fields into a single query param."""
    payload = {}
    for k in _PERSIST_KEYS:
        v = st.session_state.get(k)
        if v is not None and v is not False and v != "home":
            payload[k] = v
    try:
        if payload:
            st.query_params["_s"] = _json.dumps(payload, separators=(",", ":"))
        else:
            st.query_params.clear()
    except Exception:
        pass

def _restore_session_from_params():
    """On first load (before session keys exist), restore from query param."""
    raw = st.query_params.get("_s", None)
    if not raw:
        return
    try:
        payload = _json.loads(raw)
        for k, v in payload.items():
            st.session_state[k] = v
    except Exception:
        pass

# ── Session defaults ──────────────────────────────────────────────────────────
for key, default in [
    ("mode", "home"),
    ("patient_logged_in", False),
    ("patient_id", None),
    ("patient_google_authed", False),
    ("hospital_data", None),
    ("doctor_data", None),
    ("admin_hospital_data", None),
    ("confirm_clear", False),
    ("_session_restored", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Handle Google OAuth callback FIRST (before any session restore) ──────────
# This must run before _restore_session_from_params so the ?code= param is
# processed and removed before we try to read or write _s.
_handle_google_oauth_callback()

# Restore session from URL on very first run after a page refresh
# Skip if we just processed an OAuth callback (mode already set to patient)
if not st.session_state.get("_session_restored"):
    if not st.session_state.get("google_access_token"):
        # Normal refresh restore — only when not coming from OAuth
        _restore_session_from_params()
    st.session_state["_session_restored"] = True

# Ensure google_authed flag is in sync with token presence
if st.session_state.get("google_access_token"):
    st.session_state["patient_google_authed"] = True
    if st.session_state.get("mode") != "patient":
        st.session_state["mode"] = "patient"

# Persist current session state to URL for refresh survival
_save_session_to_params()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 1.5rem;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">🏥</div>
        <div style="font-size:1.3rem;font-weight:700;color:#A78BFA;letter-spacing:0.05em;">MediCore AI</div>
        <div style="font-size:0.75rem;color:#6B6080;letter-spacing:0.1em;
            text-transform:uppercase;margin-top:0.2rem;">Healthcare Intelligence</div>
    </div>
    <div class="divider"></div>
    """, unsafe_allow_html=True)

    st.markdown("**Navigation**")

    if st.button("🏠 Home", use_container_width=True):
        st.session_state["mode"] = "home"
        st.rerun()

    if st.button("🏥 Admin / Hospital", use_container_width=True):
        st.session_state["mode"] = "admin"
        st.rerun()

    if st.button("👨‍⚕️ Doctor Portal", use_container_width=True):
        st.session_state["mode"] = "doctor"
        st.rerun()

    if st.button("🛎️ Reception", use_container_width=True):
        st.session_state["mode"] = "reception"
        st.rerun()

    if st.button("🧑‍⚕️ Patient Portal", use_container_width=True):
        st.session_state["mode"] = "patient"
        st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Admin session info
    if st.session_state.get("admin_hospital_data") and st.session_state.get("mode") == "admin":
        hosp = st.session_state["admin_hospital_data"]
        st.markdown(f"""
        <div class="card" style="margin-top:0;">
            <div class="card-header">Admin Logged In</div>
            <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;">{hosp.get('name','')}</div>
            <div style="color:#6B6080;font-size:0.7rem;font-family:monospace;">{hosp.get('hospital_id','')}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Admin Logout", use_container_width=True):
            st.session_state["admin_hospital_data"] = None
            st.session_state["mode"] = "home"
            st.query_params.clear()
            st.rerun()

    # Doctor session info
    if st.session_state.get("doctor_data") and st.session_state.get("mode") == "doctor":
        doc  = st.session_state["doctor_data"]
        hosp = st.session_state.get("hospital_data", {})
        st.markdown(f"""
        <div class="card" style="margin-top:0;">
            <div class="card-header">Doctor Logged In</div>
            <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;">Dr. {doc.get('name','')}</div>
            <div style="color:#6B6080;font-size:0.75rem;">{hosp.get('name','')}</div>
            <div style="color:#6B6080;font-size:0.7rem;font-family:monospace;">{doc.get('doctor_id','')}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Doctor Logout", use_container_width=True):
            st.session_state["doctor_data"] = None
            st.session_state["hospital_data"] = None
            st.session_state["mode"] = "home"
            st.query_params.clear()
            st.rerun()

    if st.session_state.get("patient_logged_in"):
        st.markdown(f"""
        <div class="card" style="margin-top:0;">
            <div class="card-header">Patient Logged In</div>
            <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;">{st.session_state.get('patient_id','')}</div>
            {"<div style='color:#34D399;font-size:0.75rem;'>🔒 Google verified</div>" if st.session_state.get('google_access_token') else ""}
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Patient Logout", use_container_width=True):
            for k in ["patient_logged_in", "patient_id", "patient_google_authed",
                      "google_access_token", "google_refresh_token"]:
                st.session_state.pop(k, None)
            st.session_state["patient_logged_in"] = False
            st.session_state["patient_id"] = None
            st.session_state["patient_google_authed"] = False
            st.session_state["mode"] = "home"
            st.query_params.clear()
            st.rerun()

    st.markdown("""
    <div style="position:fixed;bottom:2rem;left:0;width:100%;padding:0 1rem;box-sizing:border-box;">
        <div style="font-size:0.7rem;color:#6B6080;text-align:center;line-height:1.5;">
            Powered by GROQ AI<br>
            <span style="color:#7C3AED;">MediCore AI v2.2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Main content ──────────────────────────────────────────────────────────────
mode = st.session_state.get("mode", "home")

if mode == "home":
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem 2rem;">
        <div style="font-size:4rem;margin-bottom:1rem;">🏥</div>
        <h1 style="font-size:2.8rem;font-weight:800;
            background:linear-gradient(135deg,#A78BFA,#7C3AED);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            margin-bottom:0.5rem;">MediCore AI</h1>
        <p style="color:#A89FC8;font-size:1.2rem;max-width:600px;margin:0 auto 3rem;">
            Intelligent Healthcare Platform powered by multi-agent AI for smarter patient care
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    cards = [
        ("🏥", "Admin Portal", "Register hospital, add doctors & receptionists"),
        ("👨‍⚕️", "Doctor Dashboard", "Date-wise patients, prescriptions, AI risk scoring & alerts"),
        ("🛎️", "Reception", "Login and register new patients with full vitals"),
        ("🤖", "LLM Context Aware", "AI reads stored history & prescriptions for smart responses"),
    ]
    for col, (icon, title, desc) in zip([col1, col2, col3, col4], cards):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2.5rem;margin-bottom:0.8rem;">{icon}</div>
                <div style="font-size:1.1rem;font-weight:700;margin-bottom:0.5rem;">{title}</div>
                <div style="color:#A89FC8;font-size:0.9rem;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    agents = [
        ("🗣️", "Conversation Agent", "GROQ-powered chat with full patient history & prescription context"),
        ("⚡", "Risk Scoring Agent", "Dynamic AI risk evaluation from patient data"),
        ("🔬", "Health Evaluation Agent", "Adherence tracking and behavioral trend detection"),
        ("🚨", "Alerting Agent", "Automated alerts triggered by AI analysis"),
        ("📅", "Scheduling Agent", "Smart prescription-to-calendar event transformation"),
    ]
    cols = st.columns(5)
    for col, (icon, name, desc) in zip(cols, agents):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;padding:1rem;">
                <div style="font-size:1.8rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:600;font-size:0.85rem;margin-bottom:0.4rem;color:#A78BFA;">{name}</div>
                <div style="color:#6B6080;font-size:0.75rem;line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

elif mode == "admin":
    render_admin_portal()

elif mode == "doctor":
    if st.session_state.get("doctor_data") and st.session_state.get("hospital_data"):
        render_doctor_dashboard()
    else:
        render_hospital_auth()

elif mode == "reception":
    render_reception_dashboard()

elif mode == "patient":
    google_authed = render_patient_google_login()
    if google_authed:
        if st.session_state.get("patient_logged_in") and st.session_state.get("patient_id"):
            render_patient_dashboard(st.session_state["patient_id"])
        else:
            render_patient_login()
