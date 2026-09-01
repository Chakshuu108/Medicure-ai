import streamlit as st
import json
import requests
from datetime import date, datetime
from core.meet_ui import render_meeting
from data.database import (
    create_patient, get_patients_by_doctor, get_patients_by_doctor_and_date,
    clear_patients_by_date, get_patient,
    get_patient_prescriptions, create_prescription,
    get_alerts, resolve_alert, get_patient_alerts,
    get_all_mcq_responses_for_doctor,
    create_opd_slots, get_opd_slots, mark_patient_visited, get_all_opd_slots_for_doctor,
    get_chat_history, save_chat_message,
)
from agents.orchestrator import AgentOrchestrator


@st.cache_resource(show_spinner=False)
def _get_orchestrator():
    return AgentOrchestrator()

def _orchestrator():
    """Lazy accessor — only initialises agents on first actual use."""
    return _get_orchestrator()


@st.cache_data(ttl=5, show_spinner=False)
def _cached_patients_by_date(doctor_id, date_str):
    return get_patients_by_doctor_and_date(doctor_id, date_str)

@st.cache_data(ttl=5, show_spinner=False)
def _cached_all_patients(doctor_id):
    return get_patients_by_doctor(doctor_id)

@st.cache_data(ttl=30, show_spinner=False)
def _cached_prescriptions(patient_id):
    return get_patient_prescriptions(patient_id)

@st.cache_data(ttl=20, show_spinner=False)
def _cached_alerts(doctor_id):
    return get_alerts(doctor_id=doctor_id)

@st.cache_data(ttl=20, show_spinner=False)
def _cached_mcq_responses(doctor_id, status_filter=None):
    return get_all_mcq_responses_for_doctor(doctor_id, status_filter)

@st.cache_data(ttl=20, show_spinner=False)
def _cached_opd_slots(doctor_id, date_str):
    return get_opd_slots(doctor_id, date_str)

def _invalidate_patient_caches(doctor_id, date_str=None):
    _cached_all_patients.clear()
    _cached_patients_by_date.clear()
    if date_str:
        pass


def render_doctor_dashboard():
    # NOTE: orchestrator is NOT initialised here — it's fetched lazily inside
    # button callbacks so the dashboard renders instantly on first load.

    doctor = st.session_state.get("doctor_data", {})
    hospital = st.session_state.get("hospital_data", {})
    doctor_id = doctor.get("doctor_id", "")
    doctor_name = doctor.get("name", "Doctor")
    hospital_id = hospital.get("hospital_id", "")

    st.markdown(f"""
    <div class="page-header">
        <h1>👨‍⚕️ Dr. {doctor_name}</h1>
        <p>{doctor.get('specialization','General')} · {hospital.get('name','')} · <code>{doctor_id}</code></p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        selected_date = st.date_input(
            "📅 Working Date",
            value=st.session_state.get("selected_date", date.today()),
            key="date_picker"
        )
        st.session_state["selected_date"] = selected_date
    with col_d2:
        n_today = len(_cached_patients_by_date(doctor_id, selected_date.isoformat()))
        st.markdown(f"""
        <div class="card" style="margin-top:0.5rem; text-align:center; padding:0.8rem;">
            <div style="font-size:0.75rem; color:#6B6080; text-transform:uppercase; letter-spacing:0.08em;">Patients Today</div>
            <div style="font-size:2rem; font-weight:700; color:#A78BFA;">{n_today}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    tabs = st.tabs(["💊 Prescriptions", "📋 Today's Patients", "📆 View by Date", "🚨 Alerts", "🧬 Patient Health Center", "🖥️ Online OPD", "📋 Consultation Summaries", "🤖 AI Assistant"])

    # ── Tab 1: Today's Patients ───────────────────────────────────────────────
    with tabs[1]:
        st.markdown(f"### Patients — {selected_date.strftime('%A, %d %B %Y')}")
        patients_today = _cached_patients_by_date(doctor_id, selected_date.isoformat())

        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.metric("Total Patients", len(patients_today))
        with col_h2:
            if st.button("🗑️ Clear Today's Patients", type="secondary", use_container_width=True):
                st.session_state["confirm_clear"] = True

        if st.session_state.get("confirm_clear"):
            st.warning(f"⚠️ This will delete **all {len(patients_today)} patients** for {selected_date}. Are you sure?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Clear", type="primary"):
                    n = clear_patients_by_date(doctor_id, selected_date.isoformat())
                    st.session_state["confirm_clear"] = False
                    _invalidate_patient_caches(doctor_id)
                    st.success(f"Cleared {n} patients.")
                    st.rerun()
            with c2:
                if st.button("❌ Cancel"):
                    st.session_state["confirm_clear"] = False
                    st.rerun()

        if not patients_today:
            st.info("No patients registered for this date.")
        else:
            for p in patients_today:
                risk_level = p.get("risk_level", "low")
                with st.expander(f"🧑 {p['name']} — `{p['id']}`"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**Age:** {p['age']}")
                    c2.markdown(f"**Gender:** {p['gender']}")
                    c3.markdown(f"**Condition:** {p['disease']}")
                    c4.markdown(f'<span class="risk-badge risk-{risk_level}">⚡ {risk_level.upper()} ({p.get("risk_score",0)})</span>', unsafe_allow_html=True)
                    if st.button("Run AI Risk Evaluation", key=f"risk_{p['id']}"):
                        with st.spinner("AI evaluating..."):
                            result = _orchestrator().risk.evaluate(p["id"])
                        st.markdown(f"""
                        <div class="card">
                            <div class="card-header">Risk Assessment</div>
                            <p><strong>Score:</strong> {result['score']}/100 &nbsp;|&nbsp; <strong>Level:</strong> {result['level'].upper()}</p>
                            <p style="color: var(--text-secondary);">{result['reasoning']}</p>
                        </div>
                        """, unsafe_allow_html=True)

    # ── Tab 2: View by Date ───────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 📆 View Patients by Date")
        view_date = st.date_input("Select Date", value=selected_date, key="view_date_picker")
        view_patients = _cached_patients_by_date(doctor_id, view_date.isoformat())
        st.markdown(f"**{len(view_patients)} patients** on {view_date.strftime('%d %B %Y')}")
        if not view_patients:
            st.info("No patients for this date.")
        else:
            for p in view_patients:
                risk_level = p.get("risk_level", "low")
                with st.expander(f"🧑 {p['name']} — `{p['id']}`"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f"**Age:** {p['age']}")
                    c2.markdown(f"**Gender:** {p['gender']}")
                    c3.markdown(f"**Condition:** {p['disease']}")
                    c4.markdown(f'<span class="risk-badge risk-{risk_level}">⚡ {risk_level.upper()}</span>', unsafe_allow_html=True)
                    prescriptions = _cached_prescriptions(p["id"])
                    if prescriptions:
                        for pr in prescriptions[:1]:
                            for m in pr.get("medicines", [])[:3]:
                                st.markdown(f"💊 `{m['name']}` {m['dosage']} — {m['timing']}")

    # ── Tab 0: Prescriptions ──────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### Create Prescription")

        col_ref1, col_ref2 = st.columns([5, 1])
        with col_ref2:
            if st.button("🔄 Refresh", use_container_width=True,
                         help="Reload patient list to include recently registered patients"):
                _cached_all_patients.clear()
                _cached_patients_by_date.clear()
                st.rerun()

        all_my_patients = _cached_all_patients(doctor_id)
        if not all_my_patients:
            st.info("Register a patient first.")
        else:
            patient_map = {f"{p['name']} ({p['id']}) — {p.get('visit_date', '')}": p["id"] for p in all_my_patients}
            with col_ref1:
                selected_p = st.selectbox("Select Patient", list(patient_map.keys()),
                                          help="Automatically includes patients registered by the receptionist")
            patient_id = patient_map[selected_p]

            st.markdown("#### Medicines")
            num_meds = st.number_input("Number of Medicines", 1, 10, 1)
            medicines = []
            for i in range(int(num_meds)):
                st.markdown(f"**Medicine {i+1}**")
                mc0, mc1, mc2, mc3, mc4 = st.columns(5)
                disease_name = mc0.text_input("Disease / Indication", placeholder="e.g. Hypertension",
                                              key=f"mdisease_{i}")
                med_name = mc1.text_input("Medicine Name", key=f"mname_{i}")
                dosage = mc2.text_input("Dosage", placeholder="e.g. 500mg", key=f"mdose_{i}")
                duration = mc3.number_input("Duration (days)", 1, 365, 7, key=f"mdur_{i}")
                timing = mc4.selectbox("Timing", ["Morning", "Afternoon", "Evening", "Night", "Before Bed",
                                                   "Twice Daily", "Thrice Daily", "With Meals", "Empty Stomach"],
                                       key=f"mtiming_{i}")
                medicines.append({"name": med_name, "disease": disease_name, "dosage": dosage,
                                   "duration_days": duration, "timing": timing,
                                   "start_date": date.today().isoformat()})

            notes = st.text_area("Doctor's Notes (Optional)")

            if st.button("Save Prescription & Generate Schedule", type="primary"):
                valid_meds = [m for m in medicines if m["name"]]
                if valid_meds:
                    with st.spinner("Saving prescription and generating AI schedule..."):
                        create_prescription(patient_id, valid_meds, notes, doctor_id=doctor_id)
                        preview = _orchestrator().on_prescription_created(patient_id)
                    _cached_prescriptions.clear()
                    st.success("Prescription saved! AI agents notified.")
                    if preview:
                        st.markdown("#### 📅 Generated Schedule Preview (Next 7 Days)")
                        for item in preview[:14]:
                            st.markdown(f"""
                            <div class="schedule-item">
                                <span style="color: var(--primary-light); font-family: 'DM Mono'; font-size: 0.85rem;">📅 {item['date']}</span>
                                <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
                                <span style="font-weight: 600;">💊 {item['medicine']}</span>
                                <span style="color: var(--text-secondary);">{item['dosage']}</span>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.error("Add at least one medicine with a name.")

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("#### View Existing Prescriptions")
            view_p = st.selectbox("Patient", list(patient_map.keys()), key="view_presc")
            vpid = patient_map[view_p]
            prescriptions = _cached_prescriptions(vpid)
            if prescriptions:
                for pr in prescriptions:
                    with st.expander(f"Prescription — {pr['created_at'][:10]}"):
                        for m in pr.get("medicines", []):
                            disease_label = f"<span style='color:#A78BFA;font-size:0.8rem;'>{m.get('disease', '')}</span> &nbsp;|&nbsp; " if m.get('disease') else ""
                            st.markdown(f"""
                            <div class="medicine-card">
                                {disease_label}<strong>💊 {m['name']}</strong> &nbsp; <code>{m['dosage']}</code>
                                &nbsp;|&nbsp; {m['duration_days']} days &nbsp;|&nbsp; {m['timing']}
                            </div>
                            """, unsafe_allow_html=True)
                        if pr.get("doctor_notes"):
                            st.markdown(f"**Notes:** {pr['doctor_notes']}")
            else:
                st.info("No prescriptions yet.")

    # ── Tab 3: Alerts ─────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("### 🚨 Patient Alerts Dashboard")

        # Controls row
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 1, 1])
        with col_ctrl1:
            filter_choice = st.radio(
                "Filter",
                ["All", "Critical", "Stable", "MCQ Alerts", "AI Alerts"],
                horizontal=True,
                key="alert_filter"
            )
        with col_ctrl3:
            if st.button("🔄 Run AI System Check"):
                with st.spinner("Running AI system-wide check..."):
                    result = _orchestrator().run_full_system_check()
                st.success(f"Check complete. {len(result)} alerts generated.")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # ── MCQ-based structured alerts ───────────────────────────────────────
        show_mcq = filter_choice in ("All", "Critical", "Stable", "MCQ Alerts")
        show_ai = filter_choice in ("All", "Critical", "AI Alerts")

        if show_mcq:
            st.markdown("#### 🩺 Daily Health Check Alerts")
            # Map filter to status
            mcq_status_filter = None
            if filter_choice == "Critical":
                mcq_status_filter = "Worsening"
            elif filter_choice == "Stable":
                mcq_status_filter = "Stable"

            mcq_responses = _cached_mcq_responses(doctor_id, mcq_status_filter)

            if not mcq_responses:
                st.success("✅ No patient health check responses yet.")
            else:
                for r in mcq_responses:
                    status = r["status"]
                    score = r["total_score"]
                    status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
                    status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
                    color = status_colors.get(status, "#A78BFA")
                    icon = status_icons.get(status, "•")

                    side_effects_raw = r.get("side_effects", "[]")
                    try:
                        side_effects = json.loads(side_effects_raw)
                    except Exception:
                        side_effects = []

                    is_critical = status == "Worsening" or score < 0 or bool(side_effects)
                    severity_label = "🔴 CRITICAL" if is_critical else ("🟡 MONITOR" if status == "Stable" else "🟢 GOOD")

                    with st.expander(
                        f"{icon} {r.get('patient_name','?')} ({r['patient_id']}) — {status} — {r['date']} {severity_label}"
                    ):
                        st.markdown(f"""
<div style="background: var(--bg-surface); border: 1px solid {color}33; border-radius: 10px;
    padding: 1.2rem; font-family: 'DM Mono', monospace; font-size: 0.85rem; line-height: 1.9;
    white-space: pre-wrap; color: var(--text-primary);">
<span style="color: #A78BFA;">Patient ID:</span>    {r['patient_id']}
<span style="color: #A78BFA;">Doctor ID:</span>     {r.get('doctor_id', doctor_id)}
<span style="color: #A78BFA;">Disease:</span>       {r.get('disease', 'N/A')}
<span style="color: {color}; font-weight: 700;">Current Status:</span> {icon} {status}
<span style="color: #A78BFA;">Score:</span>         {score:+d}

<span style="color: #A78BFA;">Medication Adherence:</span>
  - {r.get('adherence_status', 'Not recorded')}

<span style="color: #A78BFA;">Side Effects:</span>
  - {', '.join(side_effects) if side_effects else 'None reported'}

<span style="color: #A78BFA;">Recommended Action:</span>
  - {'Continue medication as prescribed' if status == 'Improving' else 'Monitor closely, follow up in 2-3 days' if status == 'Stable' else '⚠️ Immediate consultation required'}

<span style="color: #A78BFA;">Submitted:</span>     {r.get('submitted_at', '')[:16]}
</div>
                        """, unsafe_allow_html=True)

                        # Show individual answers
                        try:
                            responses_data = json.loads(r.get("responses_json", "[]"))
                            if responses_data:
                                st.markdown("**Individual Answers:**")
                                for ans in responses_data:
                                    ans_color = "#34D399" if ans.get("score", 0) > 0 else "#F87171" if ans.get("score", 0) < 0 else "#FBBF24"
                                    st.markdown(f"""
                                    <div style="display:flex; justify-content:space-between; padding:0.3rem 0;
                                        border-bottom: 1px solid #2D2640; font-size: 0.82rem;">
                                        <span style="color:var(--text-secondary);">{ans.get('question','')}</span>
                                        <span style="color:{ans_color}; font-weight:600; white-space:nowrap; margin-left:1rem;">
                                            {ans.get('selected','')} ({ans.get('score',0):+d})
                                        </span>
                                    </div>
                                    """, unsafe_allow_html=True)
                        except Exception:
                            pass

        # ── AI-generated alerts ───────────────────────────────────────────────
        if show_ai:
            st.markdown("#### 🤖 AI-Generated System Alerts")

            ai_alerts = _cached_alerts(doctor_id)
            # For "Critical" filter, only show high severity
            if filter_choice == "Critical":
                ai_alerts = [a for a in ai_alerts if a.get("severity") == "high"]

            if not ai_alerts:
                st.success("✅ No active AI alerts.")
            else:
                severity_icons = {"high": "🔴", "medium": "🟡", "low": "🔵"}
                for alert in ai_alerts:
                    severity = alert.get("severity", "medium")
                    s_icon = severity_icons.get(severity, "🟡")
                    alert_type = alert["alert_type"].replace("_", " ").title()

                    with st.expander(f"{s_icon} {alert.get('patient_name','?')} — {alert_type} ({alert['created_at'][:10]})"):
                        st.markdown(f'<span class="risk-badge risk-{severity}">{severity.upper()}</span>', unsafe_allow_html=True)

                        msg = alert["message"]
                        # Render MCQ-structured alert messages nicely
                        if "\n" in msg:
                            st.markdown(f"""
                            <div style="background: var(--bg-surface); border-radius: 8px; padding: 1rem;
                                font-family: 'DM Mono', monospace; font-size: 0.82rem;
                                white-space: pre-wrap; line-height: 1.8; color: var(--text-primary);">
{msg}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"**Message:** {msg}")

                        if st.button("✓ Dismiss Alert", key=f"dismiss_{alert['id']}"):
                            resolve_alert(alert["id"])
                            _cached_alerts.clear()
                            st.rerun()

    # ── Tab 4: Patient Health Center ─────────────────────────────────────────
    with tabs[4]:
        _render_patient_health_center(doctor_id)

        # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown("### 🖥️ Online OPD — Slot Management")
        st.markdown(
            '<p style="color:var(--text-secondary);">Set up available time slots for online consultations '
            'and track patient visit status.</p>',
            unsafe_allow_html=True
        )

        opd_sub = st.tabs(["📅 Create Slots", "📋 Manage Slots"])

        # ── Sub-tab A: Create Slots ───────────────────────────────────────────
        with opd_sub[0]:
            st.markdown("#### ➕ Add OPD Time Slots")
            col_a, col_b = st.columns(2)
            with col_a:
                opd_date = st.date_input(
                    "OPD Date",
                    value=st.session_state.get("selected_date", date.today()),
                    key="opd_date_picker"
                )
                opd_start = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time(), key="opd_start")
            with col_b:
                opd_num_slots = st.number_input("Number of Slots", min_value=1, max_value=50, value=10, key="opd_num")
                opd_duration = st.number_input("Slot Duration (minutes)", min_value=5, max_value=120, value=17, key="opd_dur")

            # Preview
            from datetime import timedelta as _td
            preview_start = datetime.combine(opd_date, opd_start)
            preview_end = preview_start + _td(minutes=int(opd_duration) * int(opd_num_slots))
            st.markdown(f"""
            <div class="card" style="padding:0.8rem 1.2rem;">
                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                    <div><span style="color:var(--text-muted);font-size:0.75rem;">SLOTS</span><br>
                         <strong style="color:#A78BFA;">{opd_num_slots}</strong></div>
                    <div><span style="color:var(--text-muted);font-size:0.75rem;">DURATION EACH</span><br>
                         <strong style="color:#A78BFA;">{opd_duration} min</strong></div>
                    <div><span style="color:var(--text-muted);font-size:0.75rem;">SESSION</span><br>
                         <strong style="color:#A78BFA;">{preview_start.strftime('%H:%M')} → {preview_end.strftime('%H:%M')}</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🗓️ Create OPD Slots", type="primary", use_container_width=True, key="create_opd_btn"):
                create_opd_slots(
                    doctor_id=doctor_id,
                    slot_date=opd_date.isoformat(),
                    start_time=opd_start.strftime("%H:%M"),
                    num_slots=int(opd_num_slots),
                    slot_duration_minutes=int(opd_duration)
                )
                _cached_opd_slots.clear()
                st.session_state["opd_created_msg"] = (
                    f"✅ {opd_num_slots} slots created for {opd_date.strftime('%d %b %Y')} "
                    f"({opd_start.strftime('%H:%M')} – {preview_end.strftime('%H:%M')})"
                )

            if st.session_state.get("opd_created_msg"):
                st.success(st.session_state["opd_created_msg"])
                st.info("👉 Go to **Manage Slots** tab to see and start video calls for booked slots.")

        # ── Sub-tab B: Manage Slots ───────────────────────────────────────────
        with opd_sub[1]:
            st.markdown("#### 📋 Slot Status & Visit Tracking")

            # Date selector for slot view
            manage_date = st.date_input(
                "View slots for date",
                value=st.session_state.get("selected_date", date.today()),
                key="opd_manage_date"
            )
            slots = _cached_opd_slots(doctor_id, manage_date.isoformat())

            if not slots:
                st.info(f"No OPD slots created for {manage_date.strftime('%d %b %Y')}. Go to 'Create Slots' to add them.")
            else:
                booked = [s for s in slots if s["is_booked"]]
                free = [s for s in slots if not s["is_booked"]]
                visited = [s for s in booked if s["patient_visited"]]

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Slots", len(slots))
                c2.metric("Booked", len(booked))
                c3.metric("Visited", len(visited))

                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

                for slot in slots:
                    is_booked = bool(slot["is_booked"])
                    visited_flag = bool(slot["patient_visited"])
                    status_color = "#34D399" if visited_flag else ("#FBBF24" if is_booked else "#6B6080")
                    status_label = "✅ Visited" if visited_flag else ("🟡 Booked" if is_booked else "⬜ Available")

                    with st.expander(
                        f"{slot['start_time']} – {slot['end_time']}  |  {status_label}  "
                        f"{'| 👤 ' + (slot.get('patient_name') or slot.get('booked_by_patient_id','')) if is_booked else ''}",
                        expanded=False
                    ):
                        safe_room = slot['id'].replace("-", "").replace(" ", "")
                        room_name = f"MediCore-{safe_room}"

                        col_info, col_action = st.columns([3, 1])
                        with col_info:
                            st.markdown(f"""
                            <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.8;">
                                <strong>Slot ID:</strong> <code>{slot['id']}</code><br>
                                <strong>Time:</strong> {slot['start_time']} – {slot['end_time']}<br>
                                {"<strong>Patient:</strong> " + (slot.get('patient_name') or '') + " &nbsp;<code>" + (slot.get('booked_by_patient_id') or '') + "</code><br>" if is_booked else ""}
                                <strong>Status:</strong> <span style="color:{status_color};">{status_label}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_action:
                            if is_booked:
                                new_visited = st.checkbox(
                                    "Consulted",
                                    value=visited_flag,
                                    key=f"visit_{slot['id']}"
                                )
                                if new_visited != visited_flag:
                                    mark_patient_visited(slot["id"], new_visited)
                                    _cached_opd_slots.clear()
                                    st.rerun()

                        # ── Embedded video call (Jitsi) ──────────────────────
                        if is_booked:
                            call_key = f"show_call_doc_{slot['id']}"
                            if st.button("🎥 Start / Join Video Call", key=f"btn_call_doc_{slot['id']}",
                                         use_container_width=True, type="primary"):
                                st.session_state[call_key] = not st.session_state.get(call_key, False)

                            if st.session_state.get(call_key, False):
                                doctor_name = st.session_state.get("doctor_data", {}).get("name", "Doctor")
                                with st.container():
                                    render_meeting(
                                        room_name=room_name,
                                        display_name=f"Dr. {doctor_name}",
                                        sender_label=f"Dr. {doctor_name}",
                                        role="doctor"
                                    )
                                    from core.meet_ui import render_consultation_summary_section
                                    patient_id_for_slot = slot.get("booked_by_patient_id", "")
                                    render_consultation_summary_section(
                                        room_name=room_name,
                                        slot_id=slot["id"],
                                        doctor_id=doctor_id,
                                        patient_id=patient_id_for_slot,
                                        role="doctor"
                                    )




    # ── Tab 6: Consultation Summaries ─────────────────────────────────────────
    with tabs[6]:
        _render_consultation_summaries_tab(doctor_id)

    # ── Tab 7: AI Assistant (Doctor) ──────────────────────────────────────────
    with tabs[7]:
        _render_doctor_ai_assistant(doctor_id, doctor)


def _render_consultation_summaries_tab(doctor_id: str):
    """Dedicated tab listing all saved post-call consultation summaries."""
    from data.database import get_doctor_meet_summaries_enriched
    from core.meet_summary import render_summaries_list

    st.markdown("### 📋 Consultation Summaries")
    st.markdown(
        '<p style="color:var(--text-secondary);">AI-generated summaries from your Online OPD video calls. '
        'Each summary includes sufferings, disease, medicines, and conclusion — saved automatically when a call ends.</p>',
        unsafe_allow_html=True
    )
    summaries = get_doctor_meet_summaries_enriched(doctor_id)
    render_summaries_list(summaries, role="doctor")


def _render_doctor_ai_assistant(doctor_id: str, doctor_data: dict):
    """
    Agentic AI assistant tab for doctors.
    Uses a doctor-specific LLM system prompt with full patient roster context.
    """
    import requests
    from core.config import GROQ_API_KEY, GROQ_MODEL

    st.markdown("### 🤖 AI Clinical Assistant")
    st.markdown(
        '<p style="color:var(--text-secondary);">Ask me anything about your patients, '
        'get AI-generated risk summaries, draft clinical notes, or query patient data.</p>',
        unsafe_allow_html=True
    )

    # ── Quick prompts ─────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
        <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                     color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
             📊 Summarise today's patients</span>
        <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                     color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
             🚨 Who are my high-risk patients?</span>
        <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                     color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
             💊 Flag medication concerns</span>
        <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                     color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
             📋 Draft a clinical note template</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Patient selector for contextual queries ───────────────────────────────
    all_patients = _cached_all_patients(doctor_id)
    patient_options = {"(No specific patient — general query)": None}
    patient_options.update({f"{p['name']} ({p['id']})": p['id'] for p in all_patients})

    selected_label = st.selectbox(
        "Focus on a specific patient (optional)",
        list(patient_options.keys()),
        key="doc_ai_patient_sel"
    )
    selected_patient_id = patient_options[selected_label]

    # ── Chat history per-doctor ───────────────────────────────────────────────
    _chat_key = f"doc_ai_history_{doctor_id}"
    if _chat_key not in st.session_state:
        st.session_state[_chat_key] = []

    for msg in st.session_state[_chat_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask about patients, prescriptions, clinical protocols…"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state[_chat_key].append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("🤖 Thinking…"):
                reply = _doctor_ai_respond(
                    prompt=prompt,
                    doctor_data=doctor_data,
                    all_patients=all_patients,
                    selected_patient_id=selected_patient_id,
                    history=st.session_state[_chat_key][-12:],
                    groq_api_key=GROQ_API_KEY,
                    groq_model=GROQ_MODEL,
                )
            st.markdown(reply)

        st.session_state[_chat_key].append({"role": "assistant", "content": reply})

    if st.button("🗑️ Clear Chat", key="doc_ai_clear"):
        st.session_state[_chat_key] = []
        st.rerun()


def _doctor_ai_respond(prompt, doctor_data, all_patients, selected_patient_id,
                        history, groq_api_key, groq_model) -> str:
    """Call Groq with doctor-specific system prompt and patient context."""
    from data.database import get_patient_prescriptions

    if not groq_api_key:
        return "⚠️ AI service not configured. Add GROQ_API_KEY to your Streamlit secrets."

    doctor_name = doctor_data.get("name", "Doctor")
    specialization = doctor_data.get("specialization", "General Medicine")

    # Build roster summary
    high_risk  = [p for p in all_patients if p.get("risk_level") == "high"]
    today_str  = date.today().isoformat()

    roster_lines = []
    for p in all_patients[:20]:
        roster_lines.append(
            f"• {p['name']} | Age {p['age']} | {p['disease']} | "
            f"Risk: {p.get('risk_level','low').upper()} ({p.get('risk_score',0)}/100)"
        )
    roster_text = "\n".join(roster_lines) if roster_lines else "No patients yet."

    # Patient-specific context if selected
    patient_detail = ""
    if selected_patient_id:
        patient = get_patient(selected_patient_id)
        if patient:
            prescriptions = get_patient_prescriptions(selected_patient_id)
            med_lines = []
            for pr in prescriptions:
                for m in pr.get("medicines", []):
                    med_lines.append(f"  - {m['name']} {m['dosage']} ({m['timing']}, {m['duration_days']}d)")
            patient_detail = f"""
SELECTED PATIENT DETAIL:
Name       : {patient['name']}
Age/Gender : {patient['age']} / {patient['gender']}
Condition  : {patient['disease']}
Risk       : {patient.get('risk_level','low').upper()} ({patient.get('risk_score',0)}/100)
Visit Date : {patient.get('visit_date','N/A')}
Prescriptions:
{''.join(med_lines) or '  None yet'}
"""

    system = f"""You are an autonomous AI clinical assistant for Dr. {doctor_name} ({specialization}).
You have full access to the doctor's patient roster and can:
- Summarise patient cohorts and identify patterns
- Flag high-risk patients and medication concerns
- Analyse MCQ health check results
- Draft clinical notes, referral letters, discharge summaries
- Answer clinical protocol questions
- Identify drug interactions or dosage issues across the roster

Today's date: {today_str}
High-risk patients: {len(high_risk)} out of {len(all_patients)} total

PATIENT ROSTER (up to 20):
{roster_text}
{patient_detail}

IMPORTANT: You are assisting a qualified doctor. Be precise, clinical, and thorough.
Flag safety concerns explicitly. When drafting documents, use professional medical language.
Always note: AI analysis assists but does not replace clinical judgment."""

    messages = [{"role": "system", "content": system}]
    for h in history[:-1]:  # exclude last (current) user message — we add it next
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"},
            json={"model": groq_model, "messages": messages,
                  "max_tokens": 1200, "temperature": 0.25},
            timeout=35,
        )
        resp.raise_for_status()
        choices = resp.json().get("choices", [])
        return choices[0]["message"]["content"] if choices else "No response received."
    except Exception as e:
        return f"AI service error: {str(e)[:100]}. Please try again."


# ══════════════════════════════════════════════════════════════════════════════
# 🧬  PATIENT HEALTH CENTER — Doctor-side view of Command Center alerts
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=15, show_spinner=False)
def _cached_hcc_alerts(doctor_id):
    """Fetch all unresolved Command Center alerts for this doctor's patients."""
    return get_alerts(doctor_id=doctor_id)


def _render_patient_health_center(doctor_id: str):
    """
    Doctor-facing Patient Health Center tab.
    Shows all alerts raised autonomously by the patient-side Health Command Center,
    grouped by patient with severity badges and notification counts.
    """
    st.markdown("""
    <div style="margin-bottom:0.3rem;">
        <span style="font-size:1.4rem;font-weight:800;
              background:linear-gradient(135deg,#A78BFA,#60A5FA);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            🧬 Patient Health Center
        </span>
    </div>
    <p style="color:var(--text-secondary);font-size:0.9rem;margin-top:-0.1rem;margin-bottom:1rem;">
        Real-time autonomous alerts raised by your patients' AI Health Command Center.
        Every notification here was triggered automatically — no manual reporting needed.
    </p>
    """, unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Controls row ──────────────────────────────────────────────────────────
    col_filter, col_refresh = st.columns([4, 1])
    with col_filter:
        severity_filter = st.radio(
            "Show",
            ["All", "🔴 High", "🟡 Medium", "🟢 Low"],
            horizontal=True,
            key="hcc_severity_filter",
        )
    with col_refresh:
        if st.button("🔄 Refresh", key="hcc_refresh_btn", use_container_width=True):
            _cached_hcc_alerts.clear()
            st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Fetch alerts ──────────────────────────────────────────────────────────
    all_alerts = _cached_hcc_alerts(doctor_id)

    # Filter to Health Command Center alert types
    hcc_types = {
        "command_center_worsening",
        "command_center_worsening_2",
        "command_center_high_risk",
        "command_center_missed_doses",
    }
    hcc_alerts = [a for a in all_alerts if a.get("alert_type", "") in hcc_types]

    # Apply severity filter
    sev_map = {"🔴 High": "high", "🟡 Medium": "medium", "🟢 Low": "low"}
    if severity_filter != "All":
        hcc_alerts = [a for a in hcc_alerts if a.get("severity") == sev_map.get(severity_filter)]

    # ── Summary notification bar ──────────────────────────────────────────────
    total      = len(hcc_alerts)
    high_count = sum(1 for a in hcc_alerts if a.get("severity") == "high")
    med_count  = sum(1 for a in hcc_alerts if a.get("severity") == "medium")
    low_count  = sum(1 for a in hcc_alerts if a.get("severity") == "low")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Notifications", total)
    c2.metric("🔴 High Priority", high_count)
    c3.metric("🟡 Medium", med_count)
    c4.metric("🟢 Low", low_count)

    st.markdown("<div style='margin-bottom:1rem;'></div>", unsafe_allow_html=True)

    if not hcc_alerts:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2.5rem;
             border-left:4px solid #34D399;background:rgba(52,211,153,0.06);">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
            <div style="font-weight:700;color:#34D399;font-size:1rem;">All Clear</div>
            <div style="color:var(--text-muted);font-size:0.88rem;margin-top:0.4rem;">
                No Health Command Center alerts for your patients right now.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Group alerts by patient ───────────────────────────────────────────────
    from collections import defaultdict
    patient_alerts: dict = defaultdict(list)
    for alert in hcc_alerts:
        pid = alert.get("patient_id", "unknown")
        patient_alerts[pid].append(alert)

    # Sort: patients with high-severity first
    def _patient_priority(item):
        _, alerts = item
        has_high = any(a.get("severity") == "high" for a in alerts)
        return (0 if has_high else 1, -len(alerts))

    severity_colors = {"high": "#F87171", "medium": "#FBBF24", "low": "#34D399"}
    severity_icons  = {"high": "🔴", "medium": "🟡", "low": "🟢"}

    type_labels = {
        "command_center_worsening":   "🚨 Worsening Trend (3+ sessions)",
        "command_center_worsening_2": "⚠️ Worsening Trend (2 sessions)",
        "command_center_high_risk":   "🔴 High Risk Score",
        "command_center_missed_doses": "💊 Missed Doses Detected",
    }

    for patient_id, p_alerts in sorted(patient_alerts.items(), key=_patient_priority):
        patient_name = p_alerts[0].get("patient_name", patient_id)
        has_high     = any(a.get("severity") == "high" for a in p_alerts)
        card_border  = "#F87171" if has_high else "#FBBF24"
        notif_count  = len(p_alerts)

        # Patient header card
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {card_border};
             background:rgba(124,58,237,0.05);margin-bottom:0.5rem;
             padding:0.9rem 1.2rem;">
            <div style="display:flex;align-items:center;
                 justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:0.8rem;">
                    <span style="font-size:1.6rem;">👤</span>
                    <div>
                        <div style="font-weight:700;color:var(--text-primary);
                             font-size:0.97rem;">{patient_name}</div>
                        <div style="color:var(--text-muted);font-size:0.78rem;">
                            Patient ID: {patient_id}
                        </div>
                    </div>
                </div>
                <span style="background:{card_border}22;color:{card_border};
                      font-size:0.75rem;font-weight:700;padding:3px 12px;
                      border-radius:12px;letter-spacing:0.06em;">
                    {notif_count} ALERT{'S' if notif_count > 1 else ''}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Individual alert cards under this patient
        for alert in sorted(p_alerts, key=lambda x: x.get("severity", "low"),
                             reverse=True):
            sev    = alert.get("severity", "medium")
            color  = severity_colors.get(sev, "#FBBF24")
            icon   = severity_icons.get(sev, "🟡")
            label  = type_labels.get(alert.get("alert_type", ""), 
                                     alert.get("alert_type", "").replace("_", " ").title())
            ts     = alert.get("created_at", "")[:16].replace("T", " ")

            with st.expander(f"{icon} {label} — {ts}", expanded=(sev == "high")):
                st.markdown(f"""
                <div style="background:rgba(0,0,0,0.15);border-radius:8px;
                     padding:0.9rem 1rem;border-left:3px solid {color};
                     font-size:0.85rem;color:var(--text-secondary);
                     line-height:1.7;white-space:pre-wrap;">
{alert.get('message', '')}
                </div>
                """, unsafe_allow_html=True)

                col_badge, col_dismiss = st.columns([3, 1])
                with col_badge:
                    st.markdown(
                        f'<span class="risk-badge risk-{sev}">'
                        f'{icon} {sev.upper()} PRIORITY</span>',
                        unsafe_allow_html=True,
                    )
                with col_dismiss:
                    if st.button("✓ Dismiss", key=f"hcc_dismiss_{alert['id']}",
                                 use_container_width=True):
                        resolve_alert(alert["id"])
                        _cached_hcc_alerts.clear()
                        st.rerun()

        st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:var(--text-muted);font-size:0.73rem;'
        f'margin-top:1rem;text-align:right;">'
        f'Last refreshed: {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
        f'</div>',
        unsafe_allow_html=True,
    )
