"""
Doctor Portal Authentication
Flow: Select Hospital (dropdown) → Enter Doctor Email/Password → Login
Doctors are created by the Hospital Admin via the Admin Portal.
"""

import streamlit as st
from data.database import (
    get_all_hospitals,
    login_doctor,
)


def render_hospital_auth():
    """Returns (hospital_data, doctor_data) when fully authenticated, else (None, None)."""
    st.markdown("""
    <div style="text-align:center;padding:2rem 1rem 1rem;">
        <div style="font-size:3rem;margin-bottom:0.5rem;">👨‍⚕️</div>
        <h1 style="font-size:2.2rem;font-weight:800;
            background:linear-gradient(135deg,#A78BFA,#7C3AED);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Doctor Portal</h1>
        <p style="color:#A89FC8;font-size:1rem;">
            Select your hospital and log in with your doctor credentials
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load all hospitals for the dropdown
    hospitals = get_all_hospitals()

    if not hospitals:
        st.warning("No hospitals registered yet. Please use the **Admin Portal** to register a hospital first.")
        return None, None

    hospital_options = {f"🏥 {h['name']}": h for h in hospitals}

    with st.form("doctor_login_form"):
        st.markdown("### 🏥 Select Your Hospital")
        selected_label = st.selectbox(
            "Hospital",
            list(hospital_options.keys()),
            label_visibility="collapsed",
            help="Select the hospital you are registered under"
        )

        st.markdown("### 👨‍⚕️ Doctor Login")
        demail = st.text_input("Doctor Email", placeholder="doctor@hospital.com")
        dpass  = st.text_input("Password", type="password", placeholder="••••••••")

        submitted = st.form_submit_button("🔐 Login", type="primary", use_container_width=True)

        if submitted:
            if not selected_label:
                st.error("Please select your hospital.")
            elif not demail.strip():
                st.error("Please enter your email address.")
            elif not dpass:
                st.error("Please enter your password.")
            else:
                selected_hospital = hospital_options[selected_label]
                doc = login_doctor(selected_hospital["hospital_id"], demail.strip(), dpass)
                if doc:
                    st.session_state["hospital_data"] = selected_hospital
                    st.session_state["doctor_data"] = doc
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials or doctor not registered under this hospital.")

    st.markdown("""
    <p style="text-align:center;color:#6B6080;font-size:0.82rem;margin-top:1rem;">
        Not registered? Ask your hospital admin to add you via the <strong>Admin Portal</strong>.
    </p>
    """, unsafe_allow_html=True)

    return None, None
