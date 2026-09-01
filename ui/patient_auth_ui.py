"""
Patient authentication UI — Google Sign-In gate before Patient ID entry.

Flow:
  1. User clicks "Sign in with Google"
  2. OAuth redirect → callback handled by _handle_google_oauth_callback() in patient_ui
  3. google_access_token stored in session → patient_google_authed = True
  4. Patient ID input shown; on success patient_logged_in = True

Google Sign-In is the ONLY login method. No guest / Patient-ID-only bypass.
"""

import streamlit as st
from agents.scheduling_agent import get_auth_url


def render_patient_google_login():
    """
    Render the Google Sign-In page for patients.
    Returns True if the patient has been Google-authenticated.
    Returns False and renders the login UI if not yet authenticated.
    """
    # Already authenticated in this session?
    if st.session_state.get("patient_google_authed"):
        return True

    # Arrived back from Google OAuth redirect — tokens already exchanged by
    # _handle_google_oauth_callback() at app level before this is called.
    if st.session_state.get("google_access_token"):
        st.session_state["patient_google_authed"] = True
        return True

    # ── Sign-In UI ────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="max-width: 480px; margin: 3rem auto; text-align: center;">
        <div style="font-size: 3.5rem; margin-bottom: 0.8rem;">🏥</div>
        <h1 style="font-size: 2rem; font-weight: 800;
            background: linear-gradient(135deg, #A78BFA, #7C3AED);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0.4rem;">Patient Portal</h1>
        <p style="color: #A89FC8; font-size: 1rem; margin-bottom: 2rem;">
            Sign in with Google to securely access your health dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # ── Google OAuth button ──────────────────────────────────────────────
        try:
            from core.config import GOOGLE_OAUTH_CLIENT_ID
            if not GOOGLE_OAUTH_CLIENT_ID:
                st.error("❌ GOOGLE_OAUTH_CLIENT_ID is missing from secrets!")
                return False

            auth_url = get_auth_url()

            st.markdown(f"""
            <a href="{auth_url}" target="_blank" style="text-decoration:none;">
                <div style="
                    display: flex; align-items: center; justify-content: center; gap: 0.75rem;
                    background: #fff; color: #3c4043;
                    border: 1px solid #dadce0; border-radius: 8px;
                    padding: 0.75rem 1.5rem; font-size: 0.95rem; font-weight: 500;
                    cursor: pointer; margin-bottom: 1rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
                    transition: box-shadow 0.2s;">
                    <svg width="18" height="18" viewBox="0 0 18 18">
                        <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
                        <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
                        <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
                        <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
                    </svg>
                    Sign in with Google
                </div>
            </a>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Error setting up Google Sign-In: {e}")

        st.markdown("""
        <p style="color:#6B6080; font-size:0.75rem; text-align:center; margin-top:1.5rem;">
            🔒 Your health data is private and secure.<br>
            Google sign-in also enables Calendar sync for your medication schedule.
        </p>
        """, unsafe_allow_html=True)

    return False
