"""
Reception Dashboard — Patient Data Entry
Receptionists must log in with their credentials before registering patients.
"""

import streamlit as st
import re
from datetime import date
from data.database import (
    get_all_hospitals,
    get_doctors_by_hospital,
    create_patient,
    get_patients_by_doctor_and_date,
    login_receptionist,
    get_hospital,
    get_doctor,
)
from core.email_service import send_registration_email


def _valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email.strip()))


def _all_hospitals():
    try:
        return get_all_hospitals()
    except Exception:
        return []


def _get_doctors(hospital_id: str):
    try:
        return get_doctors_by_hospital(hospital_id)
    except Exception:
        return []


def render_reception_dashboard():
    st.markdown("""
    <div style="display:flex;align-items:center;gap:1rem;padding-bottom:1.5rem;border-bottom:1px solid rgba(124,58,237,0.25);margin-bottom:2rem;">
        <div style="font-size:2.5rem;">🛎️</div>
        <div>
            <h1 style="margin:0;font-size:1.9rem;font-weight:800;
                background:linear-gradient(135deg,#A78BFA,#7C3AED);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Reception Dashboard
            </h1>
            <p style="margin:0;color:#A89FC8;font-size:0.9rem;">Patient registration portal</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    hospitals = _all_hospitals()
    if not hospitals:
        st.warning("⚠️ No hospitals registered yet. Please ask the administrator to register a hospital first.")
        return

    # ── Receptionist Login ─────────────────────────────────────────────────────
    if not st.session_state.get("receptionist_data"):
        _render_receptionist_login(hospitals)
        return

    rec = st.session_state["receptionist_data"]
    hosp_id = rec["hospital_id"]

    # Show logged-in banner
    st.markdown(f"""
    <div style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);border-radius:10px;
        padding:0.7rem 1.2rem;margin-bottom:1.5rem;display:flex;justify-content:space-between;align-items:center;">
        <span style="color:#34D399;font-weight:600;">🛎️ Logged in as: {rec['name']}</span>
        <span style="color:#6B6080;font-size:0.8rem;">{rec['email']}</span>
    </div>
    """, unsafe_allow_html=True)

    col_logout, _ = st.columns([1, 5])
    with col_logout:
        if st.button("🔙 Logout", use_container_width=True):
            st.session_state.pop("receptionist_data", None)
            st.rerun()

    # ── Select Doctor ─────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👨‍⚕️ Select Attending Doctor")

    doctors = _get_doctors(hosp_id)
    if not doctors:
        st.warning("No doctors registered under this hospital.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    doc_options = {f"Dr. {d['name']} — {d.get('specialization','General')}": d for d in doctors}
    chosen_doc_label = st.selectbox("Attending Doctor *", options=list(doc_options.keys()), key="rec_doctor_select")
    chosen_doctor = doc_options[chosen_doc_label]
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Patient Registration Form ─────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 Patient Details")

    with st.form("reception_patient_form", clear_on_submit=True):
        # Required fields
        st.markdown("#### Required Information")
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Full Name *", placeholder="e.g. Rajesh Kumar")
            age = st.number_input("Age *", min_value=0, max_value=130, value=30, step=1)
            gender = st.selectbox("Gender *", ["Male", "Female", "Other", "Prefer not to say"])
            contact = st.text_input("Contact Number *", placeholder="+91 98765 43210")
        with col_b:
            email = st.text_input("Email Address", placeholder="patient@example.com")
            visit_date = st.date_input("Visit Date *", value=date.today())

        st.markdown("---")
        st.markdown("#### 🩺 Vitals & Additional Info *(all optional)*")

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            blood_group = st.selectbox(
                "Blood Group",
                ["", "A+", "A−", "B+", "B−", "AB+", "AB−", "O+", "O−", "Unknown"],
            )
            weight_kg = st.number_input("Weight (kg)", min_value=0.0, max_value=500.0, value=0.0, step=0.5,
                                        help="Leave at 0 to skip")
            height_cm = st.number_input("Height (cm)", min_value=0.0, max_value=300.0, value=0.0, step=0.5,
                                        help="Leave at 0 to skip")
        with col_v2:
            temperature_c = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, value=0.0, step=0.1,
                                            help="Leave at 0 to skip")
            pulse_bpm = st.number_input("Pulse (bpm)", min_value=0, max_value=300, value=0, step=1,
                                        help="Leave at 0 to skip")
            oxygen_spo2 = st.number_input("SpO₂ (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.5,
                                          help="Leave at 0 to skip")
        with col_v3:
            blood_pressure = st.text_input("Blood Pressure", placeholder="e.g. 120/80 mmHg")
            address = st.text_area("Address", placeholder="Street, City, State", height=100)

        st.markdown("---")
        submitted = st.form_submit_button("✅ Register Patient", use_container_width=True, type="primary")

        if submitted:
            errors = []
            if not name.strip():
                errors.append("Full Name is required.")
            if not contact.strip():
                errors.append("Contact Number is required.")
            if email.strip() and not _valid_email(email):
                errors.append("Email Address is not valid.")

            if errors:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                try:
                    # Convert 0 values to None for optional numeric fields
                    w = weight_kg if weight_kg > 0 else None
                    h = height_cm if height_cm > 0 else None
                    t = temperature_c if temperature_c > 0 else None
                    p = pulse_bpm if pulse_bpm > 0 else None
                    o = oxygen_spo2 if oxygen_spo2 > 0 else None
                    bg = blood_group if blood_group and blood_group != "" else None
                    bp = blood_pressure.strip() if blood_pressure.strip() else None
                    addr = address.strip() if address.strip() else None
                    em = email.strip().lower() if email.strip() else ""

                    pid = create_patient(
                        doctor_id=chosen_doctor["doctor_id"],
                        hospital_id=hosp_id,
                        doctor_name=chosen_doctor["name"],
                        name=name.strip(),
                        age=int(age),
                        gender=gender,
                        contact=contact.strip(),
                        email=em,
                        disease="",
                        visit_date=str(visit_date),
                        blood_group=bg,
                        weight_kg=w,
                        temperature_c=t,
                        blood_pressure=bp,
                        pulse_bpm=p,
                        oxygen_spo2=o,
                        height_cm=h,
                        address=addr,
                    )
                    st.success(f"🎉 Patient registered successfully! **Patient ID: {pid}**")

                    # ── Send email receipt if email provided ──────────────────
                    if em:
                        # Fetch hospital details for the receipt
                        hosp_row = get_hospital(hosp_id)
                        hospital_name = hosp_row["name"] if hosp_row else hosp_id

                        # Auto-generate token number (today's patient count)
                        today_count = len(get_patients_by_doctor_and_date(
                            chosen_doctor["doctor_id"], str(visit_date)
                        ))
                        token_number = f"OPD-{today_count:03d}"

                        patient_data_for_email = {
                            "patient_id":        pid,
                            "name":              name.strip(),
                            "age":               int(age),
                            "gender":            gender,
                            "contact":           contact.strip(),
                            "email":             em,
                            "disease":           "",
                            "visit_date":        str(visit_date),
                            "doctor_name":       chosen_doctor["name"],
                            "doctor_dept":       chosen_doctor.get("specialization", "General Medicine"),
                            "hospital_name":     hospital_name,
                            "hospital_address":  hosp_row.get("address", "") if hosp_row else "",
                            "hospital_city":     hosp_row.get("city", "") if hosp_row else "",
                            "hospital_pincode":  hosp_row.get("pincode", "") if hosp_row else "",
                            "hospital_phone":    hosp_row.get("phone", "") if hosp_row else "",
                            "hospital_email":    hosp_row.get("email", "") if hosp_row else "",
                            "hospital_website":  hosp_row.get("website", "") if hosp_row else "",
                            "blood_group":       bg,
                            "weight_kg":         w,
                            "height_cm":         h,
                            "temperature_c":     t,
                            "blood_pressure":    bp,
                            "pulse_bpm":         p,
                            "oxygen_spo2":       o,
                            "address":           addr,
                            "token_number":      token_number,
                            "consultation_type": "OPD — Outpatient",
                        }

                        with st.spinner("📧 Sending confirmation email..."):
                            ok, msg = send_registration_email(patient_data_for_email)

                        if ok:
                            st.success(f"📧 Receipt emailed to **{em}**")
                        else:
                            st.warning(f"⚠️ Registration saved but email failed: {msg}")
                except Exception as exc:
                    st.error(f"❌ Registration failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Today's Patient List ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### 📅 Today's Patients — {date.today().strftime('%d %b %Y')}")

    today_patients = get_patients_by_doctor_and_date(chosen_doctor["doctor_id"], str(date.today()))

    if not today_patients:
        st.markdown(
            "<p style='color:#6B6080;text-align:center;padding:1.5rem 0;'>No patients registered today yet.</p>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<p style='color:#34D399;margin-bottom:1rem;'>✅ {len(today_patients)} patient(s) registered today</p>",
            unsafe_allow_html=True,
        )
        for i, p in enumerate(today_patients, 1):
            vitals_parts = []
            if p.get("blood_group"):
                vitals_parts.append(f"🩸 {p['blood_group']}")
            if p.get("weight_kg"):
                vitals_parts.append(f"⚖️ {p['weight_kg']}kg")
            if p.get("temperature_c"):
                vitals_parts.append(f"🌡️ {p['temperature_c']}°C")
            if p.get("blood_pressure"):
                vitals_parts.append(f"💉 {p['blood_pressure']}")
            if p.get("pulse_bpm"):
                vitals_parts.append(f"❤️ {p['pulse_bpm']}bpm")
            vitals_html = " &nbsp;·&nbsp; ".join(vitals_parts)

            st.markdown(f"""
            <div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);
                border-radius:10px;padding:0.9rem 1.2rem;margin-bottom:0.6rem;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="color:#A78BFA;font-weight:700;font-size:0.85rem;">#{i}</span>
                        <span style="color:#F3F0FF;font-weight:600;margin-left:0.6rem;">{p.get('name','—')}</span>
                        <span style="color:#6B6080;font-size:0.8rem;margin-left:0.8rem;">{p.get('age','?')} yrs · {p.get('gender','')}</span>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:#C084FC;font-size:0.8rem;font-family:monospace;">{p.get('id','')}</div>
                    </div>
                </div>
                {f'<div style="color:#6B6080;font-size:0.75rem;margin-top:0.4rem;">{vitals_html}</div>' if vitals_html else ''}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_receptionist_login(hospitals):
    """Login page for receptionists."""
    st.markdown("""
    <div style="max-width:480px;margin:2rem auto;">
        <div style="text-align:center;margin-bottom:2rem;">
            <div style="font-size:3rem;">🛎️</div>
            <h2 style="font-size:1.6rem;font-weight:700;color:#A78BFA;margin:0.5rem 0;">Receptionist Login</h2>
            <p style="color:#A89FC8;font-size:0.9rem;">Enter your credentials to access the registration portal</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    hosp_options = {h["name"]: h for h in hospitals}

    with st.form("rec_login_form"):
        chosen_hosp_name = st.selectbox("Select Hospital *", options=list(hosp_options.keys()))
        rec_email = st.text_input("Receptionist Email *", placeholder="reception@hospital.com")
        rec_password = st.text_input("Password *", type="password")
        login_btn = st.form_submit_button("🔐 Login", use_container_width=True, type="primary")

        if login_btn:
            if not (chosen_hosp_name and rec_email and rec_password):
                st.error("Please fill all fields.")
            else:
                hosp = hosp_options[chosen_hosp_name]
                rec = login_receptionist(hosp["hospital_id"], rec_email.strip(), rec_password)
                if rec:
                    st.session_state["receptionist_data"] = rec
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials. Please check your email and password.")

    st.markdown("""
    <p style="text-align:center;color:#6B6080;font-size:0.82rem;margin-top:1.5rem;">
        Don't have credentials? Ask your hospital administrator to register you.
    </p>
    """, unsafe_allow_html=True)
