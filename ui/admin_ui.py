"""
Admin / Hospital Portal
Flow: Register Hospital → Login → Add Doctors & Receptionists
"""

import streamlit as st
from data.database import (
    register_hospital, login_hospital,
    register_doctor, login_doctor,
    get_doctors_by_hospital,
    register_receptionist, get_receptionists_by_hospital,
    update_hospital_profile, get_hospital,
)


def render_admin_portal():
    """Main entry point for the Admin / Hospital Portal."""
    st.markdown("""
    <div style="text-align:center;padding:2rem 1rem 1.5rem;">
        <div style="font-size:3rem;margin-bottom:0.5rem;">🏥</div>
        <h1 style="font-size:2.2rem;font-weight:800;
            background:linear-gradient(135deg,#A78BFA,#7C3AED);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            margin-bottom:0.3rem;">Hospital Admin Portal</h1>
        <p style="color:#A89FC8;font-size:0.95rem;">
            Register your hospital, then manage doctors and receptionists
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Step 1: Hospital Auth ─────────────────────────────────────────────────
    if not st.session_state.get("admin_hospital_data"):
        _render_hospital_auth()
        return

    hosp = st.session_state["admin_hospital_data"]

    # Logged-in banner + logout
    st.markdown(f"""
    <div style="background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);
        border-radius:10px;padding:0.7rem 1.2rem;margin-bottom:1.5rem;
        display:flex;justify-content:space-between;align-items:center;">
        <span style="color:#34D399;font-weight:600;">🏥 {hosp['name']}</span>
        <span style="color:#6B6080;font-size:0.8rem;">ID: {hosp['hospital_id']}</span>
    </div>
    """, unsafe_allow_html=True)

    col_logout, _ = st.columns([1, 5])
    with col_logout:
        if st.button("🚪 Logout Hospital", use_container_width=True):
            st.session_state.pop("admin_hospital_data", None)
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Step 2: Manage Doctors & Receptionists (tabs) ─────────────────────────
    tab_doc, tab_rec, tab_profile = st.tabs(["👨‍⚕️ Manage Doctors", "🛎️ Manage Receptionists", "🏥 Hospital Profile"])

    with tab_doc:
        _render_manage_doctors(hosp)

    with tab_rec:
        _render_manage_receptionists(hosp)

    with tab_profile:
        _render_hospital_profile(hosp)


# ── Hospital Auth ─────────────────────────────────────────────────────────────

def _render_hospital_auth():
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register Hospital"])

    with tab_login:
        _render_hospital_login()

    with tab_register:
        _render_hospital_register()


def _render_hospital_login():
    st.markdown("### 🔐 Hospital Login")
    with st.form("admin_hosp_login"):
        email = st.text_input("Hospital Email *", placeholder="admin@hospital.com")
        password = st.text_input("Password *", type="password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
        if submitted:
            if not (email.strip() and password):
                st.error("Please fill all fields.")
            else:
                hosp = login_hospital(email.strip(), password)
                if hosp:
                    st.session_state["admin_hospital_data"] = hosp
                    st.success(f"✅ Logged in as **{hosp['name']}**")
                    st.rerun()
                else:
                    st.error("❌ Invalid email or password.")


def _render_hospital_register():
    st.markdown("### 📝 Register New Hospital")
    with st.form("admin_hosp_register"):
        hname    = st.text_input("Hospital Name *", placeholder="e.g. City Care Hospital")
        hemail   = st.text_input("Admin Email *", placeholder="admin@hospital.com")

        st.markdown("#### 📍 Hospital Contact & Address *(used on OPD receipts)*")
        col1, col2 = st.columns(2)
        with col1:
            hphone   = st.text_input("Phone Number", placeholder="+91 175 000 0000")
            hwebsite = st.text_input("Website", placeholder="www.hospital.com")
        with col2:
            hcity    = st.text_input("City", placeholder="Patiala")
            hpincode = st.text_input("PIN Code", placeholder="140001")
        haddress = st.text_area("Full Address", placeholder="123, Hospital Road, Medical District, City", height=80)

        st.markdown("---")
        hpass    = st.text_input("Password *", type="password")
        hpass2   = st.text_input("Confirm Password *", type="password")
        submitted = st.form_submit_button("Register Hospital", type="primary", use_container_width=True)
        if submitted:
            if not (hname.strip() and hemail.strip() and hpass):
                st.error("Please fill all required fields.")
            elif hpass != hpass2:
                st.error("Passwords do not match.")
            else:
                hid, err = register_hospital(
                    hname.strip(), hemail.strip(), hpass,
                    address=haddress.strip(), phone=hphone.strip(),
                    website=hwebsite.strip(), city=hcity.strip(), pincode=hpincode.strip()
                )
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.success(f"✅ Hospital registered! ID: **{hid}**")
                    # Auto-login after registration
                    hosp = login_hospital(hemail.strip(), hpass)
                    if hosp:
                        st.session_state["admin_hospital_data"] = hosp
                        st.rerun()
                    else:
                        st.info("Registration successful. Please login now.")


# ── Manage Doctors ────────────────────────────────────────────────────────────

def _render_manage_doctors(hosp):
    st.markdown("#### 👨‍⚕️ Registered Doctors")

    existing = get_doctors_by_hospital(hosp["hospital_id"])
    if existing:
        for doc in existing:
            code = doc.get("doctor_code", "—")
            st.markdown(f"""
            <div class="card" style="padding:0.8rem 1rem;margin-bottom:0.5rem;
                border-left:3px solid #34D399;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:var(--text-primary);">
                            👨‍⚕️ Dr. {doc['name']}
                        </span>
                        <span style="color:var(--text-muted);font-size:0.8rem;margin-left:0.8rem;">
                            {doc.get('specialization','General')} &nbsp;|&nbsp; {doc.get('gender','—')}
                        </span>
                    </div>
                    <code style="background:var(--primary-glow);padding:0.2rem 0.6rem;
                        border-radius:6px;color:#34D399;font-weight:700;">{code}</code>
                </div>
                <div style="color:var(--text-muted);font-size:0.75rem;margin-top:0.3rem;">
                    Patient IDs → <code>{code}YYYYMMDD001</code> &nbsp;|&nbsp;
                    Doctor ID: <code>{doc['doctor_id']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No doctors registered yet.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("#### ➕ Add New Doctor")

    with st.form("admin_add_doctor", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            dname   = st.text_input("Full Name *", placeholder="e.g. Dr. Chakshu Sharma")
            dgender = st.selectbox("Gender *", ["Not specified", "Male", "Female", "Other"])
        with col2:
            dspec   = st.text_input("Specialization *", placeholder="e.g. Cardiology")
            demail  = st.text_input("Email *", placeholder="doctor@hospital.com")

        col3, col4 = st.columns(2)
        with col3:
            dpass  = st.text_input("Password *", type="password")
        with col4:
            dpass2 = st.text_input("Confirm Password *", type="password")

        submitted = st.form_submit_button("➕ Add Doctor", type="primary", use_container_width=True)
        if submitted:
            if not (dname.strip() and dspec.strip() and demail.strip() and dpass):
                st.error("Please fill Name, Specialization, Email, and Password.")
            elif dpass != dpass2:
                st.error("Passwords do not match.")
            else:
                did, dcode, err = register_doctor(
                    hosp["hospital_id"], dname.strip(), demail.strip(),
                    dpass, dspec.strip(), dgender
                )
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.success(f"✅ Dr. {dname.strip()} registered! Doctor Code: **{dcode}**")
                    st.rerun()


# ── Manage Receptionists ──────────────────────────────────────────────────────

def _render_manage_receptionists(hosp):
    st.markdown("#### 🛎️ Registered Receptionists")

    existing = get_receptionists_by_hospital(hosp["hospital_id"])
    if existing:
        for rec in existing:
            st.markdown(f"""
            <div class="card" style="padding:0.8rem 1rem;margin-bottom:0.5rem;
                border-left:3px solid #A78BFA;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:var(--text-primary);">
                            🛎️ {rec['name']}
                        </span>
                        <span style="color:var(--text-muted);font-size:0.8rem;margin-left:0.8rem;">
                            {rec['email']}
                        </span>
                    </div>
                    <code style="color:#A78BFA;font-size:0.8rem;">{rec['receptionist_id']}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No receptionists registered yet.")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("#### ➕ Add New Receptionist")

    with st.form("admin_add_receptionist", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            rname  = st.text_input("Full Name *", placeholder="e.g. Priya Mehta")
            remail = st.text_input("Email *", placeholder="reception@hospital.com")
        with col2:
            rpass  = st.text_input("Password *", type="password")
            rpass2 = st.text_input("Confirm Password *", type="password")

        submitted = st.form_submit_button("➕ Add Receptionist", type="primary", use_container_width=True)
        if submitted:
            if not (rname.strip() and remail.strip() and rpass):
                st.error("Please fill Name, Email, and Password.")
            elif rpass != rpass2:
                st.error("Passwords do not match.")
            else:
                rid, err = register_receptionist(
                    hosp["hospital_id"], rname.strip(), remail.strip(), rpass
                )
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.success(f"✅ {rname.strip()} registered as receptionist! ID: **{rid}**")
                    st.rerun()


# ── Hospital Profile Editor ───────────────────────────────────────────────────

def _render_hospital_profile(hosp):
    """Edit hospital contact details that appear on OPD receipts."""
    st.markdown("#### 🏥 Hospital Profile")
    st.markdown(
        "<p style='color:#A89FC8;font-size:0.88rem;margin-bottom:1rem;'>"
        "These details are printed on every OPD receipt sent to patients. "
        "Keep them accurate and up-to-date.</p>",
        unsafe_allow_html=True
    )

    # Refresh hospital row from DB to get latest values
    fresh = get_hospital(hosp["hospital_id"]) or hosp

    with st.form("hospital_profile_form"):
        st.markdown("##### 🏷️ Basic Info")
        col1, col2 = st.columns(2)
        with col1:
            phone   = st.text_input("Phone / Telephone", value=fresh.get("phone", ""),
                                    placeholder="+91 175 000 0000")
            website = st.text_input("Website", value=fresh.get("website", ""),
                                    placeholder="www.hospital.com")
        with col2:
            city    = st.text_input("City", value=fresh.get("city", ""),
                                    placeholder="Patiala")
            pincode = st.text_input("PIN Code", value=fresh.get("pincode", ""),
                                    placeholder="140001")
        address = st.text_area("Full Address (Street, District)", height=80,
                               value=fresh.get("address", ""),
                               placeholder="123, Hospital Road, Medical District")

        st.markdown("---")
        st.markdown(
            "**Receipt Preview** — Header will read:  \n"
            f"`{fresh.get('name', 'Hospital Name')} · {fresh.get('address') or '[address]'}, "
            f"{fresh.get('city') or '[city]'} — {fresh.get('pincode') or '[PIN]'}  \n"
            f"Tel: {fresh.get('phone') or '[phone]'} | Email: {hosp['email']} | "
            f"{fresh.get('website') or '[website]'}`"
        )

        saved = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)
        if saved:
            update_hospital_profile(
                hosp["hospital_id"],
                address=address.strip(),
                phone=phone.strip(),
                website=website.strip(),
                city=city.strip(),
                pincode=pincode.strip(),
            )
            # Refresh session state
            updated = get_hospital(hosp["hospital_id"])
            if updated:
                st.session_state["admin_hospital_data"] = updated
            st.success("✅ Hospital profile updated! Future receipts will use these details.")
            st.rerun()
