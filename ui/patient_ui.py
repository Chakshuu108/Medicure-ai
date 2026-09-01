# # # import streamlit as st
from core.meet_ui import render_meeting
# # # import json
# # # from datetime import date, datetime
# # # from data.database import (
# # #     get_patient, get_patient_prescriptions, get_chat_history,
# # #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# # #     create_alert, check_consecutive_worsening, get_patient_alerts,
# # #     resolve_alert,
# # #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# # #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# # #     get_patient_opd_bookings, check_patient_has_booking
# # # )
# # # from agents.orchestrator import AgentOrchestrator
# # # from agents.scheduling_agent import (
# # #     SchedulingAgent, get_auth_url,
# # #     exchange_code_for_tokens, refresh_access_token
# # # )
# # # from agents.mcq_agent import MCQAgent


# # # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_chat_history(patient_id, limit=20):
# # #     return get_chat_history(patient_id, limit)

# # # @st.cache_data(ttl=15, show_spinner=False)
# # # def _cached_prescriptions(patient_id):
# # #     return get_patient_prescriptions(patient_id)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_patient_alerts(patient_id):
# # #     return get_patient_alerts(patient_id)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_opd_bookings(patient_id):
# # #     return get_patient_opd_bookings(patient_id)

# # # @st.cache_data(ttl=20, show_spinner=False)
# # # def _cached_mcq_response_today(patient_id, today_str):
# # #     return get_mcq_response_for_date(patient_id, today_str)

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_mcq_responses(patient_id, limit=30):
# # #     return get_mcq_responses(patient_id, limit)

# # # @st.cache_data(ttl=60, show_spinner=False)
# # # def _cached_opd_doctors():
# # #     return get_available_opd_doctors()

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_opd_dates(doctor_id):
# # #     return get_available_opd_dates_for_doctor(doctor_id)

# # # @st.cache_data(ttl=15, show_spinner=False)
# # # def _cached_opd_slots(doctor_id, date_str):
# # #     return get_available_opd_slots(doctor_id, date_str)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_has_booking(patient_id, doctor_id, date_str):
# # #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # # def _handle_google_oauth_callback():
# # #     """
# # #     Called once at the top of app.py.
# # #     If Google redirected back with ?code=..., exchange it for tokens,
# # #     set mode=patient, and mark patient_google_authed=True.
# # #     Only removes OAuth-specific params, preserving the _s session-restore param.
# # #     """
# # #     params = st.query_params
# # #     auth_code = params.get("code")
# # #     if auth_code and not st.session_state.get("google_access_token"):
# # #         try:
# # #             tokens = exchange_code_for_tokens(auth_code)
# # #             if "access_token" in tokens:
# # #                 st.session_state["google_access_token"] = tokens["access_token"]
# # #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# # #                 st.session_state["patient_google_authed"] = True
# # #                 st.session_state["mode"] = "patient"
# # #                 st.toast("✅ Google sign-in successful!", icon="✅")
# # #         except Exception as e:
# # #             st.warning(f"Google OAuth error: {e}")
# # #         # Remove only OAuth-specific params, preserving _s session param
# # #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# # #             try:
# # #                 if oauth_key in st.query_params:
# # #                     del st.query_params[oauth_key]
# # #             except Exception:
# # #                 pass


# # # def _get_valid_access_token() -> str | None:
# # #     """Return a valid Google access token from session, refreshing if needed."""
# # #     token = st.session_state.get("google_access_token")
# # #     if token:
# # #         return token
# # #     refresh_tok = st.session_state.get("google_refresh_token")
# # #     if refresh_tok:
# # #         new_token = refresh_access_token(refresh_tok)
# # #         if new_token:
# # #             st.session_state["google_access_token"] = new_token
# # #             return new_token
# # #     return None


# # # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # # @st.cache_resource(show_spinner=False)
# # # def _get_orchestrator():
# # #     return AgentOrchestrator()

# # # @st.cache_resource(show_spinner=False)
# # # def _get_scheduler():
# # #     return SchedulingAgent()

# # # @st.cache_resource(show_spinner=False)
# # # def _get_mcq_agent():
# # #     return MCQAgent()

# # # @st.cache_data(ttl=120, show_spinner=False)
# # # def _cached_patient_login(patient_id):
# # #     """Run the expensive on_patient_login only once per 2 minutes."""
# # #     return _get_orchestrator().on_patient_login(patient_id)

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_get_patient(patient_id):
# # #     return get_patient(patient_id)


# # # # ── Main dashboard ────────────────────────────────────────────────────────────

# # # def render_patient_dashboard(patient_id):
# # #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# # #     orchestrator = _get_orchestrator()
# # #     scheduler = _get_scheduler()
# # #     mcq_agent = _get_mcq_agent()
# # #     patient = _cached_get_patient(patient_id)

# # #     if not patient:
# # #         st.error("Patient not found. Check your Patient ID.")
# # #         return

# # #     st.markdown(f"""
# # #     <div class="page-header">
# # #         <h1>🧑‍⚕️ Patient Portal</h1>
# # #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# # #     _health_key = f"health_data_{patient_id}"
# # #     if _health_key not in st.session_state:
# # #         with st.spinner("Loading your health data..."):
# # #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# # #     health_data = st.session_state[_health_key]

# # #     risk = health_data.get("risk", {})
# # #     adherence = health_data.get("adherence", {})
# # #     trends = health_data.get("trends", {})

# # #     col1, col2, col3, col4 = st.columns(4)
# # #     risk_level = risk.get("level", "low")
# # #     col1.metric("Risk Level", risk_level.upper())
# # #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# # #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# # #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# # #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# # #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
# # #     tabs = st.tabs([
# # #         "💬 AI Assistant",
# # #         "📅 My Schedule",
# # #         "💊 My Prescriptions",
# # #         "🩺 Daily Health Check",
# # #         "🔔 Alerts",
# # #         "🖥️ Online OPD",
# # #     ])

# # #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# # #     with tabs[0]:
# # #         st.markdown("### 🤖 Autonomous AI Health Agent")
# # #         st.markdown(
# # #             '<p style="color: var(--text-secondary);">'
# # #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# # #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# # #             '</p>',
# # #             unsafe_allow_html=True
# # #         )

# # #         # ── Quick action chips ─────────────────────────────────────────────
# # #         st.markdown("""
# # #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# # #                          cursor:pointer;">📅 Book Appointment</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          💊 My Prescriptions</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          🩺 Check Symptoms</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          🔔 My Alerts</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          ❌ Cancel Appointment</span>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #         history = _cached_chat_history(patient_id, 20)
# # #         for msg in history:
# # #             with st.chat_message(msg["role"]):
# # #                 st.markdown(msg["content"])

# # #         # ── Triage action buttons ─────────────────────────────────────────
# # #         _triage_key = f"pending_triage_{patient_id}"
# # #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# # #         _confirm_key = f"triage_confirm_{patient_id}"

# # #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# # #             triage_level = st.session_state[_triage_key]
# # #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# # #             if triage_level == "URGENT":
# # #                 btn_label = "🚨 Alert My Doctor Now"
# # #                 btn_type = "primary"
# # #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# # #             else:
# # #                 btn_label = "📅 Book Urgent Appointment"
# # #                 btn_type = "secondary"
# # #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# # #             if not st.session_state.get(_confirm_key):
# # #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# # #                     st.session_state[_confirm_key] = True
# # #                     st.rerun()
# # #             else:
# # #                 st.warning(confirm_msg)
# # #                 col_yes, col_no = st.columns(2)
# # #                 with col_yes:
# # #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# # #                         severity = "high" if triage_level == "URGENT" else "medium"
# # #                         alert_message = (
# # #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# # #                             f"Patient described: \"{symptom_text}\"\n"
# # #                             f"AI Triage Verdict: {triage_level}\n"
# # #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# # #                                else "📅 Patient requests a follow-up appointment.")
# # #                         )
# # #                         _pt = get_patient(patient_id)
# # #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# # #                         create_alert(
# # #                             patient_id=patient_id,
# # #                             alert_type="patient_reported_symptoms",
# # #                             message=alert_message,
# # #                             severity=severity,
# # #                             doctor_id=_doctor_id
# # #                         )
# # #                         st.session_state.pop(_triage_key, None)
# # #                         st.session_state.pop(_triage_msg_key, None)
# # #                         st.session_state.pop(_confirm_key, None)
# # #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# # #                                    else "✅ Alert sent to your doctor!")
# # #                         st.rerun()
# # #                 with col_no:
# # #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# # #                         st.session_state.pop(_triage_key, None)
# # #                         st.session_state.pop(_triage_msg_key, None)
# # #                         st.session_state.pop(_confirm_key, None)
# # #                         st.rerun()

# # #         # ── Action result display (non-triage confirmations) ──────────────
# # #         _action_result_key = f"action_result_{patient_id}"
# # #         if st.session_state.get(_action_result_key):
# # #             ar = st.session_state[_action_result_key]
# # #             action = ar.get("action", "")
# # #             confirmed = ar.get("confirmed", False)
# # #             success = ar.get("success", False)

# # #             if confirmed and success:
# # #                 if action == "book_appointment":
# # #                     bd = ar.get("booking_details", {})
# # #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# # #                 elif action == "cancel_appointment":
# # #                     st.success("✅ Appointment successfully cancelled.")

# # #             st.session_state.pop(_action_result_key, None)

# # #         # ── Chat input ────────────────────────────────────────────────────
# # #         placeholder = (
# # #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# # #             "or 'Show my prescriptions' or 'I have chest pain'..."
# # #         )
# # #         if prompt := st.chat_input(placeholder):
# # #             with st.chat_message("user"):
# # #                 st.markdown(prompt)

# # #             with st.chat_message("assistant"):
# # #                 with st.spinner("🤖 Analysing and acting..."):
# # #                     result = orchestrator.on_patient_message(
# # #                         patient_id, prompt,
# # #                         use_agentic=True,
# # #                         session_state=st.session_state
# # #                     )

# # #                 if not isinstance(result, dict):
# # #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# # #                 reply = result.get("reply", "")
# # #                 triage = result.get("triage")
# # #                 action = result.get("action", "")
# # #                 confirmed = result.get("confirmed", False)
# # #                 success = result.get("success", False)

# # #                 # ── Show triage badge ──────────────────────────────────
# # #                 if triage == "URGENT":
# # #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# # #                 elif triage == "MODERATE":
# # #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# # #                 elif triage == "MILD":
# # #                     st.success("🟢 **MILD — Manageable at home for now.**")

# # #                 # ── Show action confirmation badge ────────────────────
# # #                 if confirmed and success:
# # #                     if action == "book_appointment":
# # #                         bd = result.get("booking_details", {})
# # #                         st.success(
# # #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# # #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# # #                         )
# # #                     elif action == "cancel_appointment":
# # #                         st.success("✅ **Appointment Cancelled Successfully**")

# # #                 st.markdown(reply)

# # #             # ── Post-response state management ────────────────────────
# # #             if triage in ("URGENT", "MODERATE"):
# # #                 st.session_state[_triage_key] = triage
# # #                 st.session_state[_triage_msg_key] = prompt
# # #                 st.session_state.pop(_confirm_key, None)
# # #             else:
# # #                 st.session_state.pop(_triage_key, None)
# # #                 st.session_state.pop(_triage_msg_key, None)
# # #                 st.session_state.pop(_confirm_key, None)

# # #             _cached_chat_history.clear()
# # #             st.rerun()

# # #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# # #     with tabs[1]:
# # #         st.markdown("### 📅 Medication Schedule")
# # #         col1, col2 = st.columns([3, 1])

# # #         with col2:
# # #             access_token = _get_valid_access_token()

# # #             if access_token:
# # #                 # Token available — show sync button
# # #                 if st.button("📆 Sync to Google Calendar"):
# # #                     with st.spinner("Syncing to calendar..."):
# # #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# # #                     if result["success"]:
# # #                         st.success(result["message"])
# # #                     else:
# # #                         st.warning(result.get("message", "Sync failed."))
# # #                         if result.get("errors"):
# # #                             for e in result["errors"]:
# # #                                 st.caption(f"⚠ {e}")
# # #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# # #                     st.session_state.pop("google_access_token", None)
# # #                     st.session_state.pop("google_refresh_token", None)
# # #                     st.rerun()
# # #             else:
# # #                 # No access token in session (e.g. user disconnected or session expired).
# # #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# # #                 st.markdown("""
# # #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# # #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# # #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# # #                         📅 Google Calendar Disconnected
# # #                     </div>
# # #                     <div style="color:#A89FC8;font-size:0.82rem;">
# # #                         Your Google session token has expired. Click below to reconnect —
# # #                         this uses the same Google account you signed in with.
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)
# # #                 try:
# # #                     auth_url = get_auth_url()
# # #                     st.markdown(f"""
# # #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# # #                         <div style="
# # #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# # #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# # #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# # #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# # #                             <svg width="16" height="16" viewBox="0 0 18 18">
# # #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# # #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# # #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# # #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# # #                             </svg>
# # #                             Reconnect Google Calendar
# # #                         </div>
# # #                     </a>
# # #                     """, unsafe_allow_html=True)
# # #                 except Exception:
# # #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# # #         schedule = scheduler.get_schedule_preview(patient_id)
# # #         if not schedule:
# # #             st.info("No schedule available. Ask your doctor to create a prescription.")
# # #         else:
# # #             current_date = None
# # #             for item in schedule:
# # #                 if item["date"] != current_date:
# # #                     current_date = item["date"]
# # #                     st.markdown(f"**📅 {current_date}**")
# # #                 st.markdown(f"""
# # #                 <div class="schedule-item">
# # #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# # #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# # #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# # #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# # #     with tabs[2]:
# # #         st.markdown("### 💊 My Prescriptions")
# # #         prescriptions = _cached_prescriptions(patient_id)
# # #         if not prescriptions:
# # #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# # #         else:
# # #             for i, pr in enumerate(prescriptions):
# # #                 st.markdown(f"""
# # #                 <div class="card">
# # #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# # #                 """, unsafe_allow_html=True)
# # #                 for m in pr.get("medicines", []):
# # #                     st.markdown(f"""
# # #                     <div class="medicine-card">
# # #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# # #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# # #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# # #                         </div>
# # #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# # #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# # #                         </div>
# # #                     </div>
# # #                     """, unsafe_allow_html=True)
# # #                 if pr.get("doctor_notes"):
# # #                     st.markdown(
# # #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# # #                         unsafe_allow_html=True
# # #                     )
# # #                 st.markdown("</div>", unsafe_allow_html=True)

# # #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# # #     with tabs[3]:
# # #         today_str = date.today().isoformat()
# # #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# # #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# # #         _mcq_show_form = True  # controls whether to show the question form

# # #         if existing_response:
# # #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# # #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# # #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# # #                 st.session_state["retake_mcq"] = True
# # #                 st.session_state["show_health_summary"] = False
# # #                 # Clear cached questions so fresh ones load
# # #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# # #                 st.rerun()
# # #             if not st.session_state.get("retake_mcq"):
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             prescriptions = _cached_prescriptions(patient_id)
# # #             if not prescriptions:
# # #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             # Cache questions per patient per day — no need to call GROQ on every rerun
# # #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# # #             if _q_key not in st.session_state:
# # #                 with st.spinner("Loading your personalized health questions..."):
# # #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# # #             questions = st.session_state[_q_key]

# # #             if not questions:
# # #                 st.error("Could not generate questions. Please try again.")
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             st.markdown("""
# # #             <div class="card" style="margin-bottom: 1.5rem;">
# # #                 <div class="card-header">📋 Today's Health Questions</div>
# # #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# # #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# # #                 </p>
# # #             </div>
# # #             """, unsafe_allow_html=True)

# # #             selected_options = {}

# # #             for q in questions:
# # #                 qid = str(q["id"])
# # #                 category_icons = {
# # #                     "symptom": "🤒",
# # #                     "adherence": "💊",
# # #                     "side_effect": "⚠️",
# # #                     "wellbeing": "💚"
# # #                 }
# # #                 icon = category_icons.get(q.get("category", ""), "❓")

# # #                 st.markdown(f"""
# # #                 <div class="card" style="margin-bottom: 1rem;">
# # #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# # #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# # #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# # #                     </div>
# # #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# # #                         {q['question']}
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #                 option_labels = [opt["text"] for opt in q["options"]]
# # #                 choice = st.radio(
# # #                     label=q["question"],
# # #                     options=range(len(option_labels)),
# # #                     format_func=lambda i, opts=option_labels: opts[i],
# # #                     key=f"mcq_{qid}",
# # #                     label_visibility="collapsed"
# # #                 )
# # #                 selected_options[qid] = choice
# # #                 st.markdown("---")

# # #             col_btn1, col_btn2 = st.columns([3, 1])
# # #             with col_btn1:
# # #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# # #                     total_score = 0
# # #                     for q in questions:
# # #                         qid = str(q["id"])
# # #                         idx = selected_options.get(qid, 0)
# # #                         try:
# # #                             total_score += q["options"][idx]["score"]
# # #                         except (IndexError, KeyError):
# # #                             pass

# # #                     status = mcq_agent.compute_status(total_score)
# # #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# # #                     responses_data = []
# # #                     for q in questions:
# # #                         qid = str(q["id"])
# # #                         idx = selected_options.get(qid, 0)
# # #                         responses_data.append({
# # #                             "question": q["question"],
# # #                             "category": q.get("category"),
# # #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# # #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# # #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# # #                         })

# # #                     doctor_id = patient.get("doctor_id")
# # #                     save_mcq_response(
# # #                         patient_id=patient_id,
# # #                         doctor_id=doctor_id,
# # #                         date_str=today_str,
# # #                         responses_json=json.dumps(responses_data),
# # #                         total_score=total_score,
# # #                         status=status,
# # #                         side_effects=json.dumps(side_effects),
# # #                         adherence_status=adherence_status
# # #                     )

# # #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# # #                                            symptoms, adherence_status, side_effects)

# # #                     st.session_state["retake_mcq"] = False
# # #                     st.session_state["show_health_summary"] = True
# # #                     # Invalidate cached data so next render is fresh
# # #                     _cached_patient_login.clear()
# # #                     _cached_mcq_response_today.clear()
# # #                     _cached_mcq_responses.clear()
# # #                     st.session_state.pop(f"health_data_{patient_id}", None)
# # #                     st.rerun()

# # #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# # #         # Show automatically after submission OR when today's response already exists
# # #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# # #         if _show_summary:
# # #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# # #             st.markdown("### 📊 Your Health Summary")

# # #             # ── AI Health Report ──────────────────────────────────────────────
# # #             col_ai1, col_ai2 = st.columns([4, 1])
# # #             with col_ai2:
# # #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# # #             if _gen_report or st.session_state.get("show_health_summary"):
# # #                 # Cache summary per patient per day - expensive GROQ call
# # #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# # #                 if _gen_report or _sum_key not in st.session_state:
# # #                     with st.spinner("AI is analyzing your health data..."):
# # #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# # #                 summary = st.session_state[_sum_key]
# # #                 st.markdown(f"""
# # #                 <div class="card">
# # #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# # #                     <p style="line-height: 1.7;">{summary}</p>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #             # ── Health Indicators ─────────────────────────────────────────────
# # #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# # #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# # #             st.markdown(f"""
# # #             <div class="card">
# # #                 <div class="card-header">Health Indicators</div>
# # #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# # #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# # #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# # #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# # #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #             """, unsafe_allow_html=True)

# # #             # ── Health Trend Chart ────────────────────────────────────────────
# # #             responses = _cached_mcq_responses(patient_id, limit=30)
# # #             if responses:
# # #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# # #                 import pandas as pd
# # #                 import plotly.graph_objects as go

# # #                 chart_responses = list(reversed(responses))
# # #                 dates  = [r["date"] for r in chart_responses]
# # #                 scores = [r["total_score"] for r in chart_responses]
# # #                 statuses = [r["status"] for r in chart_responses]

# # #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# # #                 fig = go.Figure()
# # #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=[max(s, 0) for s in scores],
# # #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# # #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# # #                 ))
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=[min(s, 0) for s in scores],
# # #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# # #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# # #                 ))
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=scores,
# # #                     mode="lines+markers",
# # #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# # #                     marker=dict(size=10, color=marker_colors,
# # #                                 line=dict(color="#1a1a2e", width=2)),
# # #                     name="Health Score",
# # #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# # #                 ))

# # #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #                 for d, s, st_ in zip(dates, scores, statuses):
# # #                     fig.add_annotation(
# # #                         x=d, y=s,
# # #                         text=status_icons_map.get(st_, ""),
# # #                         showarrow=False,
# # #                         yshift=18, font=dict(size=13)
# # #                     )

# # #                 fig.update_layout(
# # #                     paper_bgcolor="rgba(0,0,0,0)",
# # #                     plot_bgcolor="rgba(0,0,0,0)",
# # #                     font=dict(color="#A89FC8", size=12),
# # #                     margin=dict(l=10, r=10, t=10, b=10),
# # #                     height=300,
# # #                     xaxis=dict(
# # #                         showgrid=False, zeroline=False,
# # #                         tickfont=dict(size=11, color="#6B6080"),
# # #                         title=""
# # #                     ),
# # #                     yaxis=dict(
# # #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# # #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# # #                         tickfont=dict(size=11, color="#6B6080"),
# # #                         title="Score"
# # #                     ),
# # #                     hoverlabel=dict(
# # #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# # #                         font=dict(color="white", size=13)
# # #                     ),
# # #                     showlegend=False
# # #                 )

# # #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# # #                 st.markdown("""
# # #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# # #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# # #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# # #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# # #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #                 # ── Recent Check-in History ───────────────────────────────────
# # #                 st.markdown("#### 📋 Recent Daily Check-in History")
# # #                 for r in responses:
# # #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #                     color = status_colors.get(r["status"], "#A78BFA")
# # #                     icon = status_icons.get(r["status"], "•")
# # #                     st.markdown(f"""
# # #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# # #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# # #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# # #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# # #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# # #                         </div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# # #                             Adherence: {r.get('adherence_status', 'N/A')}
# # #                         </div>
# # #                     </div>
# # #                     """, unsafe_allow_html=True)

# # #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# # #     with tabs[4]:
# # #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# # #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# # #     with tabs[5]:
# # #         _render_patient_opd(patient_id, patient)


# # # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# # #     """Render the patient-facing Alerts & Notifications tab."""
# # #     st.markdown("### 🔔 Alerts & Notifications")
# # #     st.markdown(
# # #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# # #         'and doctor messages are shown here.</p>',
# # #         unsafe_allow_html=True
# # #     )

# # #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# # #     if risk_level == "high":
# # #         st.markdown(f"""
# # #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# # #             <div style="display:flex;align-items:center;gap:0.8rem;">
# # #                 <span style="font-size:1.8rem;">🚨</span>
# # #                 <div>
# # #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# # #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# # #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# # #                         Please contact your doctor or visit the clinic immediately.
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# # #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# # #     missed_dose_dates = []
# # #     for r in recent_responses:
# # #         adh = (r.get("adherence_status") or "").lower()
# # #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# # #             missed_dose_dates.append(r["date"])

# # #     if missed_dose_dates:
# # #         dates_str = ", ".join(missed_dose_dates[:3])
# # #         st.markdown(f"""
# # #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# # #             <div style="display:flex;align-items:center;gap:0.8rem;">
# # #                 <span style="font-size:1.8rem;">💊</span>
# # #                 <div>
# # #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# # #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# # #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# # #                         Consistent adherence is key to recovery — please take medications as prescribed.
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# # #     all_alerts = _cached_patient_alerts(patient_id)
# # #     unresolved = [a for a in all_alerts if not a["resolved"]]
# # #     resolved = [a for a in all_alerts if a["resolved"]]

# # #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# # #         st.markdown("""
# # #         <div class="card" style="text-align:center;padding:2rem;">
# # #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# # #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# # #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# # #                 No active alerts. Keep taking your medications and completing daily check-ins!
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)
# # #         return

# # #     severity_config = {
# # #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# # #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# # #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# # #     }
# # #     type_labels = {
# # #         "mcq_health_check": "Health Check Alert",
# # #         "doctor_message":   "Doctor Message",
# # #         "missed_dose":      "Missed Dose",
# # #         "high_risk":        "High Risk Warning",
# # #     }

# # #     if unresolved:
# # #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# # #         for alert in unresolved:
# # #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# # #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# # #             created = alert["created_at"][:16].replace("T", " ")

# # #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# # #                 st.markdown(f"""
# # #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# # #                              border-left:3px solid {cfg['color']};">
# # #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# # #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # # {alert['message']}</pre>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)
# # #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# # #                     resolve_alert(alert["id"])
# # #                     _cached_patient_alerts.clear()
# # #                     st.rerun()

# # #     if resolved:
# # #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# # #             for alert in resolved:
# # #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# # #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# # #                 created = alert["created_at"][:16].replace("T", " ")
# # #                 st.markdown(f"""
# # #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# # #                     <div style="display:flex;justify-content:space-between;">
# # #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# # #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)


# # # # ── MCQ result card ───────────────────────────────────────────────────────────

# # # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# # #     status = response["status"]
# # #     score = response["total_score"]
# # #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #     color = status_colors.get(status, "#A78BFA")
# # #     icon = status_icons.get(status, "•")

# # #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# # #     # Safely escape feedback strings to prevent HTML injection
# # #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# # #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# # #     st.markdown(f"""
# # #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# # #         <div style="text-align: center; padding: 1rem 0;">
# # #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# # #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# # #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# # #         </div>
# # #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# # #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# # #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# # #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# # #         </div>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     adherence_status = response.get("adherence_status", "")
# # #     side_effects_raw = response.get("side_effects", "[]")
# # #     try:
# # #         side_effects = json.loads(side_effects_raw)
# # #     except Exception:
# # #         side_effects = []

# # #     col1, col2 = st.columns(2)
# # #     with col1:
# # #         st.markdown(f"""
# # #         <div class="card" style="margin-top: 0;">
# # #             <div class="card-header">💊 Medication Adherence</div>
# # #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# # #         </div>
# # #         """, unsafe_allow_html=True)
# # #     with col2:
# # #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# # #         st.markdown(f"""
# # #         <div class="card" style="margin-top: 0;">
# # #             <div class="card-header">⚠️ Side Effects</div>
# # #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     if show_history and patient_id:
# # #         st.markdown(
# # #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# # #             unsafe_allow_html=True
# # #         )


# # # # ── Alert firing logic ────────────────────────────────────────────────────────

# # # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# # #     """Fire structured doctor alerts based on MCQ response."""
# # #     trigger = False
# # #     reasons = []

# # #     if total_score < 0:
# # #         trigger = True
# # #         reasons.append("negative_score")

# # #     if check_consecutive_worsening(patient_id, 2):
# # #         trigger = True
# # #         reasons.append("consecutive_worsening")

# # #     if side_effects:
# # #         trigger = True
# # #         reasons.append("side_effects")

# # #     if not trigger:
# # #         return

# # #     action_map = {
# # #         "Improving": "Continue medication as prescribed",
# # #         "Stable": "Monitor closely, follow up in 2-3 days",
# # #         "Worsening": "Immediate consultation required"
# # #     }

# # #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# # #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# # #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# # #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# # #     alert_message = f"""Patient ID: {patient_id}
# # # Doctor ID: {doctor_id}
# # # Disease: {patient.get('disease', 'N/A')}
# # # Current Status: {status}
# # # Score: {total_score:+d}

# # # Key Symptoms Reported:
# # # {symptoms_text}

# # # Medication Adherence:
# # # {adherence_text}

# # # Side Effects:
# # # {side_effects_text}

# # # Recommended Action:
# # # - {action_map.get(status, 'Monitor patient')}

# # # Triggered By: {reasons_text}"""

# # #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# # #     create_alert(
# # #         patient_id=patient_id,
# # #         alert_type="mcq_health_check",
# # #         message=alert_message,
# # #         severity=severity,
# # #         doctor_id=doctor_id
# # #     )




# # # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # # def _render_patient_opd(patient_id: str, patient: dict):
# # #     """Full Online OPD booking UI for the patient dashboard."""
# # #     import streamlit as st
# # #     from datetime import date, datetime

# # #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# # #     st.markdown(
# # #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# # #         'Slots are real-time — once booked they disappear for other patients.</p>',
# # #         unsafe_allow_html=True
# # #     )

# # #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# # #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# # #     with opd_subtabs[0]:
# # #         doctors = _cached_opd_doctors()

# # #         if not doctors:
# # #             st.info("No doctors have published OPD slots yet. Please check back later.")
# # #         else:
# # #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# # #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# # #             selected_doctor_id = doctor_options[selected_label]

# # #             available_dates = _cached_opd_dates(selected_doctor_id)
# # #             if not available_dates:
# # #                 st.warning("This doctor has no available slots right now.")
# # #             else:
# # #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# # #                 chosen_date_str = st.selectbox(
# # #                     "Select Date",
# # #                     list(date_labels.keys()),
# # #                     format_func=lambda x: date_labels[x],
# # #                     key="opd_date_sel"
# # #                 )

# # #                 # Check if patient already booked on this day with this doctor
# # #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# # #                 if already_booked:
# # #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# # #                 else:
# # #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# # #                     if not free_slots:
# # #                         st.error("All slots for this date are fully booked. Please choose another date.")
# # #                     else:
# # #                         st.markdown(f"""
# # #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# # #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# # #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# # #                                 </div>
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# # #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# # #                                 </div>
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# # #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# # #                                 </div>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # #                         slot_options = {
# # #                             f"{s['start_time']} – {s['end_time']}": s['id']
# # #                             for s in free_slots
# # #                         }
# # #                         chosen_slot_label = st.selectbox(
# # #                             "Choose a time slot",
# # #                             list(slot_options.keys()),
# # #                             key="opd_slot_sel"
# # #                         )
# # #                         chosen_slot_id = slot_options[chosen_slot_label]

# # #                         st.markdown(f"""
# # #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# # #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# # #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# # #                                 <strong>Doctor:</strong> {selected_label}<br>
# # #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# # #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# # #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# # #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# # #                             if success:
# # #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# # #                                 st.balloons()
# # #                                 _cached_opd_bookings.clear()
# # #                                 _cached_opd_slots.clear()
# # #                                 _cached_has_booking.clear()
# # #                                 st.rerun()
# # #                             else:
# # #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# # #                                 _cached_opd_slots.clear()
# # #                                 st.rerun()

# # #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# # #     with opd_subtabs[1]:
# # #         st.markdown("#### 🗓️ Your OPD Bookings")
# # #         my_bookings = _cached_opd_bookings(patient_id)

# # #         if not my_bookings:
# # #             st.markdown("""
# # #             <div class="card" style="text-align:center;padding:2rem;">
# # #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# # #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# # #             </div>
# # #             """, unsafe_allow_html=True)
# # #         else:
# # #             today_str = date.today().isoformat()
# # #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# # #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# # #             if upcoming:
# # #                 st.markdown("##### 📅 Upcoming")
# # #                 for booking in upcoming:
# # #                     visited = bool(booking["patient_visited"])
# # #                     color = "#34D399" if visited else "#A78BFA"
# # #                     status = "✅ Consulted" if visited else "⏳ Pending"
# # #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# # #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# # #                     room_name = f"MediCore-{safe_room}"

# # #                     col_b, col_c = st.columns([4, 1])
# # #                     with col_b:
# # #                         st.markdown(f"""
# # #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# # #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# # #                                 <div>
# # #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# # #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# # #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# # #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# # #                                     </div>
# # #                                 </div>
# # #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)
# # #                     with col_c:
# # #                         if not visited:
# # #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# # #                                 success = cancel_opd_booking(booking["id"], patient_id)
# # #                                 if success:
# # #                                     st.success("Booking cancelled.")
# # #                                     _cached_opd_bookings.clear()
# # #                                     _cached_opd_slots.clear()
# # #                                     _cached_has_booking.clear()
# # #                                     st.rerun()

# # #                     # ── Embedded video call (Jitsi) ───────────────────────────
# # #                     if not visited:
# # #                         call_key = f"show_call_pat_{booking['id']}"
# # #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# # #                                      use_container_width=True, type="primary"):
# # #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# # #                         if st.session_state.get(call_key, False):
# # #                             patient_name = st.session_state.get("patient_id", "Patient")
# # #                             encoded_name = str(patient_name).replace(" ", "%20")
# # #                             st.components.v1.html(f"""
# # #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# # #                             <iframe
# # #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# # #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# # #                                 allowfullscreen="true"
# # #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# # #                             ></iframe>
# # #                             </body></html>
# # #                             """, height=560)

# # #             if past:
# # #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# # #                     for booking in past:
# # #                         visited = bool(booking["patient_visited"])
# # #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# # #                         status = "✅ Consulted" if visited else "❌ Not attended"
# # #                         color = "#34D399" if visited else "#F87171"
# # #                         st.markdown(f"""
# # #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# # #                             <div style="display:flex;justify-content:space-between;">
# # #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# # #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # # # ── Patient login ─────────────────────────────────────────────────────────────

# # # def render_patient_login():
# # #     st.markdown("""
# # #     <div style="max-width: 480px; margin: 4rem auto;">
# # #         <div class="page-header" style="text-align: center;">
# # #             <h1>🏥 Patient Login</h1>
# # #             <p>Enter your Patient ID to access your health portal</p>
# # #         </div>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     with st.container():
# # #         col1, col2, col3 = st.columns([1, 2, 1])
# # #         with col2:
# # #             patient_id = st.text_input(
# # #                 "Patient ID",
# # #                 placeholder="e.g. PAT-20260413-0001",
# # #                 label_visibility="collapsed"
# # #             )
# # #             st.markdown(
# # #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# # #                 'Your ID was provided by your doctor at registration</p>',
# # #                 unsafe_allow_html=True
# # #             )

# # #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# # #                 if patient_id:
# # #                     patient = get_patient(patient_id.strip().upper())
# # #                     if patient:
# # #                         st.session_state["patient_id"] = patient_id.strip().upper()
# # #                         st.session_state["patient_logged_in"] = True
# # #                         st.rerun()
# # #                     else:
# # #                         st.error("Patient ID not found. Check with your doctor.")
# # #                 else:
# # #                     st.warning("Please enter your Patient ID.")


# # import streamlit as st
# # import json
# # from datetime import date, datetime
# # from data.database import (
# #     get_patient, get_patient_prescriptions, get_chat_history,
# #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# #     create_alert, check_consecutive_worsening, get_patient_alerts,
# #     resolve_alert,
# #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# #     get_patient_opd_bookings, check_patient_has_booking
# # )
# # from agents.orchestrator import AgentOrchestrator
# # from agents.scheduling_agent import (
# #     SchedulingAgent, get_auth_url,
# #     exchange_code_for_tokens, refresh_access_token
# # )
# # from agents.mcq_agent import MCQAgent


# # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_chat_history(patient_id, limit=20):
# #     return get_chat_history(patient_id, limit)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_prescriptions(patient_id):
# #     return get_patient_prescriptions(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_patient_alerts(patient_id):
# #     return get_patient_alerts(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_opd_bookings(patient_id):
# #     return get_patient_opd_bookings(patient_id)

# # @st.cache_data(ttl=20, show_spinner=False)
# # def _cached_mcq_response_today(patient_id, today_str):
# #     return get_mcq_response_for_date(patient_id, today_str)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_mcq_responses(patient_id, limit=30):
# #     return get_mcq_responses(patient_id, limit)

# # @st.cache_data(ttl=60, show_spinner=False)
# # def _cached_opd_doctors():
# #     return get_available_opd_doctors()

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_opd_dates(doctor_id):
# #     return get_available_opd_dates_for_doctor(doctor_id)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_opd_slots(doctor_id, date_str):
# #     return get_available_opd_slots(doctor_id, date_str)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_has_booking(patient_id, doctor_id, date_str):
# #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # def _handle_google_oauth_callback():
# #     """
# #     Called once at the top of app.py.
# #     If Google redirected back with ?code=..., exchange it for tokens,
# #     set mode=patient, and mark patient_google_authed=True.
# #     Only removes OAuth-specific params, preserving the _s session-restore param.
# #     """
# #     params = st.query_params
# #     auth_code = params.get("code")
# #     if auth_code and not st.session_state.get("google_access_token"):
# #         try:
# #             tokens = exchange_code_for_tokens(auth_code)
# #             if "access_token" in tokens:
# #                 st.session_state["google_access_token"] = tokens["access_token"]
# #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# #                 st.session_state["patient_google_authed"] = True
# #                 st.session_state["mode"] = "patient"
# #                 st.toast("✅ Google sign-in successful!", icon="✅")
# #         except Exception as e:
# #             st.warning(f"Google OAuth error: {e}")
# #         # Remove only OAuth-specific params, preserving _s session param
# #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# #             try:
# #                 if oauth_key in st.query_params:
# #                     del st.query_params[oauth_key]
# #             except Exception:
# #                 pass


# # def _get_valid_access_token() -> str | None:
# #     """Return a valid Google access token from session, refreshing if needed."""
# #     token = st.session_state.get("google_access_token")
# #     if token:
# #         return token
# #     refresh_tok = st.session_state.get("google_refresh_token")
# #     if refresh_tok:
# #         new_token = refresh_access_token(refresh_tok)
# #         if new_token:
# #             st.session_state["google_access_token"] = new_token
# #             return new_token
# #     return None


# # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # @st.cache_resource(show_spinner=False)
# # def _get_orchestrator():
# #     return AgentOrchestrator()

# # @st.cache_resource(show_spinner=False)
# # def _get_scheduler():
# #     return SchedulingAgent()

# # @st.cache_resource(show_spinner=False)
# # def _get_mcq_agent():
# #     return MCQAgent()

# # @st.cache_data(ttl=120, show_spinner=False)
# # def _cached_patient_login(patient_id):
# #     """Run the expensive on_patient_login only once per 2 minutes."""
# #     return _get_orchestrator().on_patient_login(patient_id)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_get_patient(patient_id):
# #     return get_patient(patient_id)


# # # ── Main dashboard ────────────────────────────────────────────────────────────

# # def render_patient_dashboard(patient_id):
# #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# #     orchestrator = _get_orchestrator()
# #     scheduler = _get_scheduler()
# #     mcq_agent = _get_mcq_agent()
# #     patient = _cached_get_patient(patient_id)

# #     if not patient:
# #         st.error("Patient not found. Check your Patient ID.")
# #         return

# #     st.markdown(f"""
# #     <div class="page-header">
# #         <h1>🧑‍⚕️ Patient Portal</h1>
# #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# #     _health_key = f"health_data_{patient_id}"
# #     if _health_key not in st.session_state:
# #         with st.spinner("Loading your health data..."):
# #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# #     health_data = st.session_state[_health_key]

# #     risk = health_data.get("risk", {})
# #     adherence = health_data.get("adherence", {})
# #     trends = health_data.get("trends", {})

# #     col1, col2, col3, col4 = st.columns(4)
# #     risk_level = risk.get("level", "low")
# #     col1.metric("Risk Level", risk_level.upper())
# #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
# #     tabs = st.tabs([
# #         "💬 AI Assistant",
# #         "📅 My Schedule",
# #         "💊 My Prescriptions",
# #         "🩺 Daily Health Check",
# #         "🔔 Alerts",
# #         "🖥️ Online OPD",
# #     ])

# #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# #     with tabs[0]:
# #         st.markdown("### 🤖 Autonomous AI Health Agent")
# #         st.markdown(
# #             '<p style="color: var(--text-secondary);">'
# #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# #             '</p>',
# #             unsafe_allow_html=True
# #         )

# #         # ── Quick action chips ─────────────────────────────────────────────
# #         st.markdown("""
# #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# #                          cursor:pointer;">📅 Book Appointment</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          💊 My Prescriptions</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🩺 Check Symptoms</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🔔 My Alerts</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          ❌ Cancel Appointment</span>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         history = _cached_chat_history(patient_id, 20)
# #         for msg in history:
# #             with st.chat_message(msg["role"]):
# #                 st.markdown(msg["content"])

# #         # ── Triage action buttons ─────────────────────────────────────────
# #         _triage_key = f"pending_triage_{patient_id}"
# #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# #         _confirm_key = f"triage_confirm_{patient_id}"

# #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# #             triage_level = st.session_state[_triage_key]
# #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# #             if triage_level == "URGENT":
# #                 btn_label = "🚨 Alert My Doctor Now"
# #                 btn_type = "primary"
# #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# #             else:
# #                 btn_label = "📅 Book Urgent Appointment"
# #                 btn_type = "secondary"
# #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# #             if not st.session_state.get(_confirm_key):
# #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# #                     st.session_state[_confirm_key] = True
# #                     st.rerun()
# #             else:
# #                 st.warning(confirm_msg)
# #                 col_yes, col_no = st.columns(2)
# #                 with col_yes:
# #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# #                         severity = "high" if triage_level == "URGENT" else "medium"
# #                         alert_message = (
# #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# #                             f"Patient described: \"{symptom_text}\"\n"
# #                             f"AI Triage Verdict: {triage_level}\n"
# #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# #                                else "📅 Patient requests a follow-up appointment.")
# #                         )
# #                         _pt = get_patient(patient_id)
# #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# #                         create_alert(
# #                             patient_id=patient_id,
# #                             alert_type="patient_reported_symptoms",
# #                             message=alert_message,
# #                             severity=severity,
# #                             doctor_id=_doctor_id
# #                         )
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# #                                    else "✅ Alert sent to your doctor!")
# #                         st.rerun()
# #                 with col_no:
# #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.rerun()

# #         # ── Action result display (non-triage confirmations) ──────────────
# #         _action_result_key = f"action_result_{patient_id}"
# #         if st.session_state.get(_action_result_key):
# #             ar = st.session_state[_action_result_key]
# #             action = ar.get("action", "")
# #             confirmed = ar.get("confirmed", False)
# #             success = ar.get("success", False)

# #             if confirmed and success:
# #                 if action == "book_appointment":
# #                     bd = ar.get("booking_details", {})
# #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# #                 elif action == "cancel_appointment":
# #                     st.success("✅ Appointment successfully cancelled.")

# #             st.session_state.pop(_action_result_key, None)

# #         # ── Chat input ────────────────────────────────────────────────────
# #         placeholder = (
# #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# #             "or 'Show my prescriptions' or 'I have chest pain'..."
# #         )
# #         if prompt := st.chat_input(placeholder):
# #             with st.chat_message("user"):
# #                 st.markdown(prompt)

# #             with st.chat_message("assistant"):
# #                 with st.spinner("🤖 Analysing and acting..."):
# #                     result = orchestrator.on_patient_message(
# #                         patient_id, prompt,
# #                         use_agentic=True,
# #                         session_state=st.session_state
# #                     )

# #                 if not isinstance(result, dict):
# #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# #                 reply = result.get("reply", "")
# #                 triage = result.get("triage")
# #                 action = result.get("action", "")
# #                 confirmed = result.get("confirmed", False)
# #                 success = result.get("success", False)

# #                 # ── Show triage badge ──────────────────────────────────
# #                 if triage == "URGENT":
# #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# #                 elif triage == "MODERATE":
# #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# #                 elif triage == "MILD":
# #                     st.success("🟢 **MILD — Manageable at home for now.**")

# #                 # ── Show action confirmation badge ────────────────────
# #                 if confirmed and success:
# #                     if action == "book_appointment":
# #                         bd = result.get("booking_details", {})
# #                         st.success(
# #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# #                         )
# #                     elif action == "cancel_appointment":
# #                         st.success("✅ **Appointment Cancelled Successfully**")

# #                 st.markdown(reply)

# #             # ── Post-response state management ────────────────────────
# #             if triage in ("URGENT", "MODERATE"):
# #                 st.session_state[_triage_key] = triage
# #                 st.session_state[_triage_msg_key] = prompt
# #                 st.session_state.pop(_confirm_key, None)
# #             else:
# #                 st.session_state.pop(_triage_key, None)
# #                 st.session_state.pop(_triage_msg_key, None)
# #                 st.session_state.pop(_confirm_key, None)

# #             _cached_chat_history.clear()
# #             st.rerun()

# #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# #     with tabs[1]:
# #         st.markdown("### 📅 Medication Schedule")
# #         col1, col2 = st.columns([3, 1])

# #         with col2:
# #             access_token = _get_valid_access_token()

# #             if access_token:
# #                 # Token available — show sync button
# #                 if st.button("📆 Sync to Google Calendar"):
# #                     with st.spinner("Syncing to calendar..."):
# #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# #                     if result["success"]:
# #                         st.success(result["message"])
# #                     else:
# #                         st.warning(result.get("message", "Sync failed."))
# #                         if result.get("errors"):
# #                             for e in result["errors"]:
# #                                 st.caption(f"⚠ {e}")
# #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# #                     st.session_state.pop("google_access_token", None)
# #                     st.session_state.pop("google_refresh_token", None)
# #                     st.rerun()
# #             else:
# #                 # No access token in session (e.g. user disconnected or session expired).
# #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# #                 st.markdown("""
# #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# #                         📅 Google Calendar Disconnected
# #                     </div>
# #                     <div style="color:#A89FC8;font-size:0.82rem;">
# #                         Your Google session token has expired. Click below to reconnect —
# #                         this uses the same Google account you signed in with.
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 try:
# #                     auth_url = get_auth_url()
# #                     st.markdown(f"""
# #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# #                         <div style="
# #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# #                             <svg width="16" height="16" viewBox="0 0 18 18">
# #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# #                             </svg>
# #                             Reconnect Google Calendar
# #                         </div>
# #                     </a>
# #                     """, unsafe_allow_html=True)
# #                 except Exception:
# #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# #         schedule = scheduler.get_schedule_preview(patient_id)
# #         if not schedule:
# #             st.info("No schedule available. Ask your doctor to create a prescription.")
# #         else:
# #             current_date = None
# #             for item in schedule:
# #                 if item["date"] != current_date:
# #                     current_date = item["date"]
# #                     st.markdown(f"**📅 {current_date}**")
# #                 st.markdown(f"""
# #                 <div class="schedule-item">
# #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# #     with tabs[2]:
# #         st.markdown("### 💊 My Prescriptions")
# #         prescriptions = _cached_prescriptions(patient_id)
# #         if not prescriptions:
# #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# #         else:
# #             for i, pr in enumerate(prescriptions):
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# #                 """, unsafe_allow_html=True)
# #                 for m in pr.get("medicines", []):
# #                     st.markdown(f"""
# #                     <div class="medicine-card">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# #                         </div>
# #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)
# #                 if pr.get("doctor_notes"):
# #                     st.markdown(
# #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# #                         unsafe_allow_html=True
# #                     )
# #                 st.markdown("</div>", unsafe_allow_html=True)

# #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# #     with tabs[3]:
# #         today_str = date.today().isoformat()
# #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# #         _mcq_show_form = True  # controls whether to show the question form

# #         if existing_response:
# #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# #                 st.session_state["retake_mcq"] = True
# #                 st.session_state["show_health_summary"] = False
# #                 # Clear cached questions so fresh ones load
# #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# #                 st.rerun()
# #             if not st.session_state.get("retake_mcq"):
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             prescriptions = _cached_prescriptions(patient_id)
# #             if not prescriptions:
# #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             # Cache questions per patient per day — no need to call GROQ on every rerun
# #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# #             if _q_key not in st.session_state:
# #                 with st.spinner("Loading your personalized health questions..."):
# #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# #             questions = st.session_state[_q_key]

# #             if not questions:
# #                 st.error("Could not generate questions. Please try again.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             st.markdown("""
# #             <div class="card" style="margin-bottom: 1.5rem;">
# #                 <div class="card-header">📋 Today's Health Questions</div>
# #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# #                 </p>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             selected_options = {}

# #             for q in questions:
# #                 qid = str(q["id"])
# #                 category_icons = {
# #                     "symptom": "🤒",
# #                     "adherence": "💊",
# #                     "side_effect": "⚠️",
# #                     "wellbeing": "💚"
# #                 }
# #                 icon = category_icons.get(q.get("category", ""), "❓")

# #                 st.markdown(f"""
# #                 <div class="card" style="margin-bottom: 1rem;">
# #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# #                     </div>
# #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# #                         {q['question']}
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 option_labels = [opt["text"] for opt in q["options"]]
# #                 choice = st.radio(
# #                     label=q["question"],
# #                     options=range(len(option_labels)),
# #                     format_func=lambda i, opts=option_labels: opts[i],
# #                     key=f"mcq_{qid}",
# #                     label_visibility="collapsed"
# #                 )
# #                 selected_options[qid] = choice
# #                 st.markdown("---")

# #             col_btn1, col_btn2 = st.columns([3, 1])
# #             with col_btn1:
# #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# #                     total_score = 0
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         try:
# #                             total_score += q["options"][idx]["score"]
# #                         except (IndexError, KeyError):
# #                             pass

# #                     status = mcq_agent.compute_status(total_score)
# #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# #                     responses_data = []
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         responses_data.append({
# #                             "question": q["question"],
# #                             "category": q.get("category"),
# #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# #                         })

# #                     doctor_id = patient.get("doctor_id")
# #                     save_mcq_response(
# #                         patient_id=patient_id,
# #                         doctor_id=doctor_id,
# #                         date_str=today_str,
# #                         responses_json=json.dumps(responses_data),
# #                         total_score=total_score,
# #                         status=status,
# #                         side_effects=json.dumps(side_effects),
# #                         adherence_status=adherence_status
# #                     )

# #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# #                                            symptoms, adherence_status, side_effects)

# #                     st.session_state["retake_mcq"] = False
# #                     st.session_state["show_health_summary"] = True
# #                     # Invalidate ALL cached data — must happen before rerun so
# #                     # check_consecutive_worsening sees the row just saved
# #                     _cached_patient_login.clear()
# #                     _cached_mcq_response_today.clear()
# #                     _cached_mcq_responses.clear()
# #                     _cached_patient_alerts.clear()
# #                     # Also bust the worsening booking state so a fresh check runs
# #                     st.session_state.pop(f"worsening_booking_step_{patient_id}_tab", None)
# #                     st.session_state.pop(f"health_data_{patient_id}", None)
# #                     st.rerun()

# #         # ── Worsening Trend Early Warning ─────────────────────────────────────
# #         # Shown whenever consecutive worsening is detected (after submission or
# #         # on return visits).  Booking is ALWAYS patient-initiated — no auto-booking.
# #         _worsening_doctor_id = patient.get("doctor_id")
# #         _render_worsening_warning(patient_id, patient, _worsening_doctor_id, consecutive_n=2, context="tab")

# #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# #         # Show automatically after submission OR when today's response already exists
# #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# #         if _show_summary:
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             st.markdown("### 📊 Your Health Summary")

# #             # ── AI Health Report ──────────────────────────────────────────────
# #             col_ai1, col_ai2 = st.columns([4, 1])
# #             with col_ai2:
# #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# #             if _gen_report or st.session_state.get("show_health_summary"):
# #                 # Cache summary per patient per day - expensive GROQ call
# #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# #                 if _gen_report or _sum_key not in st.session_state:
# #                     with st.spinner("AI is analyzing your health data..."):
# #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# #                 summary = st.session_state[_sum_key]
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# #                     <p style="line-height: 1.7;">{summary}</p>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #             # ── Health Indicators ─────────────────────────────────────────────
# #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# #             st.markdown(f"""
# #             <div class="card">
# #                 <div class="card-header">Health Indicators</div>
# #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# #                     </div>
# #                 </div>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             # ── Health Trend Chart ────────────────────────────────────────────
# #             responses = _cached_mcq_responses(patient_id, limit=30)
# #             if responses:
# #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# #                 import pandas as pd
# #                 import plotly.graph_objects as go

# #                 chart_responses = list(reversed(responses))
# #                 dates  = [r["date"] for r in chart_responses]
# #                 scores = [r["total_score"] for r in chart_responses]
# #                 statuses = [r["status"] for r in chart_responses]

# #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# #                 fig = go.Figure()
# #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[max(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[min(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=scores,
# #                     mode="lines+markers",
# #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# #                     marker=dict(size=10, color=marker_colors,
# #                                 line=dict(color="#1a1a2e", width=2)),
# #                     name="Health Score",
# #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# #                 ))

# #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                 for d, s, st_ in zip(dates, scores, statuses):
# #                     fig.add_annotation(
# #                         x=d, y=s,
# #                         text=status_icons_map.get(st_, ""),
# #                         showarrow=False,
# #                         yshift=18, font=dict(size=13)
# #                     )

# #                 fig.update_layout(
# #                     paper_bgcolor="rgba(0,0,0,0)",
# #                     plot_bgcolor="rgba(0,0,0,0)",
# #                     font=dict(color="#A89FC8", size=12),
# #                     margin=dict(l=10, r=10, t=10, b=10),
# #                     height=300,
# #                     xaxis=dict(
# #                         showgrid=False, zeroline=False,
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title=""
# #                     ),
# #                     yaxis=dict(
# #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title="Score"
# #                     ),
# #                     hoverlabel=dict(
# #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# #                         font=dict(color="white", size=13)
# #                     ),
# #                     showlegend=False
# #                 )

# #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# #                 st.markdown("""
# #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 # ── Recent Check-in History ───────────────────────────────────
# #                 st.markdown("#### 📋 Recent Daily Check-in History")
# #                 for r in responses:
# #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                     color = status_colors.get(r["status"], "#A78BFA")
# #                     icon = status_icons.get(r["status"], "•")
# #                     st.markdown(f"""
# #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# #                         </div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# #                             Adherence: {r.get('adherence_status', 'N/A')}
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)

# #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# #     with tabs[4]:
# #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# #     with tabs[5]:
# #         _render_patient_opd(patient_id, patient)


# # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# #     """Render the patient-facing Alerts & Notifications tab."""
# #     st.markdown("### 🔔 Alerts & Notifications")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# #         'and doctor messages are shown here.</p>',
# #         unsafe_allow_html=True
# #     )

# #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# #     if risk_level == "high":
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">🚨</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# #                         Please contact your doctor or visit the clinic immediately.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── Worsening Trend Early Warning (also surfaced here for discoverability) ──
# #     _wt_doctor_id = patient.get("doctor_id")
# #     _render_worsening_warning(patient_id, patient, _wt_doctor_id, consecutive_n=2, context="alerts")

# #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# #     missed_dose_dates = []
# #     for r in recent_responses:
# #         adh = (r.get("adherence_status") or "").lower()
# #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# #             missed_dose_dates.append(r["date"])

# #     if missed_dose_dates:
# #         dates_str = ", ".join(missed_dose_dates[:3])
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">💊</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# #                         Consistent adherence is key to recovery — please take medications as prescribed.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# #     all_alerts = _cached_patient_alerts(patient_id)
# #     unresolved = [a for a in all_alerts if not a["resolved"]]
# #     resolved = [a for a in all_alerts if a["resolved"]]

# #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# #         st.markdown("""
# #         <div class="card" style="text-align:center;padding:2rem;">
# #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# #                 No active alerts. Keep taking your medications and completing daily check-ins!
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #         return

# #     severity_config = {
# #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# #     }
# #     type_labels = {
# #         "mcq_health_check":       "Health Check Alert",
# #         "doctor_message":         "Doctor Message",
# #         "missed_dose":            "Missed Dose",
# #         "high_risk":              "High Risk Warning",
# #         "worsening_opd_booked":   "Worsening Trend — OPD Booked",
# #         "worsening_condition":    "Worsening Condition",
# #         "patient_reported_symptoms": "Patient Reported Symptoms",
# #     }

# #     if unresolved:
# #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# #         for alert in unresolved:
# #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #             created = alert["created_at"][:16].replace("T", " ")

# #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# #                 st.markdown(f"""
# #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# #                              border-left:3px solid {cfg['color']};">
# #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # {alert['message']}</pre>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# #                     resolve_alert(alert["id"])
# #                     _cached_patient_alerts.clear()
# #                     st.rerun()

# #     if resolved:
# #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# #             for alert in resolved:
# #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #                 created = alert["created_at"][:16].replace("T", " ")
# #                 st.markdown(f"""
# #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# #                     <div style="display:flex;justify-content:space-between;">
# #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)


# # # ── MCQ result card ───────────────────────────────────────────────────────────

# # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# #     status = response["status"]
# #     score = response["total_score"]
# #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #     color = status_colors.get(status, "#A78BFA")
# #     icon = status_icons.get(status, "•")

# #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# #     # Safely escape feedback strings to prevent HTML injection
# #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# #     st.markdown(f"""
# #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# #         <div style="text-align: center; padding: 1rem 0;">
# #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# #         </div>
# #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     adherence_status = response.get("adherence_status", "")
# #     side_effects_raw = response.get("side_effects", "[]")
# #     try:
# #         side_effects = json.loads(side_effects_raw)
# #     except Exception:
# #         side_effects = []

# #     col1, col2 = st.columns(2)
# #     with col1:
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">💊 Medication Adherence</div>
# #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #     with col2:
# #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">⚠️ Side Effects</div>
# #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     if show_history and patient_id:
# #         st.markdown(
# #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# #             unsafe_allow_html=True
# #         )


# # # ── Alert firing logic ────────────────────────────────────────────────────────

# # def _render_worsening_warning(patient_id: str, patient: dict, doctor_id: str, consecutive_n: int = 2, context: str = "tab"):
# #     """
# #     Worsening Trend Early Warning banner.

# #     Shown on the Daily Health Check tab immediately after MCQ submission
# #     (and on every subsequent visit while the trend persists).  It does NOT
# #     book an appointment automatically — it offers the patient a clearly
# #     labelled 'Book Appointment' button.  Only when the patient clicks that
# #     button does the UI fetch real available slots and confirm the booking.

# #     Session-state keys used (all scoped to patient_id):
# #         worsening_booking_step_{pid}   : None | 'select' | 'confirm'
# #         worsening_booking_slots_{pid}  : list[dict]  — raw slot rows
# #         worsening_booking_doctor_{pid} : dict        — chosen doctor row
# #         worsening_booking_slot_{pid}   : dict        — chosen slot row
# #     """
# #     # ── Debug: always show last 3 MCQ statuses so you can verify DB state ────
# #     from data.database import get_mcq_responses as _gmr
# #     _recent = _gmr(patient_id, limit=3)
# #     _statuses = [r["status"] for r in _recent]
# #     _is_worsening = check_consecutive_worsening(patient_id, consecutive_n)
# #     st.caption(
# #         f"🔍 Debug — last {len(_statuses)} MCQ statuses: {_statuses} | "
# #         f"consecutive_worsening({consecutive_n}) → **{_is_worsening}**"
# #     )

# #     # ── Guard: only render when consecutive worsening detected ───────────────
# #     if not check_consecutive_worsening(patient_id, consecutive_n):
# #         # If the warning was previously shown, clean up stale state gracefully
# #         for sfx in ("step", "slots", "doctor", "slot"):
# #             st.session_state.pop(f"worsening_booking_{sfx}_{patient_id}_{context}", None)
# #         return

# #     step_key   = f"worsening_booking_step_{patient_id}_{context}"
# #     slots_key  = f"worsening_booking_slots_{patient_id}_{context}"
# #     doctor_key = f"worsening_booking_doctor_{patient_id}_{context}"
# #     slot_key   = f"worsening_booking_slot_{patient_id}_{context}"

# #     step = st.session_state.get(step_key)  # None | 'select' | 'confirm'

# #     # ── Main warning banner ───────────────────────────────────────────────────
# #     st.markdown(f"""
# #     <div class="card" style="border-left:4px solid #F87171;
# #          background:rgba(248,113,113,0.08);margin-bottom:1rem;">
# #         <div style="display:flex;align-items:flex-start;gap:0.9rem;">
# #             <span style="font-size:2rem;line-height:1;">🚨</span>
# #             <div>
# #                 <div style="font-weight:700;color:#F87171;font-size:1.05rem;margin-bottom:0.3rem;">
# #                     Worsening Trend Detected
# #                 </div>
# #                 <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;">
# #                     Your last <strong style="color:#F87171;">{consecutive_n} health check-ins</strong>
# #                     have both shown a <em>Worsening</em> status.
# #                     Your doctor has been notified via an alert.
# #                     We recommend booking a consultation soon.
# #                 </div>
# #             </div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # ── Step 0: Offer the booking button (no auto-booking) ───────────────────
# #     if step is None:
# #         if st.button(
# #             "📅 Book an Appointment with My Doctor",
# #             key=f"worsening_book_btn_{patient_id}_{context}",
# #             type="primary",
# #         ):
# #             # Fetch available slots now (lazy — only on click)
# #             doctors = get_available_opd_doctors()
# #             # Filter to the patient's own doctor first; fall back to all
# #             my_doctor_id = patient.get("doctor_id")
# #             my_doctors = [d for d in doctors if d["doctor_id"] == my_doctor_id] or doctors

# #             all_slots = []
# #             for doc in my_doctors:
# #                 dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
# #                 for d in dates[:3]:  # look at next 3 available dates only
# #                     slots = get_available_opd_slots(doc["doctor_id"], d)
# #                     for s in slots:
# #                         all_slots.append({**s, "doctor_name": doc["name"],
# #                                            "doctor_id": doc["doctor_id"]})

# #             if not all_slots:
# #                 st.warning(
# #                     "⚠️ No available OPD slots found right now. "
# #                     "Please contact the clinic directly or check back later."
# #                 )
# #                 return

# #             st.session_state[slots_key] = all_slots
# #             st.session_state[step_key]  = "select"
# #             st.rerun()
# #         return  # nothing more to render at step 0

# #     # ── Step 1: Slot selector ─────────────────────────────────────────────────
# #     if step == "select":
# #         all_slots = st.session_state.get(slots_key, [])
# #         if not all_slots:
# #             st.warning("No slots loaded. Please try again.")
# #             st.session_state.pop(step_key, None)
# #             return

# #         st.markdown(
# #             "<div style='color:var(--text-secondary);font-size:0.88rem;"
# #             "margin-bottom:0.6rem;'>Select an available slot:</div>",
# #             unsafe_allow_html=True,
# #         )

# #         # Build human-readable labels
# #         slot_labels = [
# #             f"Dr. {s['doctor_name']} — {s['slot_date']}  {s['start_time']}–{s['end_time']}"
# #             for s in all_slots
# #         ]
# #         chosen_idx = st.selectbox(
# #             "Available slots",
# #             options=range(len(slot_labels)),
# #             format_func=lambda i: slot_labels[i],
# #             key=f"worsening_slot_select_{patient_id}_{context}",
# #             label_visibility="collapsed",
# #         )

# #         col_ok, col_cancel = st.columns([2, 1])
# #         with col_ok:
# #             if st.button(
# #                 "Confirm this slot →",
# #                 key=f"worsening_confirm_btn_{patient_id}_{context}",
# #                 type="primary",
# #                 use_container_width=True,
# #             ):
# #                 chosen = all_slots[chosen_idx]
# #                 st.session_state[slot_key]   = chosen
# #                 st.session_state[doctor_key] = {"name": chosen["doctor_name"],
# #                                                  "id":   chosen["doctor_id"]}
# #                 st.session_state[step_key]   = "confirm"
# #                 st.rerun()
# #         with col_cancel:
# #             if st.button(
# #                 "Cancel",
# #                 key=f"worsening_cancel_select_{patient_id}_{context}",
# #                 use_container_width=True,
# #             ):
# #                 for k in (step_key, slots_key, doctor_key, slot_key):
# #                     st.session_state.pop(k, None)
# #                 st.rerun()
# #         return

# #     # ── Step 2: Final confirmation ────────────────────────────────────────────
# #     if step == "confirm":
# #         chosen_slot   = st.session_state.get(slot_key, {})
# #         chosen_doctor = st.session_state.get(doctor_key, {})

# #         st.markdown(f"""
# #         <div class="card" style="border:1px solid rgba(167,139,250,0.4);
# #              background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
# #             <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
# #                 📋 Confirm Booking
# #             </div>
# #             <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.8;">
# #                 <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
# #                 <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
# #                 <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         col_yes, col_no = st.columns(2)
# #         with col_yes:
# #             if st.button(
# #                 "✅ Book Appointment",
# #                 key=f"worsening_book_yes_{patient_id}_{context}",
# #                 type="primary",
# #                 use_container_width=True,
# #             ):
# #                 success = book_opd_slot(
# #                     slot_id=chosen_slot["id"],
# #                     patient_id=patient_id,
# #                     patient_name=patient.get("name", ""),
# #                 )
# #                 # Clean up state regardless of outcome
# #                 for k in (step_key, slots_key, doctor_key, slot_key):
# #                     st.session_state.pop(k, None)
# #                 _cached_opd_bookings.clear()

# #                 if success:
# #                     # Upgrade the doctor-side alert to note the booking
# #                     create_alert(
# #                         patient_id=patient_id,
# #                         alert_type="worsening_opd_booked",
# #                         message=(
# #                             f"Patient self-booked an OPD slot in response to worsening trend alert.\n"
# #                             f"Slot: Dr. {chosen_doctor.get('name','')} on "
# #                             f"{chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
# #                         ),
# #                         severity="medium",
# #                         doctor_id=doctor_id,
# #                     )
# #                     st.success(
# #                         f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
# #                         f"on {chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
# #                     )
# #                 else:
# #                     st.error(
# #                         "❌ That slot was just taken by someone else. "
# #                         "Please go to the Online OPD tab to pick another slot."
# #                     )
# #                 st.rerun()

# #         with col_no:
# #             if st.button(
# #                 "← Back",
# #                 key=f"worsening_book_back_{patient_id}_{context}",
# #                 use_container_width=True,
# #             ):
# #                 st.session_state[step_key] = "select"
# #                 st.rerun()


# # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# #     """Fire structured doctor alerts based on MCQ response."""
# #     trigger = False
# #     reasons = []

# #     if total_score < 0:
# #         trigger = True
# #         reasons.append("negative_score")

# #     if check_consecutive_worsening(patient_id, 2):
# #         trigger = True
# #         reasons.append("consecutive_worsening")

# #     if side_effects:
# #         trigger = True
# #         reasons.append("side_effects")

# #     if not trigger:
# #         return

# #     action_map = {
# #         "Improving": "Continue medication as prescribed",
# #         "Stable": "Monitor closely, follow up in 2-3 days",
# #         "Worsening": "Immediate consultation required"
# #     }

# #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# #     alert_message = f"""Patient ID: {patient_id}
# # Doctor ID: {doctor_id}
# # Disease: {patient.get('disease', 'N/A')}
# # Current Status: {status}
# # Score: {total_score:+d}

# # Key Symptoms Reported:
# # {symptoms_text}

# # Medication Adherence:
# # {adherence_text}

# # Side Effects:
# # {side_effects_text}

# # Recommended Action:
# # - {action_map.get(status, 'Monitor patient')}

# # Triggered By: {reasons_text}"""

# #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# #     create_alert(
# #         patient_id=patient_id,
# #         alert_type="mcq_health_check",
# #         message=alert_message,
# #         severity=severity,
# #         doctor_id=doctor_id
# #     )




# # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # def _render_patient_opd(patient_id: str, patient: dict):
# #     """Full Online OPD booking UI for the patient dashboard."""
# #     import streamlit as st
# #     from datetime import date, datetime

# #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# #         'Slots are real-time — once booked they disappear for other patients.</p>',
# #         unsafe_allow_html=True
# #     )

# #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# #     with opd_subtabs[0]:
# #         doctors = _cached_opd_doctors()

# #         if not doctors:
# #             st.info("No doctors have published OPD slots yet. Please check back later.")
# #         else:
# #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# #             selected_doctor_id = doctor_options[selected_label]

# #             available_dates = _cached_opd_dates(selected_doctor_id)
# #             if not available_dates:
# #                 st.warning("This doctor has no available slots right now.")
# #             else:
# #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# #                 chosen_date_str = st.selectbox(
# #                     "Select Date",
# #                     list(date_labels.keys()),
# #                     format_func=lambda x: date_labels[x],
# #                     key="opd_date_sel"
# #                 )

# #                 # Check if patient already booked on this day with this doctor
# #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# #                 if already_booked:
# #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# #                 else:
# #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# #                     if not free_slots:
# #                         st.error("All slots for this date are fully booked. Please choose another date.")
# #                     else:
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# #                                 </div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         slot_options = {
# #                             f"{s['start_time']} – {s['end_time']}": s['id']
# #                             for s in free_slots
# #                         }
# #                         chosen_slot_label = st.selectbox(
# #                             "Choose a time slot",
# #                             list(slot_options.keys()),
# #                             key="opd_slot_sel"
# #                         )
# #                         chosen_slot_id = slot_options[chosen_slot_label]

# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                                 <strong>Doctor:</strong> {selected_label}<br>
# #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# #                             if success:
# #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# #                                 st.balloons()
# #                                 _cached_opd_bookings.clear()
# #                                 _cached_opd_slots.clear()
# #                                 _cached_has_booking.clear()
# #                                 st.rerun()
# #                             else:
# #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# #                                 _cached_opd_slots.clear()
# #                                 st.rerun()

# #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# #     with opd_subtabs[1]:
# #         st.markdown("#### 🗓️ Your OPD Bookings")
# #         my_bookings = _cached_opd_bookings(patient_id)

# #         if not my_bookings:
# #             st.markdown("""
# #             <div class="card" style="text-align:center;padding:2rem;">
# #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# #             </div>
# #             """, unsafe_allow_html=True)
# #         else:
# #             today_str = date.today().isoformat()
# #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# #             if upcoming:
# #                 st.markdown("##### 📅 Upcoming")
# #                 for booking in upcoming:
# #                     visited = bool(booking["patient_visited"])
# #                     color = "#34D399" if visited else "#A78BFA"
# #                     status = "✅ Consulted" if visited else "⏳ Pending"
# #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# #                     room_name = f"MediCore-{safe_room}"

# #                     col_b, col_c = st.columns([4, 1])
# #                     with col_b:
# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# #                                 <div>
# #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# #                                     </div>
# #                                 </div>
# #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)
# #                     with col_c:
# #                         if not visited:
# #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# #                                 success = cancel_opd_booking(booking["id"], patient_id)
# #                                 if success:
# #                                     st.success("Booking cancelled.")
# #                                     _cached_opd_bookings.clear()
# #                                     _cached_opd_slots.clear()
# #                                     _cached_has_booking.clear()
# #                                     st.rerun()

# #                     # ── Embedded video call (Jitsi) ───────────────────────────
# #                     if not visited:
# #                         call_key = f"show_call_pat_{booking['id']}"
# #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# #                                      use_container_width=True, type="primary"):
# #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# #                         if st.session_state.get(call_key, False):
# #                             patient_name = st.session_state.get("patient_id", "Patient")
# #                             encoded_name = str(patient_name).replace(" ", "%20")
# #                             st.components.v1.html(f"""
# #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# #                             <iframe
# #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# #                                 allowfullscreen="true"
# #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# #                             ></iframe>
# #                             </body></html>
# #                             """, height=560)

# #             if past:
# #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# #                     for booking in past:
# #                         visited = bool(booking["patient_visited"])
# #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# #                         status = "✅ Consulted" if visited else "❌ Not attended"
# #                         color = "#34D399" if visited else "#F87171"
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# #                             <div style="display:flex;justify-content:space-between;">
# #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# # # ── Patient login ─────────────────────────────────────────────────────────────

# # def render_patient_login():
# #     st.markdown("""
# #     <div style="max-width: 480px; margin: 4rem auto;">
# #         <div class="page-header" style="text-align: center;">
# #             <h1>🏥 Patient Login</h1>
# #             <p>Enter your Patient ID to access your health portal</p>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     with st.container():
# #         col1, col2, col3 = st.columns([1, 2, 1])
# #         with col2:
# #             patient_id = st.text_input(
# #                 "Patient ID",
# #                 placeholder="e.g. PAT-20260413-0001",
# #                 label_visibility="collapsed"
# #             )
# #             st.markdown(
# #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# #                 'Your ID was provided by your doctor at registration</p>',
# #                 unsafe_allow_html=True
# #             )

# #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# #                 if patient_id:
# #                     patient = get_patient(patient_id.strip().upper())
# #                     if patient:
# #                         st.session_state["patient_id"] = patient_id.strip().upper()
# #                         st.session_state["patient_logged_in"] = True
# #                         st.rerun()
# #                     else:
# #                         st.error("Patient ID not found. Check with your doctor.")
# #                 else:
# #                     st.warning("Please enter your Patient ID.")




# # import streamlit as st
# # import json
# # import requests
# # from datetime import date, datetime
# # from data.database import (
# #     get_patient, get_patient_prescriptions, get_chat_history,
# #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# #     create_alert, check_consecutive_worsening, get_patient_alerts,
# #     resolve_alert,
# #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# #     get_patient_opd_bookings, check_patient_has_booking
# # )
# # from agents.orchestrator import AgentOrchestrator
# # from agents.scheduling_agent import (
# #     SchedulingAgent, get_auth_url,
# #     exchange_code_for_tokens, refresh_access_token
# # )
# # from agents.mcq_agent import MCQAgent


# # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_chat_history(patient_id, limit=20):
# #     return get_chat_history(patient_id, limit)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_prescriptions(patient_id):
# #     return get_patient_prescriptions(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_patient_alerts(patient_id):
# #     return get_patient_alerts(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_opd_bookings(patient_id):
# #     return get_patient_opd_bookings(patient_id)

# # @st.cache_data(ttl=20, show_spinner=False)
# # def _cached_mcq_response_today(patient_id, today_str):
# #     return get_mcq_response_for_date(patient_id, today_str)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_mcq_responses(patient_id, limit=30):
# #     return get_mcq_responses(patient_id, limit)

# # @st.cache_data(ttl=60, show_spinner=False)
# # def _cached_opd_doctors():
# #     return get_available_opd_doctors()

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_opd_dates(doctor_id):
# #     return get_available_opd_dates_for_doctor(doctor_id)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_opd_slots(doctor_id, date_str):
# #     return get_available_opd_slots(doctor_id, date_str)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_has_booking(patient_id, doctor_id, date_str):
# #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # def _handle_google_oauth_callback():
# #     """
# #     Called once at the top of app.py.
# #     If Google redirected back with ?code=..., exchange it for tokens,
# #     set mode=patient, and mark patient_google_authed=True.
# #     Only removes OAuth-specific params, preserving the _s session-restore param.
# #     """
# #     params = st.query_params
# #     auth_code = params.get("code")
# #     if auth_code and not st.session_state.get("google_access_token"):
# #         try:
# #             tokens = exchange_code_for_tokens(auth_code)
# #             if "access_token" in tokens:
# #                 st.session_state["google_access_token"] = tokens["access_token"]
# #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# #                 st.session_state["patient_google_authed"] = True
# #                 st.session_state["mode"] = "patient"
# #                 st.toast("✅ Google sign-in successful!", icon="✅")
# #         except Exception as e:
# #             st.warning(f"Google OAuth error: {e}")
# #         # Remove only OAuth-specific params, preserving _s session param
# #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# #             try:
# #                 if oauth_key in st.query_params:
# #                     del st.query_params[oauth_key]
# #             except Exception:
# #                 pass


# # def _get_valid_access_token() -> str | None:
# #     """Return a valid Google access token from session, refreshing if needed."""
# #     token = st.session_state.get("google_access_token")
# #     if token:
# #         return token
# #     refresh_tok = st.session_state.get("google_refresh_token")
# #     if refresh_tok:
# #         new_token = refresh_access_token(refresh_tok)
# #         if new_token:
# #             st.session_state["google_access_token"] = new_token
# #             return new_token
# #     return None


# # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # @st.cache_resource(show_spinner=False)
# # def _get_orchestrator():
# #     return AgentOrchestrator()

# # @st.cache_resource(show_spinner=False)
# # def _get_scheduler():
# #     return SchedulingAgent()

# # @st.cache_resource(show_spinner=False)
# # def _get_mcq_agent():
# #     return MCQAgent()

# # @st.cache_data(ttl=120, show_spinner=False)
# # def _cached_patient_login(patient_id):
# #     """Run the expensive on_patient_login only once per 2 minutes."""
# #     return _get_orchestrator().on_patient_login(patient_id)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_get_patient(patient_id):
# #     return get_patient(patient_id)


# # # ── Main dashboard ────────────────────────────────────────────────────────────

# # def render_patient_dashboard(patient_id):
# #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# #     orchestrator = _get_orchestrator()
# #     scheduler = _get_scheduler()
# #     mcq_agent = _get_mcq_agent()
# #     patient = _cached_get_patient(patient_id)

# #     if not patient:
# #         st.error("Patient not found. Check your Patient ID.")
# #         return

# #     st.markdown(f"""
# #     <div class="page-header">
# #         <h1>🧑‍⚕️ Patient Portal</h1>
# #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# #     _health_key = f"health_data_{patient_id}"
# #     if _health_key not in st.session_state:
# #         with st.spinner("Loading your health data..."):
# #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# #     health_data = st.session_state[_health_key]

# #     risk = health_data.get("risk", {})
# #     adherence = health_data.get("adherence", {})
# #     trends = health_data.get("trends", {})

# #     col1, col2, col3, col4 = st.columns(4)
# #     risk_level = risk.get("level", "low")
# #     col1.metric("Risk Level", risk_level.upper())
# #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD, Proactive Agent
# #     tabs = st.tabs([
# #         "💬 AI Assistant",
# #         "📅 My Schedule",
# #         "💊 My Prescriptions",
# #         "🩺 Daily Health Check",
# #         "🔔 Alerts",
# #         "🖥️ Online OPD",
# #         "🤖 My Health Agent",
# #     ])

# #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# #     with tabs[0]:
# #         st.markdown("### 🤖 Autonomous AI Health Agent")
# #         st.markdown(
# #             '<p style="color: var(--text-secondary);">'
# #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# #             '</p>',
# #             unsafe_allow_html=True
# #         )

# #         # ── Quick action chips ─────────────────────────────────────────────
# #         st.markdown("""
# #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# #                          cursor:pointer;">📅 Book Appointment</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          💊 My Prescriptions</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🩺 Check Symptoms</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🔔 My Alerts</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          ❌ Cancel Appointment</span>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         history = _cached_chat_history(patient_id, 20)
# #         for msg in history:
# #             with st.chat_message(msg["role"]):
# #                 st.markdown(msg["content"])

# #         # ── Triage action buttons ─────────────────────────────────────────
# #         _triage_key = f"pending_triage_{patient_id}"
# #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# #         _confirm_key = f"triage_confirm_{patient_id}"

# #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# #             triage_level = st.session_state[_triage_key]
# #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# #             if triage_level == "URGENT":
# #                 btn_label = "🚨 Alert My Doctor Now"
# #                 btn_type = "primary"
# #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# #             else:
# #                 btn_label = "📅 Book Urgent Appointment"
# #                 btn_type = "secondary"
# #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# #             if not st.session_state.get(_confirm_key):
# #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# #                     st.session_state[_confirm_key] = True
# #                     st.rerun()
# #             else:
# #                 st.warning(confirm_msg)
# #                 col_yes, col_no = st.columns(2)
# #                 with col_yes:
# #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# #                         severity = "high" if triage_level == "URGENT" else "medium"
# #                         alert_message = (
# #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# #                             f"Patient described: \"{symptom_text}\"\n"
# #                             f"AI Triage Verdict: {triage_level}\n"
# #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# #                                else "📅 Patient requests a follow-up appointment.")
# #                         )
# #                         _pt = get_patient(patient_id)
# #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# #                         create_alert(
# #                             patient_id=patient_id,
# #                             alert_type="patient_reported_symptoms",
# #                             message=alert_message,
# #                             severity=severity,
# #                             doctor_id=_doctor_id
# #                         )
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# #                                    else "✅ Alert sent to your doctor!")
# #                         st.rerun()
# #                 with col_no:
# #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.rerun()

# #         # ── Action result display (non-triage confirmations) ──────────────
# #         _action_result_key = f"action_result_{patient_id}"
# #         if st.session_state.get(_action_result_key):
# #             ar = st.session_state[_action_result_key]
# #             action = ar.get("action", "")
# #             confirmed = ar.get("confirmed", False)
# #             success = ar.get("success", False)

# #             if confirmed and success:
# #                 if action == "book_appointment":
# #                     bd = ar.get("booking_details", {})
# #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# #                 elif action == "cancel_appointment":
# #                     st.success("✅ Appointment successfully cancelled.")

# #             st.session_state.pop(_action_result_key, None)

# #         # ── Chat input ────────────────────────────────────────────────────
# #         placeholder = (
# #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# #             "or 'Show my prescriptions' or 'I have chest pain'..."
# #         )
# #         if prompt := st.chat_input(placeholder):
# #             with st.chat_message("user"):
# #                 st.markdown(prompt)

# #             with st.chat_message("assistant"):
# #                 with st.spinner("🤖 Analysing and acting..."):
# #                     result = orchestrator.on_patient_message(
# #                         patient_id, prompt,
# #                         use_agentic=True,
# #                         session_state=st.session_state
# #                     )

# #                 if not isinstance(result, dict):
# #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# #                 reply = result.get("reply", "")
# #                 triage = result.get("triage")
# #                 action = result.get("action", "")
# #                 confirmed = result.get("confirmed", False)
# #                 success = result.get("success", False)

# #                 # ── Show triage badge ──────────────────────────────────
# #                 if triage == "URGENT":
# #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# #                 elif triage == "MODERATE":
# #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# #                 elif triage == "MILD":
# #                     st.success("🟢 **MILD — Manageable at home for now.**")

# #                 # ── Show action confirmation badge ────────────────────
# #                 if confirmed and success:
# #                     if action == "book_appointment":
# #                         bd = result.get("booking_details", {})
# #                         st.success(
# #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# #                         )
# #                     elif action == "cancel_appointment":
# #                         st.success("✅ **Appointment Cancelled Successfully**")

# #                 st.markdown(reply)

# #             # ── Post-response state management ────────────────────────
# #             if triage in ("URGENT", "MODERATE"):
# #                 st.session_state[_triage_key] = triage
# #                 st.session_state[_triage_msg_key] = prompt
# #                 st.session_state.pop(_confirm_key, None)
# #             else:
# #                 st.session_state.pop(_triage_key, None)
# #                 st.session_state.pop(_triage_msg_key, None)
# #                 st.session_state.pop(_confirm_key, None)

# #             _cached_chat_history.clear()
# #             st.rerun()

# #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# #     with tabs[1]:
# #         st.markdown("### 📅 Medication Schedule")
# #         col1, col2 = st.columns([3, 1])

# #         with col2:
# #             access_token = _get_valid_access_token()

# #             if access_token:
# #                 # Token available — show sync button
# #                 if st.button("📆 Sync to Google Calendar"):
# #                     with st.spinner("Syncing to calendar..."):
# #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# #                     if result["success"]:
# #                         st.success(result["message"])
# #                     else:
# #                         st.warning(result.get("message", "Sync failed."))
# #                         if result.get("errors"):
# #                             for e in result["errors"]:
# #                                 st.caption(f"⚠ {e}")
# #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# #                     st.session_state.pop("google_access_token", None)
# #                     st.session_state.pop("google_refresh_token", None)
# #                     st.rerun()
# #             else:
# #                 # No access token in session (e.g. user disconnected or session expired).
# #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# #                 st.markdown("""
# #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# #                         📅 Google Calendar Disconnected
# #                     </div>
# #                     <div style="color:#A89FC8;font-size:0.82rem;">
# #                         Your Google session token has expired. Click below to reconnect —
# #                         this uses the same Google account you signed in with.
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 try:
# #                     auth_url = get_auth_url()
# #                     st.markdown(f"""
# #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# #                         <div style="
# #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# #                             <svg width="16" height="16" viewBox="0 0 18 18">
# #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# #                             </svg>
# #                             Reconnect Google Calendar
# #                         </div>
# #                     </a>
# #                     """, unsafe_allow_html=True)
# #                 except Exception:
# #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# #         schedule = scheduler.get_schedule_preview(patient_id)
# #         if not schedule:
# #             st.info("No schedule available. Ask your doctor to create a prescription.")
# #         else:
# #             current_date = None
# #             for item in schedule:
# #                 if item["date"] != current_date:
# #                     current_date = item["date"]
# #                     st.markdown(f"**📅 {current_date}**")
# #                 st.markdown(f"""
# #                 <div class="schedule-item">
# #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# #     with tabs[2]:
# #         st.markdown("### 💊 My Prescriptions")
# #         prescriptions = _cached_prescriptions(patient_id)
# #         if not prescriptions:
# #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# #         else:
# #             for i, pr in enumerate(prescriptions):
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# #                 """, unsafe_allow_html=True)
# #                 for m in pr.get("medicines", []):
# #                     st.markdown(f"""
# #                     <div class="medicine-card">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# #                         </div>
# #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)
# #                 if pr.get("doctor_notes"):
# #                     st.markdown(
# #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# #                         unsafe_allow_html=True
# #                     )
# #                 st.markdown("</div>", unsafe_allow_html=True)

# #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# #     with tabs[3]:
# #         today_str = date.today().isoformat()
# #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# #         _mcq_show_form = True  # controls whether to show the question form

# #         if existing_response:
# #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# #                 st.session_state["retake_mcq"] = True
# #                 st.session_state["show_health_summary"] = False
# #                 # Clear cached questions so fresh ones load
# #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# #                 st.rerun()
# #             if not st.session_state.get("retake_mcq"):
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             prescriptions = _cached_prescriptions(patient_id)
# #             if not prescriptions:
# #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             # Cache questions per patient per day — no need to call GROQ on every rerun
# #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# #             if _q_key not in st.session_state:
# #                 with st.spinner("Loading your personalized health questions..."):
# #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# #             questions = st.session_state[_q_key]

# #             if not questions:
# #                 st.error("Could not generate questions. Please try again.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             st.markdown("""
# #             <div class="card" style="margin-bottom: 1.5rem;">
# #                 <div class="card-header">📋 Today's Health Questions</div>
# #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# #                 </p>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             selected_options = {}

# #             for q in questions:
# #                 qid = str(q["id"])
# #                 category_icons = {
# #                     "symptom": "🤒",
# #                     "adherence": "💊",
# #                     "side_effect": "⚠️",
# #                     "wellbeing": "💚"
# #                 }
# #                 icon = category_icons.get(q.get("category", ""), "❓")

# #                 st.markdown(f"""
# #                 <div class="card" style="margin-bottom: 1rem;">
# #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# #                     </div>
# #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# #                         {q['question']}
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 option_labels = [opt["text"] for opt in q["options"]]
# #                 choice = st.radio(
# #                     label=q["question"],
# #                     options=range(len(option_labels)),
# #                     format_func=lambda i, opts=option_labels: opts[i],
# #                     key=f"mcq_{qid}",
# #                     label_visibility="collapsed"
# #                 )
# #                 selected_options[qid] = choice
# #                 st.markdown("---")

# #             col_btn1, col_btn2 = st.columns([3, 1])
# #             with col_btn1:
# #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# #                     total_score = 0
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         try:
# #                             total_score += q["options"][idx]["score"]
# #                         except (IndexError, KeyError):
# #                             pass

# #                     status = mcq_agent.compute_status(total_score)
# #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# #                     responses_data = []
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         responses_data.append({
# #                             "question": q["question"],
# #                             "category": q.get("category"),
# #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# #                         })

# #                     doctor_id = patient.get("doctor_id")
# #                     save_mcq_response(
# #                         patient_id=patient_id,
# #                         doctor_id=doctor_id,
# #                         date_str=today_str,
# #                         responses_json=json.dumps(responses_data),
# #                         total_score=total_score,
# #                         status=status,
# #                         side_effects=json.dumps(side_effects),
# #                         adherence_status=adherence_status
# #                     )

# #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# #                                            symptoms, adherence_status, side_effects)

# #                     st.session_state["retake_mcq"] = False
# #                     st.session_state["show_health_summary"] = True
# #                     # Invalidate cached data so next render is fresh
# #                     _cached_patient_login.clear()
# #                     _cached_mcq_response_today.clear()
# #                     _cached_mcq_responses.clear()
# #                     st.session_state.pop(f"health_data_{patient_id}", None)
# #                     st.rerun()

# #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# #         # Show automatically after submission OR when today's response already exists
# #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# #         if _show_summary:
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             st.markdown("### 📊 Your Health Summary")

# #             # ── AI Health Report ──────────────────────────────────────────────
# #             col_ai1, col_ai2 = st.columns([4, 1])
# #             with col_ai2:
# #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# #             if _gen_report or st.session_state.get("show_health_summary"):
# #                 # Cache summary per patient per day - expensive GROQ call
# #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# #                 if _gen_report or _sum_key not in st.session_state:
# #                     with st.spinner("AI is analyzing your health data..."):
# #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# #                 summary = st.session_state[_sum_key]
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# #                     <p style="line-height: 1.7;">{summary}</p>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #             # ── Health Indicators ─────────────────────────────────────────────
# #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# #             st.markdown(f"""
# #             <div class="card">
# #                 <div class="card-header">Health Indicators</div>
# #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# #                     </div>
# #                 </div>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             # ── Health Trend Chart ────────────────────────────────────────────
# #             responses = _cached_mcq_responses(patient_id, limit=30)
# #             if responses:
# #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# #                 import pandas as pd
# #                 import plotly.graph_objects as go

# #                 chart_responses = list(reversed(responses))
# #                 dates  = [r["date"] for r in chart_responses]
# #                 scores = [r["total_score"] for r in chart_responses]
# #                 statuses = [r["status"] for r in chart_responses]

# #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# #                 fig = go.Figure()
# #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[max(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[min(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=scores,
# #                     mode="lines+markers",
# #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# #                     marker=dict(size=10, color=marker_colors,
# #                                 line=dict(color="#1a1a2e", width=2)),
# #                     name="Health Score",
# #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# #                 ))

# #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                 for d, s, st_ in zip(dates, scores, statuses):
# #                     fig.add_annotation(
# #                         x=d, y=s,
# #                         text=status_icons_map.get(st_, ""),
# #                         showarrow=False,
# #                         yshift=18, font=dict(size=13)
# #                     )

# #                 fig.update_layout(
# #                     paper_bgcolor="rgba(0,0,0,0)",
# #                     plot_bgcolor="rgba(0,0,0,0)",
# #                     font=dict(color="#A89FC8", size=12),
# #                     margin=dict(l=10, r=10, t=10, b=10),
# #                     height=300,
# #                     xaxis=dict(
# #                         showgrid=False, zeroline=False,
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title=""
# #                     ),
# #                     yaxis=dict(
# #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title="Score"
# #                     ),
# #                     hoverlabel=dict(
# #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# #                         font=dict(color="white", size=13)
# #                     ),
# #                     showlegend=False
# #                 )

# #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# #                 st.markdown("""
# #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 # ── Recent Check-in History ───────────────────────────────────
# #                 st.markdown("#### 📋 Recent Daily Check-in History")
# #                 for r in responses:
# #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                     color = status_colors.get(r["status"], "#A78BFA")
# #                     icon = status_icons.get(r["status"], "•")
# #                     st.markdown(f"""
# #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# #                         </div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# #                             Adherence: {r.get('adherence_status', 'N/A')}
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)

# #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# #     with tabs[4]:
# #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# #     with tabs[5]:
# #         _render_patient_opd(patient_id, patient)

# #     # ── Tab 6: Proactive AI Health Agent ──────────────────────────────────────
# #     with tabs[6]:
# #         _render_proactive_agent_tab(patient_id, patient, risk, adherence, trends)


# # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# #     """Render the patient-facing Alerts & Notifications tab."""
# #     st.markdown("### 🔔 Alerts & Notifications")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# #         'and doctor messages are shown here.</p>',
# #         unsafe_allow_html=True
# #     )

# #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# #     if risk_level == "high":
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">🚨</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# #                         Please contact your doctor or visit the clinic immediately.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# #     missed_dose_dates = []
# #     for r in recent_responses:
# #         adh = (r.get("adherence_status") or "").lower()
# #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# #             missed_dose_dates.append(r["date"])

# #     if missed_dose_dates:
# #         dates_str = ", ".join(missed_dose_dates[:3])
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">💊</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# #                         Consistent adherence is key to recovery — please take medications as prescribed.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# #     all_alerts = _cached_patient_alerts(patient_id)
# #     unresolved = [a for a in all_alerts if not a["resolved"]]
# #     resolved = [a for a in all_alerts if a["resolved"]]

# #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# #         st.markdown("""
# #         <div class="card" style="text-align:center;padding:2rem;">
# #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# #                 No active alerts. Keep taking your medications and completing daily check-ins!
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #         return

# #     severity_config = {
# #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# #     }
# #     type_labels = {
# #         "mcq_health_check": "Health Check Alert",
# #         "doctor_message":   "Doctor Message",
# #         "missed_dose":      "Missed Dose",
# #         "high_risk":        "High Risk Warning",
# #     }

# #     if unresolved:
# #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# #         for alert in unresolved:
# #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #             created = alert["created_at"][:16].replace("T", " ")

# #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# #                 st.markdown(f"""
# #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# #                              border-left:3px solid {cfg['color']};">
# #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # {alert['message']}</pre>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# #                     resolve_alert(alert["id"])
# #                     _cached_patient_alerts.clear()
# #                     st.rerun()

# #     if resolved:
# #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# #             for alert in resolved:
# #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #                 created = alert["created_at"][:16].replace("T", " ")
# #                 st.markdown(f"""
# #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# #                     <div style="display:flex;justify-content:space-between;">
# #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)


# # # ── MCQ result card ───────────────────────────────────────────────────────────

# # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# #     status = response["status"]
# #     score = response["total_score"]
# #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #     color = status_colors.get(status, "#A78BFA")
# #     icon = status_icons.get(status, "•")

# #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# #     # Safely escape feedback strings to prevent HTML injection
# #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# #     st.markdown(f"""
# #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# #         <div style="text-align: center; padding: 1rem 0;">
# #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# #         </div>
# #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     adherence_status = response.get("adherence_status", "")
# #     side_effects_raw = response.get("side_effects", "[]")
# #     try:
# #         side_effects = json.loads(side_effects_raw)
# #     except Exception:
# #         side_effects = []

# #     col1, col2 = st.columns(2)
# #     with col1:
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">💊 Medication Adherence</div>
# #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #     with col2:
# #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">⚠️ Side Effects</div>
# #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     if show_history and patient_id:
# #         st.markdown(
# #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# #             unsafe_allow_html=True
# #         )


# # # ── Alert firing logic ────────────────────────────────────────────────────────

# # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# #     """Fire structured doctor alerts based on MCQ response."""
# #     trigger = False
# #     reasons = []

# #     if total_score < 0:
# #         trigger = True
# #         reasons.append("negative_score")

# #     if check_consecutive_worsening(patient_id, 2):
# #         trigger = True
# #         reasons.append("consecutive_worsening")

# #     if side_effects:
# #         trigger = True
# #         reasons.append("side_effects")

# #     if not trigger:
# #         return

# #     action_map = {
# #         "Improving": "Continue medication as prescribed",
# #         "Stable": "Monitor closely, follow up in 2-3 days",
# #         "Worsening": "Immediate consultation required"
# #     }

# #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# #     alert_message = f"""Patient ID: {patient_id}
# # Doctor ID: {doctor_id}
# # Disease: {patient.get('disease', 'N/A')}
# # Current Status: {status}
# # Score: {total_score:+d}

# # Key Symptoms Reported:
# # {symptoms_text}

# # Medication Adherence:
# # {adherence_text}

# # Side Effects:
# # {side_effects_text}

# # Recommended Action:
# # - {action_map.get(status, 'Monitor patient')}

# # Triggered By: {reasons_text}"""

# #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# #     create_alert(
# #         patient_id=patient_id,
# #         alert_type="mcq_health_check",
# #         message=alert_message,
# #         severity=severity,
# #         doctor_id=doctor_id
# #     )




# # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # def _render_patient_opd(patient_id: str, patient: dict):
# #     """Full Online OPD booking UI for the patient dashboard."""
# #     import streamlit as st
# #     from datetime import date, datetime

# #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# #         'Slots are real-time — once booked they disappear for other patients.</p>',
# #         unsafe_allow_html=True
# #     )

# #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# #     with opd_subtabs[0]:
# #         doctors = _cached_opd_doctors()

# #         if not doctors:
# #             st.info("No doctors have published OPD slots yet. Please check back later.")
# #         else:
# #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# #             selected_doctor_id = doctor_options[selected_label]

# #             available_dates = _cached_opd_dates(selected_doctor_id)
# #             if not available_dates:
# #                 st.warning("This doctor has no available slots right now.")
# #             else:
# #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# #                 chosen_date_str = st.selectbox(
# #                     "Select Date",
# #                     list(date_labels.keys()),
# #                     format_func=lambda x: date_labels[x],
# #                     key="opd_date_sel"
# #                 )

# #                 # Check if patient already booked on this day with this doctor
# #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# #                 if already_booked:
# #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# #                 else:
# #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# #                     if not free_slots:
# #                         st.error("All slots for this date are fully booked. Please choose another date.")
# #                     else:
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# #                                 </div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         slot_options = {
# #                             f"{s['start_time']} – {s['end_time']}": s['id']
# #                             for s in free_slots
# #                         }
# #                         chosen_slot_label = st.selectbox(
# #                             "Choose a time slot",
# #                             list(slot_options.keys()),
# #                             key="opd_slot_sel"
# #                         )
# #                         chosen_slot_id = slot_options[chosen_slot_label]

# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                                 <strong>Doctor:</strong> {selected_label}<br>
# #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# #                             if success:
# #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# #                                 st.balloons()
# #                                 _cached_opd_bookings.clear()
# #                                 _cached_opd_slots.clear()
# #                                 _cached_has_booking.clear()
# #                                 st.rerun()
# #                             else:
# #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# #                                 _cached_opd_slots.clear()
# #                                 st.rerun()

# #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# #     with opd_subtabs[1]:
# #         st.markdown("#### 🗓️ Your OPD Bookings")
# #         my_bookings = _cached_opd_bookings(patient_id)

# #         if not my_bookings:
# #             st.markdown("""
# #             <div class="card" style="text-align:center;padding:2rem;">
# #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# #             </div>
# #             """, unsafe_allow_html=True)
# #         else:
# #             today_str = date.today().isoformat()
# #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# #             if upcoming:
# #                 st.markdown("##### 📅 Upcoming")
# #                 for booking in upcoming:
# #                     visited = bool(booking["patient_visited"])
# #                     color = "#34D399" if visited else "#A78BFA"
# #                     status = "✅ Consulted" if visited else "⏳ Pending"
# #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# #                     room_name = f"MediCore-{safe_room}"

# #                     col_b, col_c = st.columns([4, 1])
# #                     with col_b:
# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# #                                 <div>
# #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# #                                     </div>
# #                                 </div>
# #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)
# #                     with col_c:
# #                         if not visited:
# #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# #                                 success = cancel_opd_booking(booking["id"], patient_id)
# #                                 if success:
# #                                     st.success("Booking cancelled.")
# #                                     _cached_opd_bookings.clear()
# #                                     _cached_opd_slots.clear()
# #                                     _cached_has_booking.clear()
# #                                     st.rerun()

# #                     # ── Embedded video call (Jitsi) ───────────────────────────
# #                     if not visited:
# #                         call_key = f"show_call_pat_{booking['id']}"
# #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# #                                      use_container_width=True, type="primary"):
# #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# #                         if st.session_state.get(call_key, False):
# #                             patient_name = st.session_state.get("patient_id", "Patient")
# #                             encoded_name = str(patient_name).replace(" ", "%20")
# #                             st.components.v1.html(f"""
# #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# #                             <iframe
# #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# #                                 allowfullscreen="true"
# #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# #                             ></iframe>
# #                             </body></html>
# #                             """, height=560)

# #             if past:
# #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# #                     for booking in past:
# #                         visited = bool(booking["patient_visited"])
# #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# #                         status = "✅ Consulted" if visited else "❌ Not attended"
# #                         color = "#34D399" if visited else "#F87171"
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# #                             <div style="display:flex;justify-content:space-between;">
# #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# # # ── Patient login ─────────────────────────────────────────────────────────────

# # def render_patient_login():
# #     st.markdown("""
# #     <div style="max-width: 480px; margin: 4rem auto;">
# #         <div class="page-header" style="text-align: center;">
# #             <h1>🏥 Patient Login</h1>
# #             <p>Enter your Patient ID to access your health portal</p>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     with st.container():
# #         col1, col2, col3 = st.columns([1, 2, 1])
# #         with col2:
# #             patient_id = st.text_input(
# #                 "Patient ID",
# #                 placeholder="e.g. PAT-20260413-0001",
# #                 label_visibility="collapsed"
# #             )
# #             st.markdown(
# #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# #                 'Your ID was provided by your doctor at registration</p>',
# #                 unsafe_allow_html=True
# #             )

# #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# #                 if patient_id:
# #                     patient = get_patient(patient_id.strip().upper())
# #                     if patient:
# #                         st.session_state["patient_id"] = patient_id.strip().upper()
# #                         st.session_state["patient_logged_in"] = True
# #                         st.rerun()
# #                     else:
# #                         st.error("Patient ID not found. Check with your doctor.")
# #                 else:
# #                     st.warning("Please enter your Patient ID.")


# # # ══════════════════════════════════════════════════════════════════════════════
# # # PROACTIVE AI HEALTH AGENT TAB
# # # ══════════════════════════════════════════════════════════════════════════════

# # def _build_agent_context(patient_id: str, patient: dict, risk: dict,
# #                           adherence: dict, trends: dict) -> dict:
# #     """Gather all live signals needed for the briefing prompt."""
# #     from data.database import (
# #         get_mcq_responses, get_mcq_response_for_date,
# #         check_consecutive_worsening, get_patient_alerts,
# #         get_patient_opd_bookings, get_patient_prescriptions
# #     )

# #     today_str  = date.today().isoformat()
# #     mcq_rows   = get_mcq_responses(patient_id, limit=10)
# #     statuses   = [r["status"]      for r in mcq_rows][:5]
# #     scores     = [r["total_score"] for r in mcq_rows][:5]
# #     adherence_flags = [r.get("adherence_status", "") for r in mcq_rows[:7]]
# #     missed_dose = any(
# #         any(kw in (a or "").lower() for kw in ["miss", "skip", "forgot", "no"])
# #         for a in adherence_flags
# #     )
# #     checkin_done   = get_mcq_response_for_date(patient_id, today_str) is not None
# #     consec_worsening = check_consecutive_worsening(patient_id, 2)
# #     alerts         = get_patient_alerts(patient_id)
# #     unresolved_alerts = len([a for a in alerts if not a["resolved"]])
# #     bookings       = get_patient_opd_bookings(patient_id)
# #     upcoming_appt  = None
# #     for b in bookings:
# #         if b.get("slot_date", "") >= today_str:
# #             upcoming_appt = f"{b['slot_date']} at {b.get('start_time','')}"
# #             break
# #     prescriptions  = get_patient_prescriptions(patient_id)
# #     active_meds    = adherence.get("active_medications", 0)

# #     # Resolve doctor name from patient record (best-effort)
# #     doctor_name = patient.get("doctor_name") or patient.get("doctor_id", "your doctor")

# #     hour = datetime.now().hour
# #     if hour < 12:
# #         time_of_day = "morning"
# #     elif hour < 17:
# #         time_of_day = "afternoon"
# #     else:
# #         time_of_day = "evening"

# #     return {
# #         "name":              patient.get("name", ""),
# #         "age":               patient.get("age", ""),
# #         "disease":           patient.get("disease", ""),
# #         "doctor_name":       doctor_name,
# #         "statuses":          statuses,
# #         "scores":            scores,
# #         "checkin_done":      checkin_done,
# #         "consec_worsening":  consec_worsening,
# #         "missed_dose":       missed_dose,
# #         "active_meds":       active_meds,
# #         "risk_level":        risk.get("level", "low"),
# #         "risk_score":        risk.get("score", 0),
# #         "upcoming_appt":     upcoming_appt or "None",
# #         "unresolved_alerts": unresolved_alerts,
# #         "trend":             trends.get("trend", "stable"),
# #         "time_of_day":       time_of_day,
# #         "today":             today_str,
# #     }


# # def _call_groq_agent(ctx: dict) -> dict | None:
# #     """Call Groq with the briefing + cards prompt. Returns parsed JSON or None."""
# #     from core.config import GROQ_API_KEY, GROQ_MODEL

# #     if not GROQ_API_KEY:
# #         return None

# #     system_prompt = """You are a proactive personal health agent for a medical app called MediCure.

# # Your job is to analyse a patient's health data and produce:
# # 1. A short personalised briefing (2-3 sentences max)
# # 2. A list of action cards the patient should act on today

# # Rules for the briefing:
# # - Address the patient by first name
# # - Be specific — mention actual trends, medication status, doctor name where relevant
# # - Be warm but direct — not clinical, not robotic
# # - Never say "based on your data" or "I have analysed" — just say it naturally
# # - Never use technical terms like "risk score", "MCQ", "consecutive worsening" — translate to plain language
# # - If everything is fine, say so clearly and encouragingly

# # Rules for action cards:
# # - Only include cards that are genuinely relevant right now — do not pad with generic advice
# # - Maximum 3 cards
# # - Each card must have a clear single action the patient can take
# # - Priority order: urgent health concern > missed medication > pending check-in > upcoming appointment > general wellness
# # - If nothing needs action, return an empty array

# # Respond ONLY with valid JSON in exactly this format, no extra text, no markdown fences:
# # {
# #   "briefing": "2 to 3 sentences",
# #   "cards": [
# #     {
# #       "priority": "high | medium | low",
# #       "icon": "single emoji",
# #       "title": "short title max 6 words",
# #       "message": "1-2 sentences explaining why this matters right now",
# #       "action_label": "label for the button max 4 words",
# #       "action_type": "book_appointment | complete_checkin | view_prescription | dismiss"
# #     }
# #   ]
# # }"""

# #     user_prompt = f"""Patient name: {ctx['name']}
# # Age: {ctx['age']}
# # Condition: {ctx['disease']}
# # Assigned doctor: Dr. {ctx['doctor_name']}

# # Last 5 check-in statuses (most recent first): {ctx['statuses']}
# # Last 5 check-in scores (most recent first): {ctx['scores']}
# # Today's check-in completed: {ctx['checkin_done']}
# # Health trending downward for 2+ sessions: {ctx['consec_worsening']}

# # Missed doses detected this week: {ctx['missed_dose']}
# # Active medications: {ctx['active_meds']}

# # Current health risk level: {ctx['risk_level']} (translate — do not say "risk level")
# # Overall trend: {ctx['trend']}

# # Upcoming appointment: {ctx['upcoming_appt']}
# # Unresolved health alerts: {ctx['unresolved_alerts']}

# # Today's date: {ctx['today']}
# # Time of day: {ctx['time_of_day']}"""

# #     try:
# #         resp = requests.post(
# #             "https://api.groq.com/openai/v1/chat/completions",
# #             headers={
# #                 "Authorization": f"Bearer {GROQ_API_KEY}",
# #                 "Content-Type":  "application/json",
# #             },
# #             json={
# #                 "model":       GROQ_MODEL,
# #                 "messages":    [
# #                     {"role": "system", "content": system_prompt},
# #                     {"role": "user",   "content": user_prompt},
# #                 ],
# #                 "max_tokens":  700,
# #                 "temperature": 0.4,
# #             },
# #             timeout=20,
# #         )
# #         raw = resp.json()["choices"][0]["message"]["content"].strip()
# #         # Strip accidental markdown fences
# #         raw = raw.replace("```json", "").replace("```", "").strip()
# #         return json.loads(raw)
# #     except Exception:
# #         return None


# # def _render_proactive_agent_tab(patient_id: str, patient: dict,
# #                                   risk: dict, adherence: dict, trends: dict):
# #     """Render the Proactive AI Health Agent tab."""

# #     st.markdown("### 🤖 My Health Agent")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);margin-top:-0.5rem;">'
# #         'Your personal AI agent monitors your health around the clock '
# #         'and tells you what matters today — before you have to ask.</p>',
# #         unsafe_allow_html=True,
# #     )
# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# #     # ── Cache key: regenerate once per patient per hour ───────────────────────
# #     cache_key   = f"proactive_agent_data_{patient_id}_{date.today().isoformat()}_{datetime.now().hour}"
# #     refresh_key = f"proactive_agent_refresh_{patient_id}"

# #     force_refresh = st.session_state.pop(refresh_key, False)

# #     if force_refresh or cache_key not in st.session_state:
# #         with st.spinner("🤖 Your health agent is reviewing your data..."):
# #             ctx    = _build_agent_context(patient_id, patient, risk, adherence, trends)
# #             result = _call_groq_agent(ctx)
# #             st.session_state[cache_key] = {"result": result, "ctx": ctx}

# #     cached     = st.session_state.get(cache_key, {})
# #     result     = cached.get("result")
# #     ctx        = cached.get("ctx", {})

# #     # ── Refresh button ────────────────────────────────────────────────────────
# #     col_title, col_refresh = st.columns([5, 1])
# #     with col_refresh:
# #         if st.button("🔄 Refresh", key=f"agent_refresh_{patient_id}",
# #                      use_container_width=True):
# #             # Clear all hourly cache keys for this patient
# #             for k in list(st.session_state.keys()):
# #                 if k.startswith(f"proactive_agent_data_{patient_id}"):
# #                     del st.session_state[k]
# #             st.session_state[refresh_key] = True
# #             st.rerun()

# #     # ── Fallback if Groq failed ───────────────────────────────────────────────
# #     if not result:
# #         st.warning(
# #             "⚠️ Your health agent could not connect right now. "
# #             "Please check your API key or try refreshing."
# #         )
# #         return

# #     # ── BRIEFING BANNER ───────────────────────────────────────────────────────
# #     briefing   = result.get("briefing", "")
# #     time_icon  = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}.get(
# #         ctx.get("time_of_day", "morning"), "🌅"
# #     )

# #     st.markdown(f"""
# #     <div class="card" style="border-left:4px solid #A78BFA;
# #          background:rgba(124,58,237,0.08);margin-bottom:1.5rem;padding:1.2rem 1.4rem;">
# #         <div style="display:flex;align-items:flex-start;gap:0.9rem;">
# #             <span style="font-size:2rem;line-height:1;">{time_icon}</span>
# #             <div>
# #                 <div style="font-weight:700;color:#A78BFA;font-size:0.78rem;
# #                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">
# #                     Agent Briefing
# #                 </div>
# #                 <div style="color:var(--text-primary);font-size:0.97rem;line-height:1.7;">
# #                     {briefing}
# #                 </div>
# #             </div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # ── AGENT ACTIVITY SUMMARY (what the agent already did) ──────────────────
# #     activity_lines = []
# #     if ctx.get("consec_worsening"):
# #         activity_lines.append("✅ Detected worsening health trend — doctor alert sent")
# #     if ctx.get("unresolved_alerts", 0) > 0:
# #         activity_lines.append(f"✅ {ctx['unresolved_alerts']} active alert(s) flagged for your doctor")
# #     if ctx.get("risk_level") == "high":
# #         activity_lines.append("✅ High risk status detected — escalated to doctor dashboard")
# #     activity_lines.append(f"✅ Risk assessment run — current level: {ctx.get('risk_level','low').upper()}")
# #     activity_lines.append(f"✅ Medication adherence checked — {ctx.get('active_meds', 0)} active medication(s)")

# #     items_html = "".join(
# #         f'<div style="font-size:0.83rem;color:var(--text-secondary);'
# #         f'padding:0.25rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
# #         f'{line}</div>'
# #         for line in activity_lines
# #     )
# #     st.markdown(f"""
# #     <div class="card" style="margin-bottom:1.5rem;">
# #         <div style="font-weight:600;color:var(--text-primary);font-size:0.88rem;
# #              margin-bottom:0.6rem;">🔍 What your agent did while you were away</div>
# #         {items_html}
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # ── ACTION CARDS ─────────────────────────────────────────────────────────
# #     cards = result.get("cards", [])

# #     if not cards:
# #         st.markdown("""
# #         <div class="card" style="text-align:center;padding:2rem;
# #              border-left:4px solid #34D399;background:rgba(52,211,153,0.06);">
# #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# #             <div style="font-weight:700;color:#34D399;font-size:1rem;">All Clear</div>
# #             <div style="color:var(--text-muted);font-size:0.88rem;margin-top:0.4rem;">
# #                 Your agent has reviewed everything. No actions needed right now.
# #                 Keep taking your medications and completing your daily check-ins.
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #     else:
# #         st.markdown(
# #             '<div style="font-weight:600;color:var(--text-primary);'
# #             'margin-bottom:0.8rem;">📋 Actions for you today</div>',
# #             unsafe_allow_html=True,
# #         )

# #         priority_colors = {
# #             "high":   {"border": "#F87171", "bg": "rgba(248,113,113,0.07)",
# #                        "badge_bg": "rgba(248,113,113,0.15)", "badge_text": "#F87171"},
# #             "medium": {"border": "#FBBF24", "bg": "rgba(251,191,36,0.07)",
# #                        "badge_bg": "rgba(251,191,36,0.15)", "badge_text": "#FBBF24"},
# #             "low":    {"border": "#34D399", "bg": "rgba(52,211,153,0.06)",
# #                        "badge_bg": "rgba(52,211,153,0.15)", "badge_text": "#34D399"},
# #         }

# #         for i, card in enumerate(cards[:3]):
# #             priority    = card.get("priority", "medium")
# #             cfg         = priority_colors.get(priority, priority_colors["medium"])
# #             icon        = card.get("icon", "💡")
# #             title       = card.get("title", "")
# #             message     = card.get("message", "")
# #             action_type = card.get("action_type", "dismiss")
# #             action_label= card.get("action_label", "Take Action")

# #             st.markdown(f"""
# #             <div class="card" style="border-left:4px solid {cfg['border']};
# #                  background:{cfg['bg']};margin-bottom:1rem;">
# #                 <div style="display:flex;align-items:flex-start;
# #                      justify-content:space-between;gap:0.8rem;">
# #                     <div style="display:flex;align-items:flex-start;gap:0.8rem;flex:1;">
# #                         <span style="font-size:1.6rem;line-height:1.2;">{icon}</span>
# #                         <div>
# #                             <div style="display:flex;align-items:center;gap:0.5rem;
# #                                  margin-bottom:0.3rem;">
# #                                 <span style="font-weight:700;color:var(--text-primary);
# #                                       font-size:0.97rem;">{title}</span>
# #                                 <span style="font-size:0.72rem;padding:1px 8px;
# #                                       border-radius:10px;font-weight:600;
# #                                       background:{cfg['badge_bg']};
# #                                       color:{cfg['badge_text']};">
# #                                     {priority.upper()}
# #                                 </span>
# #                             </div>
# #                             <div style="color:var(--text-secondary);font-size:0.85rem;
# #                                  line-height:1.6;">{message}</div>
# #                         </div>
# #                     </div>
# #                 </div>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             # ── Action button per card ────────────────────────────────────────
# #             _render_card_action(
# #                 patient_id=patient_id,
# #                 patient=patient,
# #                 action_type=action_type,
# #                 action_label=action_label,
# #                 card_index=i,
# #             )
# #             st.markdown("<div style='margin-bottom:0.5rem;'></div>",
# #                         unsafe_allow_html=True)

# #     # ── SLOT BOOKING FLOW (shown below cards when triggered) ─────────────────
# #     _render_agent_booking_flow(patient_id, patient)

# #     # ── LAST UPDATED footer ───────────────────────────────────────────────────
# #     st.markdown(
# #         f'<div style="color:var(--text-muted);font-size:0.75rem;'
# #         f'margin-top:1.5rem;text-align:right;">'
# #         f'Agent last updated: {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
# #         f'</div>',
# #         unsafe_allow_html=True,
# #     )


# # def _render_card_action(patient_id: str, patient: dict, action_type: str,
# #                          action_label: str, card_index: int):
# #     """Render the action button for a single card and handle its logic."""

# #     btn_key = f"agent_card_btn_{patient_id}_{card_index}"

# #     if action_type == "complete_checkin":
# #         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
# #             st.info("👉 Head to the **🩺 Daily Health Check** tab to complete today's check-in.")

# #     elif action_type == "view_prescription":
# #         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
# #             st.info("👉 Head to the **💊 My Prescriptions** tab to review your medications.")

# #     elif action_type == "book_appointment":
# #         book_trigger_key = f"agent_book_trigger_{patient_id}"
# #         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
# #             # Fetch available slots on click — never before
# #             doctors   = get_available_opd_doctors()
# #             my_doc_id = patient.get("doctor_id")
# #             my_docs   = [d for d in doctors if d["doctor_id"] == my_doc_id] or doctors

# #             all_slots = []
# #             for doc in my_docs:
# #                 dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
# #                 for d in dates[:3]:
# #                     slots = get_available_opd_slots(doc["doctor_id"], d)
# #                     for s in slots:
# #                         all_slots.append({
# #                             **s,
# #                             "doctor_name": doc["name"],
# #                             "doctor_id":   doc["doctor_id"],
# #                         })

# #             if not all_slots:
# #                 st.warning(
# #                     "⚠️ No available slots right now. "
# #                     "Please check the **🖥️ Online OPD** tab or contact the clinic."
# #                 )
# #             else:
# #                 st.session_state[f"agent_slots_{patient_id}"]       = all_slots
# #                 st.session_state[f"agent_booking_step_{patient_id}"] = "select"
# #                 st.rerun()

# #     elif action_type == "dismiss":
# #         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
# #             st.success("✅ Noted.")


# # def _render_agent_booking_flow(patient_id: str, patient: dict):
# #     """3-step booking flow triggered from an action card. Fully scoped to agent context."""

# #     step_key   = f"agent_booking_step_{patient_id}"
# #     slots_key  = f"agent_slots_{patient_id}"
# #     slot_key   = f"agent_chosen_slot_{patient_id}"
# #     doctor_key = f"agent_chosen_doctor_{patient_id}"

# #     step = st.session_state.get(step_key)
# #     if step is None:
# #         return

# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #     st.markdown(
# #         '<div style="font-weight:600;color:var(--text-primary);'
# #         'margin-bottom:0.8rem;">📅 Book a Consultation</div>',
# #         unsafe_allow_html=True,
# #     )

# #     # ── Step: select slot ─────────────────────────────────────────────────────
# #     if step == "select":
# #         all_slots = st.session_state.get(slots_key, [])
# #         if not all_slots:
# #             st.warning("No slots loaded. Please try again.")
# #             st.session_state.pop(step_key, None)
# #             return

# #         slot_labels = [
# #             f"Dr. {s['doctor_name']}  —  {s['slot_date']}  {s['start_time']}–{s['end_time']}"
# #             for s in all_slots
# #         ]
# #         chosen_idx = st.selectbox(
# #             "Select a slot",
# #             options=range(len(slot_labels)),
# #             format_func=lambda i: slot_labels[i],
# #             key=f"agent_slot_select_{patient_id}",
# #             label_visibility="collapsed",
# #         )
# #         col_ok, col_cancel = st.columns([2, 1])
# #         with col_ok:
# #             if st.button("Confirm this slot →",
# #                          key=f"agent_confirm_slot_{patient_id}",
# #                          type="primary", use_container_width=True):
# #                 chosen = all_slots[chosen_idx]
# #                 st.session_state[slot_key]   = chosen
# #                 st.session_state[doctor_key] = {
# #                     "name": chosen["doctor_name"],
# #                     "id":   chosen["doctor_id"],
# #                 }
# #                 st.session_state[step_key] = "confirm"
# #                 st.rerun()
# #         with col_cancel:
# #             if st.button("Cancel", key=f"agent_cancel_slot_{patient_id}",
# #                          use_container_width=True):
# #                 for k in (step_key, slots_key, slot_key, doctor_key):
# #                     st.session_state.pop(k, None)
# #                 st.rerun()

# #     # ── Step: confirm booking ─────────────────────────────────────────────────
# #     elif step == "confirm":
# #         chosen_slot   = st.session_state.get(slot_key, {})
# #         chosen_doctor = st.session_state.get(doctor_key, {})

# #         st.markdown(f"""
# #         <div class="card" style="border:1px solid rgba(167,139,250,0.4);
# #              background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
# #             <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
# #                 📋 Confirm Booking
# #             </div>
# #             <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.9;">
# #                 <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
# #                 <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
# #                 <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         col_yes, col_back = st.columns(2)
# #         with col_yes:
# #             if st.button("✅ Book Appointment",
# #                          key=f"agent_book_yes_{patient_id}",
# #                          type="primary", use_container_width=True):
# #                 success = book_opd_slot(
# #                     slot_id=chosen_slot["id"],
# #                     patient_id=patient_id,
# #                     patient_name=patient.get("name", ""),
# #                 )
# #                 for k in (step_key, slots_key, slot_key, doctor_key):
# #                     st.session_state.pop(k, None)
# #                 _cached_opd_bookings.clear()

# #                 if success:
# #                     doctor_id = patient.get("doctor_id")
# #                     create_alert(
# #                         patient_id=patient_id,
# #                         alert_type="agent_opd_booked",
# #                         message=(
# #                             f"Patient booked an OPD slot via the Proactive Health Agent tab.\n"
# #                             f"Slot: Dr. {chosen_doctor.get('name','')} on "
# #                             f"{chosen_slot.get('slot_date','')} "
# #                             f"at {chosen_slot.get('start_time','')}."
# #                         ),
# #                         severity="low",
# #                         doctor_id=doctor_id,
# #                     )
# #                     st.success(
# #                         f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
# #                         f"on {chosen_slot.get('slot_date','')} "
# #                         f"at {chosen_slot.get('start_time','')}."
# #                     )
# #                 else:
# #                     st.error(
# #                         "❌ That slot was just taken. "
# #                         "Please go to the **🖥️ Online OPD** tab to pick another."
# #                     )
# #                 st.rerun()

# #         with col_back:
# #             if st.button("← Back", key=f"agent_book_back_{patient_id}",
# #                          use_container_width=True):
# #                 st.session_state[step_key] = "select"
# #                 st.rerun()



# # # import streamlit as st
# # # import json
# # # from datetime import date, datetime
# # # from data.database import (
# # #     get_patient, get_patient_prescriptions, get_chat_history,
# # #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# # #     create_alert, check_consecutive_worsening, get_patient_alerts,
# # #     resolve_alert,
# # #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# # #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# # #     get_patient_opd_bookings, check_patient_has_booking
# # # )
# # # from agents.orchestrator import AgentOrchestrator
# # # from agents.scheduling_agent import (
# # #     SchedulingAgent, get_auth_url,
# # #     exchange_code_for_tokens, refresh_access_token
# # # )
# # # from agents.mcq_agent import MCQAgent


# # # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_chat_history(patient_id, limit=20):
# # #     return get_chat_history(patient_id, limit)

# # # @st.cache_data(ttl=15, show_spinner=False)
# # # def _cached_prescriptions(patient_id):
# # #     return get_patient_prescriptions(patient_id)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_patient_alerts(patient_id):
# # #     return get_patient_alerts(patient_id)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_opd_bookings(patient_id):
# # #     return get_patient_opd_bookings(patient_id)

# # # @st.cache_data(ttl=20, show_spinner=False)
# # # def _cached_mcq_response_today(patient_id, today_str):
# # #     return get_mcq_response_for_date(patient_id, today_str)

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_mcq_responses(patient_id, limit=30):
# # #     return get_mcq_responses(patient_id, limit)

# # # @st.cache_data(ttl=60, show_spinner=False)
# # # def _cached_opd_doctors():
# # #     return get_available_opd_doctors()

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_opd_dates(doctor_id):
# # #     return get_available_opd_dates_for_doctor(doctor_id)

# # # @st.cache_data(ttl=15, show_spinner=False)
# # # def _cached_opd_slots(doctor_id, date_str):
# # #     return get_available_opd_slots(doctor_id, date_str)

# # # @st.cache_data(ttl=10, show_spinner=False)
# # # def _cached_has_booking(patient_id, doctor_id, date_str):
# # #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # # def _handle_google_oauth_callback():
# # #     """
# # #     Called once at the top of app.py.
# # #     If Google redirected back with ?code=..., exchange it for tokens,
# # #     set mode=patient, and mark patient_google_authed=True.
# # #     Only removes OAuth-specific params, preserving the _s session-restore param.
# # #     """
# # #     params = st.query_params
# # #     auth_code = params.get("code")
# # #     if auth_code and not st.session_state.get("google_access_token"):
# # #         try:
# # #             tokens = exchange_code_for_tokens(auth_code)
# # #             if "access_token" in tokens:
# # #                 st.session_state["google_access_token"] = tokens["access_token"]
# # #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# # #                 st.session_state["patient_google_authed"] = True
# # #                 st.session_state["mode"] = "patient"
# # #                 st.toast("✅ Google sign-in successful!", icon="✅")
# # #         except Exception as e:
# # #             st.warning(f"Google OAuth error: {e}")
# # #         # Remove only OAuth-specific params, preserving _s session param
# # #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# # #             try:
# # #                 if oauth_key in st.query_params:
# # #                     del st.query_params[oauth_key]
# # #             except Exception:
# # #                 pass


# # # def _get_valid_access_token() -> str | None:
# # #     """Return a valid Google access token from session, refreshing if needed."""
# # #     token = st.session_state.get("google_access_token")
# # #     if token:
# # #         return token
# # #     refresh_tok = st.session_state.get("google_refresh_token")
# # #     if refresh_tok:
# # #         new_token = refresh_access_token(refresh_tok)
# # #         if new_token:
# # #             st.session_state["google_access_token"] = new_token
# # #             return new_token
# # #     return None


# # # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # # @st.cache_resource(show_spinner=False)
# # # def _get_orchestrator():
# # #     return AgentOrchestrator()

# # # @st.cache_resource(show_spinner=False)
# # # def _get_scheduler():
# # #     return SchedulingAgent()

# # # @st.cache_resource(show_spinner=False)
# # # def _get_mcq_agent():
# # #     return MCQAgent()

# # # @st.cache_data(ttl=120, show_spinner=False)
# # # def _cached_patient_login(patient_id):
# # #     """Run the expensive on_patient_login only once per 2 minutes."""
# # #     return _get_orchestrator().on_patient_login(patient_id)

# # # @st.cache_data(ttl=30, show_spinner=False)
# # # def _cached_get_patient(patient_id):
# # #     return get_patient(patient_id)


# # # # ── Main dashboard ────────────────────────────────────────────────────────────

# # # def render_patient_dashboard(patient_id):
# # #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# # #     orchestrator = _get_orchestrator()
# # #     scheduler = _get_scheduler()
# # #     mcq_agent = _get_mcq_agent()
# # #     patient = _cached_get_patient(patient_id)

# # #     if not patient:
# # #         st.error("Patient not found. Check your Patient ID.")
# # #         return

# # #     st.markdown(f"""
# # #     <div class="page-header">
# # #         <h1>🧑‍⚕️ Patient Portal</h1>
# # #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# # #     _health_key = f"health_data_{patient_id}"
# # #     if _health_key not in st.session_state:
# # #         with st.spinner("Loading your health data..."):
# # #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# # #     health_data = st.session_state[_health_key]

# # #     risk = health_data.get("risk", {})
# # #     adherence = health_data.get("adherence", {})
# # #     trends = health_data.get("trends", {})

# # #     col1, col2, col3, col4 = st.columns(4)
# # #     risk_level = risk.get("level", "low")
# # #     col1.metric("Risk Level", risk_level.upper())
# # #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# # #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# # #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# # #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# # #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
# # #     tabs = st.tabs([
# # #         "💬 AI Assistant",
# # #         "📅 My Schedule",
# # #         "💊 My Prescriptions",
# # #         "🩺 Daily Health Check",
# # #         "🔔 Alerts",
# # #         "🖥️ Online OPD",
# # #     ])

# # #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# # #     with tabs[0]:
# # #         st.markdown("### 🤖 Autonomous AI Health Agent")
# # #         st.markdown(
# # #             '<p style="color: var(--text-secondary);">'
# # #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# # #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# # #             '</p>',
# # #             unsafe_allow_html=True
# # #         )

# # #         # ── Quick action chips ─────────────────────────────────────────────
# # #         st.markdown("""
# # #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# # #                          cursor:pointer;">📅 Book Appointment</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          💊 My Prescriptions</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          🩺 Check Symptoms</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          🔔 My Alerts</span>
# # #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# # #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# # #                          ❌ Cancel Appointment</span>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #         history = _cached_chat_history(patient_id, 20)
# # #         for msg in history:
# # #             with st.chat_message(msg["role"]):
# # #                 st.markdown(msg["content"])

# # #         # ── Triage action buttons ─────────────────────────────────────────
# # #         _triage_key = f"pending_triage_{patient_id}"
# # #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# # #         _confirm_key = f"triage_confirm_{patient_id}"

# # #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# # #             triage_level = st.session_state[_triage_key]
# # #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# # #             if triage_level == "URGENT":
# # #                 btn_label = "🚨 Alert My Doctor Now"
# # #                 btn_type = "primary"
# # #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# # #             else:
# # #                 btn_label = "📅 Book Urgent Appointment"
# # #                 btn_type = "secondary"
# # #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# # #             if not st.session_state.get(_confirm_key):
# # #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# # #                     st.session_state[_confirm_key] = True
# # #                     st.rerun()
# # #             else:
# # #                 st.warning(confirm_msg)
# # #                 col_yes, col_no = st.columns(2)
# # #                 with col_yes:
# # #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# # #                         severity = "high" if triage_level == "URGENT" else "medium"
# # #                         alert_message = (
# # #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# # #                             f"Patient described: \"{symptom_text}\"\n"
# # #                             f"AI Triage Verdict: {triage_level}\n"
# # #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# # #                                else "📅 Patient requests a follow-up appointment.")
# # #                         )
# # #                         _pt = get_patient(patient_id)
# # #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# # #                         create_alert(
# # #                             patient_id=patient_id,
# # #                             alert_type="patient_reported_symptoms",
# # #                             message=alert_message,
# # #                             severity=severity,
# # #                             doctor_id=_doctor_id
# # #                         )
# # #                         st.session_state.pop(_triage_key, None)
# # #                         st.session_state.pop(_triage_msg_key, None)
# # #                         st.session_state.pop(_confirm_key, None)
# # #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# # #                                    else "✅ Alert sent to your doctor!")
# # #                         st.rerun()
# # #                 with col_no:
# # #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# # #                         st.session_state.pop(_triage_key, None)
# # #                         st.session_state.pop(_triage_msg_key, None)
# # #                         st.session_state.pop(_confirm_key, None)
# # #                         st.rerun()

# # #         # ── Action result display (non-triage confirmations) ──────────────
# # #         _action_result_key = f"action_result_{patient_id}"
# # #         if st.session_state.get(_action_result_key):
# # #             ar = st.session_state[_action_result_key]
# # #             action = ar.get("action", "")
# # #             confirmed = ar.get("confirmed", False)
# # #             success = ar.get("success", False)

# # #             if confirmed and success:
# # #                 if action == "book_appointment":
# # #                     bd = ar.get("booking_details", {})
# # #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# # #                 elif action == "cancel_appointment":
# # #                     st.success("✅ Appointment successfully cancelled.")

# # #             st.session_state.pop(_action_result_key, None)

# # #         # ── Chat input ────────────────────────────────────────────────────
# # #         placeholder = (
# # #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# # #             "or 'Show my prescriptions' or 'I have chest pain'..."
# # #         )
# # #         if prompt := st.chat_input(placeholder):
# # #             with st.chat_message("user"):
# # #                 st.markdown(prompt)

# # #             with st.chat_message("assistant"):
# # #                 with st.spinner("🤖 Analysing and acting..."):
# # #                     result = orchestrator.on_patient_message(
# # #                         patient_id, prompt,
# # #                         use_agentic=True,
# # #                         session_state=st.session_state
# # #                     )

# # #                 if not isinstance(result, dict):
# # #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# # #                 reply = result.get("reply", "")
# # #                 triage = result.get("triage")
# # #                 action = result.get("action", "")
# # #                 confirmed = result.get("confirmed", False)
# # #                 success = result.get("success", False)

# # #                 # ── Show triage badge ──────────────────────────────────
# # #                 if triage == "URGENT":
# # #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# # #                 elif triage == "MODERATE":
# # #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# # #                 elif triage == "MILD":
# # #                     st.success("🟢 **MILD — Manageable at home for now.**")

# # #                 # ── Show action confirmation badge ────────────────────
# # #                 if confirmed and success:
# # #                     if action == "book_appointment":
# # #                         bd = result.get("booking_details", {})
# # #                         st.success(
# # #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# # #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# # #                         )
# # #                     elif action == "cancel_appointment":
# # #                         st.success("✅ **Appointment Cancelled Successfully**")

# # #                 st.markdown(reply)

# # #             # ── Post-response state management ────────────────────────
# # #             if triage in ("URGENT", "MODERATE"):
# # #                 st.session_state[_triage_key] = triage
# # #                 st.session_state[_triage_msg_key] = prompt
# # #                 st.session_state.pop(_confirm_key, None)
# # #             else:
# # #                 st.session_state.pop(_triage_key, None)
# # #                 st.session_state.pop(_triage_msg_key, None)
# # #                 st.session_state.pop(_confirm_key, None)

# # #             _cached_chat_history.clear()
# # #             st.rerun()

# # #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# # #     with tabs[1]:
# # #         st.markdown("### 📅 Medication Schedule")
# # #         col1, col2 = st.columns([3, 1])

# # #         with col2:
# # #             access_token = _get_valid_access_token()

# # #             if access_token:
# # #                 # Token available — show sync button
# # #                 if st.button("📆 Sync to Google Calendar"):
# # #                     with st.spinner("Syncing to calendar..."):
# # #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# # #                     if result["success"]:
# # #                         st.success(result["message"])
# # #                     else:
# # #                         st.warning(result.get("message", "Sync failed."))
# # #                         if result.get("errors"):
# # #                             for e in result["errors"]:
# # #                                 st.caption(f"⚠ {e}")
# # #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# # #                     st.session_state.pop("google_access_token", None)
# # #                     st.session_state.pop("google_refresh_token", None)
# # #                     st.rerun()
# # #             else:
# # #                 # No access token in session (e.g. user disconnected or session expired).
# # #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# # #                 st.markdown("""
# # #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# # #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# # #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# # #                         📅 Google Calendar Disconnected
# # #                     </div>
# # #                     <div style="color:#A89FC8;font-size:0.82rem;">
# # #                         Your Google session token has expired. Click below to reconnect —
# # #                         this uses the same Google account you signed in with.
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)
# # #                 try:
# # #                     auth_url = get_auth_url()
# # #                     st.markdown(f"""
# # #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# # #                         <div style="
# # #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# # #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# # #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# # #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# # #                             <svg width="16" height="16" viewBox="0 0 18 18">
# # #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# # #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# # #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# # #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# # #                             </svg>
# # #                             Reconnect Google Calendar
# # #                         </div>
# # #                     </a>
# # #                     """, unsafe_allow_html=True)
# # #                 except Exception:
# # #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# # #         schedule = scheduler.get_schedule_preview(patient_id)
# # #         if not schedule:
# # #             st.info("No schedule available. Ask your doctor to create a prescription.")
# # #         else:
# # #             current_date = None
# # #             for item in schedule:
# # #                 if item["date"] != current_date:
# # #                     current_date = item["date"]
# # #                     st.markdown(f"**📅 {current_date}**")
# # #                 st.markdown(f"""
# # #                 <div class="schedule-item">
# # #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# # #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# # #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# # #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# # #     with tabs[2]:
# # #         st.markdown("### 💊 My Prescriptions")
# # #         prescriptions = _cached_prescriptions(patient_id)
# # #         if not prescriptions:
# # #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# # #         else:
# # #             for i, pr in enumerate(prescriptions):
# # #                 st.markdown(f"""
# # #                 <div class="card">
# # #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# # #                 """, unsafe_allow_html=True)
# # #                 for m in pr.get("medicines", []):
# # #                     st.markdown(f"""
# # #                     <div class="medicine-card">
# # #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# # #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# # #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# # #                         </div>
# # #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# # #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# # #                         </div>
# # #                     </div>
# # #                     """, unsafe_allow_html=True)
# # #                 if pr.get("doctor_notes"):
# # #                     st.markdown(
# # #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# # #                         unsafe_allow_html=True
# # #                     )
# # #                 st.markdown("</div>", unsafe_allow_html=True)

# # #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# # #     with tabs[3]:
# # #         today_str = date.today().isoformat()
# # #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# # #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# # #         _mcq_show_form = True  # controls whether to show the question form

# # #         if existing_response:
# # #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# # #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# # #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# # #                 st.session_state["retake_mcq"] = True
# # #                 st.session_state["show_health_summary"] = False
# # #                 # Clear cached questions so fresh ones load
# # #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# # #                 st.rerun()
# # #             if not st.session_state.get("retake_mcq"):
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             prescriptions = _cached_prescriptions(patient_id)
# # #             if not prescriptions:
# # #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             # Cache questions per patient per day — no need to call GROQ on every rerun
# # #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# # #             if _q_key not in st.session_state:
# # #                 with st.spinner("Loading your personalized health questions..."):
# # #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# # #             questions = st.session_state[_q_key]

# # #             if not questions:
# # #                 st.error("Could not generate questions. Please try again.")
# # #                 _mcq_show_form = False

# # #         if _mcq_show_form:
# # #             st.markdown("""
# # #             <div class="card" style="margin-bottom: 1.5rem;">
# # #                 <div class="card-header">📋 Today's Health Questions</div>
# # #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# # #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# # #                 </p>
# # #             </div>
# # #             """, unsafe_allow_html=True)

# # #             selected_options = {}

# # #             for q in questions:
# # #                 qid = str(q["id"])
# # #                 category_icons = {
# # #                     "symptom": "🤒",
# # #                     "adherence": "💊",
# # #                     "side_effect": "⚠️",
# # #                     "wellbeing": "💚"
# # #                 }
# # #                 icon = category_icons.get(q.get("category", ""), "❓")

# # #                 st.markdown(f"""
# # #                 <div class="card" style="margin-bottom: 1rem;">
# # #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# # #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# # #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# # #                     </div>
# # #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# # #                         {q['question']}
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #                 option_labels = [opt["text"] for opt in q["options"]]
# # #                 choice = st.radio(
# # #                     label=q["question"],
# # #                     options=range(len(option_labels)),
# # #                     format_func=lambda i, opts=option_labels: opts[i],
# # #                     key=f"mcq_{qid}",
# # #                     label_visibility="collapsed"
# # #                 )
# # #                 selected_options[qid] = choice
# # #                 st.markdown("---")

# # #             col_btn1, col_btn2 = st.columns([3, 1])
# # #             with col_btn1:
# # #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# # #                     total_score = 0
# # #                     for q in questions:
# # #                         qid = str(q["id"])
# # #                         idx = selected_options.get(qid, 0)
# # #                         try:
# # #                             total_score += q["options"][idx]["score"]
# # #                         except (IndexError, KeyError):
# # #                             pass

# # #                     status = mcq_agent.compute_status(total_score)
# # #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# # #                     responses_data = []
# # #                     for q in questions:
# # #                         qid = str(q["id"])
# # #                         idx = selected_options.get(qid, 0)
# # #                         responses_data.append({
# # #                             "question": q["question"],
# # #                             "category": q.get("category"),
# # #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# # #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# # #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# # #                         })

# # #                     doctor_id = patient.get("doctor_id")
# # #                     save_mcq_response(
# # #                         patient_id=patient_id,
# # #                         doctor_id=doctor_id,
# # #                         date_str=today_str,
# # #                         responses_json=json.dumps(responses_data),
# # #                         total_score=total_score,
# # #                         status=status,
# # #                         side_effects=json.dumps(side_effects),
# # #                         adherence_status=adherence_status
# # #                     )

# # #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# # #                                            symptoms, adherence_status, side_effects)

# # #                     st.session_state["retake_mcq"] = False
# # #                     st.session_state["show_health_summary"] = True
# # #                     # Invalidate cached data so next render is fresh
# # #                     _cached_patient_login.clear()
# # #                     _cached_mcq_response_today.clear()
# # #                     _cached_mcq_responses.clear()
# # #                     st.session_state.pop(f"health_data_{patient_id}", None)
# # #                     st.rerun()

# # #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# # #         # Show automatically after submission OR when today's response already exists
# # #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# # #         if _show_summary:
# # #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# # #             st.markdown("### 📊 Your Health Summary")

# # #             # ── AI Health Report ──────────────────────────────────────────────
# # #             col_ai1, col_ai2 = st.columns([4, 1])
# # #             with col_ai2:
# # #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# # #             if _gen_report or st.session_state.get("show_health_summary"):
# # #                 # Cache summary per patient per day - expensive GROQ call
# # #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# # #                 if _gen_report or _sum_key not in st.session_state:
# # #                     with st.spinner("AI is analyzing your health data..."):
# # #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# # #                 summary = st.session_state[_sum_key]
# # #                 st.markdown(f"""
# # #                 <div class="card">
# # #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# # #                     <p style="line-height: 1.7;">{summary}</p>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #             # ── Health Indicators ─────────────────────────────────────────────
# # #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# # #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# # #             st.markdown(f"""
# # #             <div class="card">
# # #                 <div class="card-header">Health Indicators</div>
# # #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# # #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# # #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# # #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# # #                     </div>
# # #                     <div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# # #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #             """, unsafe_allow_html=True)

# # #             # ── Health Trend Chart ────────────────────────────────────────────
# # #             responses = _cached_mcq_responses(patient_id, limit=30)
# # #             if responses:
# # #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# # #                 import pandas as pd
# # #                 import plotly.graph_objects as go

# # #                 chart_responses = list(reversed(responses))
# # #                 dates  = [r["date"] for r in chart_responses]
# # #                 scores = [r["total_score"] for r in chart_responses]
# # #                 statuses = [r["status"] for r in chart_responses]

# # #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# # #                 fig = go.Figure()
# # #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=[max(s, 0) for s in scores],
# # #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# # #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# # #                 ))
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=[min(s, 0) for s in scores],
# # #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# # #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# # #                 ))
# # #                 fig.add_trace(go.Scatter(
# # #                     x=dates, y=scores,
# # #                     mode="lines+markers",
# # #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# # #                     marker=dict(size=10, color=marker_colors,
# # #                                 line=dict(color="#1a1a2e", width=2)),
# # #                     name="Health Score",
# # #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# # #                 ))

# # #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #                 for d, s, st_ in zip(dates, scores, statuses):
# # #                     fig.add_annotation(
# # #                         x=d, y=s,
# # #                         text=status_icons_map.get(st_, ""),
# # #                         showarrow=False,
# # #                         yshift=18, font=dict(size=13)
# # #                     )

# # #                 fig.update_layout(
# # #                     paper_bgcolor="rgba(0,0,0,0)",
# # #                     plot_bgcolor="rgba(0,0,0,0)",
# # #                     font=dict(color="#A89FC8", size=12),
# # #                     margin=dict(l=10, r=10, t=10, b=10),
# # #                     height=300,
# # #                     xaxis=dict(
# # #                         showgrid=False, zeroline=False,
# # #                         tickfont=dict(size=11, color="#6B6080"),
# # #                         title=""
# # #                     ),
# # #                     yaxis=dict(
# # #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# # #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# # #                         tickfont=dict(size=11, color="#6B6080"),
# # #                         title="Score"
# # #                     ),
# # #                     hoverlabel=dict(
# # #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# # #                         font=dict(color="white", size=13)
# # #                     ),
# # #                     showlegend=False
# # #                 )

# # #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# # #                 st.markdown("""
# # #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# # #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# # #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# # #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# # #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)

# # #                 # ── Recent Check-in History ───────────────────────────────────
# # #                 st.markdown("#### 📋 Recent Daily Check-in History")
# # #                 for r in responses:
# # #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #                     color = status_colors.get(r["status"], "#A78BFA")
# # #                     icon = status_icons.get(r["status"], "•")
# # #                     st.markdown(f"""
# # #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# # #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# # #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# # #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# # #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# # #                         </div>
# # #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# # #                             Adherence: {r.get('adherence_status', 'N/A')}
# # #                         </div>
# # #                     </div>
# # #                     """, unsafe_allow_html=True)

# # #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# # #     with tabs[4]:
# # #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# # #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# # #     with tabs[5]:
# # #         _render_patient_opd(patient_id, patient)


# # # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# # #     """Render the patient-facing Alerts & Notifications tab."""
# # #     st.markdown("### 🔔 Alerts & Notifications")
# # #     st.markdown(
# # #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# # #         'and doctor messages are shown here.</p>',
# # #         unsafe_allow_html=True
# # #     )

# # #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# # #     if risk_level == "high":
# # #         st.markdown(f"""
# # #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# # #             <div style="display:flex;align-items:center;gap:0.8rem;">
# # #                 <span style="font-size:1.8rem;">🚨</span>
# # #                 <div>
# # #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# # #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# # #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# # #                         Please contact your doctor or visit the clinic immediately.
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# # #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# # #     missed_dose_dates = []
# # #     for r in recent_responses:
# # #         adh = (r.get("adherence_status") or "").lower()
# # #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# # #             missed_dose_dates.append(r["date"])

# # #     if missed_dose_dates:
# # #         dates_str = ", ".join(missed_dose_dates[:3])
# # #         st.markdown(f"""
# # #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# # #             <div style="display:flex;align-items:center;gap:0.8rem;">
# # #                 <span style="font-size:1.8rem;">💊</span>
# # #                 <div>
# # #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# # #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# # #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# # #                         Consistent adherence is key to recovery — please take medications as prescribed.
# # #                     </div>
# # #                 </div>
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# # #     all_alerts = _cached_patient_alerts(patient_id)
# # #     unresolved = [a for a in all_alerts if not a["resolved"]]
# # #     resolved = [a for a in all_alerts if a["resolved"]]

# # #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# # #         st.markdown("""
# # #         <div class="card" style="text-align:center;padding:2rem;">
# # #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# # #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# # #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# # #                 No active alerts. Keep taking your medications and completing daily check-ins!
# # #             </div>
# # #         </div>
# # #         """, unsafe_allow_html=True)
# # #         return

# # #     severity_config = {
# # #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# # #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# # #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# # #     }
# # #     type_labels = {
# # #         "mcq_health_check": "Health Check Alert",
# # #         "doctor_message":   "Doctor Message",
# # #         "missed_dose":      "Missed Dose",
# # #         "high_risk":        "High Risk Warning",
# # #     }

# # #     if unresolved:
# # #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# # #         for alert in unresolved:
# # #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# # #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# # #             created = alert["created_at"][:16].replace("T", " ")

# # #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# # #                 st.markdown(f"""
# # #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# # #                              border-left:3px solid {cfg['color']};">
# # #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# # #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # # {alert['message']}</pre>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)
# # #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# # #                     resolve_alert(alert["id"])
# # #                     _cached_patient_alerts.clear()
# # #                     st.rerun()

# # #     if resolved:
# # #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# # #             for alert in resolved:
# # #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# # #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# # #                 created = alert["created_at"][:16].replace("T", " ")
# # #                 st.markdown(f"""
# # #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# # #                     <div style="display:flex;justify-content:space-between;">
# # #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# # #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# # #                     </div>
# # #                 </div>
# # #                 """, unsafe_allow_html=True)


# # # # ── MCQ result card ───────────────────────────────────────────────────────────

# # # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# # #     status = response["status"]
# # #     score = response["total_score"]
# # #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# # #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# # #     color = status_colors.get(status, "#A78BFA")
# # #     icon = status_icons.get(status, "•")

# # #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# # #     # Safely escape feedback strings to prevent HTML injection
# # #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# # #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# # #     st.markdown(f"""
# # #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# # #         <div style="text-align: center; padding: 1rem 0;">
# # #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# # #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# # #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# # #         </div>
# # #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# # #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# # #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# # #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# # #         </div>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     adherence_status = response.get("adherence_status", "")
# # #     side_effects_raw = response.get("side_effects", "[]")
# # #     try:
# # #         side_effects = json.loads(side_effects_raw)
# # #     except Exception:
# # #         side_effects = []

# # #     col1, col2 = st.columns(2)
# # #     with col1:
# # #         st.markdown(f"""
# # #         <div class="card" style="margin-top: 0;">
# # #             <div class="card-header">💊 Medication Adherence</div>
# # #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# # #         </div>
# # #         """, unsafe_allow_html=True)
# # #     with col2:
# # #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# # #         st.markdown(f"""
# # #         <div class="card" style="margin-top: 0;">
# # #             <div class="card-header">⚠️ Side Effects</div>
# # #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# # #         </div>
# # #         """, unsafe_allow_html=True)

# # #     if show_history and patient_id:
# # #         st.markdown(
# # #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# # #             unsafe_allow_html=True
# # #         )


# # # # ── Alert firing logic ────────────────────────────────────────────────────────

# # # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# # #     """Fire structured doctor alerts based on MCQ response."""
# # #     trigger = False
# # #     reasons = []

# # #     if total_score < 0:
# # #         trigger = True
# # #         reasons.append("negative_score")

# # #     if check_consecutive_worsening(patient_id, 2):
# # #         trigger = True
# # #         reasons.append("consecutive_worsening")

# # #     if side_effects:
# # #         trigger = True
# # #         reasons.append("side_effects")

# # #     if not trigger:
# # #         return

# # #     action_map = {
# # #         "Improving": "Continue medication as prescribed",
# # #         "Stable": "Monitor closely, follow up in 2-3 days",
# # #         "Worsening": "Immediate consultation required"
# # #     }

# # #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# # #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# # #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# # #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# # #     alert_message = f"""Patient ID: {patient_id}
# # # Doctor ID: {doctor_id}
# # # Disease: {patient.get('disease', 'N/A')}
# # # Current Status: {status}
# # # Score: {total_score:+d}

# # # Key Symptoms Reported:
# # # {symptoms_text}

# # # Medication Adherence:
# # # {adherence_text}

# # # Side Effects:
# # # {side_effects_text}

# # # Recommended Action:
# # # - {action_map.get(status, 'Monitor patient')}

# # # Triggered By: {reasons_text}"""

# # #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# # #     create_alert(
# # #         patient_id=patient_id,
# # #         alert_type="mcq_health_check",
# # #         message=alert_message,
# # #         severity=severity,
# # #         doctor_id=doctor_id
# # #     )




# # # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # # def _render_patient_opd(patient_id: str, patient: dict):
# # #     """Full Online OPD booking UI for the patient dashboard."""
# # #     import streamlit as st
# # #     from datetime import date, datetime

# # #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# # #     st.markdown(
# # #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# # #         'Slots are real-time — once booked they disappear for other patients.</p>',
# # #         unsafe_allow_html=True
# # #     )

# # #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# # #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# # #     with opd_subtabs[0]:
# # #         doctors = _cached_opd_doctors()

# # #         if not doctors:
# # #             st.info("No doctors have published OPD slots yet. Please check back later.")
# # #         else:
# # #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# # #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# # #             selected_doctor_id = doctor_options[selected_label]

# # #             available_dates = _cached_opd_dates(selected_doctor_id)
# # #             if not available_dates:
# # #                 st.warning("This doctor has no available slots right now.")
# # #             else:
# # #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# # #                 chosen_date_str = st.selectbox(
# # #                     "Select Date",
# # #                     list(date_labels.keys()),
# # #                     format_func=lambda x: date_labels[x],
# # #                     key="opd_date_sel"
# # #                 )

# # #                 # Check if patient already booked on this day with this doctor
# # #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# # #                 if already_booked:
# # #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# # #                 else:
# # #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# # #                     if not free_slots:
# # #                         st.error("All slots for this date are fully booked. Please choose another date.")
# # #                     else:
# # #                         st.markdown(f"""
# # #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# # #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# # #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# # #                                 </div>
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# # #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# # #                                 </div>
# # #                                 <div>
# # #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# # #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# # #                                 </div>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # #                         slot_options = {
# # #                             f"{s['start_time']} – {s['end_time']}": s['id']
# # #                             for s in free_slots
# # #                         }
# # #                         chosen_slot_label = st.selectbox(
# # #                             "Choose a time slot",
# # #                             list(slot_options.keys()),
# # #                             key="opd_slot_sel"
# # #                         )
# # #                         chosen_slot_id = slot_options[chosen_slot_label]

# # #                         st.markdown(f"""
# # #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# # #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# # #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# # #                                 <strong>Doctor:</strong> {selected_label}<br>
# # #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# # #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# # #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# # #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# # #                             if success:
# # #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# # #                                 st.balloons()
# # #                                 _cached_opd_bookings.clear()
# # #                                 _cached_opd_slots.clear()
# # #                                 _cached_has_booking.clear()
# # #                                 st.rerun()
# # #                             else:
# # #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# # #                                 _cached_opd_slots.clear()
# # #                                 st.rerun()

# # #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# # #     with opd_subtabs[1]:
# # #         st.markdown("#### 🗓️ Your OPD Bookings")
# # #         my_bookings = _cached_opd_bookings(patient_id)

# # #         if not my_bookings:
# # #             st.markdown("""
# # #             <div class="card" style="text-align:center;padding:2rem;">
# # #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# # #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# # #             </div>
# # #             """, unsafe_allow_html=True)
# # #         else:
# # #             today_str = date.today().isoformat()
# # #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# # #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# # #             if upcoming:
# # #                 st.markdown("##### 📅 Upcoming")
# # #                 for booking in upcoming:
# # #                     visited = bool(booking["patient_visited"])
# # #                     color = "#34D399" if visited else "#A78BFA"
# # #                     status = "✅ Consulted" if visited else "⏳ Pending"
# # #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# # #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# # #                     room_name = f"MediCore-{safe_room}"

# # #                     col_b, col_c = st.columns([4, 1])
# # #                     with col_b:
# # #                         st.markdown(f"""
# # #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# # #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# # #                                 <div>
# # #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# # #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# # #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# # #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# # #                                     </div>
# # #                                 </div>
# # #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)
# # #                     with col_c:
# # #                         if not visited:
# # #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# # #                                 success = cancel_opd_booking(booking["id"], patient_id)
# # #                                 if success:
# # #                                     st.success("Booking cancelled.")
# # #                                     _cached_opd_bookings.clear()
# # #                                     _cached_opd_slots.clear()
# # #                                     _cached_has_booking.clear()
# # #                                     st.rerun()

# # #                     # ── Embedded video call (Jitsi) ───────────────────────────
# # #                     if not visited:
# # #                         call_key = f"show_call_pat_{booking['id']}"
# # #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# # #                                      use_container_width=True, type="primary"):
# # #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# # #                         if st.session_state.get(call_key, False):
# # #                             patient_name = st.session_state.get("patient_id", "Patient")
# # #                             encoded_name = str(patient_name).replace(" ", "%20")
# # #                             st.components.v1.html(f"""
# # #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# # #                             <iframe
# # #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# # #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# # #                                 allowfullscreen="true"
# # #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# # #                             ></iframe>
# # #                             </body></html>
# # #                             """, height=560)

# # #             if past:
# # #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# # #                     for booking in past:
# # #                         visited = bool(booking["patient_visited"])
# # #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# # #                         status = "✅ Consulted" if visited else "❌ Not attended"
# # #                         color = "#34D399" if visited else "#F87171"
# # #                         st.markdown(f"""
# # #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# # #                             <div style="display:flex;justify-content:space-between;">
# # #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# # #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# # #                             </div>
# # #                         </div>
# # #                         """, unsafe_allow_html=True)

# # # # ── Patient login ─────────────────────────────────────────────────────────────

# # # def render_patient_login():
# # #     st.markdown("""
# # #     <div style="max-width: 480px; margin: 4rem auto;">
# # #         <div class="page-header" style="text-align: center;">
# # #             <h1>🏥 Patient Login</h1>
# # #             <p>Enter your Patient ID to access your health portal</p>
# # #         </div>
# # #     </div>
# # #     """, unsafe_allow_html=True)

# # #     with st.container():
# # #         col1, col2, col3 = st.columns([1, 2, 1])
# # #         with col2:
# # #             patient_id = st.text_input(
# # #                 "Patient ID",
# # #                 placeholder="e.g. PAT-20260413-0001",
# # #                 label_visibility="collapsed"
# # #             )
# # #             st.markdown(
# # #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# # #                 'Your ID was provided by your doctor at registration</p>',
# # #                 unsafe_allow_html=True
# # #             )

# # #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# # #                 if patient_id:
# # #                     patient = get_patient(patient_id.strip().upper())
# # #                     if patient:
# # #                         st.session_state["patient_id"] = patient_id.strip().upper()
# # #                         st.session_state["patient_logged_in"] = True
# # #                         st.rerun()
# # #                     else:
# # #                         st.error("Patient ID not found. Check with your doctor.")
# # #                 else:
# # #                     st.warning("Please enter your Patient ID.")


# # import streamlit as st
# # import json
# # from datetime import date, datetime
# # from data.database import (
# #     get_patient, get_patient_prescriptions, get_chat_history,
# #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# #     create_alert, check_consecutive_worsening, get_patient_alerts,
# #     resolve_alert,
# #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# #     get_patient_opd_bookings, check_patient_has_booking
# # )
# # from agents.orchestrator import AgentOrchestrator
# # from agents.scheduling_agent import (
# #     SchedulingAgent, get_auth_url,
# #     exchange_code_for_tokens, refresh_access_token
# # )
# # from agents.mcq_agent import MCQAgent


# # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_chat_history(patient_id, limit=20):
# #     return get_chat_history(patient_id, limit)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_prescriptions(patient_id):
# #     return get_patient_prescriptions(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_patient_alerts(patient_id):
# #     return get_patient_alerts(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_opd_bookings(patient_id):
# #     return get_patient_opd_bookings(patient_id)

# # @st.cache_data(ttl=20, show_spinner=False)
# # def _cached_mcq_response_today(patient_id, today_str):
# #     return get_mcq_response_for_date(patient_id, today_str)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_mcq_responses(patient_id, limit=30):
# #     return get_mcq_responses(patient_id, limit)

# # @st.cache_data(ttl=60, show_spinner=False)
# # def _cached_opd_doctors():
# #     return get_available_opd_doctors()

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_opd_dates(doctor_id):
# #     return get_available_opd_dates_for_doctor(doctor_id)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_opd_slots(doctor_id, date_str):
# #     return get_available_opd_slots(doctor_id, date_str)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_has_booking(patient_id, doctor_id, date_str):
# #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # def _handle_google_oauth_callback():
# #     """
# #     Called once at the top of app.py.
# #     If Google redirected back with ?code=..., exchange it for tokens,
# #     set mode=patient, and mark patient_google_authed=True.
# #     Only removes OAuth-specific params, preserving the _s session-restore param.
# #     """
# #     params = st.query_params
# #     auth_code = params.get("code")
# #     if auth_code and not st.session_state.get("google_access_token"):
# #         try:
# #             tokens = exchange_code_for_tokens(auth_code)
# #             if "access_token" in tokens:
# #                 st.session_state["google_access_token"] = tokens["access_token"]
# #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# #                 st.session_state["patient_google_authed"] = True
# #                 st.session_state["mode"] = "patient"
# #                 st.toast("✅ Google sign-in successful!", icon="✅")
# #         except Exception as e:
# #             st.warning(f"Google OAuth error: {e}")
# #         # Remove only OAuth-specific params, preserving _s session param
# #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# #             try:
# #                 if oauth_key in st.query_params:
# #                     del st.query_params[oauth_key]
# #             except Exception:
# #                 pass


# # def _get_valid_access_token() -> str | None:
# #     """Return a valid Google access token from session, refreshing if needed."""
# #     token = st.session_state.get("google_access_token")
# #     if token:
# #         return token
# #     refresh_tok = st.session_state.get("google_refresh_token")
# #     if refresh_tok:
# #         new_token = refresh_access_token(refresh_tok)
# #         if new_token:
# #             st.session_state["google_access_token"] = new_token
# #             return new_token
# #     return None


# # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # @st.cache_resource(show_spinner=False)
# # def _get_orchestrator():
# #     return AgentOrchestrator()

# # @st.cache_resource(show_spinner=False)
# # def _get_scheduler():
# #     return SchedulingAgent()

# # @st.cache_resource(show_spinner=False)
# # def _get_mcq_agent():
# #     return MCQAgent()

# # @st.cache_data(ttl=120, show_spinner=False)
# # def _cached_patient_login(patient_id):
# #     """Run the expensive on_patient_login only once per 2 minutes."""
# #     return _get_orchestrator().on_patient_login(patient_id)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_get_patient(patient_id):
# #     return get_patient(patient_id)


# # # ── Main dashboard ────────────────────────────────────────────────────────────

# # def render_patient_dashboard(patient_id):
# #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# #     orchestrator = _get_orchestrator()
# #     scheduler = _get_scheduler()
# #     mcq_agent = _get_mcq_agent()
# #     patient = _cached_get_patient(patient_id)

# #     if not patient:
# #         st.error("Patient not found. Check your Patient ID.")
# #         return

# #     st.markdown(f"""
# #     <div class="page-header">
# #         <h1>🧑‍⚕️ Patient Portal</h1>
# #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# #     _health_key = f"health_data_{patient_id}"
# #     if _health_key not in st.session_state:
# #         with st.spinner("Loading your health data..."):
# #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# #     health_data = st.session_state[_health_key]

# #     risk = health_data.get("risk", {})
# #     adherence = health_data.get("adherence", {})
# #     trends = health_data.get("trends", {})

# #     col1, col2, col3, col4 = st.columns(4)
# #     risk_level = risk.get("level", "low")
# #     col1.metric("Risk Level", risk_level.upper())
# #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
# #     tabs = st.tabs([
# #         "💬 AI Assistant",
# #         "📅 My Schedule",
# #         "💊 My Prescriptions",
# #         "🩺 Daily Health Check",
# #         "🔔 Alerts",
# #         "🖥️ Online OPD",
# #     ])

# #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# #     with tabs[0]:
# #         st.markdown("### 🤖 Autonomous AI Health Agent")
# #         st.markdown(
# #             '<p style="color: var(--text-secondary);">'
# #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# #             '</p>',
# #             unsafe_allow_html=True
# #         )

# #         # ── Quick action chips ─────────────────────────────────────────────
# #         st.markdown("""
# #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# #                          cursor:pointer;">📅 Book Appointment</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          💊 My Prescriptions</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🩺 Check Symptoms</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🔔 My Alerts</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          ❌ Cancel Appointment</span>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         history = _cached_chat_history(patient_id, 20)
# #         for msg in history:
# #             with st.chat_message(msg["role"]):
# #                 st.markdown(msg["content"])

# #         # ── Triage action buttons ─────────────────────────────────────────
# #         _triage_key = f"pending_triage_{patient_id}"
# #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# #         _confirm_key = f"triage_confirm_{patient_id}"

# #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# #             triage_level = st.session_state[_triage_key]
# #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# #             if triage_level == "URGENT":
# #                 btn_label = "🚨 Alert My Doctor Now"
# #                 btn_type = "primary"
# #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# #             else:
# #                 btn_label = "📅 Book Urgent Appointment"
# #                 btn_type = "secondary"
# #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# #             if not st.session_state.get(_confirm_key):
# #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# #                     st.session_state[_confirm_key] = True
# #                     st.rerun()
# #             else:
# #                 st.warning(confirm_msg)
# #                 col_yes, col_no = st.columns(2)
# #                 with col_yes:
# #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# #                         severity = "high" if triage_level == "URGENT" else "medium"
# #                         alert_message = (
# #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# #                             f"Patient described: \"{symptom_text}\"\n"
# #                             f"AI Triage Verdict: {triage_level}\n"
# #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# #                                else "📅 Patient requests a follow-up appointment.")
# #                         )
# #                         _pt = get_patient(patient_id)
# #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# #                         create_alert(
# #                             patient_id=patient_id,
# #                             alert_type="patient_reported_symptoms",
# #                             message=alert_message,
# #                             severity=severity,
# #                             doctor_id=_doctor_id
# #                         )
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# #                                    else "✅ Alert sent to your doctor!")
# #                         st.rerun()
# #                 with col_no:
# #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.rerun()

# #         # ── Action result display (non-triage confirmations) ──────────────
# #         _action_result_key = f"action_result_{patient_id}"
# #         if st.session_state.get(_action_result_key):
# #             ar = st.session_state[_action_result_key]
# #             action = ar.get("action", "")
# #             confirmed = ar.get("confirmed", False)
# #             success = ar.get("success", False)

# #             if confirmed and success:
# #                 if action == "book_appointment":
# #                     bd = ar.get("booking_details", {})
# #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# #                 elif action == "cancel_appointment":
# #                     st.success("✅ Appointment successfully cancelled.")

# #             st.session_state.pop(_action_result_key, None)

# #         # ── Chat input ────────────────────────────────────────────────────
# #         placeholder = (
# #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# #             "or 'Show my prescriptions' or 'I have chest pain'..."
# #         )
# #         if prompt := st.chat_input(placeholder):
# #             with st.chat_message("user"):
# #                 st.markdown(prompt)

# #             with st.chat_message("assistant"):
# #                 with st.spinner("🤖 Analysing and acting..."):
# #                     result = orchestrator.on_patient_message(
# #                         patient_id, prompt,
# #                         use_agentic=True,
# #                         session_state=st.session_state
# #                     )

# #                 if not isinstance(result, dict):
# #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# #                 reply = result.get("reply", "")
# #                 triage = result.get("triage")
# #                 action = result.get("action", "")
# #                 confirmed = result.get("confirmed", False)
# #                 success = result.get("success", False)

# #                 # ── Show triage badge ──────────────────────────────────
# #                 if triage == "URGENT":
# #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# #                 elif triage == "MODERATE":
# #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# #                 elif triage == "MILD":
# #                     st.success("🟢 **MILD — Manageable at home for now.**")

# #                 # ── Show action confirmation badge ────────────────────
# #                 if confirmed and success:
# #                     if action == "book_appointment":
# #                         bd = result.get("booking_details", {})
# #                         st.success(
# #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# #                         )
# #                     elif action == "cancel_appointment":
# #                         st.success("✅ **Appointment Cancelled Successfully**")

# #                 st.markdown(reply)

# #             # ── Post-response state management ────────────────────────
# #             if triage in ("URGENT", "MODERATE"):
# #                 st.session_state[_triage_key] = triage
# #                 st.session_state[_triage_msg_key] = prompt
# #                 st.session_state.pop(_confirm_key, None)
# #             else:
# #                 st.session_state.pop(_triage_key, None)
# #                 st.session_state.pop(_triage_msg_key, None)
# #                 st.session_state.pop(_confirm_key, None)

# #             _cached_chat_history.clear()
# #             st.rerun()

# #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# #     with tabs[1]:
# #         st.markdown("### 📅 Medication Schedule")
# #         col1, col2 = st.columns([3, 1])

# #         with col2:
# #             access_token = _get_valid_access_token()

# #             if access_token:
# #                 # Token available — show sync button
# #                 if st.button("📆 Sync to Google Calendar"):
# #                     with st.spinner("Syncing to calendar..."):
# #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# #                     if result["success"]:
# #                         st.success(result["message"])
# #                     else:
# #                         st.warning(result.get("message", "Sync failed."))
# #                         if result.get("errors"):
# #                             for e in result["errors"]:
# #                                 st.caption(f"⚠ {e}")
# #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# #                     st.session_state.pop("google_access_token", None)
# #                     st.session_state.pop("google_refresh_token", None)
# #                     st.rerun()
# #             else:
# #                 # No access token in session (e.g. user disconnected or session expired).
# #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# #                 st.markdown("""
# #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# #                         📅 Google Calendar Disconnected
# #                     </div>
# #                     <div style="color:#A89FC8;font-size:0.82rem;">
# #                         Your Google session token has expired. Click below to reconnect —
# #                         this uses the same Google account you signed in with.
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 try:
# #                     auth_url = get_auth_url()
# #                     st.markdown(f"""
# #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# #                         <div style="
# #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# #                             <svg width="16" height="16" viewBox="0 0 18 18">
# #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# #                             </svg>
# #                             Reconnect Google Calendar
# #                         </div>
# #                     </a>
# #                     """, unsafe_allow_html=True)
# #                 except Exception:
# #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# #         schedule = scheduler.get_schedule_preview(patient_id)
# #         if not schedule:
# #             st.info("No schedule available. Ask your doctor to create a prescription.")
# #         else:
# #             current_date = None
# #             for item in schedule:
# #                 if item["date"] != current_date:
# #                     current_date = item["date"]
# #                     st.markdown(f"**📅 {current_date}**")
# #                 st.markdown(f"""
# #                 <div class="schedule-item">
# #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# #     with tabs[2]:
# #         st.markdown("### 💊 My Prescriptions")
# #         prescriptions = _cached_prescriptions(patient_id)
# #         if not prescriptions:
# #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# #         else:
# #             for i, pr in enumerate(prescriptions):
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# #                 """, unsafe_allow_html=True)
# #                 for m in pr.get("medicines", []):
# #                     st.markdown(f"""
# #                     <div class="medicine-card">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# #                         </div>
# #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)
# #                 if pr.get("doctor_notes"):
# #                     st.markdown(
# #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# #                         unsafe_allow_html=True
# #                     )
# #                 st.markdown("</div>", unsafe_allow_html=True)

# #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# #     with tabs[3]:
# #         today_str = date.today().isoformat()
# #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# #         _mcq_show_form = True  # controls whether to show the question form

# #         if existing_response:
# #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# #                 st.session_state["retake_mcq"] = True
# #                 st.session_state["show_health_summary"] = False
# #                 # Clear cached questions so fresh ones load
# #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# #                 st.rerun()
# #             if not st.session_state.get("retake_mcq"):
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             prescriptions = _cached_prescriptions(patient_id)
# #             if not prescriptions:
# #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             # Cache questions per patient per day — no need to call GROQ on every rerun
# #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# #             if _q_key not in st.session_state:
# #                 with st.spinner("Loading your personalized health questions..."):
# #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# #             questions = st.session_state[_q_key]

# #             if not questions:
# #                 st.error("Could not generate questions. Please try again.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             st.markdown("""
# #             <div class="card" style="margin-bottom: 1.5rem;">
# #                 <div class="card-header">📋 Today's Health Questions</div>
# #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# #                 </p>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             selected_options = {}

# #             for q in questions:
# #                 qid = str(q["id"])
# #                 category_icons = {
# #                     "symptom": "🤒",
# #                     "adherence": "💊",
# #                     "side_effect": "⚠️",
# #                     "wellbeing": "💚"
# #                 }
# #                 icon = category_icons.get(q.get("category", ""), "❓")

# #                 st.markdown(f"""
# #                 <div class="card" style="margin-bottom: 1rem;">
# #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# #                     </div>
# #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# #                         {q['question']}
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 option_labels = [opt["text"] for opt in q["options"]]
# #                 choice = st.radio(
# #                     label=q["question"],
# #                     options=range(len(option_labels)),
# #                     format_func=lambda i, opts=option_labels: opts[i],
# #                     key=f"mcq_{qid}",
# #                     label_visibility="collapsed"
# #                 )
# #                 selected_options[qid] = choice
# #                 st.markdown("---")

# #             col_btn1, col_btn2 = st.columns([3, 1])
# #             with col_btn1:
# #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# #                     total_score = 0
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         try:
# #                             total_score += q["options"][idx]["score"]
# #                         except (IndexError, KeyError):
# #                             pass

# #                     status = mcq_agent.compute_status(total_score)
# #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# #                     responses_data = []
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         responses_data.append({
# #                             "question": q["question"],
# #                             "category": q.get("category"),
# #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# #                         })

# #                     doctor_id = patient.get("doctor_id")
# #                     save_mcq_response(
# #                         patient_id=patient_id,
# #                         doctor_id=doctor_id,
# #                         date_str=today_str,
# #                         responses_json=json.dumps(responses_data),
# #                         total_score=total_score,
# #                         status=status,
# #                         side_effects=json.dumps(side_effects),
# #                         adherence_status=adherence_status
# #                     )

# #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# #                                            symptoms, adherence_status, side_effects)

# #                     st.session_state["retake_mcq"] = False
# #                     st.session_state["show_health_summary"] = True
# #                     # Invalidate ALL cached data — must happen before rerun so
# #                     # check_consecutive_worsening sees the row just saved
# #                     _cached_patient_login.clear()
# #                     _cached_mcq_response_today.clear()
# #                     _cached_mcq_responses.clear()
# #                     _cached_patient_alerts.clear()
# #                     # Also bust the worsening booking state so a fresh check runs
# #                     st.session_state.pop(f"worsening_booking_step_{patient_id}_tab", None)
# #                     st.session_state.pop(f"health_data_{patient_id}", None)
# #                     st.rerun()

# #         # ── Worsening Trend Early Warning ─────────────────────────────────────
# #         # Shown whenever consecutive worsening is detected (after submission or
# #         # on return visits).  Booking is ALWAYS patient-initiated — no auto-booking.
# #         _worsening_doctor_id = patient.get("doctor_id")
# #         _render_worsening_warning(patient_id, patient, _worsening_doctor_id, consecutive_n=2, context="tab")

# #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# #         # Show automatically after submission OR when today's response already exists
# #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# #         if _show_summary:
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             st.markdown("### 📊 Your Health Summary")

# #             # ── AI Health Report ──────────────────────────────────────────────
# #             col_ai1, col_ai2 = st.columns([4, 1])
# #             with col_ai2:
# #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# #             if _gen_report or st.session_state.get("show_health_summary"):
# #                 # Cache summary per patient per day - expensive GROQ call
# #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# #                 if _gen_report or _sum_key not in st.session_state:
# #                     with st.spinner("AI is analyzing your health data..."):
# #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# #                 summary = st.session_state[_sum_key]
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# #                     <p style="line-height: 1.7;">{summary}</p>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #             # ── Health Indicators ─────────────────────────────────────────────
# #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# #             st.markdown(f"""
# #             <div class="card">
# #                 <div class="card-header">Health Indicators</div>
# #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# #                     </div>
# #                 </div>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             # ── Health Trend Chart ────────────────────────────────────────────
# #             responses = _cached_mcq_responses(patient_id, limit=30)
# #             if responses:
# #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# #                 import pandas as pd
# #                 import plotly.graph_objects as go

# #                 chart_responses = list(reversed(responses))
# #                 dates  = [r["date"] for r in chart_responses]
# #                 scores = [r["total_score"] for r in chart_responses]
# #                 statuses = [r["status"] for r in chart_responses]

# #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# #                 fig = go.Figure()
# #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[max(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[min(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=scores,
# #                     mode="lines+markers",
# #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# #                     marker=dict(size=10, color=marker_colors,
# #                                 line=dict(color="#1a1a2e", width=2)),
# #                     name="Health Score",
# #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# #                 ))

# #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                 for d, s, st_ in zip(dates, scores, statuses):
# #                     fig.add_annotation(
# #                         x=d, y=s,
# #                         text=status_icons_map.get(st_, ""),
# #                         showarrow=False,
# #                         yshift=18, font=dict(size=13)
# #                     )

# #                 fig.update_layout(
# #                     paper_bgcolor="rgba(0,0,0,0)",
# #                     plot_bgcolor="rgba(0,0,0,0)",
# #                     font=dict(color="#A89FC8", size=12),
# #                     margin=dict(l=10, r=10, t=10, b=10),
# #                     height=300,
# #                     xaxis=dict(
# #                         showgrid=False, zeroline=False,
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title=""
# #                     ),
# #                     yaxis=dict(
# #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title="Score"
# #                     ),
# #                     hoverlabel=dict(
# #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# #                         font=dict(color="white", size=13)
# #                     ),
# #                     showlegend=False
# #                 )

# #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# #                 st.markdown("""
# #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 # ── Recent Check-in History ───────────────────────────────────
# #                 st.markdown("#### 📋 Recent Daily Check-in History")
# #                 for r in responses:
# #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                     color = status_colors.get(r["status"], "#A78BFA")
# #                     icon = status_icons.get(r["status"], "•")
# #                     st.markdown(f"""
# #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# #                         </div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# #                             Adherence: {r.get('adherence_status', 'N/A')}
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)

# #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# #     with tabs[4]:
# #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# #     with tabs[5]:
# #         _render_patient_opd(patient_id, patient)


# # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# #     """Render the patient-facing Alerts & Notifications tab."""
# #     st.markdown("### 🔔 Alerts & Notifications")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# #         'and doctor messages are shown here.</p>',
# #         unsafe_allow_html=True
# #     )

# #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# #     if risk_level == "high":
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">🚨</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# #                         Please contact your doctor or visit the clinic immediately.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── Worsening Trend Early Warning (also surfaced here for discoverability) ──
# #     _wt_doctor_id = patient.get("doctor_id")
# #     _render_worsening_warning(patient_id, patient, _wt_doctor_id, consecutive_n=2, context="alerts")

# #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# #     missed_dose_dates = []
# #     for r in recent_responses:
# #         adh = (r.get("adherence_status") or "").lower()
# #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# #             missed_dose_dates.append(r["date"])

# #     if missed_dose_dates:
# #         dates_str = ", ".join(missed_dose_dates[:3])
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">💊</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# #                         Consistent adherence is key to recovery — please take medications as prescribed.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# #     all_alerts = _cached_patient_alerts(patient_id)
# #     unresolved = [a for a in all_alerts if not a["resolved"]]
# #     resolved = [a for a in all_alerts if a["resolved"]]

# #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# #         st.markdown("""
# #         <div class="card" style="text-align:center;padding:2rem;">
# #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# #                 No active alerts. Keep taking your medications and completing daily check-ins!
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #         return

# #     severity_config = {
# #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# #     }
# #     type_labels = {
# #         "mcq_health_check":       "Health Check Alert",
# #         "doctor_message":         "Doctor Message",
# #         "missed_dose":            "Missed Dose",
# #         "high_risk":              "High Risk Warning",
# #         "worsening_opd_booked":   "Worsening Trend — OPD Booked",
# #         "worsening_condition":    "Worsening Condition",
# #         "patient_reported_symptoms": "Patient Reported Symptoms",
# #     }

# #     if unresolved:
# #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# #         for alert in unresolved:
# #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #             created = alert["created_at"][:16].replace("T", " ")

# #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# #                 st.markdown(f"""
# #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# #                              border-left:3px solid {cfg['color']};">
# #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # {alert['message']}</pre>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# #                     resolve_alert(alert["id"])
# #                     _cached_patient_alerts.clear()
# #                     st.rerun()

# #     if resolved:
# #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# #             for alert in resolved:
# #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #                 created = alert["created_at"][:16].replace("T", " ")
# #                 st.markdown(f"""
# #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# #                     <div style="display:flex;justify-content:space-between;">
# #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)


# # # ── MCQ result card ───────────────────────────────────────────────────────────

# # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# #     status = response["status"]
# #     score = response["total_score"]
# #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #     color = status_colors.get(status, "#A78BFA")
# #     icon = status_icons.get(status, "•")

# #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# #     # Safely escape feedback strings to prevent HTML injection
# #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# #     st.markdown(f"""
# #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# #         <div style="text-align: center; padding: 1rem 0;">
# #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# #         </div>
# #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     adherence_status = response.get("adherence_status", "")
# #     side_effects_raw = response.get("side_effects", "[]")
# #     try:
# #         side_effects = json.loads(side_effects_raw)
# #     except Exception:
# #         side_effects = []

# #     col1, col2 = st.columns(2)
# #     with col1:
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">💊 Medication Adherence</div>
# #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #     with col2:
# #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">⚠️ Side Effects</div>
# #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     if show_history and patient_id:
# #         st.markdown(
# #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# #             unsafe_allow_html=True
# #         )


# # # ── Alert firing logic ────────────────────────────────────────────────────────

# # def _render_worsening_warning(patient_id: str, patient: dict, doctor_id: str, consecutive_n: int = 2, context: str = "tab"):
# #     """
# #     Worsening Trend Early Warning banner.

# #     Shown on the Daily Health Check tab immediately after MCQ submission
# #     (and on every subsequent visit while the trend persists).  It does NOT
# #     book an appointment automatically — it offers the patient a clearly
# #     labelled 'Book Appointment' button.  Only when the patient clicks that
# #     button does the UI fetch real available slots and confirm the booking.

# #     Session-state keys used (all scoped to patient_id):
# #         worsening_booking_step_{pid}   : None | 'select' | 'confirm'
# #         worsening_booking_slots_{pid}  : list[dict]  — raw slot rows
# #         worsening_booking_doctor_{pid} : dict        — chosen doctor row
# #         worsening_booking_slot_{pid}   : dict        — chosen slot row
# #     """
# #     # ── Debug: always show last 3 MCQ statuses so you can verify DB state ────
# #     from data.database import get_mcq_responses as _gmr
# #     _recent = _gmr(patient_id, limit=3)
# #     _statuses = [r["status"] for r in _recent]
# #     _is_worsening = check_consecutive_worsening(patient_id, consecutive_n)
# #     st.caption(
# #         f"🔍 Debug — last {len(_statuses)} MCQ statuses: {_statuses} | "
# #         f"consecutive_worsening({consecutive_n}) → **{_is_worsening}**"
# #     )

# #     # ── Guard: only render when consecutive worsening detected ───────────────
# #     if not check_consecutive_worsening(patient_id, consecutive_n):
# #         # If the warning was previously shown, clean up stale state gracefully
# #         for sfx in ("step", "slots", "doctor", "slot"):
# #             st.session_state.pop(f"worsening_booking_{sfx}_{patient_id}_{context}", None)
# #         return

# #     step_key   = f"worsening_booking_step_{patient_id}_{context}"
# #     slots_key  = f"worsening_booking_slots_{patient_id}_{context}"
# #     doctor_key = f"worsening_booking_doctor_{patient_id}_{context}"
# #     slot_key   = f"worsening_booking_slot_{patient_id}_{context}"

# #     step = st.session_state.get(step_key)  # None | 'select' | 'confirm'

# #     # ── Main warning banner ───────────────────────────────────────────────────
# #     st.markdown(f"""
# #     <div class="card" style="border-left:4px solid #F87171;
# #          background:rgba(248,113,113,0.08);margin-bottom:1rem;">
# #         <div style="display:flex;align-items:flex-start;gap:0.9rem;">
# #             <span style="font-size:2rem;line-height:1;">🚨</span>
# #             <div>
# #                 <div style="font-weight:700;color:#F87171;font-size:1.05rem;margin-bottom:0.3rem;">
# #                     Worsening Trend Detected
# #                 </div>
# #                 <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;">
# #                     Your last <strong style="color:#F87171;">{consecutive_n} health check-ins</strong>
# #                     have both shown a <em>Worsening</em> status.
# #                     Your doctor has been notified via an alert.
# #                     We recommend booking a consultation soon.
# #                 </div>
# #             </div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # ── Step 0: Offer the booking button (no auto-booking) ───────────────────
# #     if step is None:
# #         if st.button(
# #             "📅 Book an Appointment with My Doctor",
# #             key=f"worsening_book_btn_{patient_id}_{context}",
# #             type="primary",
# #         ):
# #             # Fetch available slots now (lazy — only on click)
# #             doctors = get_available_opd_doctors()
# #             # Filter to the patient's own doctor first; fall back to all
# #             my_doctor_id = patient.get("doctor_id")
# #             my_doctors = [d for d in doctors if d["doctor_id"] == my_doctor_id] or doctors

# #             all_slots = []
# #             for doc in my_doctors:
# #                 dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
# #                 for d in dates[:3]:  # look at next 3 available dates only
# #                     slots = get_available_opd_slots(doc["doctor_id"], d)
# #                     for s in slots:
# #                         all_slots.append({**s, "doctor_name": doc["name"],
# #                                            "doctor_id": doc["doctor_id"]})

# #             if not all_slots:
# #                 st.warning(
# #                     "⚠️ No available OPD slots found right now. "
# #                     "Please contact the clinic directly or check back later."
# #                 )
# #                 return

# #             st.session_state[slots_key] = all_slots
# #             st.session_state[step_key]  = "select"
# #             st.rerun()
# #         return  # nothing more to render at step 0

# #     # ── Step 1: Slot selector ─────────────────────────────────────────────────
# #     if step == "select":
# #         all_slots = st.session_state.get(slots_key, [])
# #         if not all_slots:
# #             st.warning("No slots loaded. Please try again.")
# #             st.session_state.pop(step_key, None)
# #             return

# #         st.markdown(
# #             "<div style='color:var(--text-secondary);font-size:0.88rem;"
# #             "margin-bottom:0.6rem;'>Select an available slot:</div>",
# #             unsafe_allow_html=True,
# #         )

# #         # Build human-readable labels
# #         slot_labels = [
# #             f"Dr. {s['doctor_name']} — {s['slot_date']}  {s['start_time']}–{s['end_time']}"
# #             for s in all_slots
# #         ]
# #         chosen_idx = st.selectbox(
# #             "Available slots",
# #             options=range(len(slot_labels)),
# #             format_func=lambda i: slot_labels[i],
# #             key=f"worsening_slot_select_{patient_id}_{context}",
# #             label_visibility="collapsed",
# #         )

# #         col_ok, col_cancel = st.columns([2, 1])
# #         with col_ok:
# #             if st.button(
# #                 "Confirm this slot →",
# #                 key=f"worsening_confirm_btn_{patient_id}_{context}",
# #                 type="primary",
# #                 use_container_width=True,
# #             ):
# #                 chosen = all_slots[chosen_idx]
# #                 st.session_state[slot_key]   = chosen
# #                 st.session_state[doctor_key] = {"name": chosen["doctor_name"],
# #                                                  "id":   chosen["doctor_id"]}
# #                 st.session_state[step_key]   = "confirm"
# #                 st.rerun()
# #         with col_cancel:
# #             if st.button(
# #                 "Cancel",
# #                 key=f"worsening_cancel_select_{patient_id}_{context}",
# #                 use_container_width=True,
# #             ):
# #                 for k in (step_key, slots_key, doctor_key, slot_key):
# #                     st.session_state.pop(k, None)
# #                 st.rerun()
# #         return

# #     # ── Step 2: Final confirmation ────────────────────────────────────────────
# #     if step == "confirm":
# #         chosen_slot   = st.session_state.get(slot_key, {})
# #         chosen_doctor = st.session_state.get(doctor_key, {})

# #         st.markdown(f"""
# #         <div class="card" style="border:1px solid rgba(167,139,250,0.4);
# #              background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
# #             <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
# #                 📋 Confirm Booking
# #             </div>
# #             <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.8;">
# #                 <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
# #                 <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
# #                 <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         col_yes, col_no = st.columns(2)
# #         with col_yes:
# #             if st.button(
# #                 "✅ Book Appointment",
# #                 key=f"worsening_book_yes_{patient_id}_{context}",
# #                 type="primary",
# #                 use_container_width=True,
# #             ):
# #                 success = book_opd_slot(
# #                     slot_id=chosen_slot["id"],
# #                     patient_id=patient_id,
# #                     patient_name=patient.get("name", ""),
# #                 )
# #                 # Clean up state regardless of outcome
# #                 for k in (step_key, slots_key, doctor_key, slot_key):
# #                     st.session_state.pop(k, None)
# #                 _cached_opd_bookings.clear()

# #                 if success:
# #                     # Upgrade the doctor-side alert to note the booking
# #                     create_alert(
# #                         patient_id=patient_id,
# #                         alert_type="worsening_opd_booked",
# #                         message=(
# #                             f"Patient self-booked an OPD slot in response to worsening trend alert.\n"
# #                             f"Slot: Dr. {chosen_doctor.get('name','')} on "
# #                             f"{chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
# #                         ),
# #                         severity="medium",
# #                         doctor_id=doctor_id,
# #                     )
# #                     st.success(
# #                         f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
# #                         f"on {chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
# #                     )
# #                 else:
# #                     st.error(
# #                         "❌ That slot was just taken by someone else. "
# #                         "Please go to the Online OPD tab to pick another slot."
# #                     )
# #                 st.rerun()

# #         with col_no:
# #             if st.button(
# #                 "← Back",
# #                 key=f"worsening_book_back_{patient_id}_{context}",
# #                 use_container_width=True,
# #             ):
# #                 st.session_state[step_key] = "select"
# #                 st.rerun()


# # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# #     """Fire structured doctor alerts based on MCQ response."""
# #     trigger = False
# #     reasons = []

# #     if total_score < 0:
# #         trigger = True
# #         reasons.append("negative_score")

# #     if check_consecutive_worsening(patient_id, 2):
# #         trigger = True
# #         reasons.append("consecutive_worsening")

# #     if side_effects:
# #         trigger = True
# #         reasons.append("side_effects")

# #     if not trigger:
# #         return

# #     action_map = {
# #         "Improving": "Continue medication as prescribed",
# #         "Stable": "Monitor closely, follow up in 2-3 days",
# #         "Worsening": "Immediate consultation required"
# #     }

# #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# #     alert_message = f"""Patient ID: {patient_id}
# # Doctor ID: {doctor_id}
# # Disease: {patient.get('disease', 'N/A')}
# # Current Status: {status}
# # Score: {total_score:+d}

# # Key Symptoms Reported:
# # {symptoms_text}

# # Medication Adherence:
# # {adherence_text}

# # Side Effects:
# # {side_effects_text}

# # Recommended Action:
# # - {action_map.get(status, 'Monitor patient')}

# # Triggered By: {reasons_text}"""

# #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# #     create_alert(
# #         patient_id=patient_id,
# #         alert_type="mcq_health_check",
# #         message=alert_message,
# #         severity=severity,
# #         doctor_id=doctor_id
# #     )




# # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # def _render_patient_opd(patient_id: str, patient: dict):
# #     """Full Online OPD booking UI for the patient dashboard."""
# #     import streamlit as st
# #     from datetime import date, datetime

# #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# #         'Slots are real-time — once booked they disappear for other patients.</p>',
# #         unsafe_allow_html=True
# #     )

# #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# #     with opd_subtabs[0]:
# #         doctors = _cached_opd_doctors()

# #         if not doctors:
# #             st.info("No doctors have published OPD slots yet. Please check back later.")
# #         else:
# #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# #             selected_doctor_id = doctor_options[selected_label]

# #             available_dates = _cached_opd_dates(selected_doctor_id)
# #             if not available_dates:
# #                 st.warning("This doctor has no available slots right now.")
# #             else:
# #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# #                 chosen_date_str = st.selectbox(
# #                     "Select Date",
# #                     list(date_labels.keys()),
# #                     format_func=lambda x: date_labels[x],
# #                     key="opd_date_sel"
# #                 )

# #                 # Check if patient already booked on this day with this doctor
# #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# #                 if already_booked:
# #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# #                 else:
# #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# #                     if not free_slots:
# #                         st.error("All slots for this date are fully booked. Please choose another date.")
# #                     else:
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# #                                 </div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         slot_options = {
# #                             f"{s['start_time']} – {s['end_time']}": s['id']
# #                             for s in free_slots
# #                         }
# #                         chosen_slot_label = st.selectbox(
# #                             "Choose a time slot",
# #                             list(slot_options.keys()),
# #                             key="opd_slot_sel"
# #                         )
# #                         chosen_slot_id = slot_options[chosen_slot_label]

# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                                 <strong>Doctor:</strong> {selected_label}<br>
# #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# #                             if success:
# #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# #                                 st.balloons()
# #                                 _cached_opd_bookings.clear()
# #                                 _cached_opd_slots.clear()
# #                                 _cached_has_booking.clear()
# #                                 st.rerun()
# #                             else:
# #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# #                                 _cached_opd_slots.clear()
# #                                 st.rerun()

# #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# #     with opd_subtabs[1]:
# #         st.markdown("#### 🗓️ Your OPD Bookings")
# #         my_bookings = _cached_opd_bookings(patient_id)

# #         if not my_bookings:
# #             st.markdown("""
# #             <div class="card" style="text-align:center;padding:2rem;">
# #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# #             </div>
# #             """, unsafe_allow_html=True)
# #         else:
# #             today_str = date.today().isoformat()
# #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# #             if upcoming:
# #                 st.markdown("##### 📅 Upcoming")
# #                 for booking in upcoming:
# #                     visited = bool(booking["patient_visited"])
# #                     color = "#34D399" if visited else "#A78BFA"
# #                     status = "✅ Consulted" if visited else "⏳ Pending"
# #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# #                     room_name = f"MediCore-{safe_room}"

# #                     col_b, col_c = st.columns([4, 1])
# #                     with col_b:
# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# #                                 <div>
# #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# #                                     </div>
# #                                 </div>
# #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)
# #                     with col_c:
# #                         if not visited:
# #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# #                                 success = cancel_opd_booking(booking["id"], patient_id)
# #                                 if success:
# #                                     st.success("Booking cancelled.")
# #                                     _cached_opd_bookings.clear()
# #                                     _cached_opd_slots.clear()
# #                                     _cached_has_booking.clear()
# #                                     st.rerun()

# #                     # ── Embedded video call (Jitsi) ───────────────────────────
# #                     if not visited:
# #                         call_key = f"show_call_pat_{booking['id']}"
# #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# #                                      use_container_width=True, type="primary"):
# #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# #                         if st.session_state.get(call_key, False):
# #                             patient_name = st.session_state.get("patient_id", "Patient")
# #                             encoded_name = str(patient_name).replace(" ", "%20")
# #                             st.components.v1.html(f"""
# #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# #                             <iframe
# #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# #                                 allowfullscreen="true"
# #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# #                             ></iframe>
# #                             </body></html>
# #                             """, height=560)

# #             if past:
# #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# #                     for booking in past:
# #                         visited = bool(booking["patient_visited"])
# #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# #                         status = "✅ Consulted" if visited else "❌ Not attended"
# #                         color = "#34D399" if visited else "#F87171"
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# #                             <div style="display:flex;justify-content:space-between;">
# #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# # # ── Patient login ─────────────────────────────────────────────────────────────

# # def render_patient_login():
# #     st.markdown("""
# #     <div style="max-width: 480px; margin: 4rem auto;">
# #         <div class="page-header" style="text-align: center;">
# #             <h1>🏥 Patient Login</h1>
# #             <p>Enter your Patient ID to access your health portal</p>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     with st.container():
# #         col1, col2, col3 = st.columns([1, 2, 1])
# #         with col2:
# #             patient_id = st.text_input(
# #                 "Patient ID",
# #                 placeholder="e.g. PAT-20260413-0001",
# #                 label_visibility="collapsed"
# #             )
# #             st.markdown(
# #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# #                 'Your ID was provided by your doctor at registration</p>',
# #                 unsafe_allow_html=True
# #             )

# #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# #                 if patient_id:
# #                     patient = get_patient(patient_id.strip().upper())
# #                     if patient:
# #                         st.session_state["patient_id"] = patient_id.strip().upper()
# #                         st.session_state["patient_logged_in"] = True
# #                         st.rerun()
# #                     else:
# #                         st.error("Patient ID not found. Check with your doctor.")
# #                 else:
# #                     st.warning("Please enter your Patient ID.")




# import streamlit as st
# import json
# import requests
# from datetime import date, datetime
# from data.database import (
#     get_patient, get_patient_prescriptions, get_chat_history,
#     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
#     create_alert, check_consecutive_worsening, get_patient_alerts,
#     resolve_alert,
#     get_available_opd_doctors, get_available_opd_dates_for_doctor,
#     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
#     get_patient_opd_bookings, check_patient_has_booking
# )
# from agents.orchestrator import AgentOrchestrator
# from agents.scheduling_agent import (
#     SchedulingAgent, get_auth_url,
#     exchange_code_for_tokens, refresh_access_token
# )
# from agents.mcq_agent import MCQAgent


# # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_chat_history(patient_id, limit=20):
#     return get_chat_history(patient_id, limit)

# @st.cache_data(ttl=15, show_spinner=False)
# def _cached_prescriptions(patient_id):
#     return get_patient_prescriptions(patient_id)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_patient_alerts(patient_id):
#     return get_patient_alerts(patient_id)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_opd_bookings(patient_id):
#     return get_patient_opd_bookings(patient_id)

# @st.cache_data(ttl=20, show_spinner=False)
# def _cached_mcq_response_today(patient_id, today_str):
#     return get_mcq_response_for_date(patient_id, today_str)

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_mcq_responses(patient_id, limit=30):
#     return get_mcq_responses(patient_id, limit)

# @st.cache_data(ttl=60, show_spinner=False)
# def _cached_opd_doctors():
#     return get_available_opd_doctors()

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_opd_dates(doctor_id):
#     return get_available_opd_dates_for_doctor(doctor_id)

# @st.cache_data(ttl=15, show_spinner=False)
# def _cached_opd_slots(doctor_id, date_str):
#     return get_available_opd_slots(doctor_id, date_str)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_has_booking(patient_id, doctor_id, date_str):
#     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # ── OAuth token helpers ───────────────────────────────────────────────────────

# def _handle_google_oauth_callback():
#     """
#     Called once at the top of app.py.
#     If Google redirected back with ?code=..., exchange it for tokens,
#     set mode=patient, and mark patient_google_authed=True.
#     Only removes OAuth-specific params, preserving the _s session-restore param.
#     """
#     params = st.query_params
#     auth_code = params.get("code")
#     if auth_code and not st.session_state.get("google_access_token"):
#         try:
#             tokens = exchange_code_for_tokens(auth_code)
#             if "access_token" in tokens:
#                 st.session_state["google_access_token"] = tokens["access_token"]
#                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
#                 st.session_state["patient_google_authed"] = True
#                 st.session_state["mode"] = "patient"
#                 st.toast("✅ Google sign-in successful!", icon="✅")
#         except Exception as e:
#             st.warning(f"Google OAuth error: {e}")
#         # Remove only OAuth-specific params, preserving _s session param
#         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
#             try:
#                 if oauth_key in st.query_params:
#                     del st.query_params[oauth_key]
#             except Exception:
#                 pass


# def _get_valid_access_token() -> str | None:
#     """Return a valid Google access token from session, refreshing if needed."""
#     token = st.session_state.get("google_access_token")
#     if token:
#         return token
#     refresh_tok = st.session_state.get("google_refresh_token")
#     if refresh_tok:
#         new_token = refresh_access_token(refresh_tok)
#         if new_token:
#             st.session_state["google_access_token"] = new_token
#             return new_token
#     return None


# # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# @st.cache_resource(show_spinner=False)
# def _get_orchestrator():
#     return AgentOrchestrator()

# @st.cache_resource(show_spinner=False)
# def _get_scheduler():
#     return SchedulingAgent()

# @st.cache_resource(show_spinner=False)
# def _get_mcq_agent():
#     return MCQAgent()

# @st.cache_data(ttl=120, show_spinner=False)
# def _cached_patient_login(patient_id):
#     """Run the expensive on_patient_login only once per 2 minutes."""
#     return _get_orchestrator().on_patient_login(patient_id)

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_get_patient(patient_id):
#     return get_patient(patient_id)


# # ── Main dashboard ────────────────────────────────────────────────────────────

# def render_patient_dashboard(patient_id):
#     # OAuth callback is handled at app level (app.py) — no need to call it here again.
#     orchestrator = _get_orchestrator()
#     scheduler = _get_scheduler()
#     mcq_agent = _get_mcq_agent()
#     patient = _cached_get_patient(patient_id)

#     if not patient:
#         st.error("Patient not found. Check your Patient ID.")
#         return

#     st.markdown(f"""
#     <div class="page-header">
#         <h1>🧑‍⚕️ Patient Portal</h1>
#         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
#     </div>
#     """, unsafe_allow_html=True)

#     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
#     _health_key = f"health_data_{patient_id}"
#     if _health_key not in st.session_state:
#         with st.spinner("Loading your health data..."):
#             st.session_state[_health_key] = _cached_patient_login(patient_id)
#     health_data = st.session_state[_health_key]

#     risk = health_data.get("risk", {})
#     adherence = health_data.get("adherence", {})
#     trends = health_data.get("trends", {})

#     col1, col2, col3, col4 = st.columns(4)
#     risk_level = risk.get("level", "low")
#     col1.metric("Risk Level", risk_level.upper())
#     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
#     col3.metric("Active Meds", adherence.get("active_medications", 0))
#     col4.metric("Health Trend", trends.get("trend", "stable").title())

#     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

#     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD, Proactive Agent
#     tabs = st.tabs([
#         "💬 AI Assistant",
#         "📅 My Schedule",
#         "💊 My Prescriptions",
#         "🩺 Daily Health Check",
#         "🔔 Alerts",
#         "🖥️ Online OPD",
#         "🤖 My Health Agent",
#     ])

#     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
#     with tabs[0]:
#         st.markdown("### 🤖 Autonomous AI Health Agent")
#         st.markdown(
#             '<p style="color: var(--text-secondary);">'
#             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
#             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
#             '</p>',
#             unsafe_allow_html=True
#         )

#         # ── Quick action chips ─────────────────────────────────────────────
#         st.markdown("""
#         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
#                          cursor:pointer;">📅 Book Appointment</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          💊 My Prescriptions</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          🩺 Check Symptoms</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          🔔 My Alerts</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          ❌ Cancel Appointment</span>
#         </div>
#         """, unsafe_allow_html=True)

#         history = _cached_chat_history(patient_id, 20)
#         for msg in history:
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])

#         # ── Triage action buttons ─────────────────────────────────────────
#         _triage_key = f"pending_triage_{patient_id}"
#         _triage_msg_key = f"pending_triage_msg_{patient_id}"
#         _confirm_key = f"triage_confirm_{patient_id}"

#         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
#             triage_level = st.session_state[_triage_key]
#             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

#             if triage_level == "URGENT":
#                 btn_label = "🚨 Alert My Doctor Now"
#                 btn_type = "primary"
#                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
#             else:
#                 btn_label = "📅 Book Urgent Appointment"
#                 btn_type = "secondary"
#                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

#             if not st.session_state.get(_confirm_key):
#                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
#                     st.session_state[_confirm_key] = True
#                     st.rerun()
#             else:
#                 st.warning(confirm_msg)
#                 col_yes, col_no = st.columns(2)
#                 with col_yes:
#                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
#                         severity = "high" if triage_level == "URGENT" else "medium"
#                         alert_message = (
#                             f"[Agentic AI — Patient Reported Symptoms]\n"
#                             f"Patient described: \"{symptom_text}\"\n"
#                             f"AI Triage Verdict: {triage_level}\n"
#                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
#                                else "📅 Patient requests a follow-up appointment.")
#                         )
#                         _pt = get_patient(patient_id)
#                         _doctor_id = _pt.get("doctor_id") if _pt else None
#                         create_alert(
#                             patient_id=patient_id,
#                             alert_type="patient_reported_symptoms",
#                             message=alert_message,
#                             severity=severity,
#                             doctor_id=_doctor_id
#                         )
#                         st.session_state.pop(_triage_key, None)
#                         st.session_state.pop(_triage_msg_key, None)
#                         st.session_state.pop(_confirm_key, None)
#                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
#                                    else "✅ Alert sent to your doctor!")
#                         st.rerun()
#                 with col_no:
#                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
#                         st.session_state.pop(_triage_key, None)
#                         st.session_state.pop(_triage_msg_key, None)
#                         st.session_state.pop(_confirm_key, None)
#                         st.rerun()

#         # ── Action result display (non-triage confirmations) ──────────────
#         _action_result_key = f"action_result_{patient_id}"
#         if st.session_state.get(_action_result_key):
#             ar = st.session_state[_action_result_key]
#             action = ar.get("action", "")
#             confirmed = ar.get("confirmed", False)
#             success = ar.get("success", False)

#             if confirmed and success:
#                 if action == "book_appointment":
#                     bd = ar.get("booking_details", {})
#                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
#                 elif action == "cancel_appointment":
#                     st.success("✅ Appointment successfully cancelled.")

#             st.session_state.pop(_action_result_key, None)

#         # ── Chat input ────────────────────────────────────────────────────
#         placeholder = (
#             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
#             "or 'Show my prescriptions' or 'I have chest pain'..."
#         )
#         if prompt := st.chat_input(placeholder):
#             with st.chat_message("user"):
#                 st.markdown(prompt)

#             with st.chat_message("assistant"):
#                 with st.spinner("🤖 Analysing and acting..."):
#                     result = orchestrator.on_patient_message(
#                         patient_id, prompt,
#                         use_agentic=True,
#                         session_state=st.session_state
#                     )

#                 if not isinstance(result, dict):
#                     result = {"reply": str(result), "triage": None, "action": "general_health"}

#                 reply = result.get("reply", "")
#                 triage = result.get("triage")
#                 action = result.get("action", "")
#                 confirmed = result.get("confirmed", False)
#                 success = result.get("success", False)

#                 # ── Show triage badge ──────────────────────────────────
#                 if triage == "URGENT":
#                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
#                 elif triage == "MODERATE":
#                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
#                 elif triage == "MILD":
#                     st.success("🟢 **MILD — Manageable at home for now.**")

#                 # ── Show action confirmation badge ────────────────────
#                 if confirmed and success:
#                     if action == "book_appointment":
#                         bd = result.get("booking_details", {})
#                         st.success(
#                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
#                             f"{bd.get('date', '')} · {bd.get('time', '')}"
#                         )
#                     elif action == "cancel_appointment":
#                         st.success("✅ **Appointment Cancelled Successfully**")

#                 st.markdown(reply)

#             # ── Post-response state management ────────────────────────
#             if triage in ("URGENT", "MODERATE"):
#                 st.session_state[_triage_key] = triage
#                 st.session_state[_triage_msg_key] = prompt
#                 st.session_state.pop(_confirm_key, None)
#             else:
#                 st.session_state.pop(_triage_key, None)
#                 st.session_state.pop(_triage_msg_key, None)
#                 st.session_state.pop(_confirm_key, None)

#             _cached_chat_history.clear()
#             st.rerun()

#     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
#     with tabs[1]:
#         st.markdown("### 📅 Medication Schedule")
#         col1, col2 = st.columns([3, 1])

#         with col2:
#             access_token = _get_valid_access_token()

#             if access_token:
#                 # Token available — show sync button
#                 if st.button("📆 Sync to Google Calendar"):
#                     with st.spinner("Syncing to calendar..."):
#                         result = scheduler.schedule_for_patient(patient_id, access_token)
#                     if result["success"]:
#                         st.success(result["message"])
#                     else:
#                         st.warning(result.get("message", "Sync failed."))
#                         if result.get("errors"):
#                             for e in result["errors"]:
#                                 st.caption(f"⚠ {e}")
#                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
#                     st.session_state.pop("google_access_token", None)
#                     st.session_state.pop("google_refresh_token", None)
#                     st.rerun()
#             else:
#                 # No access token in session (e.g. user disconnected or session expired).
#                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
#                 st.markdown("""
#                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
#                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
#                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
#                         📅 Google Calendar Disconnected
#                     </div>
#                     <div style="color:#A89FC8;font-size:0.82rem;">
#                         Your Google session token has expired. Click below to reconnect —
#                         this uses the same Google account you signed in with.
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
#                 try:
#                     auth_url = get_auth_url()
#                     st.markdown(f"""
#                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
#                         <div style="
#                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
#                             background:#fff;color:#3c4043;border:1px solid #dadce0;
#                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
#                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
#                             <svg width="16" height="16" viewBox="0 0 18 18">
#                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
#                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
#                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
#                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
#                             </svg>
#                             Reconnect Google Calendar
#                         </div>
#                     </a>
#                     """, unsafe_allow_html=True)
#                 except Exception:
#                     st.info("Google Calendar integration not configured. Ask your administrator.")

#         schedule = scheduler.get_schedule_preview(patient_id)
#         if not schedule:
#             st.info("No schedule available. Ask your doctor to create a prescription.")
#         else:
#             current_date = None
#             for item in schedule:
#                 if item["date"] != current_date:
#                     current_date = item["date"]
#                     st.markdown(f"**📅 {current_date}**")
#                 st.markdown(f"""
#                 <div class="schedule-item">
#                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
#                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
#                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
#                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
#                 </div>
#                 """, unsafe_allow_html=True)

#     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
#     with tabs[2]:
#         st.markdown("### 💊 My Prescriptions")
#         prescriptions = _cached_prescriptions(patient_id)
#         if not prescriptions:
#             st.info("No prescriptions assigned yet. Please consult your doctor.")
#         else:
#             for i, pr in enumerate(prescriptions):
#                 st.markdown(f"""
#                 <div class="card">
#                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
#                 """, unsafe_allow_html=True)
#                 for m in pr.get("medicines", []):
#                     st.markdown(f"""
#                     <div class="medicine-card">
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
#                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
#                         </div>
#                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
#                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
#                         </div>
#                     </div>
#                     """, unsafe_allow_html=True)
#                 if pr.get("doctor_notes"):
#                     st.markdown(
#                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
#                         unsafe_allow_html=True
#                     )
#                 st.markdown("</div>", unsafe_allow_html=True)

#     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
#     with tabs[3]:
#         today_str = date.today().isoformat()
#         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

#         existing_response = _cached_mcq_response_today(patient_id, today_str)
#         _mcq_show_form = True  # controls whether to show the question form

#         if existing_response:
#             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
#             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#             if st.button("🔄 Retake Today's Check-in", type="secondary"):
#                 st.session_state["retake_mcq"] = True
#                 st.session_state["show_health_summary"] = False
#                 # Clear cached questions so fresh ones load
#                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
#                 st.rerun()
#             if not st.session_state.get("retake_mcq"):
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             prescriptions = _cached_prescriptions(patient_id)
#             if not prescriptions:
#                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             # Cache questions per patient per day — no need to call GROQ on every rerun
#             _q_key = f"mcq_questions_{patient_id}_{today_str}"
#             if _q_key not in st.session_state:
#                 with st.spinner("Loading your personalized health questions..."):
#                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
#             questions = st.session_state[_q_key]

#             if not questions:
#                 st.error("Could not generate questions. Please try again.")
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             st.markdown("""
#             <div class="card" style="margin-bottom: 1.5rem;">
#                 <div class="card-header">📋 Today's Health Questions</div>
#                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
#                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
#                 </p>
#             </div>
#             """, unsafe_allow_html=True)

#             selected_options = {}

#             for q in questions:
#                 qid = str(q["id"])
#                 category_icons = {
#                     "symptom": "🤒",
#                     "adherence": "💊",
#                     "side_effect": "⚠️",
#                     "wellbeing": "💚"
#                 }
#                 icon = category_icons.get(q.get("category", ""), "❓")

#                 st.markdown(f"""
#                 <div class="card" style="margin-bottom: 1rem;">
#                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
#                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
#                         {icon} {q.get('category', '').replace('_', ' ').title()}
#                     </div>
#                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
#                         {q['question']}
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)

#                 option_labels = [opt["text"] for opt in q["options"]]
#                 choice = st.radio(
#                     label=q["question"],
#                     options=range(len(option_labels)),
#                     format_func=lambda i, opts=option_labels: opts[i],
#                     key=f"mcq_{qid}",
#                     label_visibility="collapsed"
#                 )
#                 selected_options[qid] = choice
#                 st.markdown("---")

#             col_btn1, col_btn2 = st.columns([3, 1])
#             with col_btn1:
#                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
#                     total_score = 0
#                     for q in questions:
#                         qid = str(q["id"])
#                         idx = selected_options.get(qid, 0)
#                         try:
#                             total_score += q["options"][idx]["score"]
#                         except (IndexError, KeyError):
#                             pass

#                     status = mcq_agent.compute_status(total_score)
#                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

#                     responses_data = []
#                     for q in questions:
#                         qid = str(q["id"])
#                         idx = selected_options.get(qid, 0)
#                         responses_data.append({
#                             "question": q["question"],
#                             "category": q.get("category"),
#                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
#                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
#                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
#                         })

#                     doctor_id = patient.get("doctor_id")
#                     save_mcq_response(
#                         patient_id=patient_id,
#                         doctor_id=doctor_id,
#                         date_str=today_str,
#                         responses_json=json.dumps(responses_data),
#                         total_score=total_score,
#                         status=status,
#                         side_effects=json.dumps(side_effects),
#                         adherence_status=adherence_status
#                     )

#                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
#                                            symptoms, adherence_status, side_effects)

#                     st.session_state["retake_mcq"] = False
#                     st.session_state["show_health_summary"] = True
#                     # Invalidate cached data so next render is fresh
#                     _cached_patient_login.clear()
#                     _cached_mcq_response_today.clear()
#                     _cached_mcq_responses.clear()
#                     st.session_state.pop(f"health_data_{patient_id}", None)
#                     st.rerun()

#         # ── Inline Health Summary — shown after MCQ completion ────────────────
#         # Show automatically after submission OR when today's response already exists
#         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
#         if _show_summary:
#             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#             st.markdown("### 📊 Your Health Summary")

#             # ── AI Health Report ──────────────────────────────────────────────
#             col_ai1, col_ai2 = st.columns([4, 1])
#             with col_ai2:
#                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
#             if _gen_report or st.session_state.get("show_health_summary"):
#                 # Cache summary per patient per day - expensive GROQ call
#                 _sum_key = f"health_summary_{patient_id}_{today_str}"
#                 if _gen_report or _sum_key not in st.session_state:
#                     with st.spinner("AI is analyzing your health data..."):
#                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
#                 summary = st.session_state[_sum_key]
#                 st.markdown(f"""
#                 <div class="card">
#                     <div class="card-header">🤖 AI Clinical Assessment</div>
#                     <p style="line-height: 1.7;">{summary}</p>
#                 </div>
#                 """, unsafe_allow_html=True)

#             # ── Health Indicators ─────────────────────────────────────────────
#             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
#             risk_color = risk_colors.get(risk_level, "#A78BFA")
#             st.markdown(f"""
#             <div class="card">
#                 <div class="card-header">Health Indicators</div>
#                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
#                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
#                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
#                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
#                         <span style="color: var(--text-primary);">{patient['disease']}</span>
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)

#             # ── Health Trend Chart ────────────────────────────────────────────
#             responses = _cached_mcq_responses(patient_id, limit=30)
#             if responses:
#                 st.markdown("#### 📈 Health Trend — Score Over Time")

#                 import pandas as pd
#                 import plotly.graph_objects as go

#                 chart_responses = list(reversed(responses))
#                 dates  = [r["date"] for r in chart_responses]
#                 scores = [r["total_score"] for r in chart_responses]
#                 statuses = [r["status"] for r in chart_responses]

#                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

#                 fig = go.Figure()
#                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=[max(s, 0) for s in scores],
#                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
#                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#                 ))
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=[min(s, 0) for s in scores],
#                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
#                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#                 ))
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=scores,
#                     mode="lines+markers",
#                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
#                     marker=dict(size=10, color=marker_colors,
#                                 line=dict(color="#1a1a2e", width=2)),
#                     name="Health Score",
#                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
#                 ))

#                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#                 for d, s, st_ in zip(dates, scores, statuses):
#                     fig.add_annotation(
#                         x=d, y=s,
#                         text=status_icons_map.get(st_, ""),
#                         showarrow=False,
#                         yshift=18, font=dict(size=13)
#                     )

#                 fig.update_layout(
#                     paper_bgcolor="rgba(0,0,0,0)",
#                     plot_bgcolor="rgba(0,0,0,0)",
#                     font=dict(color="#A89FC8", size=12),
#                     margin=dict(l=10, r=10, t=10, b=10),
#                     height=300,
#                     xaxis=dict(
#                         showgrid=False, zeroline=False,
#                         tickfont=dict(size=11, color="#6B6080"),
#                         title=""
#                     ),
#                     yaxis=dict(
#                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
#                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
#                         tickfont=dict(size=11, color="#6B6080"),
#                         title="Score"
#                     ),
#                     hoverlabel=dict(
#                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
#                         font=dict(color="white", size=13)
#                     ),
#                     showlegend=False
#                 )

#                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

#                 st.markdown("""
#                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
#                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
#                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
#                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
#                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
#                 </div>
#                 """, unsafe_allow_html=True)

#                 # ── Recent Check-in History ───────────────────────────────────
#                 st.markdown("#### 📋 Recent Daily Check-in History")
#                 for r in responses:
#                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#                     color = status_colors.get(r["status"], "#A78BFA")
#                     icon = status_icons.get(r["status"], "•")
#                     st.markdown(f"""
#                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
#                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
#                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
#                         </div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
#                             Adherence: {r.get('adherence_status', 'N/A')}
#                         </div>
#                     </div>
#                     """, unsafe_allow_html=True)

#     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
#     with tabs[4]:
#         _render_patient_alerts(patient_id, patient, risk_level, risk)

#     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
#     with tabs[5]:
#         _render_patient_opd(patient_id, patient)

#     # ── Tab 6: Proactive AI Health Agent ──────────────────────────────────────
#     with tabs[6]:
#         _render_proactive_agent_tab(patient_id, patient, risk, adherence, trends)


# # ── Alerts tab renderer ───────────────────────────────────────────────────────

# def _render_patient_alerts(patient_id, patient, risk_level, risk):
#     """Render the patient-facing Alerts & Notifications tab."""
#     st.markdown("### 🔔 Alerts & Notifications")
#     st.markdown(
#         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
#         'and doctor messages are shown here.</p>',
#         unsafe_allow_html=True
#     )

#     # ── High-Risk Banner ──────────────────────────────────────────────────────
#     if risk_level == "high":
#         st.markdown(f"""
#         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
#             <div style="display:flex;align-items:center;gap:0.8rem;">
#                 <span style="font-size:1.8rem;">🚨</span>
#                 <div>
#                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
#                     <div style="color:var(--text-secondary);font-size:0.9rem;">
#                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
#                         Please contact your doctor or visit the clinic immediately.
#                     </div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
#     recent_responses = _cached_mcq_responses(patient_id, limit=7)
#     missed_dose_dates = []
#     for r in recent_responses:
#         adh = (r.get("adherence_status") or "").lower()
#         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
#             missed_dose_dates.append(r["date"])

#     if missed_dose_dates:
#         dates_str = ", ".join(missed_dose_dates[:3])
#         st.markdown(f"""
#         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
#             <div style="display:flex;align-items:center;gap:0.8rem;">
#                 <span style="font-size:1.8rem;">💊</span>
#                 <div>
#                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
#                     <div style="color:var(--text-secondary);font-size:0.85rem;">
#                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
#                         Consistent adherence is key to recovery — please take medications as prescribed.
#                     </div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── DB Alerts ─────────────────────────────────────────────────────────────
#     all_alerts = _cached_patient_alerts(patient_id)
#     unresolved = [a for a in all_alerts if not a["resolved"]]
#     resolved = [a for a in all_alerts if a["resolved"]]

#     if not all_alerts and not missed_dose_dates and risk_level != "high":
#         st.markdown("""
#         <div class="card" style="text-align:center;padding:2rem;">
#             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
#             <div style="font-weight:600;color:#34D399;">All Clear</div>
#             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
#                 No active alerts. Keep taking your medications and completing daily check-ins!
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#         return

#     severity_config = {
#         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
#         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
#         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
#     }
#     type_labels = {
#         "mcq_health_check": "Health Check Alert",
#         "doctor_message":   "Doctor Message",
#         "missed_dose":      "Missed Dose",
#         "high_risk":        "High Risk Warning",
#     }

#     if unresolved:
#         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
#         for alert in unresolved:
#             cfg = severity_config.get(alert["severity"], severity_config["medium"])
#             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
#             created = alert["created_at"][:16].replace("T", " ")

#             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
#                 st.markdown(f"""
#                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
#                              border-left:3px solid {cfg['color']};">
#                     <pre style="font-size:0.82rem;color:var(--text-secondary);
#                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# {alert['message']}</pre>
#                 </div>
#                 """, unsafe_allow_html=True)
#                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
#                     resolve_alert(alert["id"])
#                     _cached_patient_alerts.clear()
#                     st.rerun()

#     if resolved:
#         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
#             for alert in resolved:
#                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
#                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
#                 created = alert["created_at"][:16].replace("T", " ")
#                 st.markdown(f"""
#                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
#                     <div style="display:flex;justify-content:space-between;">
#                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
#                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)


# # ── MCQ result card ───────────────────────────────────────────────────────────

# def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
#     status = response["status"]
#     score = response["total_score"]
#     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#     color = status_colors.get(status, "#A78BFA")
#     icon = status_icons.get(status, "•")

#     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

#     # Safely escape feedback strings to prevent HTML injection
#     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
#     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

#     st.markdown(f"""
#     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
#         <div style="text-align: center; padding: 1rem 0;">
#             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
#             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
#             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
#         </div>
#         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
#             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
#             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
#             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     adherence_status = response.get("adherence_status", "")
#     side_effects_raw = response.get("side_effects", "[]")
#     try:
#         side_effects = json.loads(side_effects_raw)
#     except Exception:
#         side_effects = []

#     col1, col2 = st.columns(2)
#     with col1:
#         st.markdown(f"""
#         <div class="card" style="margin-top: 0;">
#             <div class="card-header">💊 Medication Adherence</div>
#             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
#         </div>
#         """, unsafe_allow_html=True)
#     with col2:
#         effects_text = ", ".join(side_effects) if side_effects else "None reported"
#         st.markdown(f"""
#         <div class="card" style="margin-top: 0;">
#             <div class="card-header">⚠️ Side Effects</div>
#             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
#         </div>
#         """, unsafe_allow_html=True)

#     if show_history and patient_id:
#         st.markdown(
#             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
#             unsafe_allow_html=True
#         )


# # ── Alert firing logic ────────────────────────────────────────────────────────

# def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
#     """Fire structured doctor alerts based on MCQ response."""
#     trigger = False
#     reasons = []

#     if total_score < 0:
#         trigger = True
#         reasons.append("negative_score")

#     if check_consecutive_worsening(patient_id, 2):
#         trigger = True
#         reasons.append("consecutive_worsening")

#     if side_effects:
#         trigger = True
#         reasons.append("side_effects")

#     if not trigger:
#         return

#     action_map = {
#         "Improving": "Continue medication as prescribed",
#         "Stable": "Monitor closely, follow up in 2-3 days",
#         "Worsening": "Immediate consultation required"
#     }

#     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
#     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
#     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
#     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

#     alert_message = f"""Patient ID: {patient_id}
# Doctor ID: {doctor_id}
# Disease: {patient.get('disease', 'N/A')}
# Current Status: {status}
# Score: {total_score:+d}

# Key Symptoms Reported:
# {symptoms_text}

# Medication Adherence:
# {adherence_text}

# Side Effects:
# {side_effects_text}

# Recommended Action:
# - {action_map.get(status, 'Monitor patient')}

# Triggered By: {reasons_text}"""

#     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

#     create_alert(
#         patient_id=patient_id,
#         alert_type="mcq_health_check",
#         message=alert_message,
#         severity=severity,
#         doctor_id=doctor_id
#     )




# # ── Online OPD booking tab ────────────────────────────────────────────────────

# def _render_patient_opd(patient_id: str, patient: dict):
#     """Full Online OPD booking UI for the patient dashboard."""
#     import streamlit as st
#     from datetime import date, datetime

#     st.markdown("### 🖥️ Online OPD — Book a Consultation")
#     st.markdown(
#         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
#         'Slots are real-time — once booked they disappear for other patients.</p>',
#         unsafe_allow_html=True
#     )

#     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

#     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
#     with opd_subtabs[0]:
#         doctors = _cached_opd_doctors()

#         if not doctors:
#             st.info("No doctors have published OPD slots yet. Please check back later.")
#         else:
#             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
#             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
#             selected_doctor_id = doctor_options[selected_label]

#             available_dates = _cached_opd_dates(selected_doctor_id)
#             if not available_dates:
#                 st.warning("This doctor has no available slots right now.")
#             else:
#                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
#                 chosen_date_str = st.selectbox(
#                     "Select Date",
#                     list(date_labels.keys()),
#                     format_func=lambda x: date_labels[x],
#                     key="opd_date_sel"
#                 )

#                 # Check if patient already booked on this day with this doctor
#                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
#                 if already_booked:
#                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
#                 else:
#                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

#                     if not free_slots:
#                         st.error("All slots for this date are fully booked. Please choose another date.")
#                     else:
#                         st.markdown(f"""
#                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
#                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
#                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
#                                 </div>
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
#                                     <strong style="color:#A78BFA;">17 minutes</strong>
#                                 </div>
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
#                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
#                                 </div>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

#                         slot_options = {
#                             f"{s['start_time']} – {s['end_time']}": s['id']
#                             for s in free_slots
#                         }
#                         chosen_slot_label = st.selectbox(
#                             "Choose a time slot",
#                             list(slot_options.keys()),
#                             key="opd_slot_sel"
#                         )
#                         chosen_slot_id = slot_options[chosen_slot_label]

#                         st.markdown(f"""
#                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
#                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
#                             <div style="color:var(--text-secondary);font-size:0.9rem;">
#                                 <strong>Doctor:</strong> {selected_label}<br>
#                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
#                                 <strong>Time:</strong> {chosen_slot_label}<br>
#                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

#                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
#                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
#                             if success:
#                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
#                                 st.balloons()
#                                 _cached_opd_bookings.clear()
#                                 _cached_opd_slots.clear()
#                                 _cached_has_booking.clear()
#                                 st.rerun()
#                             else:
#                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
#                                 _cached_opd_slots.clear()
#                                 st.rerun()

#     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
#     with opd_subtabs[1]:
#         st.markdown("#### 🗓️ Your OPD Bookings")
#         my_bookings = _cached_opd_bookings(patient_id)

#         if not my_bookings:
#             st.markdown("""
#             <div class="card" style="text-align:center;padding:2rem;">
#                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
#                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
#             </div>
#             """, unsafe_allow_html=True)
#         else:
#             today_str = date.today().isoformat()
#             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
#             past = [b for b in my_bookings if b["slot_date"] < today_str]

#             if upcoming:
#                 st.markdown("##### 📅 Upcoming")
#                 for booking in upcoming:
#                     visited = bool(booking["patient_visited"])
#                     color = "#34D399" if visited else "#A78BFA"
#                     status = "✅ Consulted" if visited else "⏳ Pending"
#                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

#                     safe_room = booking["id"].replace("-", "").replace(" ", "")
#                     room_name = f"MediCore-{safe_room}"

#                     col_b, col_c = st.columns([4, 1])
#                     with col_b:
#                         st.markdown(f"""
#                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
#                             <div style="display:flex;justify-content:space-between;align-items:center;">
#                                 <div>
#                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
#                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
#                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
#                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
#                                     </div>
#                                 </div>
#                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)
#                     with col_c:
#                         if not visited:
#                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
#                                 success = cancel_opd_booking(booking["id"], patient_id)
#                                 if success:
#                                     st.success("Booking cancelled.")
#                                     _cached_opd_bookings.clear()
#                                     _cached_opd_slots.clear()
#                                     _cached_has_booking.clear()
#                                     st.rerun()

#                     # ── Embedded video call (Jitsi) ───────────────────────────
#                     if not visited:
#                         call_key = f"show_call_pat_{booking['id']}"
#                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
#                                      use_container_width=True, type="primary"):
#                             st.session_state[call_key] = not st.session_state.get(call_key, False)

#                         if st.session_state.get(call_key, False):
#                             patient_name = st.session_state.get("patient_id", "Patient")
#                             encoded_name = str(patient_name).replace(" ", "%20")
#                             st.components.v1.html(f"""
#                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
#                             <iframe
#                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
#                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
#                                 allowfullscreen="true"
#                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
#                             ></iframe>
#                             </body></html>
#                             """, height=560)

#             if past:
#                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
#                     for booking in past:
#                         visited = bool(booking["patient_visited"])
#                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
#                         status = "✅ Consulted" if visited else "❌ Not attended"
#                         color = "#34D399" if visited else "#F87171"
#                         st.markdown(f"""
#                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
#                             <div style="display:flex;justify-content:space-between;">
#                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
#                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

# # ── Patient login ─────────────────────────────────────────────────────────────

# def render_patient_login():
#     st.markdown("""
#     <div style="max-width: 480px; margin: 4rem auto;">
#         <div class="page-header" style="text-align: center;">
#             <h1>🏥 Patient Login</h1>
#             <p>Enter your Patient ID to access your health portal</p>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     with st.container():
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col2:
#             patient_id = st.text_input(
#                 "Patient ID",
#                 placeholder="e.g. PAT-20260413-0001",
#                 label_visibility="collapsed"
#             )
#             st.markdown(
#                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
#                 'Your ID was provided by your doctor at registration</p>',
#                 unsafe_allow_html=True
#             )

#             if st.button("Access My Health Portal", type="primary", use_container_width=True):
#                 if patient_id:
#                     patient = get_patient(patient_id.strip().upper())
#                     if patient:
#                         st.session_state["patient_id"] = patient_id.strip().upper()
#                         st.session_state["patient_logged_in"] = True
#                         st.rerun()
#                     else:
#                         st.error("Patient ID not found. Check with your doctor.")
#                 else:
#                     st.warning("Please enter your Patient ID.")


# # ══════════════════════════════════════════════════════════════════════════════
# # PROACTIVE AI HEALTH AGENT TAB
# # ══════════════════════════════════════════════════════════════════════════════

# def _build_agent_context(patient_id: str, patient: dict, risk: dict,
#                           adherence: dict, trends: dict) -> dict:
#     """Gather all live signals needed for the briefing prompt."""
#     from data.database import (
#         get_mcq_responses, get_mcq_response_for_date,
#         check_consecutive_worsening, get_patient_alerts,
#         get_patient_opd_bookings, get_patient_prescriptions
#     )

#     today_str  = date.today().isoformat()
#     mcq_rows   = get_mcq_responses(patient_id, limit=10)
#     statuses   = [r["status"]      for r in mcq_rows][:5]
#     scores     = [r["total_score"] for r in mcq_rows][:5]
#     adherence_flags = [r.get("adherence_status", "") for r in mcq_rows[:7]]
#     missed_dose = any(
#         any(kw in (a or "").lower() for kw in ["miss", "skip", "forgot", "no"])
#         for a in adherence_flags
#     )
#     checkin_done   = get_mcq_response_for_date(patient_id, today_str) is not None
#     consec_worsening = check_consecutive_worsening(patient_id, 2)
#     alerts         = get_patient_alerts(patient_id)
#     unresolved_alerts = len([a for a in alerts if not a["resolved"]])
#     bookings       = get_patient_opd_bookings(patient_id)
#     upcoming_appt  = None
#     for b in bookings:
#         if b.get("slot_date", "") >= today_str:
#             upcoming_appt = f"{b['slot_date']} at {b.get('start_time','')}"
#             break
#     prescriptions  = get_patient_prescriptions(patient_id)
#     active_meds    = adherence.get("active_medications", 0)

#     # Resolve doctor name from patient record (best-effort)
#     doctor_name = patient.get("doctor_name") or patient.get("doctor_id", "your doctor")

#     hour = datetime.now().hour
#     if hour < 12:
#         time_of_day = "morning"
#     elif hour < 17:
#         time_of_day = "afternoon"
#     else:
#         time_of_day = "evening"

#     return {
#         "name":              patient.get("name", ""),
#         "age":               patient.get("age", ""),
#         "disease":           patient.get("disease", ""),
#         "doctor_name":       doctor_name,
#         "statuses":          statuses,
#         "scores":            scores,
#         "checkin_done":      checkin_done,
#         "consec_worsening":  consec_worsening,
#         "missed_dose":       missed_dose,
#         "active_meds":       active_meds,
#         "risk_level":        risk.get("level", "low"),
#         "risk_score":        risk.get("score", 0),
#         "upcoming_appt":     upcoming_appt or "None",
#         "unresolved_alerts": unresolved_alerts,
#         "trend":             trends.get("trend", "stable"),
#         "time_of_day":       time_of_day,
#         "today":             today_str,
#     }


# def _call_groq_agent(ctx: dict) -> dict | None:
#     """Call Groq with the briefing + cards prompt. Returns parsed JSON or None."""
#     from core.config import GROQ_API_KEY, GROQ_MODEL

#     if not GROQ_API_KEY:
#         return None

#     system_prompt = """You are a proactive personal health agent for a medical app called MediCure.

# Your job is to analyse a patient's health data and produce:
# 1. A short personalised briefing (2-3 sentences max)
# 2. A list of action cards the patient should act on today

# Rules for the briefing:
# - Address the patient by first name
# - Be specific — mention actual trends, medication status, doctor name where relevant
# - Be warm but direct — not clinical, not robotic
# - Never say "based on your data" or "I have analysed" — just say it naturally
# - Never use technical terms like "risk score", "MCQ", "consecutive worsening" — translate to plain language
# - If everything is fine, say so clearly and encouragingly

# Rules for action cards:
# - Only include cards that are genuinely relevant right now — do not pad with generic advice
# - Maximum 3 cards
# - Each card must have a clear single action the patient can take
# - Priority order: urgent health concern > missed medication > pending check-in > upcoming appointment > general wellness
# - If nothing needs action, return an empty array

# Respond ONLY with valid JSON in exactly this format, no extra text, no markdown fences:
# {
#   "briefing": "2 to 3 sentences",
#   "cards": [
#     {
#       "priority": "high | medium | low",
#       "icon": "single emoji",
#       "title": "short title max 6 words",
#       "message": "1-2 sentences explaining why this matters right now",
#       "action_label": "label for the button max 4 words",
#       "action_type": "book_appointment | complete_checkin | view_prescription | dismiss"
#     }
#   ]
# }"""

#     user_prompt = f"""Patient name: {ctx['name']}
# Age: {ctx['age']}
# Condition: {ctx['disease']}
# Assigned doctor: Dr. {ctx['doctor_name']}

# Last 5 check-in statuses (most recent first): {ctx['statuses']}
# Last 5 check-in scores (most recent first): {ctx['scores']}
# Today's check-in completed: {ctx['checkin_done']}
# Health trending downward for 2+ sessions: {ctx['consec_worsening']}

# Missed doses detected this week: {ctx['missed_dose']}
# Active medications: {ctx['active_meds']}

# Current health risk level: {ctx['risk_level']} (translate — do not say "risk level")
# Overall trend: {ctx['trend']}

# Upcoming appointment: {ctx['upcoming_appt']}
# Unresolved health alerts: {ctx['unresolved_alerts']}

# Today's date: {ctx['today']}
# Time of day: {ctx['time_of_day']}"""

#     try:
#         resp = requests.post(
#             "https://api.groq.com/openai/v1/chat/completions",
#             headers={
#                 "Authorization": f"Bearer {GROQ_API_KEY}",
#                 "Content-Type":  "application/json",
#             },
#             json={
#                 "model":       GROQ_MODEL,
#                 "messages":    [
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user",   "content": user_prompt},
#                 ],
#                 "max_tokens":  700,
#                 "temperature": 0.4,
#             },
#             timeout=20,
#         )
#         raw = resp.json()["choices"][0]["message"]["content"].strip()
#         # Strip accidental markdown fences
#         raw = raw.replace("```json", "").replace("```", "").strip()
#         return json.loads(raw)
#     except Exception:
#         return None


# def _render_proactive_agent_tab(patient_id: str, patient: dict,
#                                   risk: dict, adherence: dict, trends: dict):
#     """Render the Proactive AI Health Agent tab."""

#     st.markdown("### 🤖 My Health Agent")
#     st.markdown(
#         '<p style="color:var(--text-secondary);margin-top:-0.5rem;">'
#         'Your personal AI agent monitors your health around the clock '
#         'and tells you what matters today — before you have to ask.</p>',
#         unsafe_allow_html=True,
#     )
#     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

#     # ── Cache key: regenerate once per patient per hour ───────────────────────
#     cache_key   = f"proactive_agent_data_{patient_id}_{date.today().isoformat()}_{datetime.now().hour}"
#     refresh_key = f"proactive_agent_refresh_{patient_id}"

#     force_refresh = st.session_state.pop(refresh_key, False)

#     if force_refresh or cache_key not in st.session_state:
#         with st.spinner("🤖 Your health agent is reviewing your data..."):
#             ctx    = _build_agent_context(patient_id, patient, risk, adherence, trends)
#             result = _call_groq_agent(ctx)
#             st.session_state[cache_key] = {"result": result, "ctx": ctx}

#     cached     = st.session_state.get(cache_key, {})
#     result     = cached.get("result")
#     ctx        = cached.get("ctx", {})

#     # ── Refresh button ────────────────────────────────────────────────────────
#     col_title, col_refresh = st.columns([5, 1])
#     with col_refresh:
#         if st.button("🔄 Refresh", key=f"agent_refresh_{patient_id}",
#                      use_container_width=True):
#             # Clear all hourly cache keys for this patient
#             for k in list(st.session_state.keys()):
#                 if k.startswith(f"proactive_agent_data_{patient_id}"):
#                     del st.session_state[k]
#             st.session_state[refresh_key] = True
#             st.rerun()

#     # ── Fallback if Groq failed ───────────────────────────────────────────────
#     if not result:
#         st.warning(
#             "⚠️ Your health agent could not connect right now. "
#             "Please check your API key or try refreshing."
#         )
#         return

#     # ── BRIEFING BANNER ───────────────────────────────────────────────────────
#     briefing   = result.get("briefing", "")
#     time_icon  = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}.get(
#         ctx.get("time_of_day", "morning"), "🌅"
#     )

#     st.markdown(f"""
#     <div class="card" style="border-left:4px solid #A78BFA;
#          background:rgba(124,58,237,0.08);margin-bottom:1.5rem;padding:1.2rem 1.4rem;">
#         <div style="display:flex;align-items:flex-start;gap:0.9rem;">
#             <span style="font-size:2rem;line-height:1;">{time_icon}</span>
#             <div>
#                 <div style="font-weight:700;color:#A78BFA;font-size:0.78rem;
#                      text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">
#                     Agent Briefing
#                 </div>
#                 <div style="color:var(--text-primary);font-size:0.97rem;line-height:1.7;">
#                     {briefing}
#                 </div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── AGENT ACTIVITY SUMMARY (what the agent already did) ──────────────────
#     activity_lines = []
#     if ctx.get("consec_worsening"):
#         activity_lines.append("✅ Detected worsening health trend — doctor alert sent")
#     if ctx.get("unresolved_alerts", 0) > 0:
#         activity_lines.append(f"✅ {ctx['unresolved_alerts']} active alert(s) flagged for your doctor")
#     if ctx.get("risk_level") == "high":
#         activity_lines.append("✅ High risk status detected — escalated to doctor dashboard")
#     activity_lines.append(f"✅ Risk assessment run — current level: {ctx.get('risk_level','low').upper()}")
#     activity_lines.append(f"✅ Medication adherence checked — {ctx.get('active_meds', 0)} active medication(s)")

#     items_html = "".join(
#         f'<div style="font-size:0.83rem;color:var(--text-secondary);'
#         f'padding:0.25rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
#         f'{line}</div>'
#         for line in activity_lines
#     )
#     st.markdown(f"""
#     <div class="card" style="margin-bottom:1.5rem;">
#         <div style="font-weight:600;color:var(--text-primary);font-size:0.88rem;
#              margin-bottom:0.6rem;">🔍 What your agent did while you were away</div>
#         {items_html}
#     </div>
#     """, unsafe_allow_html=True)

#     # ── ACTION CARDS ─────────────────────────────────────────────────────────
#     cards = result.get("cards", [])

#     if not cards:
#         st.markdown("""
#         <div class="card" style="text-align:center;padding:2rem;
#              border-left:4px solid #34D399;background:rgba(52,211,153,0.06);">
#             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
#             <div style="font-weight:700;color:#34D399;font-size:1rem;">All Clear</div>
#             <div style="color:var(--text-muted);font-size:0.88rem;margin-top:0.4rem;">
#                 Your agent has reviewed everything. No actions needed right now.
#                 Keep taking your medications and completing your daily check-ins.
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.markdown(
#             '<div style="font-weight:600;color:var(--text-primary);'
#             'margin-bottom:0.8rem;">📋 Actions for you today</div>',
#             unsafe_allow_html=True,
#         )

#         priority_colors = {
#             "high":   {"border": "#F87171", "bg": "rgba(248,113,113,0.07)",
#                        "badge_bg": "rgba(248,113,113,0.15)", "badge_text": "#F87171"},
#             "medium": {"border": "#FBBF24", "bg": "rgba(251,191,36,0.07)",
#                        "badge_bg": "rgba(251,191,36,0.15)", "badge_text": "#FBBF24"},
#             "low":    {"border": "#34D399", "bg": "rgba(52,211,153,0.06)",
#                        "badge_bg": "rgba(52,211,153,0.15)", "badge_text": "#34D399"},
#         }

#         for i, card in enumerate(cards[:3]):
#             priority    = card.get("priority", "medium")
#             cfg         = priority_colors.get(priority, priority_colors["medium"])
#             icon        = card.get("icon", "💡")
#             title       = card.get("title", "")
#             message     = card.get("message", "")
#             action_type = card.get("action_type", "dismiss")
#             action_label= card.get("action_label", "Take Action")

#             st.markdown(f"""
#             <div class="card" style="border-left:4px solid {cfg['border']};
#                  background:{cfg['bg']};margin-bottom:1rem;">
#                 <div style="display:flex;align-items:flex-start;
#                      justify-content:space-between;gap:0.8rem;">
#                     <div style="display:flex;align-items:flex-start;gap:0.8rem;flex:1;">
#                         <span style="font-size:1.6rem;line-height:1.2;">{icon}</span>
#                         <div>
#                             <div style="display:flex;align-items:center;gap:0.5rem;
#                                  margin-bottom:0.3rem;">
#                                 <span style="font-weight:700;color:var(--text-primary);
#                                       font-size:0.97rem;">{title}</span>
#                                 <span style="font-size:0.72rem;padding:1px 8px;
#                                       border-radius:10px;font-weight:600;
#                                       background:{cfg['badge_bg']};
#                                       color:{cfg['badge_text']};">
#                                     {priority.upper()}
#                                 </span>
#                             </div>
#                             <div style="color:var(--text-secondary);font-size:0.85rem;
#                                  line-height:1.6;">{message}</div>
#                         </div>
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)

#             # ── Action button per card ────────────────────────────────────────
#             _render_card_action(
#                 patient_id=patient_id,
#                 patient=patient,
#                 action_type=action_type,
#                 action_label=action_label,
#                 card_index=i,
#             )
#             st.markdown("<div style='margin-bottom:0.5rem;'></div>",
#                         unsafe_allow_html=True)

#     # ── SLOT BOOKING FLOW (shown below cards when triggered) ─────────────────
#     _render_agent_booking_flow(patient_id, patient)

#     # ── TRACK PROGRESS SECTION ────────────────────────────────────────────────
#     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#     st.markdown(
#         '<div style="font-weight:700;color:var(--text-primary);font-size:1rem;'
#         'margin-bottom:0.8rem;">📊 Track Progress</div>',
#         unsafe_allow_html=True,
#     )

#     trend_toggle_key = f"agent_show_trends_{patient_id}"
#     btn_label = "🔼 Hide Trends" if st.session_state.get(trend_toggle_key) else "📈 View Trends"
#     if st.button(btn_label, key=f"agent_trend_btn_{patient_id}"):
#         st.session_state[trend_toggle_key] = not st.session_state.get(trend_toggle_key, False)
#         st.rerun()

#     if st.session_state.get(trend_toggle_key):
#         responses = _cached_mcq_responses(patient_id, limit=30)
#         if not responses:
#             st.info("No health check-in data yet. Complete your daily check-ins to see trends.")
#         else:
#             import plotly.graph_objects as go

#             chart_responses = list(reversed(responses))
#             dates    = [r["date"] for r in chart_responses]
#             scores   = [r["total_score"] for r in chart_responses]
#             statuses = [r["status"] for r in chart_responses]

#             status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#             marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

#             # Rolling 3-day average for the bold trend line (like the reference image)
#             import statistics
#             rolling_avg = []
#             for i in range(len(scores)):
#                 window = scores[max(0, i - 2): i + 1]
#                 rolling_avg.append(statistics.mean(window))

#             fig = go.Figure()

#             # Shaded fill — positive zone green, negative zone red
#             fig.add_trace(go.Scatter(
#                 x=dates, y=[max(s, 0) for s in scores],
#                 fill="tozeroy", fillcolor="rgba(52,211,153,0.10)",
#                 line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#             ))
#             fig.add_trace(go.Scatter(
#                 x=dates, y=[min(s, 0) for s in scores],
#                 fill="tozeroy", fillcolor="rgba(248,113,113,0.10)",
#                 line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#             ))

#             # Raw daily score — thin salmon line (jagged, like the light line in reference)
#             fig.add_trace(go.Scatter(
#                 x=dates, y=scores,
#                 mode="lines+markers",
#                 line=dict(color="rgba(251,146,100,0.65)", width=1.5, shape="spline", smoothing=0.4),
#                 marker=dict(size=6, color=marker_colors,
#                             line=dict(color="#1a1a2e", width=1.5)),
#                 name="Daily Score",
#                 hovertemplate="<b>%{x}</b><br>Daily Score: %{y:+d}<extra></extra>"
#             ))

#             # Bold rolling average line — thick dark red (dominant line like reference)
#             fig.add_trace(go.Scatter(
#                 x=dates, y=rolling_avg,
#                 mode="lines",
#                 line=dict(color="#C0392B", width=3.5, shape="spline", smoothing=0.7),
#                 name="3-Day Avg",
#                 hovertemplate="<b>%{x}</b><br>3-Day Avg: %{y:.1f}<extra></extra>"
#             ))

#             # Status icons above each daily point
#             status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#             for d, s, st_ in zip(dates, scores, statuses):
#                 fig.add_annotation(
#                     x=d, y=s,
#                     text=status_icons_map.get(st_, ""),
#                     showarrow=False,
#                     yshift=18, font=dict(size=11)
#                 )

#             fig.update_layout(
#                 paper_bgcolor="rgba(0,0,0,0)",
#                 plot_bgcolor="rgba(0,0,0,0)",
#                 font=dict(color="#A89FC8", size=12),
#                 margin=dict(l=10, r=10, t=20, b=10),
#                 height=320,
#                 xaxis=dict(
#                     showgrid=False, zeroline=False,
#                     tickfont=dict(size=11, color="#6B6080"),
#                     title="Day"
#                 ),
#                 yaxis=dict(
#                     showgrid=True, gridcolor="rgba(255,255,255,0.05)",
#                     zeroline=True, zerolinecolor="rgba(255,255,255,0.25)",
#                     tickfont=dict(size=11, color="#6B6080"),
#                     title="Condition Score"
#                 ),
#                 hoverlabel=dict(
#                     bgcolor="#1E1B4B", bordercolor="#A78BFA",
#                     font=dict(color="white", size=13)
#                 ),
#                 legend=dict(
#                     orientation="h", yanchor="bottom", y=1.02,
#                     xanchor="right", x=1,
#                     font=dict(size=11, color="#A89FC8"),
#                     bgcolor="rgba(0,0,0,0)"
#                 ),
#             )

#             st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

#             st.markdown("""
#             <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
#                 <span style="color:#C0392B;font-size:0.82rem;">━━ 3-Day Trend</span>
#                 <span style="color:rgba(251,146,100,0.9);font-size:0.82rem;">━ Daily Score</span>
#                 <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
#                 <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
#                 <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
#             </div>
#             """, unsafe_allow_html=True)

#     # ── LAST UPDATED footer ───────────────────────────────────────────────────
#     st.markdown(
#         f'<div style="color:var(--text-muted);font-size:0.75rem;'
#         f'margin-top:1.5rem;text-align:right;">'
#         f'Agent last updated: {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
#         f'</div>',
#         unsafe_allow_html=True,
#     )


# def _render_card_action(patient_id: str, patient: dict, action_type: str,
#                          action_label: str, card_index: int):
#     """Render the action button for a single card and handle its logic."""

#     btn_key = f"agent_card_btn_{patient_id}_{card_index}"

#     if action_type == "complete_checkin":
#         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
#             st.info("👉 Head to the **🩺 Daily Health Check** tab to complete today's check-in.")

#     elif action_type == "view_prescription":
#         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
#             st.info("👉 Head to the **💊 My Prescriptions** tab to review your medications.")

#     elif action_type == "book_appointment":
#         book_trigger_key = f"agent_book_trigger_{patient_id}"
#         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
#             # Fetch available slots on click — never before
#             doctors   = get_available_opd_doctors()
#             my_doc_id = patient.get("doctor_id")
#             my_docs   = [d for d in doctors if d["doctor_id"] == my_doc_id] or doctors

#             all_slots = []
#             for doc in my_docs:
#                 dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
#                 for d in dates[:3]:
#                     slots = get_available_opd_slots(doc["doctor_id"], d)
#                     for s in slots:
#                         all_slots.append({
#                             **s,
#                             "doctor_name": doc["name"],
#                             "doctor_id":   doc["doctor_id"],
#                         })

#             if not all_slots:
#                 st.warning(
#                     "⚠️ No available slots right now. "
#                     "Please check the **🖥️ Online OPD** tab or contact the clinic."
#                 )
#             else:
#                 st.session_state[f"agent_slots_{patient_id}"]       = all_slots
#                 st.session_state[f"agent_booking_step_{patient_id}"] = "select"
#                 st.rerun()

#     elif action_type == "dismiss":
#         if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
#             st.success("✅ Noted.")


# def _render_agent_booking_flow(patient_id: str, patient: dict):
#     """3-step booking flow triggered from an action card. Fully scoped to agent context."""

#     step_key   = f"agent_booking_step_{patient_id}"
#     slots_key  = f"agent_slots_{patient_id}"
#     slot_key   = f"agent_chosen_slot_{patient_id}"
#     doctor_key = f"agent_chosen_doctor_{patient_id}"

#     step = st.session_state.get(step_key)
#     if step is None:
#         return

#     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#     st.markdown(
#         '<div style="font-weight:600;color:var(--text-primary);'
#         'margin-bottom:0.8rem;">📅 Book a Consultation</div>',
#         unsafe_allow_html=True,
#     )

#     # ── Step: select slot ─────────────────────────────────────────────────────
#     if step == "select":
#         all_slots = st.session_state.get(slots_key, [])
#         if not all_slots:
#             st.warning("No slots loaded. Please try again.")
#             st.session_state.pop(step_key, None)
#             return

#         slot_labels = [
#             f"Dr. {s['doctor_name']}  —  {s['slot_date']}  {s['start_time']}–{s['end_time']}"
#             for s in all_slots
#         ]
#         chosen_idx = st.selectbox(
#             "Select a slot",
#             options=range(len(slot_labels)),
#             format_func=lambda i: slot_labels[i],
#             key=f"agent_slot_select_{patient_id}",
#             label_visibility="collapsed",
#         )
#         col_ok, col_cancel = st.columns([2, 1])
#         with col_ok:
#             if st.button("Confirm this slot →",
#                          key=f"agent_confirm_slot_{patient_id}",
#                          type="primary", use_container_width=True):
#                 chosen = all_slots[chosen_idx]
#                 st.session_state[slot_key]   = chosen
#                 st.session_state[doctor_key] = {
#                     "name": chosen["doctor_name"],
#                     "id":   chosen["doctor_id"],
#                 }
#                 st.session_state[step_key] = "confirm"
#                 st.rerun()
#         with col_cancel:
#             if st.button("Cancel", key=f"agent_cancel_slot_{patient_id}",
#                          use_container_width=True):
#                 for k in (step_key, slots_key, slot_key, doctor_key):
#                     st.session_state.pop(k, None)
#                 st.rerun()

#     # ── Step: confirm booking ─────────────────────────────────────────────────
#     elif step == "confirm":
#         chosen_slot   = st.session_state.get(slot_key, {})
#         chosen_doctor = st.session_state.get(doctor_key, {})

#         st.markdown(f"""
#         <div class="card" style="border:1px solid rgba(167,139,250,0.4);
#              background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
#             <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
#                 📋 Confirm Booking
#             </div>
#             <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.9;">
#                 <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
#                 <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
#                 <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         col_yes, col_back = st.columns(2)
#         with col_yes:
#             if st.button("✅ Book Appointment",
#                          key=f"agent_book_yes_{patient_id}",
#                          type="primary", use_container_width=True):
#                 success = book_opd_slot(
#                     slot_id=chosen_slot["id"],
#                     patient_id=patient_id,
#                     patient_name=patient.get("name", ""),
#                 )
#                 for k in (step_key, slots_key, slot_key, doctor_key):
#                     st.session_state.pop(k, None)
#                 _cached_opd_bookings.clear()

#                 if success:
#                     doctor_id = patient.get("doctor_id")
#                     create_alert(
#                         patient_id=patient_id,
#                         alert_type="agent_opd_booked",
#                         message=(
#                             f"Patient booked an OPD slot via the Proactive Health Agent tab.\n"
#                             f"Slot: Dr. {chosen_doctor.get('name','')} on "
#                             f"{chosen_slot.get('slot_date','')} "
#                             f"at {chosen_slot.get('start_time','')}."
#                         ),
#                         severity="low",
#                         doctor_id=doctor_id,
#                     )
#                     st.success(
#                         f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
#                         f"on {chosen_slot.get('slot_date','')} "
#                         f"at {chosen_slot.get('start_time','')}."
#                     )
#                 else:
#                     st.error(
#                         "❌ That slot was just taken. "
#                         "Please go to the **🖥️ Online OPD** tab to pick another."
#                     )
#                 st.rerun()

#         with col_back:
#             if st.button("← Back", key=f"agent_book_back_{patient_id}",
#                          use_container_width=True):
#                 st.session_state[step_key] = "select"
#                 st.rerun()


# # import streamlit as st
# # import json
# # from datetime import date, datetime
# # from data.database import (
# #     get_patient, get_patient_prescriptions, get_chat_history,
# #     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
# #     create_alert, check_consecutive_worsening, get_patient_alerts,
# #     resolve_alert,
# #     get_available_opd_doctors, get_available_opd_dates_for_doctor,
# #     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
# #     get_patient_opd_bookings, check_patient_has_booking
# # )
# # from agents.orchestrator import AgentOrchestrator
# # from agents.scheduling_agent import (
# #     SchedulingAgent, get_auth_url,
# #     exchange_code_for_tokens, refresh_access_token
# # )
# # from agents.mcq_agent import MCQAgent


# # # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_chat_history(patient_id, limit=20):
# #     return get_chat_history(patient_id, limit)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_prescriptions(patient_id):
# #     return get_patient_prescriptions(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_patient_alerts(patient_id):
# #     return get_patient_alerts(patient_id)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_opd_bookings(patient_id):
# #     return get_patient_opd_bookings(patient_id)

# # @st.cache_data(ttl=20, show_spinner=False)
# # def _cached_mcq_response_today(patient_id, today_str):
# #     return get_mcq_response_for_date(patient_id, today_str)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_mcq_responses(patient_id, limit=30):
# #     return get_mcq_responses(patient_id, limit)

# # @st.cache_data(ttl=60, show_spinner=False)
# # def _cached_opd_doctors():
# #     return get_available_opd_doctors()

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_opd_dates(doctor_id):
# #     return get_available_opd_dates_for_doctor(doctor_id)

# # @st.cache_data(ttl=15, show_spinner=False)
# # def _cached_opd_slots(doctor_id, date_str):
# #     return get_available_opd_slots(doctor_id, date_str)

# # @st.cache_data(ttl=10, show_spinner=False)
# # def _cached_has_booking(patient_id, doctor_id, date_str):
# #     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # # ── OAuth token helpers ───────────────────────────────────────────────────────

# # def _handle_google_oauth_callback():
# #     """
# #     Called once at the top of app.py.
# #     If Google redirected back with ?code=..., exchange it for tokens,
# #     set mode=patient, and mark patient_google_authed=True.
# #     Only removes OAuth-specific params, preserving the _s session-restore param.
# #     """
# #     params = st.query_params
# #     auth_code = params.get("code")
# #     if auth_code and not st.session_state.get("google_access_token"):
# #         try:
# #             tokens = exchange_code_for_tokens(auth_code)
# #             if "access_token" in tokens:
# #                 st.session_state["google_access_token"] = tokens["access_token"]
# #                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
# #                 st.session_state["patient_google_authed"] = True
# #                 st.session_state["mode"] = "patient"
# #                 st.toast("✅ Google sign-in successful!", icon="✅")
# #         except Exception as e:
# #             st.warning(f"Google OAuth error: {e}")
# #         # Remove only OAuth-specific params, preserving _s session param
# #         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
# #             try:
# #                 if oauth_key in st.query_params:
# #                     del st.query_params[oauth_key]
# #             except Exception:
# #                 pass


# # def _get_valid_access_token() -> str | None:
# #     """Return a valid Google access token from session, refreshing if needed."""
# #     token = st.session_state.get("google_access_token")
# #     if token:
# #         return token
# #     refresh_tok = st.session_state.get("google_refresh_token")
# #     if refresh_tok:
# #         new_token = refresh_access_token(refresh_tok)
# #         if new_token:
# #             st.session_state["google_access_token"] = new_token
# #             return new_token
# #     return None


# # # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# # @st.cache_resource(show_spinner=False)
# # def _get_orchestrator():
# #     return AgentOrchestrator()

# # @st.cache_resource(show_spinner=False)
# # def _get_scheduler():
# #     return SchedulingAgent()

# # @st.cache_resource(show_spinner=False)
# # def _get_mcq_agent():
# #     return MCQAgent()

# # @st.cache_data(ttl=120, show_spinner=False)
# # def _cached_patient_login(patient_id):
# #     """Run the expensive on_patient_login only once per 2 minutes."""
# #     return _get_orchestrator().on_patient_login(patient_id)

# # @st.cache_data(ttl=30, show_spinner=False)
# # def _cached_get_patient(patient_id):
# #     return get_patient(patient_id)


# # # ── Main dashboard ────────────────────────────────────────────────────────────

# # def render_patient_dashboard(patient_id):
# #     # OAuth callback is handled at app level (app.py) — no need to call it here again.
# #     orchestrator = _get_orchestrator()
# #     scheduler = _get_scheduler()
# #     mcq_agent = _get_mcq_agent()
# #     patient = _cached_get_patient(patient_id)

# #     if not patient:
# #         st.error("Patient not found. Check your Patient ID.")
# #         return

# #     st.markdown(f"""
# #     <div class="page-header">
# #         <h1>🧑‍⚕️ Patient Portal</h1>
# #         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
# #     _health_key = f"health_data_{patient_id}"
# #     if _health_key not in st.session_state:
# #         with st.spinner("Loading your health data..."):
# #             st.session_state[_health_key] = _cached_patient_login(patient_id)
# #     health_data = st.session_state[_health_key]

# #     risk = health_data.get("risk", {})
# #     adherence = health_data.get("adherence", {})
# #     trends = health_data.get("trends", {})

# #     col1, col2, col3, col4 = st.columns(4)
# #     risk_level = risk.get("level", "low")
# #     col1.metric("Risk Level", risk_level.upper())
# #     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
# #     col3.metric("Active Meds", adherence.get("active_medications", 0))
# #     col4.metric("Health Trend", trends.get("trend", "stable").title())

# #     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# #     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
# #     tabs = st.tabs([
# #         "💬 AI Assistant",
# #         "📅 My Schedule",
# #         "💊 My Prescriptions",
# #         "🩺 Daily Health Check",
# #         "🔔 Alerts",
# #         "🖥️ Online OPD",
# #     ])

# #     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
# #     with tabs[0]:
# #         st.markdown("### 🤖 Autonomous AI Health Agent")
# #         st.markdown(
# #             '<p style="color: var(--text-secondary);">'
# #             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
# #             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
# #             '</p>',
# #             unsafe_allow_html=True
# #         )

# #         # ── Quick action chips ─────────────────────────────────────────────
# #         st.markdown("""
# #         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
# #                          cursor:pointer;">📅 Book Appointment</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          💊 My Prescriptions</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🩺 Check Symptoms</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          🔔 My Alerts</span>
# #             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
# #                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
# #                          ❌ Cancel Appointment</span>
# #         </div>
# #         """, unsafe_allow_html=True)

# #         history = _cached_chat_history(patient_id, 20)
# #         for msg in history:
# #             with st.chat_message(msg["role"]):
# #                 st.markdown(msg["content"])

# #         # ── Triage action buttons ─────────────────────────────────────────
# #         _triage_key = f"pending_triage_{patient_id}"
# #         _triage_msg_key = f"pending_triage_msg_{patient_id}"
# #         _confirm_key = f"triage_confirm_{patient_id}"

# #         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
# #             triage_level = st.session_state[_triage_key]
# #             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

# #             if triage_level == "URGENT":
# #                 btn_label = "🚨 Alert My Doctor Now"
# #                 btn_type = "primary"
# #                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
# #             else:
# #                 btn_label = "📅 Book Urgent Appointment"
# #                 btn_type = "secondary"
# #                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

# #             if not st.session_state.get(_confirm_key):
# #                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
# #                     st.session_state[_confirm_key] = True
# #                     st.rerun()
# #             else:
# #                 st.warning(confirm_msg)
# #                 col_yes, col_no = st.columns(2)
# #                 with col_yes:
# #                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
# #                         severity = "high" if triage_level == "URGENT" else "medium"
# #                         alert_message = (
# #                             f"[Agentic AI — Patient Reported Symptoms]\n"
# #                             f"Patient described: \"{symptom_text}\"\n"
# #                             f"AI Triage Verdict: {triage_level}\n"
# #                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
# #                                else "📅 Patient requests a follow-up appointment.")
# #                         )
# #                         _pt = get_patient(patient_id)
# #                         _doctor_id = _pt.get("doctor_id") if _pt else None
# #                         create_alert(
# #                             patient_id=patient_id,
# #                             alert_type="patient_reported_symptoms",
# #                             message=alert_message,
# #                             severity=severity,
# #                             doctor_id=_doctor_id
# #                         )
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
# #                                    else "✅ Alert sent to your doctor!")
# #                         st.rerun()
# #                 with col_no:
# #                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
# #                         st.session_state.pop(_triage_key, None)
# #                         st.session_state.pop(_triage_msg_key, None)
# #                         st.session_state.pop(_confirm_key, None)
# #                         st.rerun()

# #         # ── Action result display (non-triage confirmations) ──────────────
# #         _action_result_key = f"action_result_{patient_id}"
# #         if st.session_state.get(_action_result_key):
# #             ar = st.session_state[_action_result_key]
# #             action = ar.get("action", "")
# #             confirmed = ar.get("confirmed", False)
# #             success = ar.get("success", False)

# #             if confirmed and success:
# #                 if action == "book_appointment":
# #                     bd = ar.get("booking_details", {})
# #                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
# #                 elif action == "cancel_appointment":
# #                     st.success("✅ Appointment successfully cancelled.")

# #             st.session_state.pop(_action_result_key, None)

# #         # ── Chat input ────────────────────────────────────────────────────
# #         placeholder = (
# #             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
# #             "or 'Show my prescriptions' or 'I have chest pain'..."
# #         )
# #         if prompt := st.chat_input(placeholder):
# #             with st.chat_message("user"):
# #                 st.markdown(prompt)

# #             with st.chat_message("assistant"):
# #                 with st.spinner("🤖 Analysing and acting..."):
# #                     result = orchestrator.on_patient_message(
# #                         patient_id, prompt,
# #                         use_agentic=True,
# #                         session_state=st.session_state
# #                     )

# #                 if not isinstance(result, dict):
# #                     result = {"reply": str(result), "triage": None, "action": "general_health"}

# #                 reply = result.get("reply", "")
# #                 triage = result.get("triage")
# #                 action = result.get("action", "")
# #                 confirmed = result.get("confirmed", False)
# #                 success = result.get("success", False)

# #                 # ── Show triage badge ──────────────────────────────────
# #                 if triage == "URGENT":
# #                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
# #                 elif triage == "MODERATE":
# #                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
# #                 elif triage == "MILD":
# #                     st.success("🟢 **MILD — Manageable at home for now.**")

# #                 # ── Show action confirmation badge ────────────────────
# #                 if confirmed and success:
# #                     if action == "book_appointment":
# #                         bd = result.get("booking_details", {})
# #                         st.success(
# #                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
# #                             f"{bd.get('date', '')} · {bd.get('time', '')}"
# #                         )
# #                     elif action == "cancel_appointment":
# #                         st.success("✅ **Appointment Cancelled Successfully**")

# #                 st.markdown(reply)

# #             # ── Post-response state management ────────────────────────
# #             if triage in ("URGENT", "MODERATE"):
# #                 st.session_state[_triage_key] = triage
# #                 st.session_state[_triage_msg_key] = prompt
# #                 st.session_state.pop(_confirm_key, None)
# #             else:
# #                 st.session_state.pop(_triage_key, None)
# #                 st.session_state.pop(_triage_msg_key, None)
# #                 st.session_state.pop(_confirm_key, None)

# #             _cached_chat_history.clear()
# #             st.rerun()

# #     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
# #     with tabs[1]:
# #         st.markdown("### 📅 Medication Schedule")
# #         col1, col2 = st.columns([3, 1])

# #         with col2:
# #             access_token = _get_valid_access_token()

# #             if access_token:
# #                 # Token available — show sync button
# #                 if st.button("📆 Sync to Google Calendar"):
# #                     with st.spinner("Syncing to calendar..."):
# #                         result = scheduler.schedule_for_patient(patient_id, access_token)
# #                     if result["success"]:
# #                         st.success(result["message"])
# #                     else:
# #                         st.warning(result.get("message", "Sync failed."))
# #                         if result.get("errors"):
# #                             for e in result["errors"]:
# #                                 st.caption(f"⚠ {e}")
# #                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
# #                     st.session_state.pop("google_access_token", None)
# #                     st.session_state.pop("google_refresh_token", None)
# #                     st.rerun()
# #             else:
# #                 # No access token in session (e.g. user disconnected or session expired).
# #                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
# #                 st.markdown("""
# #                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
# #                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
# #                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
# #                         📅 Google Calendar Disconnected
# #                     </div>
# #                     <div style="color:#A89FC8;font-size:0.82rem;">
# #                         Your Google session token has expired. Click below to reconnect —
# #                         this uses the same Google account you signed in with.
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 try:
# #                     auth_url = get_auth_url()
# #                     st.markdown(f"""
# #                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
# #                         <div style="
# #                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
# #                             background:#fff;color:#3c4043;border:1px solid #dadce0;
# #                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
# #                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
# #                             <svg width="16" height="16" viewBox="0 0 18 18">
# #                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
# #                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
# #                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
# #                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
# #                             </svg>
# #                             Reconnect Google Calendar
# #                         </div>
# #                     </a>
# #                     """, unsafe_allow_html=True)
# #                 except Exception:
# #                     st.info("Google Calendar integration not configured. Ask your administrator.")

# #         schedule = scheduler.get_schedule_preview(patient_id)
# #         if not schedule:
# #             st.info("No schedule available. Ask your doctor to create a prescription.")
# #         else:
# #             current_date = None
# #             for item in schedule:
# #                 if item["date"] != current_date:
# #                     current_date = item["date"]
# #                     st.markdown(f"**📅 {current_date}**")
# #                 st.markdown(f"""
# #                 <div class="schedule-item">
# #                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
# #                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
# #                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
# #                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
# #     with tabs[2]:
# #         st.markdown("### 💊 My Prescriptions")
# #         prescriptions = _cached_prescriptions(patient_id)
# #         if not prescriptions:
# #             st.info("No prescriptions assigned yet. Please consult your doctor.")
# #         else:
# #             for i, pr in enumerate(prescriptions):
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
# #                 """, unsafe_allow_html=True)
# #                 for m in pr.get("medicines", []):
# #                     st.markdown(f"""
# #                     <div class="medicine-card">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
# #                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
# #                         </div>
# #                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
# #                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)
# #                 if pr.get("doctor_notes"):
# #                     st.markdown(
# #                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
# #                         unsafe_allow_html=True
# #                     )
# #                 st.markdown("</div>", unsafe_allow_html=True)

# #     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
# #     with tabs[3]:
# #         today_str = date.today().isoformat()
# #         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

# #         existing_response = _cached_mcq_response_today(patient_id, today_str)
# #         _mcq_show_form = True  # controls whether to show the question form

# #         if existing_response:
# #             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             if st.button("🔄 Retake Today's Check-in", type="secondary"):
# #                 st.session_state["retake_mcq"] = True
# #                 st.session_state["show_health_summary"] = False
# #                 # Clear cached questions so fresh ones load
# #                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
# #                 st.rerun()
# #             if not st.session_state.get("retake_mcq"):
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             prescriptions = _cached_prescriptions(patient_id)
# #             if not prescriptions:
# #                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             # Cache questions per patient per day — no need to call GROQ on every rerun
# #             _q_key = f"mcq_questions_{patient_id}_{today_str}"
# #             if _q_key not in st.session_state:
# #                 with st.spinner("Loading your personalized health questions..."):
# #                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
# #             questions = st.session_state[_q_key]

# #             if not questions:
# #                 st.error("Could not generate questions. Please try again.")
# #                 _mcq_show_form = False

# #         if _mcq_show_form:
# #             st.markdown("""
# #             <div class="card" style="margin-bottom: 1.5rem;">
# #                 <div class="card-header">📋 Today's Health Questions</div>
# #                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
# #                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
# #                 </p>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             selected_options = {}

# #             for q in questions:
# #                 qid = str(q["id"])
# #                 category_icons = {
# #                     "symptom": "🤒",
# #                     "adherence": "💊",
# #                     "side_effect": "⚠️",
# #                     "wellbeing": "💚"
# #                 }
# #                 icon = category_icons.get(q.get("category", ""), "❓")

# #                 st.markdown(f"""
# #                 <div class="card" style="margin-bottom: 1rem;">
# #                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
# #                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
# #                         {icon} {q.get('category', '').replace('_', ' ').title()}
# #                     </div>
# #                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
# #                         {q['question']}
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 option_labels = [opt["text"] for opt in q["options"]]
# #                 choice = st.radio(
# #                     label=q["question"],
# #                     options=range(len(option_labels)),
# #                     format_func=lambda i, opts=option_labels: opts[i],
# #                     key=f"mcq_{qid}",
# #                     label_visibility="collapsed"
# #                 )
# #                 selected_options[qid] = choice
# #                 st.markdown("---")

# #             col_btn1, col_btn2 = st.columns([3, 1])
# #             with col_btn1:
# #                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
# #                     total_score = 0
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         try:
# #                             total_score += q["options"][idx]["score"]
# #                         except (IndexError, KeyError):
# #                             pass

# #                     status = mcq_agent.compute_status(total_score)
# #                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

# #                     responses_data = []
# #                     for q in questions:
# #                         qid = str(q["id"])
# #                         idx = selected_options.get(qid, 0)
# #                         responses_data.append({
# #                             "question": q["question"],
# #                             "category": q.get("category"),
# #                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
# #                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
# #                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
# #                         })

# #                     doctor_id = patient.get("doctor_id")
# #                     save_mcq_response(
# #                         patient_id=patient_id,
# #                         doctor_id=doctor_id,
# #                         date_str=today_str,
# #                         responses_json=json.dumps(responses_data),
# #                         total_score=total_score,
# #                         status=status,
# #                         side_effects=json.dumps(side_effects),
# #                         adherence_status=adherence_status
# #                     )

# #                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
# #                                            symptoms, adherence_status, side_effects)

# #                     st.session_state["retake_mcq"] = False
# #                     st.session_state["show_health_summary"] = True
# #                     # Invalidate cached data so next render is fresh
# #                     _cached_patient_login.clear()
# #                     _cached_mcq_response_today.clear()
# #                     _cached_mcq_responses.clear()
# #                     st.session_state.pop(f"health_data_{patient_id}", None)
# #                     st.rerun()

# #         # ── Inline Health Summary — shown after MCQ completion ────────────────
# #         # Show automatically after submission OR when today's response already exists
# #         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
# #         if _show_summary:
# #             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
# #             st.markdown("### 📊 Your Health Summary")

# #             # ── AI Health Report ──────────────────────────────────────────────
# #             col_ai1, col_ai2 = st.columns([4, 1])
# #             with col_ai2:
# #                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
# #             if _gen_report or st.session_state.get("show_health_summary"):
# #                 # Cache summary per patient per day - expensive GROQ call
# #                 _sum_key = f"health_summary_{patient_id}_{today_str}"
# #                 if _gen_report or _sum_key not in st.session_state:
# #                     with st.spinner("AI is analyzing your health data..."):
# #                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
# #                 summary = st.session_state[_sum_key]
# #                 st.markdown(f"""
# #                 <div class="card">
# #                     <div class="card-header">🤖 AI Clinical Assessment</div>
# #                     <p style="line-height: 1.7;">{summary}</p>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #             # ── Health Indicators ─────────────────────────────────────────────
# #             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
# #             risk_color = risk_colors.get(risk_level, "#A78BFA")
# #             st.markdown(f"""
# #             <div class="card">
# #                 <div class="card-header">Health Indicators</div>
# #                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
# #                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
# #                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
# #                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
# #                     </div>
# #                     <div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
# #                         <span style="color: var(--text-primary);">{patient['disease']}</span>
# #                     </div>
# #                 </div>
# #             </div>
# #             """, unsafe_allow_html=True)

# #             # ── Health Trend Chart ────────────────────────────────────────────
# #             responses = _cached_mcq_responses(patient_id, limit=30)
# #             if responses:
# #                 st.markdown("#### 📈 Health Trend — Score Over Time")

# #                 import pandas as pd
# #                 import plotly.graph_objects as go

# #                 chart_responses = list(reversed(responses))
# #                 dates  = [r["date"] for r in chart_responses]
# #                 scores = [r["total_score"] for r in chart_responses]
# #                 statuses = [r["status"] for r in chart_responses]

# #                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

# #                 fig = go.Figure()
# #                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[max(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=[min(s, 0) for s in scores],
# #                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
# #                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
# #                 ))
# #                 fig.add_trace(go.Scatter(
# #                     x=dates, y=scores,
# #                     mode="lines+markers",
# #                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
# #                     marker=dict(size=10, color=marker_colors,
# #                                 line=dict(color="#1a1a2e", width=2)),
# #                     name="Health Score",
# #                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
# #                 ))

# #                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                 for d, s, st_ in zip(dates, scores, statuses):
# #                     fig.add_annotation(
# #                         x=d, y=s,
# #                         text=status_icons_map.get(st_, ""),
# #                         showarrow=False,
# #                         yshift=18, font=dict(size=13)
# #                     )

# #                 fig.update_layout(
# #                     paper_bgcolor="rgba(0,0,0,0)",
# #                     plot_bgcolor="rgba(0,0,0,0)",
# #                     font=dict(color="#A89FC8", size=12),
# #                     margin=dict(l=10, r=10, t=10, b=10),
# #                     height=300,
# #                     xaxis=dict(
# #                         showgrid=False, zeroline=False,
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title=""
# #                     ),
# #                     yaxis=dict(
# #                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
# #                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
# #                         tickfont=dict(size=11, color="#6B6080"),
# #                         title="Score"
# #                     ),
# #                     hoverlabel=dict(
# #                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
# #                         font=dict(color="white", size=13)
# #                     ),
# #                     showlegend=False
# #                 )

# #                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# #                 st.markdown("""
# #                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
# #                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
# #                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
# #                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
# #                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
# #                 </div>
# #                 """, unsafe_allow_html=True)

# #                 # ── Recent Check-in History ───────────────────────────────────
# #                 st.markdown("#### 📋 Recent Daily Check-in History")
# #                 for r in responses:
# #                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #                     color = status_colors.get(r["status"], "#A78BFA")
# #                     icon = status_icons.get(r["status"], "•")
# #                     st.markdown(f"""
# #                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
# #                         <div style="display: flex; justify-content: space-between; align-items: center;">
# #                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
# #                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
# #                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
# #                         </div>
# #                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
# #                             Adherence: {r.get('adherence_status', 'N/A')}
# #                         </div>
# #                     </div>
# #                     """, unsafe_allow_html=True)

# #     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
# #     with tabs[4]:
# #         _render_patient_alerts(patient_id, patient, risk_level, risk)

# #     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
# #     with tabs[5]:
# #         _render_patient_opd(patient_id, patient)


# # # ── Alerts tab renderer ───────────────────────────────────────────────────────

# # def _render_patient_alerts(patient_id, patient, risk_level, risk):
# #     """Render the patient-facing Alerts & Notifications tab."""
# #     st.markdown("### 🔔 Alerts & Notifications")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
# #         'and doctor messages are shown here.</p>',
# #         unsafe_allow_html=True
# #     )

# #     # ── High-Risk Banner ──────────────────────────────────────────────────────
# #     if risk_level == "high":
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">🚨</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
# #                     <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
# #                         Please contact your doctor or visit the clinic immediately.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
# #     recent_responses = _cached_mcq_responses(patient_id, limit=7)
# #     missed_dose_dates = []
# #     for r in recent_responses:
# #         adh = (r.get("adherence_status") or "").lower()
# #         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
# #             missed_dose_dates.append(r["date"])

# #     if missed_dose_dates:
# #         dates_str = ", ".join(missed_dose_dates[:3])
# #         st.markdown(f"""
# #         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
# #             <div style="display:flex;align-items:center;gap:0.8rem;">
# #                 <span style="font-size:1.8rem;">💊</span>
# #                 <div>
# #                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
# #                     <div style="color:var(--text-secondary);font-size:0.85rem;">
# #                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
# #                         Consistent adherence is key to recovery — please take medications as prescribed.
# #                     </div>
# #                 </div>
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     # ── DB Alerts ─────────────────────────────────────────────────────────────
# #     all_alerts = _cached_patient_alerts(patient_id)
# #     unresolved = [a for a in all_alerts if not a["resolved"]]
# #     resolved = [a for a in all_alerts if a["resolved"]]

# #     if not all_alerts and not missed_dose_dates and risk_level != "high":
# #         st.markdown("""
# #         <div class="card" style="text-align:center;padding:2rem;">
# #             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
# #             <div style="font-weight:600;color:#34D399;">All Clear</div>
# #             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
# #                 No active alerts. Keep taking your medications and completing daily check-ins!
# #             </div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #         return

# #     severity_config = {
# #         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
# #         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
# #         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
# #     }
# #     type_labels = {
# #         "mcq_health_check": "Health Check Alert",
# #         "doctor_message":   "Doctor Message",
# #         "missed_dose":      "Missed Dose",
# #         "high_risk":        "High Risk Warning",
# #     }

# #     if unresolved:
# #         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
# #         for alert in unresolved:
# #             cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #             created = alert["created_at"][:16].replace("T", " ")

# #             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
# #                 st.markdown(f"""
# #                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
# #                              border-left:3px solid {cfg['color']};">
# #                     <pre style="font-size:0.82rem;color:var(--text-secondary);
# #                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# # {alert['message']}</pre>
# #                 </div>
# #                 """, unsafe_allow_html=True)
# #                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
# #                     resolve_alert(alert["id"])
# #                     _cached_patient_alerts.clear()
# #                     st.rerun()

# #     if resolved:
# #         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
# #             for alert in resolved:
# #                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
# #                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
# #                 created = alert["created_at"][:16].replace("T", " ")
# #                 st.markdown(f"""
# #                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
# #                     <div style="display:flex;justify-content:space-between;">
# #                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
# #                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
# #                     </div>
# #                 </div>
# #                 """, unsafe_allow_html=True)


# # # ── MCQ result card ───────────────────────────────────────────────────────────

# # def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
# #     status = response["status"]
# #     score = response["total_score"]
# #     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
# #     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
# #     color = status_colors.get(status, "#A78BFA")
# #     icon = status_icons.get(status, "•")

# #     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

# #     # Safely escape feedback strings to prevent HTML injection
# #     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
# #     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

# #     st.markdown(f"""
# #     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
# #         <div style="text-align: center; padding: 1rem 0;">
# #             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
# #             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
# #             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
# #         </div>
# #         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
# #             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
# #             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
# #             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     adherence_status = response.get("adherence_status", "")
# #     side_effects_raw = response.get("side_effects", "[]")
# #     try:
# #         side_effects = json.loads(side_effects_raw)
# #     except Exception:
# #         side_effects = []

# #     col1, col2 = st.columns(2)
# #     with col1:
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">💊 Medication Adherence</div>
# #             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
# #         </div>
# #         """, unsafe_allow_html=True)
# #     with col2:
# #         effects_text = ", ".join(side_effects) if side_effects else "None reported"
# #         st.markdown(f"""
# #         <div class="card" style="margin-top: 0;">
# #             <div class="card-header">⚠️ Side Effects</div>
# #             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
# #         </div>
# #         """, unsafe_allow_html=True)

# #     if show_history and patient_id:
# #         st.markdown(
# #             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
# #             unsafe_allow_html=True
# #         )


# # # ── Alert firing logic ────────────────────────────────────────────────────────

# # def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
# #     """Fire structured doctor alerts based on MCQ response."""
# #     trigger = False
# #     reasons = []

# #     if total_score < 0:
# #         trigger = True
# #         reasons.append("negative_score")

# #     if check_consecutive_worsening(patient_id, 2):
# #         trigger = True
# #         reasons.append("consecutive_worsening")

# #     if side_effects:
# #         trigger = True
# #         reasons.append("side_effects")

# #     if not trigger:
# #         return

# #     action_map = {
# #         "Improving": "Continue medication as prescribed",
# #         "Stable": "Monitor closely, follow up in 2-3 days",
# #         "Worsening": "Immediate consultation required"
# #     }

# #     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
# #     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
# #     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
# #     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

# #     alert_message = f"""Patient ID: {patient_id}
# # Doctor ID: {doctor_id}
# # Disease: {patient.get('disease', 'N/A')}
# # Current Status: {status}
# # Score: {total_score:+d}

# # Key Symptoms Reported:
# # {symptoms_text}

# # Medication Adherence:
# # {adherence_text}

# # Side Effects:
# # {side_effects_text}

# # Recommended Action:
# # - {action_map.get(status, 'Monitor patient')}

# # Triggered By: {reasons_text}"""

# #     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

# #     create_alert(
# #         patient_id=patient_id,
# #         alert_type="mcq_health_check",
# #         message=alert_message,
# #         severity=severity,
# #         doctor_id=doctor_id
# #     )




# # # ── Online OPD booking tab ────────────────────────────────────────────────────

# # def _render_patient_opd(patient_id: str, patient: dict):
# #     """Full Online OPD booking UI for the patient dashboard."""
# #     import streamlit as st
# #     from datetime import date, datetime

# #     st.markdown("### 🖥️ Online OPD — Book a Consultation")
# #     st.markdown(
# #         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
# #         'Slots are real-time — once booked they disappear for other patients.</p>',
# #         unsafe_allow_html=True
# #     )

# #     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

# #     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
# #     with opd_subtabs[0]:
# #         doctors = _cached_opd_doctors()

# #         if not doctors:
# #             st.info("No doctors have published OPD slots yet. Please check back later.")
# #         else:
# #             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
# #             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
# #             selected_doctor_id = doctor_options[selected_label]

# #             available_dates = _cached_opd_dates(selected_doctor_id)
# #             if not available_dates:
# #                 st.warning("This doctor has no available slots right now.")
# #             else:
# #                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
# #                 chosen_date_str = st.selectbox(
# #                     "Select Date",
# #                     list(date_labels.keys()),
# #                     format_func=lambda x: date_labels[x],
# #                     key="opd_date_sel"
# #                 )

# #                 # Check if patient already booked on this day with this doctor
# #                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
# #                 if already_booked:
# #                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
# #                 else:
# #                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

# #                     if not free_slots:
# #                         st.error("All slots for this date are fully booked. Please choose another date.")
# #                     else:
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
# #                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
# #                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
# #                                     <strong style="color:#A78BFA;">17 minutes</strong>
# #                                 </div>
# #                                 <div>
# #                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
# #                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
# #                                 </div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         slot_options = {
# #                             f"{s['start_time']} – {s['end_time']}": s['id']
# #                             for s in free_slots
# #                         }
# #                         chosen_slot_label = st.selectbox(
# #                             "Choose a time slot",
# #                             list(slot_options.keys()),
# #                             key="opd_slot_sel"
# #                         )
# #                         chosen_slot_id = slot_options[chosen_slot_label]

# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
# #                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
# #                             <div style="color:var(--text-secondary);font-size:0.9rem;">
# #                                 <strong>Doctor:</strong> {selected_label}<br>
# #                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
# #                                 <strong>Time:</strong> {chosen_slot_label}<br>
# #                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# #                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
# #                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
# #                             if success:
# #                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
# #                                 st.balloons()
# #                                 _cached_opd_bookings.clear()
# #                                 _cached_opd_slots.clear()
# #                                 _cached_has_booking.clear()
# #                                 st.rerun()
# #                             else:
# #                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
# #                                 _cached_opd_slots.clear()
# #                                 st.rerun()

# #     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
# #     with opd_subtabs[1]:
# #         st.markdown("#### 🗓️ Your OPD Bookings")
# #         my_bookings = _cached_opd_bookings(patient_id)

# #         if not my_bookings:
# #             st.markdown("""
# #             <div class="card" style="text-align:center;padding:2rem;">
# #                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
# #                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
# #             </div>
# #             """, unsafe_allow_html=True)
# #         else:
# #             today_str = date.today().isoformat()
# #             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
# #             past = [b for b in my_bookings if b["slot_date"] < today_str]

# #             if upcoming:
# #                 st.markdown("##### 📅 Upcoming")
# #                 for booking in upcoming:
# #                     visited = bool(booking["patient_visited"])
# #                     color = "#34D399" if visited else "#A78BFA"
# #                     status = "✅ Consulted" if visited else "⏳ Pending"
# #                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

# #                     safe_room = booking["id"].replace("-", "").replace(" ", "")
# #                     room_name = f"MediCore-{safe_room}"

# #                     col_b, col_c = st.columns([4, 1])
# #                     with col_b:
# #                         st.markdown(f"""
# #                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
# #                             <div style="display:flex;justify-content:space-between;align-items:center;">
# #                                 <div>
# #                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
# #                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
# #                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
# #                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
# #                                     </div>
# #                                 </div>
# #                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)
# #                     with col_c:
# #                         if not visited:
# #                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
# #                                 success = cancel_opd_booking(booking["id"], patient_id)
# #                                 if success:
# #                                     st.success("Booking cancelled.")
# #                                     _cached_opd_bookings.clear()
# #                                     _cached_opd_slots.clear()
# #                                     _cached_has_booking.clear()
# #                                     st.rerun()

# #                     # ── Embedded video call (Jitsi) ───────────────────────────
# #                     if not visited:
# #                         call_key = f"show_call_pat_{booking['id']}"
# #                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
# #                                      use_container_width=True, type="primary"):
# #                             st.session_state[call_key] = not st.session_state.get(call_key, False)

# #                         if st.session_state.get(call_key, False):
# #                             patient_name = st.session_state.get("patient_id", "Patient")
# #                             encoded_name = str(patient_name).replace(" ", "%20")
# #                             st.components.v1.html(f"""
# #                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
# #                             <iframe
# #                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
# #                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
# #                                 allowfullscreen="true"
# #                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
# #                             ></iframe>
# #                             </body></html>
# #                             """, height=560)

# #             if past:
# #                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
# #                     for booking in past:
# #                         visited = bool(booking["patient_visited"])
# #                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
# #                         status = "✅ Consulted" if visited else "❌ Not attended"
# #                         color = "#34D399" if visited else "#F87171"
# #                         st.markdown(f"""
# #                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
# #                             <div style="display:flex;justify-content:space-between;">
# #                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
# #                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
# #                             </div>
# #                         </div>
# #                         """, unsafe_allow_html=True)

# # # ── Patient login ─────────────────────────────────────────────────────────────

# # def render_patient_login():
# #     st.markdown("""
# #     <div style="max-width: 480px; margin: 4rem auto;">
# #         <div class="page-header" style="text-align: center;">
# #             <h1>🏥 Patient Login</h1>
# #             <p>Enter your Patient ID to access your health portal</p>
# #         </div>
# #     </div>
# #     """, unsafe_allow_html=True)

# #     with st.container():
# #         col1, col2, col3 = st.columns([1, 2, 1])
# #         with col2:
# #             patient_id = st.text_input(
# #                 "Patient ID",
# #                 placeholder="e.g. PAT-20260413-0001",
# #                 label_visibility="collapsed"
# #             )
# #             st.markdown(
# #                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
# #                 'Your ID was provided by your doctor at registration</p>',
# #                 unsafe_allow_html=True
# #             )

# #             if st.button("Access My Health Portal", type="primary", use_container_width=True):
# #                 if patient_id:
# #                     patient = get_patient(patient_id.strip().upper())
# #                     if patient:
# #                         st.session_state["patient_id"] = patient_id.strip().upper()
# #                         st.session_state["patient_logged_in"] = True
# #                         st.rerun()
# #                     else:
# #                         st.error("Patient ID not found. Check with your doctor.")
# #                 else:
# #                     st.warning("Please enter your Patient ID.")


# import streamlit as st
# import json
# from datetime import date, datetime
# from data.database import (
#     get_patient, get_patient_prescriptions, get_chat_history,
#     save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
#     create_alert, check_consecutive_worsening, get_patient_alerts,
#     resolve_alert,
#     get_available_opd_doctors, get_available_opd_dates_for_doctor,
#     get_available_opd_slots, book_opd_slot, cancel_opd_booking,
#     get_patient_opd_bookings, check_patient_has_booking
# )
# from agents.orchestrator import AgentOrchestrator
# from agents.scheduling_agent import (
#     SchedulingAgent, get_auth_url,
#     exchange_code_for_tokens, refresh_access_token
# )
# from agents.mcq_agent import MCQAgent


# # ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_chat_history(patient_id, limit=20):
#     return get_chat_history(patient_id, limit)

# @st.cache_data(ttl=15, show_spinner=False)
# def _cached_prescriptions(patient_id):
#     return get_patient_prescriptions(patient_id)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_patient_alerts(patient_id):
#     return get_patient_alerts(patient_id)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_opd_bookings(patient_id):
#     return get_patient_opd_bookings(patient_id)

# @st.cache_data(ttl=20, show_spinner=False)
# def _cached_mcq_response_today(patient_id, today_str):
#     return get_mcq_response_for_date(patient_id, today_str)

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_mcq_responses(patient_id, limit=30):
#     return get_mcq_responses(patient_id, limit)

# @st.cache_data(ttl=60, show_spinner=False)
# def _cached_opd_doctors():
#     return get_available_opd_doctors()

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_opd_dates(doctor_id):
#     return get_available_opd_dates_for_doctor(doctor_id)

# @st.cache_data(ttl=15, show_spinner=False)
# def _cached_opd_slots(doctor_id, date_str):
#     return get_available_opd_slots(doctor_id, date_str)

# @st.cache_data(ttl=10, show_spinner=False)
# def _cached_has_booking(patient_id, doctor_id, date_str):
#     return check_patient_has_booking(patient_id, doctor_id, date_str)


# # ── OAuth token helpers ───────────────────────────────────────────────────────

# def _handle_google_oauth_callback():
#     """
#     Called once at the top of app.py.
#     If Google redirected back with ?code=..., exchange it for tokens,
#     set mode=patient, and mark patient_google_authed=True.
#     Only removes OAuth-specific params, preserving the _s session-restore param.
#     """
#     params = st.query_params
#     auth_code = params.get("code")
#     if auth_code and not st.session_state.get("google_access_token"):
#         try:
#             tokens = exchange_code_for_tokens(auth_code)
#             if "access_token" in tokens:
#                 st.session_state["google_access_token"] = tokens["access_token"]
#                 st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
#                 st.session_state["patient_google_authed"] = True
#                 st.session_state["mode"] = "patient"
#                 st.toast("✅ Google sign-in successful!", icon="✅")
#         except Exception as e:
#             st.warning(f"Google OAuth error: {e}")
#         # Remove only OAuth-specific params, preserving _s session param
#         for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
#             try:
#                 if oauth_key in st.query_params:
#                     del st.query_params[oauth_key]
#             except Exception:
#                 pass


# def _get_valid_access_token() -> str | None:
#     """Return a valid Google access token from session, refreshing if needed."""
#     token = st.session_state.get("google_access_token")
#     if token:
#         return token
#     refresh_tok = st.session_state.get("google_refresh_token")
#     if refresh_tok:
#         new_token = refresh_access_token(refresh_tok)
#         if new_token:
#             st.session_state["google_access_token"] = new_token
#             return new_token
#     return None


# # ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

# @st.cache_resource(show_spinner=False)
# def _get_orchestrator():
#     return AgentOrchestrator()

# @st.cache_resource(show_spinner=False)
# def _get_scheduler():
#     return SchedulingAgent()

# @st.cache_resource(show_spinner=False)
# def _get_mcq_agent():
#     return MCQAgent()

# @st.cache_data(ttl=120, show_spinner=False)
# def _cached_patient_login(patient_id):
#     """Run the expensive on_patient_login only once per 2 minutes."""
#     return _get_orchestrator().on_patient_login(patient_id)

# @st.cache_data(ttl=30, show_spinner=False)
# def _cached_get_patient(patient_id):
#     return get_patient(patient_id)


# # ── Main dashboard ────────────────────────────────────────────────────────────

# def render_patient_dashboard(patient_id):
#     # OAuth callback is handled at app level (app.py) — no need to call it here again.
#     orchestrator = _get_orchestrator()
#     scheduler = _get_scheduler()
#     mcq_agent = _get_mcq_agent()
#     patient = _cached_get_patient(patient_id)

#     if not patient:
#         st.error("Patient not found. Check your Patient ID.")
#         return

#     st.markdown(f"""
#     <div class="page-header">
#         <h1>🧑‍⚕️ Patient Portal</h1>
#         <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
#     </div>
#     """, unsafe_allow_html=True)

#     # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
#     _health_key = f"health_data_{patient_id}"
#     if _health_key not in st.session_state:
#         with st.spinner("Loading your health data..."):
#             st.session_state[_health_key] = _cached_patient_login(patient_id)
#     health_data = st.session_state[_health_key]

#     risk = health_data.get("risk", {})
#     adherence = health_data.get("adherence", {})
#     trends = health_data.get("trends", {})

#     col1, col2, col3, col4 = st.columns(4)
#     risk_level = risk.get("level", "low")
#     col1.metric("Risk Level", risk_level.upper())
#     col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
#     col3.metric("Active Meds", adherence.get("active_medications", 0))
#     col4.metric("Health Trend", trends.get("trend", "stable").title())

#     st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

#     # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD
#     tabs = st.tabs([
#         "💬 AI Assistant",
#         "📅 My Schedule",
#         "💊 My Prescriptions",
#         "🩺 Daily Health Check",
#         "🔔 Alerts",
#         "🖥️ Online OPD",
#     ])

#     # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
#     with tabs[0]:
#         st.markdown("### 🤖 Autonomous AI Health Agent")
#         st.markdown(
#             '<p style="color: var(--text-secondary);">'
#             'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
#             'and answer any health question — just tell me what you need, and I\'ll take care of it.'
#             '</p>',
#             unsafe_allow_html=True
#         )

#         # ── Quick action chips ─────────────────────────────────────────────
#         st.markdown("""
#         <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
#                          cursor:pointer;">📅 Book Appointment</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          💊 My Prescriptions</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          🩺 Check Symptoms</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          🔔 My Alerts</span>
#             <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
#                          color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
#                          ❌ Cancel Appointment</span>
#         </div>
#         """, unsafe_allow_html=True)

#         history = _cached_chat_history(patient_id, 20)
#         for msg in history:
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])

#         # ── Triage action buttons ─────────────────────────────────────────
#         _triage_key = f"pending_triage_{patient_id}"
#         _triage_msg_key = f"pending_triage_msg_{patient_id}"
#         _confirm_key = f"triage_confirm_{patient_id}"

#         if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
#             triage_level = st.session_state[_triage_key]
#             symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

#             if triage_level == "URGENT":
#                 btn_label = "🚨 Alert My Doctor Now"
#                 btn_type = "primary"
#                 confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
#             else:
#                 btn_label = "📅 Book Urgent Appointment"
#                 btn_type = "secondary"
#                 confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

#             if not st.session_state.get(_confirm_key):
#                 if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
#                     st.session_state[_confirm_key] = True
#                     st.rerun()
#             else:
#                 st.warning(confirm_msg)
#                 col_yes, col_no = st.columns(2)
#                 with col_yes:
#                     if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
#                         severity = "high" if triage_level == "URGENT" else "medium"
#                         alert_message = (
#                             f"[Agentic AI — Patient Reported Symptoms]\n"
#                             f"Patient described: \"{symptom_text}\"\n"
#                             f"AI Triage Verdict: {triage_level}\n"
#                             + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
#                                else "📅 Patient requests a follow-up appointment.")
#                         )
#                         _pt = get_patient(patient_id)
#                         _doctor_id = _pt.get("doctor_id") if _pt else None
#                         create_alert(
#                             patient_id=patient_id,
#                             alert_type="patient_reported_symptoms",
#                             message=alert_message,
#                             severity=severity,
#                             doctor_id=_doctor_id
#                         )
#                         st.session_state.pop(_triage_key, None)
#                         st.session_state.pop(_triage_msg_key, None)
#                         st.session_state.pop(_confirm_key, None)
#                         st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
#                                    else "✅ Alert sent to your doctor!")
#                         st.rerun()
#                 with col_no:
#                     if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
#                         st.session_state.pop(_triage_key, None)
#                         st.session_state.pop(_triage_msg_key, None)
#                         st.session_state.pop(_confirm_key, None)
#                         st.rerun()

#         # ── Action result display (non-triage confirmations) ──────────────
#         _action_result_key = f"action_result_{patient_id}"
#         if st.session_state.get(_action_result_key):
#             ar = st.session_state[_action_result_key]
#             action = ar.get("action", "")
#             confirmed = ar.get("confirmed", False)
#             success = ar.get("success", False)

#             if confirmed and success:
#                 if action == "book_appointment":
#                     bd = ar.get("booking_details", {})
#                     st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
#                 elif action == "cancel_appointment":
#                     st.success("✅ Appointment successfully cancelled.")

#             st.session_state.pop(_action_result_key, None)

#         # ── Chat input ────────────────────────────────────────────────────
#         placeholder = (
#             "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
#             "or 'Show my prescriptions' or 'I have chest pain'..."
#         )
#         if prompt := st.chat_input(placeholder):
#             with st.chat_message("user"):
#                 st.markdown(prompt)

#             with st.chat_message("assistant"):
#                 with st.spinner("🤖 Analysing and acting..."):
#                     result = orchestrator.on_patient_message(
#                         patient_id, prompt,
#                         use_agentic=True,
#                         session_state=st.session_state
#                     )

#                 if not isinstance(result, dict):
#                     result = {"reply": str(result), "triage": None, "action": "general_health"}

#                 reply = result.get("reply", "")
#                 triage = result.get("triage")
#                 action = result.get("action", "")
#                 confirmed = result.get("confirmed", False)
#                 success = result.get("success", False)

#                 # ── Show triage badge ──────────────────────────────────
#                 if triage == "URGENT":
#                     st.error("🔴 **URGENT — Please seek medical attention immediately.**")
#                 elif triage == "MODERATE":
#                     st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
#                 elif triage == "MILD":
#                     st.success("🟢 **MILD — Manageable at home for now.**")

#                 # ── Show action confirmation badge ────────────────────
#                 if confirmed and success:
#                     if action == "book_appointment":
#                         bd = result.get("booking_details", {})
#                         st.success(
#                             f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
#                             f"{bd.get('date', '')} · {bd.get('time', '')}"
#                         )
#                     elif action == "cancel_appointment":
#                         st.success("✅ **Appointment Cancelled Successfully**")

#                 st.markdown(reply)

#             # ── Post-response state management ────────────────────────
#             if triage in ("URGENT", "MODERATE"):
#                 st.session_state[_triage_key] = triage
#                 st.session_state[_triage_msg_key] = prompt
#                 st.session_state.pop(_confirm_key, None)
#             else:
#                 st.session_state.pop(_triage_key, None)
#                 st.session_state.pop(_triage_msg_key, None)
#                 st.session_state.pop(_confirm_key, None)

#             _cached_chat_history.clear()
#             st.rerun()

#     # ── Tab 1: Schedule ───────────────────────────────────────────────────────
#     with tabs[1]:
#         st.markdown("### 📅 Medication Schedule")
#         col1, col2 = st.columns([3, 1])

#         with col2:
#             access_token = _get_valid_access_token()

#             if access_token:
#                 # Token available — show sync button
#                 if st.button("📆 Sync to Google Calendar"):
#                     with st.spinner("Syncing to calendar..."):
#                         result = scheduler.schedule_for_patient(patient_id, access_token)
#                     if result["success"]:
#                         st.success(result["message"])
#                     else:
#                         st.warning(result.get("message", "Sync failed."))
#                         if result.get("errors"):
#                             for e in result["errors"]:
#                                 st.caption(f"⚠ {e}")
#                 if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
#                     st.session_state.pop("google_access_token", None)
#                     st.session_state.pop("google_refresh_token", None)
#                     st.rerun()
#             else:
#                 # No access token in session (e.g. user disconnected or session expired).
#                 # Offer a reconnect via the same Google OAuth flow — same URL used at login.
#                 st.markdown("""
#                 <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
#                              border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
#                     <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
#                         📅 Google Calendar Disconnected
#                     </div>
#                     <div style="color:#A89FC8;font-size:0.82rem;">
#                         Your Google session token has expired. Click below to reconnect —
#                         this uses the same Google account you signed in with.
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)
#                 try:
#                     auth_url = get_auth_url()
#                     st.markdown(f"""
#                     <a href="{auth_url}" target="_self" style="text-decoration:none;">
#                         <div style="
#                             display:flex;align-items:center;justify-content:center;gap:0.6rem;
#                             background:#fff;color:#3c4043;border:1px solid #dadce0;
#                             border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
#                             font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
#                             <svg width="16" height="16" viewBox="0 0 18 18">
#                                 <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
#                                 <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
#                                 <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
#                                 <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
#                             </svg>
#                             Reconnect Google Calendar
#                         </div>
#                     </a>
#                     """, unsafe_allow_html=True)
#                 except Exception:
#                     st.info("Google Calendar integration not configured. Ask your administrator.")

#         schedule = scheduler.get_schedule_preview(patient_id)
#         if not schedule:
#             st.info("No schedule available. Ask your doctor to create a prescription.")
#         else:
#             current_date = None
#             for item in schedule:
#                 if item["date"] != current_date:
#                     current_date = item["date"]
#                     st.markdown(f"**📅 {current_date}**")
#                 st.markdown(f"""
#                 <div class="schedule-item">
#                     <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
#                     <span style="font-weight: 600;">💊 {item['medicine']}</span>
#                     <span style="color: var(--text-secondary);">{item['dosage']}</span>
#                     <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
#                 </div>
#                 """, unsafe_allow_html=True)

#     # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
#     with tabs[2]:
#         st.markdown("### 💊 My Prescriptions")
#         prescriptions = _cached_prescriptions(patient_id)
#         if not prescriptions:
#             st.info("No prescriptions assigned yet. Please consult your doctor.")
#         else:
#             for i, pr in enumerate(prescriptions):
#                 st.markdown(f"""
#                 <div class="card">
#                     <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
#                 """, unsafe_allow_html=True)
#                 for m in pr.get("medicines", []):
#                     st.markdown(f"""
#                     <div class="medicine-card">
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
#                             <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
#                         </div>
#                         <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
#                             ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
#                         </div>
#                     </div>
#                     """, unsafe_allow_html=True)
#                 if pr.get("doctor_notes"):
#                     st.markdown(
#                         f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
#                         unsafe_allow_html=True
#                     )
#                 st.markdown("</div>", unsafe_allow_html=True)

#     # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
#     with tabs[3]:
#         today_str = date.today().isoformat()
#         st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

#         existing_response = _cached_mcq_response_today(patient_id, today_str)
#         _mcq_show_form = True  # controls whether to show the question form

#         if existing_response:
#             _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
#             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#             if st.button("🔄 Retake Today's Check-in", type="secondary"):
#                 st.session_state["retake_mcq"] = True
#                 st.session_state["show_health_summary"] = False
#                 # Clear cached questions so fresh ones load
#                 st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
#                 st.rerun()
#             if not st.session_state.get("retake_mcq"):
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             prescriptions = _cached_prescriptions(patient_id)
#             if not prescriptions:
#                 st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             # Cache questions per patient per day — no need to call GROQ on every rerun
#             _q_key = f"mcq_questions_{patient_id}_{today_str}"
#             if _q_key not in st.session_state:
#                 with st.spinner("Loading your personalized health questions..."):
#                     st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
#             questions = st.session_state[_q_key]

#             if not questions:
#                 st.error("Could not generate questions. Please try again.")
#                 _mcq_show_form = False

#         if _mcq_show_form:
#             st.markdown("""
#             <div class="card" style="margin-bottom: 1.5rem;">
#                 <div class="card-header">📋 Today's Health Questions</div>
#                 <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
#                     Answer honestly based on how you feel today. This helps your doctor monitor your progress.
#                 </p>
#             </div>
#             """, unsafe_allow_html=True)

#             selected_options = {}

#             for q in questions:
#                 qid = str(q["id"])
#                 category_icons = {
#                     "symptom": "🤒",
#                     "adherence": "💊",
#                     "side_effect": "⚠️",
#                     "wellbeing": "💚"
#                 }
#                 icon = category_icons.get(q.get("category", ""), "❓")

#                 st.markdown(f"""
#                 <div class="card" style="margin-bottom: 1rem;">
#                     <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
#                         letter-spacing: 0.08em; margin-bottom: 0.4rem;">
#                         {icon} {q.get('category', '').replace('_', ' ').title()}
#                     </div>
#                     <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
#                         {q['question']}
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)

#                 option_labels = [opt["text"] for opt in q["options"]]
#                 choice = st.radio(
#                     label=q["question"],
#                     options=range(len(option_labels)),
#                     format_func=lambda i, opts=option_labels: opts[i],
#                     key=f"mcq_{qid}",
#                     label_visibility="collapsed"
#                 )
#                 selected_options[qid] = choice
#                 st.markdown("---")

#             col_btn1, col_btn2 = st.columns([3, 1])
#             with col_btn1:
#                 if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
#                     total_score = 0
#                     for q in questions:
#                         qid = str(q["id"])
#                         idx = selected_options.get(qid, 0)
#                         try:
#                             total_score += q["options"][idx]["score"]
#                         except (IndexError, KeyError):
#                             pass

#                     status = mcq_agent.compute_status(total_score)
#                     symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

#                     responses_data = []
#                     for q in questions:
#                         qid = str(q["id"])
#                         idx = selected_options.get(qid, 0)
#                         responses_data.append({
#                             "question": q["question"],
#                             "category": q.get("category"),
#                             "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
#                             "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
#                             "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
#                         })

#                     doctor_id = patient.get("doctor_id")
#                     save_mcq_response(
#                         patient_id=patient_id,
#                         doctor_id=doctor_id,
#                         date_str=today_str,
#                         responses_json=json.dumps(responses_data),
#                         total_score=total_score,
#                         status=status,
#                         side_effects=json.dumps(side_effects),
#                         adherence_status=adherence_status
#                     )

#                     _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
#                                            symptoms, adherence_status, side_effects)

#                     st.session_state["retake_mcq"] = False
#                     st.session_state["show_health_summary"] = True
#                     # Invalidate ALL cached data — must happen before rerun so
#                     # check_consecutive_worsening sees the row just saved
#                     _cached_patient_login.clear()
#                     _cached_mcq_response_today.clear()
#                     _cached_mcq_responses.clear()
#                     _cached_patient_alerts.clear()
#                     # Also bust the worsening booking state so a fresh check runs
#                     st.session_state.pop(f"worsening_booking_step_{patient_id}_tab", None)
#                     st.session_state.pop(f"health_data_{patient_id}", None)
#                     st.rerun()

#         # ── Worsening Trend Early Warning ─────────────────────────────────────
#         # Shown whenever consecutive worsening is detected (after submission or
#         # on return visits).  Booking is ALWAYS patient-initiated — no auto-booking.
#         _worsening_doctor_id = patient.get("doctor_id")
#         _render_worsening_warning(patient_id, patient, _worsening_doctor_id, consecutive_n=2, context="tab")

#         # ── Inline Health Summary — shown after MCQ completion ────────────────
#         # Show automatically after submission OR when today's response already exists
#         _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
#         if _show_summary:
#             st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
#             st.markdown("### 📊 Your Health Summary")

#             # ── AI Health Report ──────────────────────────────────────────────
#             col_ai1, col_ai2 = st.columns([4, 1])
#             with col_ai2:
#                 _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
#             if _gen_report or st.session_state.get("show_health_summary"):
#                 # Cache summary per patient per day - expensive GROQ call
#                 _sum_key = f"health_summary_{patient_id}_{today_str}"
#                 if _gen_report or _sum_key not in st.session_state:
#                     with st.spinner("AI is analyzing your health data..."):
#                         st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
#                 summary = st.session_state[_sum_key]
#                 st.markdown(f"""
#                 <div class="card">
#                     <div class="card-header">🤖 AI Clinical Assessment</div>
#                     <p style="line-height: 1.7;">{summary}</p>
#                 </div>
#                 """, unsafe_allow_html=True)

#             # ── Health Indicators ─────────────────────────────────────────────
#             risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
#             risk_color = risk_colors.get(risk_level, "#A78BFA")
#             st.markdown(f"""
#             <div class="card">
#                 <div class="card-header">Health Indicators</div>
#                 <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
#                         <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
#                         <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
#                         <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
#                     </div>
#                     <div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
#                         <span style="color: var(--text-primary);">{patient['disease']}</span>
#                     </div>
#                 </div>
#             </div>
#             """, unsafe_allow_html=True)

#             # ── Health Trend Chart ────────────────────────────────────────────
#             responses = _cached_mcq_responses(patient_id, limit=30)
#             if responses:
#                 st.markdown("#### 📈 Health Trend — Score Over Time")

#                 import pandas as pd
#                 import plotly.graph_objects as go

#                 chart_responses = list(reversed(responses))
#                 dates  = [r["date"] for r in chart_responses]
#                 scores = [r["total_score"] for r in chart_responses]
#                 statuses = [r["status"] for r in chart_responses]

#                 status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#                 marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

#                 fig = go.Figure()
#                 fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=[max(s, 0) for s in scores],
#                     fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
#                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#                 ))
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=[min(s, 0) for s in scores],
#                     fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
#                     line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
#                 ))
#                 fig.add_trace(go.Scatter(
#                     x=dates, y=scores,
#                     mode="lines+markers",
#                     line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
#                     marker=dict(size=10, color=marker_colors,
#                                 line=dict(color="#1a1a2e", width=2)),
#                     name="Health Score",
#                     hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
#                 ))

#                 status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#                 for d, s, st_ in zip(dates, scores, statuses):
#                     fig.add_annotation(
#                         x=d, y=s,
#                         text=status_icons_map.get(st_, ""),
#                         showarrow=False,
#                         yshift=18, font=dict(size=13)
#                     )

#                 fig.update_layout(
#                     paper_bgcolor="rgba(0,0,0,0)",
#                     plot_bgcolor="rgba(0,0,0,0)",
#                     font=dict(color="#A89FC8", size=12),
#                     margin=dict(l=10, r=10, t=10, b=10),
#                     height=300,
#                     xaxis=dict(
#                         showgrid=False, zeroline=False,
#                         tickfont=dict(size=11, color="#6B6080"),
#                         title=""
#                     ),
#                     yaxis=dict(
#                         showgrid=True, gridcolor="rgba(255,255,255,0.05)",
#                         zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
#                         tickfont=dict(size=11, color="#6B6080"),
#                         title="Score"
#                     ),
#                     hoverlabel=dict(
#                         bgcolor="#1E1B4B", bordercolor="#A78BFA",
#                         font=dict(color="white", size=13)
#                     ),
#                     showlegend=False
#                 )

#                 st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

#                 st.markdown("""
#                 <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
#                     <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
#                     <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
#                     <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
#                     <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
#                 </div>
#                 """, unsafe_allow_html=True)

#                 # ── Recent Check-in History ───────────────────────────────────
#                 st.markdown("#### 📋 Recent Daily Check-in History")
#                 for r in responses:
#                     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#                     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#                     color = status_colors.get(r["status"], "#A78BFA")
#                     icon = status_icons.get(r["status"], "•")
#                     st.markdown(f"""
#                     <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
#                             <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
#                             <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
#                         </div>
#                         <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
#                             Adherence: {r.get('adherence_status', 'N/A')}
#                         </div>
#                     </div>
#                     """, unsafe_allow_html=True)

#     # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
#     with tabs[4]:
#         _render_patient_alerts(patient_id, patient, risk_level, risk)

#     # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
#     with tabs[5]:
#         _render_patient_opd(patient_id, patient)


# # ── Alerts tab renderer ───────────────────────────────────────────────────────

# def _render_patient_alerts(patient_id, patient, risk_level, risk):
#     """Render the patient-facing Alerts & Notifications tab."""
#     st.markdown("### 🔔 Alerts & Notifications")
#     st.markdown(
#         '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
#         'and doctor messages are shown here.</p>',
#         unsafe_allow_html=True
#     )

#     # ── High-Risk Banner ──────────────────────────────────────────────────────
#     if risk_level == "high":
#         st.markdown(f"""
#         <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
#             <div style="display:flex;align-items:center;gap:0.8rem;">
#                 <span style="font-size:1.8rem;">🚨</span>
#                 <div>
#                     <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
#                     <div style="color:var(--text-secondary);font-size:0.9rem;">
#                         Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
#                         Please contact your doctor or visit the clinic immediately.
#                     </div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── Worsening Trend Early Warning (also surfaced here for discoverability) ──
#     _wt_doctor_id = patient.get("doctor_id")
#     _render_worsening_warning(patient_id, patient, _wt_doctor_id, consecutive_n=2, context="alerts")

#     # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
#     recent_responses = _cached_mcq_responses(patient_id, limit=7)
#     missed_dose_dates = []
#     for r in recent_responses:
#         adh = (r.get("adherence_status") or "").lower()
#         if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
#             missed_dose_dates.append(r["date"])

#     if missed_dose_dates:
#         dates_str = ", ".join(missed_dose_dates[:3])
#         st.markdown(f"""
#         <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
#             <div style="display:flex;align-items:center;gap:0.8rem;">
#                 <span style="font-size:1.8rem;">💊</span>
#                 <div>
#                     <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
#                     <div style="color:var(--text-secondary);font-size:0.85rem;">
#                         Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
#                         Consistent adherence is key to recovery — please take medications as prescribed.
#                     </div>
#                 </div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── DB Alerts ─────────────────────────────────────────────────────────────
#     all_alerts = _cached_patient_alerts(patient_id)
#     unresolved = [a for a in all_alerts if not a["resolved"]]
#     resolved = [a for a in all_alerts if a["resolved"]]

#     if not all_alerts and not missed_dose_dates and risk_level != "high":
#         st.markdown("""
#         <div class="card" style="text-align:center;padding:2rem;">
#             <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
#             <div style="font-weight:600;color:#34D399;">All Clear</div>
#             <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
#                 No active alerts. Keep taking your medications and completing daily check-ins!
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#         return

#     severity_config = {
#         "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
#         "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
#         "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
#     }
#     type_labels = {
#         "mcq_health_check":       "Health Check Alert",
#         "doctor_message":         "Doctor Message",
#         "missed_dose":            "Missed Dose",
#         "high_risk":              "High Risk Warning",
#         "worsening_opd_booked":   "Worsening Trend — OPD Booked",
#         "worsening_condition":    "Worsening Condition",
#         "patient_reported_symptoms": "Patient Reported Symptoms",
#     }

#     if unresolved:
#         st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
#         for alert in unresolved:
#             cfg = severity_config.get(alert["severity"], severity_config["medium"])
#             type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
#             created = alert["created_at"][:16].replace("T", " ")

#             with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
#                 st.markdown(f"""
#                 <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
#                              border-left:3px solid {cfg['color']};">
#                     <pre style="font-size:0.82rem;color:var(--text-secondary);
#                                 white-space:pre-wrap;word-break:break-word;margin:0;">
# {alert['message']}</pre>
#                 </div>
#                 """, unsafe_allow_html=True)
#                 if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
#                     resolve_alert(alert["id"])
#                     _cached_patient_alerts.clear()
#                     st.rerun()

#     if resolved:
#         with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
#             for alert in resolved:
#                 cfg = severity_config.get(alert["severity"], severity_config["medium"])
#                 type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
#                 created = alert["created_at"][:16].replace("T", " ")
#                 st.markdown(f"""
#                 <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
#                     <div style="display:flex;justify-content:space-between;">
#                         <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
#                         <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
#                     </div>
#                 </div>
#                 """, unsafe_allow_html=True)


# # ── MCQ result card ───────────────────────────────────────────────────────────

# def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
#     status = response["status"]
#     score = response["total_score"]
#     status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
#     status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
#     color = status_colors.get(status, "#A78BFA")
#     icon = status_icons.get(status, "•")

#     feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

#     # Safely escape feedback strings to prevent HTML injection
#     action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
#     message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

#     st.markdown(f"""
#     <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
#         <div style="text-align: center; padding: 1rem 0;">
#             <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
#             <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
#             <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
#         </div>
#         <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
#             <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
#             <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
#             <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     adherence_status = response.get("adherence_status", "")
#     side_effects_raw = response.get("side_effects", "[]")
#     try:
#         side_effects = json.loads(side_effects_raw)
#     except Exception:
#         side_effects = []

#     col1, col2 = st.columns(2)
#     with col1:
#         st.markdown(f"""
#         <div class="card" style="margin-top: 0;">
#             <div class="card-header">💊 Medication Adherence</div>
#             <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
#         </div>
#         """, unsafe_allow_html=True)
#     with col2:
#         effects_text = ", ".join(side_effects) if side_effects else "None reported"
#         st.markdown(f"""
#         <div class="card" style="margin-top: 0;">
#             <div class="card-header">⚠️ Side Effects</div>
#             <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
#         </div>
#         """, unsafe_allow_html=True)

#     if show_history and patient_id:
#         st.markdown(
#             f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
#             unsafe_allow_html=True
#         )


# # ── Alert firing logic ────────────────────────────────────────────────────────

# def _render_worsening_warning(patient_id: str, patient: dict, doctor_id: str, consecutive_n: int = 2, context: str = "tab"):
#     """
#     Worsening Trend Early Warning banner.

#     Shown on the Daily Health Check tab immediately after MCQ submission
#     (and on every subsequent visit while the trend persists).  It does NOT
#     book an appointment automatically — it offers the patient a clearly
#     labelled 'Book Appointment' button.  Only when the patient clicks that
#     button does the UI fetch real available slots and confirm the booking.

#     Session-state keys used (all scoped to patient_id):
#         worsening_booking_step_{pid}   : None | 'select' | 'confirm'
#         worsening_booking_slots_{pid}  : list[dict]  — raw slot rows
#         worsening_booking_doctor_{pid} : dict        — chosen doctor row
#         worsening_booking_slot_{pid}   : dict        — chosen slot row
#     """
#     # ── Debug: always show last 3 MCQ statuses so you can verify DB state ────
#     from data.database import get_mcq_responses as _gmr
#     _recent = _gmr(patient_id, limit=3)
#     _statuses = [r["status"] for r in _recent]
#     _is_worsening = check_consecutive_worsening(patient_id, consecutive_n)
#     st.caption(
#         f"🔍 Debug — last {len(_statuses)} MCQ statuses: {_statuses} | "
#         f"consecutive_worsening({consecutive_n}) → **{_is_worsening}**"
#     )

#     # ── Guard: only render when consecutive worsening detected ───────────────
#     if not check_consecutive_worsening(patient_id, consecutive_n):
#         # If the warning was previously shown, clean up stale state gracefully
#         for sfx in ("step", "slots", "doctor", "slot"):
#             st.session_state.pop(f"worsening_booking_{sfx}_{patient_id}_{context}", None)
#         return

#     step_key   = f"worsening_booking_step_{patient_id}_{context}"
#     slots_key  = f"worsening_booking_slots_{patient_id}_{context}"
#     doctor_key = f"worsening_booking_doctor_{patient_id}_{context}"
#     slot_key   = f"worsening_booking_slot_{patient_id}_{context}"

#     step = st.session_state.get(step_key)  # None | 'select' | 'confirm'

#     # ── Main warning banner ───────────────────────────────────────────────────
#     st.markdown(f"""
#     <div class="card" style="border-left:4px solid #F87171;
#          background:rgba(248,113,113,0.08);margin-bottom:1rem;">
#         <div style="display:flex;align-items:flex-start;gap:0.9rem;">
#             <span style="font-size:2rem;line-height:1;">🚨</span>
#             <div>
#                 <div style="font-weight:700;color:#F87171;font-size:1.05rem;margin-bottom:0.3rem;">
#                     Worsening Trend Detected
#                 </div>
#                 <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;">
#                     Your last <strong style="color:#F87171;">{consecutive_n} health check-ins</strong>
#                     have both shown a <em>Worsening</em> status.
#                     Your doctor has been notified via an alert.
#                     We recommend booking a consultation soon.
#                 </div>
#             </div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Step 0: Offer the booking button (no auto-booking) ───────────────────
#     if step is None:
#         if st.button(
#             "📅 Book an Appointment with My Doctor",
#             key=f"worsening_book_btn_{patient_id}_{context}",
#             type="primary",
#         ):
#             # Fetch available slots now (lazy — only on click)
#             doctors = get_available_opd_doctors()
#             # Filter to the patient's own doctor first; fall back to all
#             my_doctor_id = patient.get("doctor_id")
#             my_doctors = [d for d in doctors if d["doctor_id"] == my_doctor_id] or doctors

#             all_slots = []
#             for doc in my_doctors:
#                 dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
#                 for d in dates[:3]:  # look at next 3 available dates only
#                     slots = get_available_opd_slots(doc["doctor_id"], d)
#                     for s in slots:
#                         all_slots.append({**s, "doctor_name": doc["name"],
#                                            "doctor_id": doc["doctor_id"]})

#             if not all_slots:
#                 st.warning(
#                     "⚠️ No available OPD slots found right now. "
#                     "Please contact the clinic directly or check back later."
#                 )
#                 return

#             st.session_state[slots_key] = all_slots
#             st.session_state[step_key]  = "select"
#             st.rerun()
#         return  # nothing more to render at step 0

#     # ── Step 1: Slot selector ─────────────────────────────────────────────────
#     if step == "select":
#         all_slots = st.session_state.get(slots_key, [])
#         if not all_slots:
#             st.warning("No slots loaded. Please try again.")
#             st.session_state.pop(step_key, None)
#             return

#         st.markdown(
#             "<div style='color:var(--text-secondary);font-size:0.88rem;"
#             "margin-bottom:0.6rem;'>Select an available slot:</div>",
#             unsafe_allow_html=True,
#         )

#         # Build human-readable labels
#         slot_labels = [
#             f"Dr. {s['doctor_name']} — {s['slot_date']}  {s['start_time']}–{s['end_time']}"
#             for s in all_slots
#         ]
#         chosen_idx = st.selectbox(
#             "Available slots",
#             options=range(len(slot_labels)),
#             format_func=lambda i: slot_labels[i],
#             key=f"worsening_slot_select_{patient_id}_{context}",
#             label_visibility="collapsed",
#         )

#         col_ok, col_cancel = st.columns([2, 1])
#         with col_ok:
#             if st.button(
#                 "Confirm this slot →",
#                 key=f"worsening_confirm_btn_{patient_id}_{context}",
#                 type="primary",
#                 use_container_width=True,
#             ):
#                 chosen = all_slots[chosen_idx]
#                 st.session_state[slot_key]   = chosen
#                 st.session_state[doctor_key] = {"name": chosen["doctor_name"],
#                                                  "id":   chosen["doctor_id"]}
#                 st.session_state[step_key]   = "confirm"
#                 st.rerun()
#         with col_cancel:
#             if st.button(
#                 "Cancel",
#                 key=f"worsening_cancel_select_{patient_id}_{context}",
#                 use_container_width=True,
#             ):
#                 for k in (step_key, slots_key, doctor_key, slot_key):
#                     st.session_state.pop(k, None)
#                 st.rerun()
#         return

#     # ── Step 2: Final confirmation ────────────────────────────────────────────
#     if step == "confirm":
#         chosen_slot   = st.session_state.get(slot_key, {})
#         chosen_doctor = st.session_state.get(doctor_key, {})

#         st.markdown(f"""
#         <div class="card" style="border:1px solid rgba(167,139,250,0.4);
#              background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
#             <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
#                 📋 Confirm Booking
#             </div>
#             <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.8;">
#                 <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
#                 <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
#                 <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#         col_yes, col_no = st.columns(2)
#         with col_yes:
#             if st.button(
#                 "✅ Book Appointment",
#                 key=f"worsening_book_yes_{patient_id}_{context}",
#                 type="primary",
#                 use_container_width=True,
#             ):
#                 success = book_opd_slot(
#                     slot_id=chosen_slot["id"],
#                     patient_id=patient_id,
#                     patient_name=patient.get("name", ""),
#                 )
#                 # Clean up state regardless of outcome
#                 for k in (step_key, slots_key, doctor_key, slot_key):
#                     st.session_state.pop(k, None)
#                 _cached_opd_bookings.clear()

#                 if success:
#                     # Upgrade the doctor-side alert to note the booking
#                     create_alert(
#                         patient_id=patient_id,
#                         alert_type="worsening_opd_booked",
#                         message=(
#                             f"Patient self-booked an OPD slot in response to worsening trend alert.\n"
#                             f"Slot: Dr. {chosen_doctor.get('name','')} on "
#                             f"{chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
#                         ),
#                         severity="medium",
#                         doctor_id=doctor_id,
#                     )
#                     st.success(
#                         f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
#                         f"on {chosen_slot.get('slot_date','')} at {chosen_slot.get('start_time','')}."
#                     )
#                 else:
#                     st.error(
#                         "❌ That slot was just taken by someone else. "
#                         "Please go to the Online OPD tab to pick another slot."
#                     )
#                 st.rerun()

#         with col_no:
#             if st.button(
#                 "← Back",
#                 key=f"worsening_book_back_{patient_id}_{context}",
#                 use_container_width=True,
#             ):
#                 st.session_state[step_key] = "select"
#                 st.rerun()


# def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
#     """Fire structured doctor alerts based on MCQ response."""
#     trigger = False
#     reasons = []

#     if total_score < 0:
#         trigger = True
#         reasons.append("negative_score")

#     if check_consecutive_worsening(patient_id, 2):
#         trigger = True
#         reasons.append("consecutive_worsening")

#     if side_effects:
#         trigger = True
#         reasons.append("side_effects")

#     if not trigger:
#         return

#     action_map = {
#         "Improving": "Continue medication as prescribed",
#         "Stable": "Monitor closely, follow up in 2-3 days",
#         "Worsening": "Immediate consultation required"
#     }

#     symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
#     side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
#     adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
#     reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

#     alert_message = f"""Patient ID: {patient_id}
# Doctor ID: {doctor_id}
# Disease: {patient.get('disease', 'N/A')}
# Current Status: {status}
# Score: {total_score:+d}

# Key Symptoms Reported:
# {symptoms_text}

# Medication Adherence:
# {adherence_text}

# Side Effects:
# {side_effects_text}

# Recommended Action:
# - {action_map.get(status, 'Monitor patient')}

# Triggered By: {reasons_text}"""

#     severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

#     create_alert(
#         patient_id=patient_id,
#         alert_type="mcq_health_check",
#         message=alert_message,
#         severity=severity,
#         doctor_id=doctor_id
#     )




# # ── Online OPD booking tab ────────────────────────────────────────────────────

# def _render_patient_opd(patient_id: str, patient: dict):
#     """Full Online OPD booking UI for the patient dashboard."""
#     import streamlit as st
#     from datetime import date, datetime

#     st.markdown("### 🖥️ Online OPD — Book a Consultation")
#     st.markdown(
#         '<p style="color:var(--text-secondary);">Book a 17-minute online consultation slot with your doctor. '
#         'Slots are real-time — once booked they disappear for other patients.</p>',
#         unsafe_allow_html=True
#     )

#     opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

#     # ── Sub-tab A: Book ───────────────────────────────────────────────────────
#     with opd_subtabs[0]:
#         doctors = _cached_opd_doctors()

#         if not doctors:
#             st.info("No doctors have published OPD slots yet. Please check back later.")
#         else:
#             doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
#             selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
#             selected_doctor_id = doctor_options[selected_label]

#             available_dates = _cached_opd_dates(selected_doctor_id)
#             if not available_dates:
#                 st.warning("This doctor has no available slots right now.")
#             else:
#                 date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
#                 chosen_date_str = st.selectbox(
#                     "Select Date",
#                     list(date_labels.keys()),
#                     format_func=lambda x: date_labels[x],
#                     key="opd_date_sel"
#                 )

#                 # Check if patient already booked on this day with this doctor
#                 already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
#                 if already_booked:
#                     st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
#                 else:
#                     free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

#                     if not free_slots:
#                         st.error("All slots for this date are fully booked. Please choose another date.")
#                     else:
#                         st.markdown(f"""
#                         <div class="card" style="padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
#                             <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">AVAILABLE SLOTS</span><br>
#                                     <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
#                                 </div>
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">SLOT DURATION</span><br>
#                                     <strong style="color:#A78BFA;">17 minutes</strong>
#                                 </div>
#                                 <div>
#                                     <span style="color:var(--text-muted);font-size:0.75rem;">EARLIEST SLOT</span><br>
#                                     <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
#                                 </div>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

#                         slot_options = {
#                             f"{s['start_time']} – {s['end_time']}": s['id']
#                             for s in free_slots
#                         }
#                         chosen_slot_label = st.selectbox(
#                             "Choose a time slot",
#                             list(slot_options.keys()),
#                             key="opd_slot_sel"
#                         )
#                         chosen_slot_id = slot_options[chosen_slot_label]

#                         st.markdown(f"""
#                         <div class="card" style="border-left:3px solid #A78BFA;padding:0.8rem 1.2rem;">
#                             <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
#                             <div style="color:var(--text-secondary);font-size:0.9rem;">
#                                 <strong>Doctor:</strong> {selected_label}<br>
#                                 <strong>Date:</strong> {date_labels[chosen_date_str]}<br>
#                                 <strong>Time:</strong> {chosen_slot_label}<br>
#                                 <strong>Patient:</strong> {patient['name']} (<code>{patient_id}</code>)
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

#                         if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
#                             success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
#                             if success:
#                                 st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
#                                 st.balloons()
#                                 _cached_opd_bookings.clear()
#                                 _cached_opd_slots.clear()
#                                 _cached_has_booking.clear()
#                                 st.rerun()
#                             else:
#                                 st.error("❌ This slot was just booked by someone else. Please select another slot.")
#                                 _cached_opd_slots.clear()
#                                 st.rerun()

#     # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
#     with opd_subtabs[1]:
#         st.markdown("#### 🗓️ Your OPD Bookings")
#         my_bookings = _cached_opd_bookings(patient_id)

#         if not my_bookings:
#             st.markdown("""
#             <div class="card" style="text-align:center;padding:2rem;">
#                 <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
#                 <div style="color:var(--text-muted);">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
#             </div>
#             """, unsafe_allow_html=True)
#         else:
#             today_str = date.today().isoformat()
#             upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
#             past = [b for b in my_bookings if b["slot_date"] < today_str]

#             if upcoming:
#                 st.markdown("##### 📅 Upcoming")
#                 for booking in upcoming:
#                     visited = bool(booking["patient_visited"])
#                     color = "#34D399" if visited else "#A78BFA"
#                     status = "✅ Consulted" if visited else "⏳ Pending"
#                     slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

#                     safe_room = booking["id"].replace("-", "").replace(" ", "")
#                     room_name = f"MediCore-{safe_room}"

#                     col_b, col_c = st.columns([4, 1])
#                     with col_b:
#                         st.markdown(f"""
#                         <div class="card" style="border-left:3px solid {color};padding:0.8rem 1.2rem;">
#                             <div style="display:flex;justify-content:space-between;align-items:center;">
#                                 <div>
#                                     <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
#                                     <div style="color:var(--text-secondary);font-size:0.85rem;">{booking['specialization']}</div>
#                                     <div style="color:var(--text-muted);font-size:0.8rem;margin-top:0.3rem;">
#                                         📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
#                                     </div>
#                                 </div>
#                                 <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)
#                     with col_c:
#                         if not visited:
#                             if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
#                                 success = cancel_opd_booking(booking["id"], patient_id)
#                                 if success:
#                                     st.success("Booking cancelled.")
#                                     _cached_opd_bookings.clear()
#                                     _cached_opd_slots.clear()
#                                     _cached_has_booking.clear()
#                                     st.rerun()

#                     # ── Embedded video call (Jitsi) ───────────────────────────
#                     if not visited:
#                         call_key = f"show_call_pat_{booking['id']}"
#                         if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
#                                      use_container_width=True, type="primary"):
#                             st.session_state[call_key] = not st.session_state.get(call_key, False)

#                         if st.session_state.get(call_key, False):
#                             patient_name = st.session_state.get("patient_id", "Patient")
#                             encoded_name = str(patient_name).replace(" ", "%20")
#                             st.components.v1.html(f"""
#                             <!DOCTYPE html><html><body style="margin:0;padding:0;background:#0f0f1a;">
#                             <iframe
#                                 src="https://meet.jit.si/{room_name}#userInfo.displayName={encoded_name}&config.prejoinPageEnabled=false&config.startWithAudioMuted=false&config.startWithVideoMuted=false&interfaceConfig.SHOW_JITSI_WATERMARK=false&interfaceConfig.TOOLBAR_BUTTONS=[%22microphone%22,%22camera%22,%22hangup%22,%22chat%22,%22tileview%22,%22fullscreen%22]"
#                                 allow="camera; microphone; fullscreen; display-capture; autoplay; screen-wake-lock"
#                                 allowfullscreen="true"
#                                 style="width:100%;height:540px;border:none;border-radius:12px;border:2px solid #7C3AED;"
#                             ></iframe>
#                             </body></html>
#                             """, height=560)

#             if past:
#                 with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
#                     for booking in past:
#                         visited = bool(booking["patient_visited"])
#                         slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
#                         status = "✅ Consulted" if visited else "❌ Not attended"
#                         color = "#34D399" if visited else "#F87171"
#                         st.markdown(f"""
#                         <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
#                             <div style="display:flex;justify-content:space-between;">
#                                 <span style="font-size:0.85rem;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
#                                 <span style="font-size:0.8rem;color:{color};">{status}</span>
#                             </div>
#                         </div>
#                         """, unsafe_allow_html=True)

# # ── Patient login ─────────────────────────────────────────────────────────────

# def render_patient_login():
#     st.markdown("""
#     <div style="max-width: 480px; margin: 4rem auto;">
#         <div class="page-header" style="text-align: center;">
#             <h1>🏥 Patient Login</h1>
#             <p>Enter your Patient ID to access your health portal</p>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     with st.container():
#         col1, col2, col3 = st.columns([1, 2, 1])
#         with col2:
#             patient_id = st.text_input(
#                 "Patient ID",
#                 placeholder="e.g. PAT-20260413-0001",
#                 label_visibility="collapsed"
#             )
#             st.markdown(
#                 '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
#                 'Your ID was provided by your doctor at registration</p>',
#                 unsafe_allow_html=True
#             )

#             if st.button("Access My Health Portal", type="primary", use_container_width=True):
#                 if patient_id:
#                     patient = get_patient(patient_id.strip().upper())
#                     if patient:
#                         st.session_state["patient_id"] = patient_id.strip().upper()
#                         st.session_state["patient_logged_in"] = True
#                         st.rerun()
#                     else:
#                         st.error("Patient ID not found. Check with your doctor.")
#                 else:
#                     st.warning("Please enter your Patient ID.")




import streamlit as st
import json
import requests
from datetime import date, datetime
from data.database import (
    get_patient, get_patient_prescriptions, get_chat_history,
    save_mcq_response, get_mcq_response_for_date, get_mcq_responses,
    create_alert, check_consecutive_worsening, get_patient_alerts,
    resolve_alert,
    get_available_opd_doctors, get_available_opd_dates_for_doctor,
    get_available_opd_slots, book_opd_slot, cancel_opd_booking,
    get_patient_opd_bookings, check_patient_has_booking
)
from agents.orchestrator import AgentOrchestrator
from agents.scheduling_agent import (
    SchedulingAgent, get_auth_url,
    exchange_code_for_tokens, refresh_access_token
)
from agents.mcq_agent import MCQAgent


# ── Cached DB wrappers (prevent repeated DB hits on every Streamlit rerun) ────

@st.cache_data(ttl=10, show_spinner=False)
def _cached_chat_history(patient_id, limit=20):
    return get_chat_history(patient_id, limit)

@st.cache_data(ttl=15, show_spinner=False)
def _cached_prescriptions(patient_id):
    return get_patient_prescriptions(patient_id)

@st.cache_data(ttl=10, show_spinner=False)
def _cached_patient_alerts(patient_id):
    return get_patient_alerts(patient_id)

@st.cache_data(ttl=10, show_spinner=False)
def _cached_opd_bookings(patient_id):
    return get_patient_opd_bookings(patient_id)

@st.cache_data(ttl=20, show_spinner=False)
def _cached_mcq_response_today(patient_id, today_str):
    return get_mcq_response_for_date(patient_id, today_str)

@st.cache_data(ttl=30, show_spinner=False)
def _cached_mcq_responses(patient_id, limit=30):
    return get_mcq_responses(patient_id, limit)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_opd_doctors():
    return get_available_opd_doctors()

@st.cache_data(ttl=30, show_spinner=False)
def _cached_opd_dates(doctor_id):
    return get_available_opd_dates_for_doctor(doctor_id)

@st.cache_data(ttl=15, show_spinner=False)
def _cached_opd_slots(doctor_id, date_str):
    return get_available_opd_slots(doctor_id, date_str)

@st.cache_data(ttl=10, show_spinner=False)
def _cached_has_booking(patient_id, doctor_id, date_str):
    return check_patient_has_booking(patient_id, doctor_id, date_str)


# ── OAuth token helpers ───────────────────────────────────────────────────────

def _handle_google_oauth_callback():
    """
    Called once at the top of app.py.
    If Google redirected back with ?code=..., exchange it for tokens,
    set mode=patient, and mark patient_google_authed=True.
    Only removes OAuth-specific params, preserving the _s session-restore param.
    """
    params = st.query_params
    auth_code = params.get("code")
    if auth_code and not st.session_state.get("google_access_token"):
        try:
            tokens = exchange_code_for_tokens(auth_code)
            if "access_token" in tokens:
                st.session_state["google_access_token"] = tokens["access_token"]
                st.session_state["google_refresh_token"] = tokens.get("refresh_token", "")
                st.session_state["patient_google_authed"] = True
                st.session_state["mode"] = "patient"
                st.toast("✅ Google sign-in successful!", icon="✅")
        except Exception as e:
            st.warning(f"Google OAuth error: {e}")
        # Remove only OAuth-specific params, preserving _s session param
        for oauth_key in ["code", "scope", "state", "session_state", "authuser", "prompt"]:
            try:
                if oauth_key in st.query_params:
                    del st.query_params[oauth_key]
            except Exception:
                pass


def _get_valid_access_token() -> str | None:
    """Return a valid Google access token from session, refreshing if needed."""
    token = st.session_state.get("google_access_token")
    if token:
        return token
    refresh_tok = st.session_state.get("google_refresh_token")
    if refresh_tok:
        new_token = refresh_access_token(refresh_tok)
        if new_token:
            st.session_state["google_access_token"] = new_token
            return new_token
    return None


# ── Cached helpers (avoid re-instantiating agents on every render) ─────────────

@st.cache_resource(show_spinner=False)
def _get_orchestrator():
    return AgentOrchestrator()

@st.cache_resource(show_spinner=False)
def _get_scheduler():
    return SchedulingAgent()

@st.cache_resource(show_spinner=False)
def _get_mcq_agent():
    return MCQAgent()

@st.cache_data(ttl=120, show_spinner=False)
def _cached_patient_login(patient_id):
    """Run the expensive on_patient_login only once per 2 minutes."""
    return _get_orchestrator().on_patient_login(patient_id)

@st.cache_data(ttl=30, show_spinner=False)
def _cached_get_patient(patient_id):
    return get_patient(patient_id)


# ── Main dashboard ────────────────────────────────────────────────────────────

def render_patient_dashboard(patient_id):
    # OAuth callback is handled at app level (app.py) — no need to call it here again.
    orchestrator = _get_orchestrator()
    scheduler = _get_scheduler()
    mcq_agent = _get_mcq_agent()
    patient = _cached_get_patient(patient_id)

    if not patient:
        st.error("Patient not found. Check your Patient ID.")
        return

    st.markdown(f"""
    <div class="page-header">
        <h1>🧑‍⚕️ Patient Portal</h1>
        <p>Welcome back, <strong>{patient['name']}</strong> — ID: <code>{patient_id}</code></p>
    </div>
    """, unsafe_allow_html=True)

    # Use cached health data — only re-fetches after 2 minutes or on explicit refresh
    _health_key = f"health_data_{patient_id}"
    if _health_key not in st.session_state:
        with st.spinner("Loading your health data..."):
            st.session_state[_health_key] = _cached_patient_login(patient_id)
    health_data = st.session_state[_health_key]

    risk = health_data.get("risk", {})
    adherence = health_data.get("adherence", {})
    trends = health_data.get("trends", {})

    col1, col2, col3, col4 = st.columns(4)
    risk_level = risk.get("level", "low")
    col1.metric("Risk Level", risk_level.upper())
    col2.metric("Risk Score", f"{risk.get('score', 0)}/100")
    col3.metric("Active Meds", adherence.get("active_medications", 0))
    col4.metric("Health Trend", trends.get("trend", "stable").title())

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Tab order: AI Assistant, Schedule, Prescriptions, Daily Health Check & Summary, Alerts, Online OPD, Health Command Center
    tabs = st.tabs([
        "💬 AI Assistant",
        "📅 My Schedule",
        "💊 My Prescriptions",
        "🩺 Daily Health Check",
        "🔔 Alerts",
        "🖥️ Online OPD",
        "📋 Consultation Summaries",
        "🧬 Health Command Center",
    ])

    # ── Tab 0: Agentic AI Assistant ───────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 🤖 Autonomous AI Health Agent")
        st.markdown(
            '<p style="color: var(--text-secondary);">'
            'I can <strong>book appointments, cancel bookings, check prescriptions, triage symptoms</strong> '
            'and answer any health question — just tell me what you need, and I\'ll take care of it.'
            '</p>',
            unsafe_allow_html=True
        )

        # ── Quick action chips ─────────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-bottom:1rem;">
            <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                         color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;
                         cursor:pointer;">📅 Book Appointment</span>
            <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                         color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
                         💊 My Prescriptions</span>
            <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                         color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
                         🩺 Check Symptoms</span>
            <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                         color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
                         🔔 My Alerts</span>
            <span style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.4);
                         color:#A5B4FC;padding:0.3rem 0.75rem;border-radius:20px;font-size:0.82rem;">
                         ❌ Cancel Appointment</span>
        </div>
        """, unsafe_allow_html=True)

        history = _cached_chat_history(patient_id, 20)
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # ── Triage action buttons ─────────────────────────────────────────
        _triage_key = f"pending_triage_{patient_id}"
        _triage_msg_key = f"pending_triage_msg_{patient_id}"
        _confirm_key = f"triage_confirm_{patient_id}"

        if st.session_state.get(_triage_key) in ("URGENT", "MODERATE"):
            triage_level = st.session_state[_triage_key]
            symptom_text = st.session_state.get(_triage_msg_key, "Symptoms reported via chat")

            if triage_level == "URGENT":
                btn_label = "🚨 Alert My Doctor Now"
                btn_type = "primary"
                confirm_msg = "🚨 This will immediately notify your doctor. Confirm?"
            else:
                btn_label = "📅 Book Urgent Appointment"
                btn_type = "secondary"
                confirm_msg = "📅 This will create an urgent alert for your doctor. Confirm?"

            if not st.session_state.get(_confirm_key):
                if st.button(btn_label, type=btn_type, key=f"triage_btn_{patient_id}"):
                    st.session_state[_confirm_key] = True
                    st.rerun()
            else:
                st.warning(confirm_msg)
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Yes, send alert", key=f"triage_yes_{patient_id}"):
                        severity = "high" if triage_level == "URGENT" else "medium"
                        alert_message = (
                            f"[Agentic AI — Patient Reported Symptoms]\n"
                            f"Patient described: \"{symptom_text}\"\n"
                            f"AI Triage Verdict: {triage_level}\n"
                            + ("⚠️ Patient requires IMMEDIATE attention." if triage_level == "URGENT"
                               else "📅 Patient requests a follow-up appointment.")
                        )
                        _pt = get_patient(patient_id)
                        _doctor_id = _pt.get("doctor_id") if _pt else None
                        create_alert(
                            patient_id=patient_id,
                            alert_type="patient_reported_symptoms",
                            message=alert_message,
                            severity=severity,
                            doctor_id=_doctor_id
                        )
                        st.session_state.pop(_triage_key, None)
                        st.session_state.pop(_triage_msg_key, None)
                        st.session_state.pop(_confirm_key, None)
                        st.success("✅ Your doctor has been notified!" if triage_level == "URGENT"
                                   else "✅ Alert sent to your doctor!")
                        st.rerun()
                with col_no:
                    if st.button("❌ Cancel", key=f"triage_no_{patient_id}"):
                        st.session_state.pop(_triage_key, None)
                        st.session_state.pop(_triage_msg_key, None)
                        st.session_state.pop(_confirm_key, None)
                        st.rerun()

        # ── Action result display (non-triage confirmations) ──────────────
        _action_result_key = f"action_result_{patient_id}"
        if st.session_state.get(_action_result_key):
            ar = st.session_state[_action_result_key]
            action = ar.get("action", "")
            confirmed = ar.get("confirmed", False)
            success = ar.get("success", False)

            if confirmed and success:
                if action == "book_appointment":
                    bd = ar.get("booking_details", {})
                    st.success(f"✅ Appointment booked with Dr. {bd.get('doctor', '')} on {bd.get('date', '')} at {bd.get('time', '')}")
                elif action == "cancel_appointment":
                    st.success("✅ Appointment successfully cancelled.")

            st.session_state.pop(_action_result_key, None)

        # ── Chat input ────────────────────────────────────────────────────
        placeholder = (
            "e.g. 'Book appointment with Dr. Sharma on 15 April at 10am' "
            "or 'Show my prescriptions' or 'I have chest pain'..."
        )
        if prompt := st.chat_input(placeholder):
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("🤖 Analysing and acting..."):
                    result = orchestrator.on_patient_message(
                        patient_id, prompt,
                        use_agentic=True,
                        session_state=st.session_state
                    )

                if not isinstance(result, dict):
                    result = {"reply": str(result), "triage": None, "action": "general_health"}

                reply = result.get("reply", "")
                triage = result.get("triage")
                action = result.get("action", "")
                confirmed = result.get("confirmed", False)
                success = result.get("success", False)

                # ── Show triage badge ──────────────────────────────────
                if triage == "URGENT":
                    st.error("🔴 **URGENT — Please seek medical attention immediately.**")
                elif triage == "MODERATE":
                    st.warning("🟡 **MODERATE — Consult your doctor within 1–2 days.**")
                elif triage == "MILD":
                    st.success("🟢 **MILD — Manageable at home for now.**")

                # ── Show action confirmation badge ────────────────────
                if confirmed and success:
                    if action == "book_appointment":
                        bd = result.get("booking_details", {})
                        st.success(
                            f"✅ **Appointment Booked!** Dr. {bd.get('doctor', '')} · "
                            f"{bd.get('date', '')} · {bd.get('time', '')}"
                        )
                    elif action == "cancel_appointment":
                        st.success("✅ **Appointment Cancelled Successfully**")

                st.markdown(reply)

            # ── Post-response state management ────────────────────────
            if triage in ("URGENT", "MODERATE"):
                st.session_state[_triage_key] = triage
                st.session_state[_triage_msg_key] = prompt
                st.session_state.pop(_confirm_key, None)
            else:
                st.session_state.pop(_triage_key, None)
                st.session_state.pop(_triage_msg_key, None)
                st.session_state.pop(_confirm_key, None)

            _cached_chat_history.clear()
            st.rerun()

    # ── Tab 1: Schedule ───────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 📅 Medication Schedule")
        col1, col2 = st.columns([3, 1])

        with col2:
            access_token = _get_valid_access_token()

            if access_token:
                # Token available — show sync button
                if st.button("📆 Sync to Google Calendar"):
                    with st.spinner("Syncing to calendar..."):
                        result = scheduler.schedule_for_patient(patient_id, access_token)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.warning(result.get("message", "Sync failed."))
                        if result.get("errors"):
                            for e in result["errors"]:
                                st.caption(f"⚠ {e}")
                if st.button("🔌 Disconnect Calendar", type="secondary", use_container_width=True):
                    st.session_state.pop("google_access_token", None)
                    st.session_state.pop("google_refresh_token", None)
                    st.rerun()
            else:
                # No access token in session (e.g. user disconnected or session expired).
                # Offer a reconnect via the same Google OAuth flow — same URL used at login.
                st.markdown("""
                <div style="background:rgba(167,139,250,0.08);border:1px solid #A78BFA;
                             border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.8rem;">
                    <div style="color:#A78BFA;font-weight:600;font-size:0.9rem;margin-bottom:0.3rem;">
                        📅 Google Calendar Disconnected
                    </div>
                    <div style="color:#A89FC8;font-size:0.82rem;">
                        Your Google session token has expired. Click below to reconnect —
                        this uses the same Google account you signed in with.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                try:
                    auth_url = get_auth_url()
                    st.markdown(f"""
                    <a href="{auth_url}" target="_self" style="text-decoration:none;">
                        <div style="
                            display:flex;align-items:center;justify-content:center;gap:0.6rem;
                            background:#fff;color:#3c4043;border:1px solid #dadce0;
                            border-radius:8px;padding:0.6rem 1rem;font-size:0.88rem;
                            font-weight:500;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,0.15);">
                            <svg width="16" height="16" viewBox="0 0 18 18">
                                <path fill="#4285F4" d="M16.51 8H8.98v3h4.3c-.18 1-.74 1.48-1.6 2.04v2.01h2.6a7.8 7.8 0 002.38-5.88c0-.57-.05-.66-.15-1.18z"/>
                                <path fill="#34A853" d="M8.98 17c2.16 0 3.97-.72 5.3-1.94l-2.6-2a4.8 4.8 0 01-7.18-2.54H1.83v2.07A8 8 0 008.98 17z"/>
                                <path fill="#FBBC05" d="M4.5 10.52a4.8 4.8 0 010-3.04V5.41H1.83a8 8 0 000 7.18l2.67-2.07z"/>
                                <path fill="#EA4335" d="M8.98 4.18c1.17 0 2.23.4 3.06 1.2l2.3-2.3A8 8 0 001.83 5.4L4.5 7.49a4.77 4.77 0 014.48-3.31z"/>
                            </svg>
                            Reconnect Google Calendar
                        </div>
                    </a>
                    """, unsafe_allow_html=True)
                except Exception:
                    st.info("Google Calendar integration not configured. Ask your administrator.")

        schedule = scheduler.get_schedule_preview(patient_id)
        if not schedule:
            st.info("No schedule available. Ask your doctor to create a prescription.")
        else:
            current_date = None
            for item in schedule:
                if item["date"] != current_date:
                    current_date = item["date"]
                    st.markdown(f"**📅 {current_date}**")
                st.markdown(f"""
                <div class="schedule-item">
                    <span style="color: var(--accent); font-family: 'DM Mono';">🕐 {item['time']}</span>
                    <span style="font-weight: 600;">💊 {item['medicine']}</span>
                    <span style="color: var(--text-secondary);">{item['dosage']}</span>
                    <span style="color: var(--text-muted); font-size: 0.85rem;">{item['timing']}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Tab 2: Prescriptions ──────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("### 💊 My Prescriptions")
        prescriptions = _cached_prescriptions(patient_id)
        if not prescriptions:
            st.info("No prescriptions assigned yet. Please consult your doctor.")
        else:
            for i, pr in enumerate(prescriptions):
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">Prescription {i+1} — {pr['created_at'][:10]}</div>
                """, unsafe_allow_html=True)
                for m in pr.get("medicines", []):
                    st.markdown(f"""
                    <div class="medicine-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 1.1rem;">💊 {m['name']}</strong>
                            <code style="background: var(--primary-glow); padding: 0.2rem 0.6rem; border-radius: 6px;">{m['dosage']}</code>
                        </div>
                        <div style="color: var(--text-secondary); margin-top: 0.4rem; font-size: 0.9rem;">
                            ⏱ {m['timing']} &nbsp;|&nbsp; 📆 {m['duration_days']} days
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                if pr.get("doctor_notes"):
                    st.markdown(
                        f'<p style="color: var(--text-secondary); margin-top: 0.8rem;">📝 **Doctor\'s Notes:** {pr["doctor_notes"]}</p>',
                        unsafe_allow_html=True
                    )
                st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3: Daily Health Check & Summary (unified) ─────────────────────────
    with tabs[3]:
        today_str = date.today().isoformat()
        st.markdown(f"### 🩺 Daily Health Check — {date.today().strftime('%A, %d %B %Y')}")

        existing_response = _cached_mcq_response_today(patient_id, today_str)
        _mcq_show_form = True  # controls whether to show the question form

        if existing_response:
            _render_mcq_result(existing_response, show_history=True, patient_id=patient_id, mcq_agent=mcq_agent)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            if st.button("🔄 Retake Today's Check-in", type="secondary"):
                st.session_state["retake_mcq"] = True
                st.session_state["show_health_summary"] = False
                # Clear cached questions so fresh ones load
                st.session_state.pop(f"mcq_questions_{patient_id}_{today_str}", None)
                st.rerun()
            if not st.session_state.get("retake_mcq"):
                _mcq_show_form = False

        if _mcq_show_form:
            prescriptions = _cached_prescriptions(patient_id)
            if not prescriptions:
                st.info("⚕️ No prescription found. Your doctor needs to assign a prescription before you can complete the daily check-in.")
                _mcq_show_form = False

        if _mcq_show_form:
            # Cache questions per patient per day — no need to call GROQ on every rerun
            _q_key = f"mcq_questions_{patient_id}_{today_str}"
            if _q_key not in st.session_state:
                with st.spinner("Loading your personalized health questions..."):
                    st.session_state[_q_key] = mcq_agent.generate_mcqs(patient_id, today_str)
            questions = st.session_state[_q_key]

            if not questions:
                st.error("Could not generate questions. Please try again.")
                _mcq_show_form = False

        if _mcq_show_form:
            st.markdown("""
            <div class="card" style="margin-bottom: 1.5rem;">
                <div class="card-header">📋 Today's Health Questions</div>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">
                    Answer honestly based on how you feel today. This helps your doctor monitor your progress.
                </p>
            </div>
            """, unsafe_allow_html=True)

            selected_options = {}

            for q in questions:
                qid = str(q["id"])
                category_icons = {
                    "symptom": "🤒",
                    "adherence": "💊",
                    "side_effect": "⚠️",
                    "wellbeing": "💚"
                }
                icon = category_icons.get(q.get("category", ""), "❓")

                st.markdown(f"""
                <div class="card" style="margin-bottom: 1rem;">
                    <div style="font-size: 0.75rem; color: #7C3AED; text-transform: uppercase;
                        letter-spacing: 0.08em; margin-bottom: 0.4rem;">
                        {icon} {q.get('category', '').replace('_', ' ').title()}
                    </div>
                    <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.8rem; color: var(--text-primary);">
                        {q['question']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                option_labels = [opt["text"] for opt in q["options"]]
                choice = st.radio(
                    label=q["question"],
                    options=range(len(option_labels)),
                    format_func=lambda i, opts=option_labels: opts[i],
                    key=f"mcq_{qid}",
                    label_visibility="collapsed"
                )
                selected_options[qid] = choice
                st.markdown("---")

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                if st.button("✅ Submit Daily Health Check", type="primary", use_container_width=True):
                    total_score = 0
                    for q in questions:
                        qid = str(q["id"])
                        idx = selected_options.get(qid, 0)
                        try:
                            total_score += q["options"][idx]["score"]
                        except (IndexError, KeyError):
                            pass

                    status = mcq_agent.compute_status(total_score)
                    symptoms, adherence_status, side_effects = mcq_agent.extract_response_details(questions, selected_options)

                    responses_data = []
                    for q in questions:
                        qid = str(q["id"])
                        idx = selected_options.get(qid, 0)
                        responses_data.append({
                            "question": q["question"],
                            "category": q.get("category"),
                            "selected": q["options"][idx]["text"] if idx < len(q["options"]) else "",
                            "score": q["options"][idx]["score"] if idx < len(q["options"]) else 0,
                            "tag": q["options"][idx].get("tag", "") if idx < len(q["options"]) else ""
                        })

                    doctor_id = patient.get("doctor_id")
                    save_mcq_response(
                        patient_id=patient_id,
                        doctor_id=doctor_id,
                        date_str=today_str,
                        responses_json=json.dumps(responses_data),
                        total_score=total_score,
                        status=status,
                        side_effects=json.dumps(side_effects),
                        adherence_status=adherence_status
                    )

                    _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score,
                                           symptoms, adherence_status, side_effects)

                    st.session_state["retake_mcq"] = False
                    st.session_state["show_health_summary"] = True
                    # Invalidate cached data so next render is fresh
                    _cached_patient_login.clear()
                    _cached_mcq_response_today.clear()
                    _cached_mcq_responses.clear()
                    st.session_state.pop(f"health_data_{patient_id}", None)
                    st.rerun()

        # ── Inline Health Summary — shown after MCQ completion ────────────────
        # Show automatically after submission OR when today's response already exists
        _show_summary = st.session_state.get("show_health_summary", False) or (existing_response and not st.session_state.get("retake_mcq"))
        if _show_summary:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown("### 📊 Your Health Summary")

            # ── AI Health Report ──────────────────────────────────────────────
            col_ai1, col_ai2 = st.columns([4, 1])
            with col_ai2:
                _gen_report = st.button("🔄 Refresh Report", use_container_width=True)
            if _gen_report or st.session_state.get("show_health_summary"):
                # Cache summary per patient per day - expensive GROQ call
                _sum_key = f"health_summary_{patient_id}_{today_str}"
                if _gen_report or _sum_key not in st.session_state:
                    with st.spinner("AI is analyzing your health data..."):
                        st.session_state[_sum_key] = orchestrator.health.generate_health_summary(patient_id)
                summary = st.session_state[_sum_key]
                st.markdown(f"""
                <div class="card">
                    <div class="card-header">🤖 AI Clinical Assessment</div>
                    <p style="line-height: 1.7;">{summary}</p>
                </div>
                """, unsafe_allow_html=True)

            # ── Health Indicators ─────────────────────────────────────────────
            risk_colors = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}
            risk_color = risk_colors.get(risk_level, "#A78BFA")
            st.markdown(f"""
            <div class="card">
                <div class="card-header">Health Indicators</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem;">
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">RISK LEVEL</div>
                        <span class="risk-badge risk-{risk_level}">{risk_level.upper()}</span>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">BEHAVIORAL TREND</div>
                        <span style="color: {'#34D399' if trends.get('trend') == 'improving' else '#F87171' if trends.get('trend') == 'worsening' else '#A78BFA'}; font-weight: 600;">{trends.get('trend', 'stable').upper()}</span>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">ACTIVE MEDICATIONS</div>
                        <span style="color: var(--primary-light); font-weight: 700; font-size: 1.2rem;">{adherence.get('active_medications', 0)}</span>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-bottom: 0.3rem;">CONDITION</div>
                        <span style="color: var(--text-primary);">{patient['disease']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Health Trend Chart ────────────────────────────────────────────
            responses = _cached_mcq_responses(patient_id, limit=30)
            if responses:
                st.markdown("#### 📈 Health Trend — Score Over Time")

                import pandas as pd
                import plotly.graph_objects as go

                chart_responses = list(reversed(responses))
                dates  = [r["date"] for r in chart_responses]
                scores = [r["total_score"] for r in chart_responses]
                statuses = [r["status"] for r in chart_responses]

                status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
                marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

                fig = go.Figure()
                fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.15)", line_width=1)
                fig.add_trace(go.Scatter(
                    x=dates, y=[max(s, 0) for s in scores],
                    fill="tozeroy", fillcolor="rgba(52,211,153,0.12)",
                    line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
                ))
                fig.add_trace(go.Scatter(
                    x=dates, y=[min(s, 0) for s in scores],
                    fill="tozeroy", fillcolor="rgba(248,113,113,0.12)",
                    line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
                ))
                fig.add_trace(go.Scatter(
                    x=dates, y=scores,
                    mode="lines+markers",
                    line=dict(color="#A78BFA", width=2.5, shape="spline", smoothing=0.6),
                    marker=dict(size=10, color=marker_colors,
                                line=dict(color="#1a1a2e", width=2)),
                    name="Health Score",
                    hovertemplate="<b>%{x}</b><br>Score: %{y:+d}<br><extra></extra>"
                ))

                status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
                for d, s, st_ in zip(dates, scores, statuses):
                    fig.add_annotation(
                        x=d, y=s,
                        text=status_icons_map.get(st_, ""),
                        showarrow=False,
                        yshift=18, font=dict(size=13)
                    )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#A89FC8", size=12),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    xaxis=dict(
                        showgrid=False, zeroline=False,
                        tickfont=dict(size=11, color="#6B6080"),
                        title=""
                    ),
                    yaxis=dict(
                        showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                        zeroline=True, zerolinecolor="rgba(255,255,255,0.2)",
                        tickfont=dict(size=11, color="#6B6080"),
                        title="Score"
                    ),
                    hoverlabel=dict(
                        bgcolor="#1E1B4B", bordercolor="#A78BFA",
                        font=dict(color="white", size=13)
                    ),
                    showlegend=False
                )

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                st.markdown("""
                <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
                    <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
                    <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
                    <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
                    <span style="color:#6B6080;font-size:0.82rem;">🟢 Green zone = positive score &nbsp; 🔴 Red zone = negative score</span>
                </div>
                """, unsafe_allow_html=True)

                # ── Recent Check-in History ───────────────────────────────────
                st.markdown("#### 📋 Recent Daily Check-in History")
                for r in responses:
                    status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
                    status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
                    color = status_colors.get(r["status"], "#A78BFA")
                    icon = status_icons.get(r["status"], "•")
                    st.markdown(f"""
                    <div class="card" style="padding: 0.8rem 1rem; margin-bottom: 0.5rem; border-left: 3px solid {color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: var(--text-muted); font-size: 0.85rem;">📅 {r['date']}</span>
                            <span style="color: {color}; font-weight: 700;">{icon} {r['status']}</span>
                            <span style="color: var(--text-secondary); font-size: 0.85rem;">Score: {r['total_score']:+d}</span>
                        </div>
                        <div style="color: var(--text-muted); font-size: 0.8rem; margin-top: 0.3rem;">
                            Adherence: {r.get('adherence_status', 'N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Tab 4: Alerts & Notifications ─────────────────────────────────────────
    with tabs[4]:
        _render_patient_alerts(patient_id, patient, risk_level, risk)

    # ── Tab 5: Online OPD ─────────────────────────────────────────────────────
    with tabs[5]:
        _render_patient_opd(patient_id, patient)

    # ── Tab 6: Consultation Summaries ─────────────────────────────────────────
    with tabs[6]:
        _render_consultation_summaries_tab(patient_id)

    # ── Tab 7: Health Command Center (Autonomous AI Agent) ────────────────────
    with tabs[7]:
        _render_health_command_center(patient_id, patient, risk, adherence, trends)


def _render_consultation_summaries_tab(patient_id: str):
    """Dedicated tab listing all saved post-call consultation summaries."""
    from data.database import get_patient_meet_summaries_enriched
    from core.meet_summary import render_summaries_list

    st.markdown("### 📋 My Consultation Summaries")
    st.markdown(
        '<p style="color:var(--text-secondary);">Records from your Online OPD video consultations. '
        'Each summary includes what was discussed, medicines recommended, and the doctor\'s conclusion.</p>',
        unsafe_allow_html=True
    )
    summaries = get_patient_meet_summaries_enriched(patient_id)
    render_summaries_list(summaries, role="patient")


# ── Alerts tab renderer ───────────────────────────────────────────────────────

def _render_patient_alerts(patient_id, patient, risk_level, risk):
    """Render the patient-facing Alerts & Notifications tab."""
    st.markdown("### 🔔 Alerts & Notifications")
    st.markdown(
        '<p style="color:var(--text-secondary);">Important health warnings, missed dose reminders, '
        'and doctor messages are shown here.</p>',
        unsafe_allow_html=True
    )

    # ── High-Risk Banner ──────────────────────────────────────────────────────
    if risk_level == "high":
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #F87171;background:rgba(248,113,113,0.08);">
            <div style="display:flex;align-items:center;gap:0.8rem;">
                <span style="font-size:1.8rem;">🚨</span>
                <div>
                    <div style="font-weight:700;color:#F87171;font-size:1.05rem;">High Risk Warning</div>
                    <div style="color:var(--text-secondary);font-size:0.9rem;">
                        Your current risk score is <strong style="color:#F87171;">{risk.get('score', 0)}/100</strong>.
                        Please contact your doctor or visit the clinic immediately.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Missed Dose Check (from recent MCQ adherence) ─────────────────────────
    recent_responses = _cached_mcq_responses(patient_id, limit=7)
    missed_dose_dates = []
    for r in recent_responses:
        adh = (r.get("adherence_status") or "").lower()
        if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
            missed_dose_dates.append(r["date"])

    if missed_dose_dates:
        dates_str = ", ".join(missed_dose_dates[:3])
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #FBBF24;background:rgba(251,191,36,0.07);margin-top:0.8rem;">
            <div style="display:flex;align-items:center;gap:0.8rem;">
                <span style="font-size:1.8rem;">💊</span>
                <div>
                    <div style="font-weight:700;color:#FBBF24;font-size:1rem;">Missed Doses Detected</div>
                    <div style="color:var(--text-secondary);font-size:0.85rem;">
                        Your check-in responses suggest missed medications on: <strong>{dates_str}</strong>.
                        Consistent adherence is key to recovery — please take medications as prescribed.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── DB Alerts ─────────────────────────────────────────────────────────────
    all_alerts = _cached_patient_alerts(patient_id)
    unresolved = [a for a in all_alerts if not a["resolved"]]
    resolved = [a for a in all_alerts if a["resolved"]]

    if not all_alerts and not missed_dose_dates and risk_level != "high":
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
            <div style="font-weight:600;color:#34D399;">All Clear</div>
            <div style="color:var(--text-muted);font-size:0.9rem;margin-top:0.3rem;">
                No active alerts. Keep taking your medications and completing daily check-ins!
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    severity_config = {
        "high":   {"color": "#F87171", "icon": "🚨", "label": "High"},
        "medium": {"color": "#FBBF24", "icon": "⚠️", "label": "Medium"},
        "low":    {"color": "#34D399",  "icon": "ℹ️", "label": "Low"},
    }
    type_labels = {
        "mcq_health_check": "Health Check Alert",
        "doctor_message":   "Doctor Message",
        "missed_dose":      "Missed Dose",
        "high_risk":        "High Risk Warning",
    }

    if unresolved:
        st.markdown(f"#### 🔴 Active Alerts ({len(unresolved)})")
        for alert in unresolved:
            cfg = severity_config.get(alert["severity"], severity_config["medium"])
            type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
            created = alert["created_at"][:16].replace("T", " ")

            with st.expander(f"{cfg['icon']} {type_name} — {created}", expanded=False):
                st.markdown(f"""
                <div style="background:rgba(0,0,0,0.15);border-radius:8px;padding:0.8rem;
                             border-left:3px solid {cfg['color']};">
                    <pre style="font-size:0.82rem;color:var(--text-secondary);
                                white-space:pre-wrap;word-break:break-word;margin:0;">
{alert['message']}</pre>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"✅ Mark Resolved", key=f"resolve_{alert['id']}"):
                    resolve_alert(alert["id"])
                    _cached_patient_alerts.clear()
                    st.rerun()

    if resolved:
        with st.expander(f"📁 Resolved Alerts ({len(resolved)})", expanded=False):
            for alert in resolved:
                cfg = severity_config.get(alert["severity"], severity_config["medium"])
                type_name = type_labels.get(alert["alert_type"], alert["alert_type"].replace("_", " ").title())
                created = alert["created_at"][:16].replace("T", " ")
                st.markdown(f"""
                <div class="card" style="padding:0.6rem 1rem;margin-bottom:0.4rem;opacity:0.6;">
                    <div style="display:flex;justify-content:space-between;">
                        <span style="font-size:0.85rem;color:var(--text-muted);">{cfg['icon']} {type_name}</span>
                        <span style="font-size:0.8rem;color:var(--text-muted);">{created}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ── MCQ result card ───────────────────────────────────────────────────────────

def _render_mcq_result(response, show_history=False, patient_id=None, mcq_agent=None):
    status = response["status"]
    score = response["total_score"]
    status_colors = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
    status_icons = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
    color = status_colors.get(status, "#A78BFA")
    icon = status_icons.get(status, "•")

    feedback = mcq_agent.get_feedback(status) if mcq_agent else {}

    # Safely escape feedback strings to prevent HTML injection
    action_text = str(feedback.get('action', '')).replace('<', '&lt;').replace('>', '&gt;')
    message_text = str(feedback.get('message', '')).replace('<', '&lt;').replace('>', '&gt;')

    st.markdown(f"""
    <div class="card" style="border-left: 4px solid {color}; padding: 1.5rem;">
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 3.5rem; margin-bottom: 0.6rem; line-height:1;">{icon}</div>
            <div style="font-size: 2rem; font-weight: 800; color: {color}; margin-bottom: 0.3rem; letter-spacing:-0.02em;">{status}</div>
            <div style="color: var(--text-muted); font-size: 1rem;">Today's Health Status</div>
        </div>
        <div style="background: var(--bg-card); border-radius: 8px; padding: 1.2rem 1.5rem; margin-top: 1rem; text-align: center;">
            <div style="color: var(--text-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem;">Recommended Action</div>
            <div style="font-weight: 700; color: {color}; font-size: 1.15rem; margin-bottom: 0.4rem;">{action_text}</div>
            <div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.5;">{message_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    adherence_status = response.get("adherence_status", "")
    side_effects_raw = response.get("side_effects", "[]")
    try:
        side_effects = json.loads(side_effects_raw)
    except Exception:
        side_effects = []

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="card" style="margin-top: 0;">
            <div class="card-header">💊 Medication Adherence</div>
            <div style="font-weight: 600; color: var(--primary-light);">{adherence_status or 'Not recorded'}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        effects_text = ", ".join(side_effects) if side_effects else "None reported"
        st.markdown(f"""
        <div class="card" style="margin-top: 0;">
            <div class="card-header">⚠️ Side Effects</div>
            <div style="font-weight: 600; color: {'#F87171' if side_effects else '#34D399'};">{effects_text}</div>
        </div>
        """, unsafe_allow_html=True)

    if show_history and patient_id:
        st.markdown(
            f'<p style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">✓ Submitted for {response["date"]}</p>',
            unsafe_allow_html=True
        )


# ── Alert firing logic ────────────────────────────────────────────────────────

def _check_and_fire_alerts(patient_id, doctor_id, patient, status, total_score, symptoms, adherence_status, side_effects):
    """Fire structured doctor alerts based on MCQ response."""
    trigger = False
    reasons = []

    if total_score < 0:
        trigger = True
        reasons.append("negative_score")

    if check_consecutive_worsening(patient_id, 2):
        trigger = True
        reasons.append("consecutive_worsening")

    if side_effects:
        trigger = True
        reasons.append("side_effects")

    if not trigger:
        return

    action_map = {
        "Improving": "Continue medication as prescribed",
        "Stable": "Monitor closely, follow up in 2-3 days",
        "Worsening": "Immediate consultation required"
    }

    symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- No specific symptoms flagged"
    side_effects_text = "\n".join([f"- {e}" for e in side_effects]) if side_effects else "- None"
    adherence_text = f"- {adherence_status}" if adherence_status else "- Not recorded"
    reasons_text = ", ".join(r.replace("_", " ").title() for r in reasons)

    alert_message = f"""Patient ID: {patient_id}
Doctor ID: {doctor_id}
Disease: {patient.get('disease', 'N/A')}
Current Status: {status}
Score: {total_score:+d}

Key Symptoms Reported:
{symptoms_text}

Medication Adherence:
{adherence_text}

Side Effects:
{side_effects_text}

Recommended Action:
- {action_map.get(status, 'Monitor patient')}

Triggered By: {reasons_text}"""

    severity = "high" if "consecutive_worsening" in reasons or total_score <= -3 else "medium"

    create_alert(
        patient_id=patient_id,
        alert_type="mcq_health_check",
        message=alert_message,
        severity=severity,
        doctor_id=doctor_id
    )




# ── Online OPD booking tab ────────────────────────────────────────────────────

def _render_patient_opd(patient_id: str, patient: dict):
    """Full Online OPD booking UI for the patient dashboard."""
    # Note: st, date, datetime already imported at module level

    st.markdown("### 🖥️ Online OPD — Book a Consultation")
    st.markdown(
        '<p style="color:#94a3b8;">Book a 17-minute online consultation slot with your doctor. '
        'Slots are real-time — once booked they disappear for other patients.</p>',
        unsafe_allow_html=True
    )

    opd_subtabs = st.tabs(["📅 Book a Slot", "🗓️ My Bookings"])

    # ── Sub-tab A: Book ───────────────────────────────────────────────────────
    with opd_subtabs[0]:
        doctors = _cached_opd_doctors()

        if not doctors:
            st.info("No doctors have published OPD slots yet. Please check back later.")
        else:
            doctor_options = {f"Dr. {d['name']} ({d['specialization']})": d['doctor_id'] for d in doctors}
            selected_label = st.selectbox("Select Doctor", list(doctor_options.keys()), key="opd_doc_sel")
            selected_doctor_id = doctor_options[selected_label]

            available_dates = _cached_opd_dates(selected_doctor_id)
            if not available_dates:
                st.warning("This doctor has no available slots right now.")
            else:
                date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %b %Y") for d in available_dates}
                chosen_date_str = st.selectbox(
                    "Select Date",
                    list(date_labels.keys()),
                    format_func=lambda x: date_labels[x],
                    key="opd_date_sel"
                )

                # Check if patient already booked on this day with this doctor
                already_booked = _cached_has_booking(patient_id, selected_doctor_id, chosen_date_str)
                if already_booked:
                    st.warning("⚠️ You already have a booking with this doctor on this date. Check 'My Bookings' tab.")
                else:
                    free_slots = _cached_opd_slots(selected_doctor_id, chosen_date_str)

                    if not free_slots:
                        st.error("All slots for this date are fully booked. Please choose another date.")
                    else:
                        st.markdown(f"""
                        <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:12px;padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
                            <div style="display:flex;gap:2rem;flex-wrap:wrap;align-items:center;">
                                <div>
                                    <span style="color:#64748b;font-size:0.75rem;">AVAILABLE SLOTS</span><br>
                                    <strong style="color:#34D399;font-size:1.4rem;">{len(free_slots)}</strong>
                                </div>
                                <div>
                                    <span style="color:#64748b;font-size:0.75rem;">SLOT DURATION</span><br>
                                    <strong style="color:#A78BFA;">17 minutes</strong>
                                </div>
                                <div>
                                    <span style="color:#64748b;font-size:0.75rem;">EARLIEST SLOT</span><br>
                                    <strong style="color:#A78BFA;">{free_slots[0]['start_time']}</strong>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        slot_options = {
                            f"{s['start_time']} – {s['end_time']}": s['id']
                            for s in free_slots
                        }
                        chosen_slot_label = st.selectbox(
                            "Choose a time slot",
                            list(slot_options.keys()),
                            key="opd_slot_sel"
                        )
                        chosen_slot_id = slot_options[chosen_slot_label]

                        st.markdown(f"""
                        <div style="background:#1a1a2e;border:1px solid #7C3AED;border-left:3px solid #A78BFA;border-radius:12px;padding:0.8rem 1.2rem;margin-bottom:0.8rem;">
                            <div style="font-weight:600;color:#A78BFA;margin-bottom:0.3rem;">📋 Booking Summary</div>
                            <div style="color:#94a3b8;font-size:0.9rem;">
                                <strong style="color:#e2e8f0;">Doctor:</strong> {selected_label}<br>
                                <strong style="color:#e2e8f0;">Date:</strong> {date_labels[chosen_date_str]}<br>
                                <strong style="color:#e2e8f0;">Time:</strong> {chosen_slot_label}<br>
                                <strong style="color:#e2e8f0;">Patient:</strong> {patient['name']} &nbsp;<code style="background:#2d2d44;padding:2px 6px;border-radius:4px;font-size:0.8rem;">{patient_id}</code>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="opd_confirm"):
                            success = book_opd_slot(chosen_slot_id, patient_id, patient['name'])
                            if success:
                                st.success(f"🎉 Slot booked! {chosen_slot_label} on {date_labels[chosen_date_str]}")
                                st.balloons()
                                _cached_opd_bookings.clear()
                                _cached_opd_slots.clear()
                                _cached_has_booking.clear()
                                st.rerun()
                            else:
                                st.error("❌ This slot was just booked by someone else. Please select another slot.")
                                _cached_opd_slots.clear()
                                st.rerun()

    # ── Sub-tab B: My Bookings ────────────────────────────────────────────────
    with opd_subtabs[1]:
        st.markdown("#### 🗓️ Your OPD Bookings")
        my_bookings = _cached_opd_bookings(patient_id)

        if not my_bookings:
            st.markdown("""
            <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:16px;text-align:center;padding:2rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">📭</div>
                <div style="color:#64748b;">No OPD bookings yet. Go to 'Book a Slot' to schedule a consultation.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            today_str = date.today().isoformat()
            upcoming = [b for b in my_bookings if b["slot_date"] >= today_str]
            past = [b for b in my_bookings if b["slot_date"] < today_str]

            if upcoming:
                st.markdown("##### 📅 Upcoming")
                for booking in upcoming:
                    visited = bool(booking["patient_visited"])
                    color = "#34D399" if visited else "#A78BFA"
                    status = "✅ Consulted" if visited else "⏳ Pending"
                    slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")

                    safe_room = booking["id"].replace("-", "").replace(" ", "")
                    room_name = f"MediCore-{safe_room}"

                    col_b, col_c = st.columns([4, 1])
                    with col_b:
                        st.markdown(f"""
                        <div style="background:#1a1a2e;border:1px solid #2d2d44;border-left:3px solid {color};border-radius:12px;padding:0.8rem 1.2rem;margin-bottom:0.4rem;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div>
                                    <div style="font-weight:600;color:{color};">Dr. {booking['doctor_name']}</div>
                                    <div style="color:#94a3b8;font-size:0.85rem;">{booking['specialization']}</div>
                                    <div style="color:#64748b;font-size:0.8rem;margin-top:0.3rem;">
                                        📅 {slot_date_fmt} &nbsp;|&nbsp; ⏰ {booking['start_time']} – {booking['end_time']}
                                    </div>
                                </div>
                                <div style="font-size:0.85rem;color:{color};font-weight:600;">{status}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_c:
                        if not visited:
                            if st.button("❌ Cancel", key=f"cancel_{booking['id']}", use_container_width=True):
                                success = cancel_opd_booking(booking["id"], patient_id)
                                if success:
                                    st.success("Booking cancelled.")
                                    _cached_opd_bookings.clear()
                                    _cached_opd_slots.clear()
                                    _cached_has_booking.clear()
                                    st.rerun()

                    # ── Embedded video call (Jitsi) ───────────────────────────
                    if not visited:
                        call_key = f"show_call_pat_{booking['id']}"
                        if st.button("🎥 Join Video Call", key=f"btn_call_pat_{booking['id']}",
                                     use_container_width=True, type="primary"):
                            st.session_state[call_key] = not st.session_state.get(call_key, False)

                        if st.session_state.get(call_key, False):
                            # Use patient dict name (already available in scope) for display
                            patient_display = patient.get("name", patient_id) if isinstance(patient, dict) else str(patient_id)
                            with st.container():
                                render_meeting(
                                    room_name=room_name,
                                    display_name=patient_display,
                                    sender_label=patient_display,
                                    role="patient"
                                )
                                from core.meet_ui import render_consultation_summary_section
                                render_consultation_summary_section(
                                    room_name=room_name,
                                    slot_id=booking["id"],
                                    doctor_id=booking.get("doctor_id", ""),
                                    patient_id=str(patient_id),
                                    role="patient"
                                )

            if past:
                with st.expander(f"📁 Past Bookings ({len(past)})", expanded=False):
                    for booking in past:
                        visited = bool(booking["patient_visited"])
                        slot_date_fmt = datetime.strptime(booking["slot_date"], "%Y-%m-%d").strftime("%d %b %Y")
                        status = "✅ Consulted" if visited else "❌ Not attended"
                        color = "#34D399" if visited else "#F87171"
                        st.markdown(f"""
                        <div style="background:#1a1a2e;border:1px solid #2d2d44;border-radius:10px;padding:0.6rem 1rem;margin-bottom:0.3rem;opacity:0.75;">
                            <div style="display:flex;justify-content:space-between;">
                                <span style="font-size:0.85rem;color:#e2e8f0;">Dr. {booking['doctor_name']} — {slot_date_fmt} {booking['start_time']}</span>
                                <span style="font-size:0.8rem;color:{color};">{status}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        # Show consultation summary if available
                        from data.database import get_meet_summary
                        from core.meet_summary import render_summary_card
                        import json as _json
                        saved = get_meet_summary(booking["id"])
                        if saved:
                            with st.expander(f"🧠 View Consultation Summary — {slot_date_fmt}", expanded=False):
                                try:
                                    render_summary_card(_json.loads(saved["summary_json"]), saved.get("created_at",""))
                                except Exception:
                                    st.warning("Could not load summary.")

# ── Patient login ─────────────────────────────────────────────────────────────

def render_patient_login():
    st.markdown("""
    <div style="max-width: 480px; margin: 4rem auto;">
        <div class="page-header" style="text-align: center;">
            <h1>🏥 Patient Login</h1>
            <p>Enter your Patient ID to access your health portal</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            patient_id = st.text_input(
                "Patient ID",
                placeholder="e.g. PAT-20260413-0001",
                label_visibility="collapsed"
            )
            st.markdown(
                '<p style="color: var(--text-muted); font-size: 0.8rem; text-align: center;">'
                'Your ID was provided by your doctor at registration</p>',
                unsafe_allow_html=True
            )

            if st.button("Access My Health Portal", type="primary", use_container_width=True):
                if patient_id:
                    patient = get_patient(patient_id.strip().upper())
                    if patient:
                        st.session_state["patient_id"] = patient_id.strip().upper()
                        st.session_state["patient_logged_in"] = True
                        st.rerun()
                    else:
                        st.error("Patient ID not found. Check with your doctor.")
                else:
                    st.warning("Please enter your Patient ID.")


# ══════════════════════════════════════════════════════════════════════════════
# PROACTIVE AI HEALTH AGENT TAB
# ══════════════════════════════════════════════════════════════════════════════

def _build_agent_context(patient_id: str, patient: dict, risk: dict,
                          adherence: dict, trends: dict) -> dict:
    """Gather all live signals needed for the briefing prompt."""
    from data.database import (
        get_mcq_responses, get_mcq_response_for_date,
        check_consecutive_worsening, get_patient_alerts,
        get_patient_opd_bookings, get_patient_prescriptions
    )

    today_str  = date.today().isoformat()
    mcq_rows   = get_mcq_responses(patient_id, limit=10)
    statuses   = [r["status"]      for r in mcq_rows][:5]
    scores     = [r["total_score"] for r in mcq_rows][:5]
    adherence_flags = [r.get("adherence_status", "") for r in mcq_rows[:7]]
    missed_dose = any(
        any(kw in (a or "").lower() for kw in ["miss", "skip", "forgot", "no"])
        for a in adherence_flags
    )
    checkin_done   = get_mcq_response_for_date(patient_id, today_str) is not None
    consec_worsening = check_consecutive_worsening(patient_id, 2)
    alerts         = get_patient_alerts(patient_id)
    unresolved_alerts = len([a for a in alerts if not a["resolved"]])
    bookings       = get_patient_opd_bookings(patient_id)
    upcoming_appt  = None
    for b in bookings:
        if b.get("slot_date", "") >= today_str:
            upcoming_appt = f"{b['slot_date']} at {b.get('start_time','')}"
            break
    prescriptions  = get_patient_prescriptions(patient_id)
    active_meds    = adherence.get("active_medications", 0)

    # Resolve doctor name from patient record (best-effort)
    doctor_name = patient.get("doctor_name") or patient.get("doctor_id", "your doctor")

    hour = datetime.now().hour
    if hour < 12:
        time_of_day = "morning"
    elif hour < 17:
        time_of_day = "afternoon"
    else:
        time_of_day = "evening"

    return {
        "name":              patient.get("name", ""),
        "age":               patient.get("age", ""),
        "disease":           patient.get("disease", ""),
        "doctor_name":       doctor_name,
        "statuses":          statuses,
        "scores":            scores,
        "checkin_done":      checkin_done,
        "consec_worsening":  consec_worsening,
        "missed_dose":       missed_dose,
        "active_meds":       active_meds,
        "risk_level":        risk.get("level", "low"),
        "risk_score":        risk.get("score", 0),
        "upcoming_appt":     upcoming_appt or "None",
        "unresolved_alerts": unresolved_alerts,
        "trend":             trends.get("trend", "stable"),
        "time_of_day":       time_of_day,
        "today":             today_str,
    }


def _call_groq_agent(ctx: dict) -> dict | None:
    """Call Groq with the briefing + cards prompt. Returns parsed JSON or None."""
    from core.config import GROQ_API_KEY, GROQ_MODEL

    if not GROQ_API_KEY:
        return None

    system_prompt = """You are a proactive personal health agent for a medical app called MediCure.

Your job is to analyse a patient's health data and produce:
1. A short personalised briefing (2-3 sentences max)
2. A list of action cards the patient should act on today

Rules for the briefing:
- Address the patient by first name
- Be specific — mention actual trends, medication status, doctor name where relevant
- Be warm but direct — not clinical, not robotic
- Never say "based on your data" or "I have analysed" — just say it naturally
- Never use technical terms like "risk score", "MCQ", "consecutive worsening" — translate to plain language
- If everything is fine, say so clearly and encouragingly

Rules for action cards:
- Only include cards that are genuinely relevant right now — do not pad with generic advice
- Maximum 3 cards
- Each card must have a clear single action the patient can take
- Priority order: urgent health concern > missed medication > pending check-in > upcoming appointment > general wellness
- If nothing needs action, return an empty array

Respond ONLY with valid JSON in exactly this format, no extra text, no markdown fences:
{
  "briefing": "2 to 3 sentences",
  "cards": [
    {
      "priority": "high | medium | low",
      "icon": "single emoji",
      "title": "short title max 6 words",
      "message": "1-2 sentences explaining why this matters right now",
      "action_label": "label for the button max 4 words",
      "action_type": "book_appointment | complete_checkin | view_prescription | dismiss"
    }
  ]
}"""

    user_prompt = f"""Patient name: {ctx['name']}
Age: {ctx['age']}
Condition: {ctx['disease']}
Assigned doctor: Dr. {ctx['doctor_name']}

Last 5 check-in statuses (most recent first): {ctx['statuses']}
Last 5 check-in scores (most recent first): {ctx['scores']}
Today's check-in completed: {ctx['checkin_done']}
Health trending downward for 2+ sessions: {ctx['consec_worsening']}

Missed doses detected this week: {ctx['missed_dose']}
Active medications: {ctx['active_meds']}

Current health risk level: {ctx['risk_level']} (translate — do not say "risk level")
Overall trend: {ctx['trend']}

Upcoming appointment: {ctx['upcoming_appt']}
Unresolved health alerts: {ctx['unresolved_alerts']}

Today's date: {ctx['today']}
Time of day: {ctx['time_of_day']}"""

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       GROQ_MODEL,
                "messages":    [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "max_tokens":  700,
                "temperature": 0.4,
            },
            timeout=20,
        )
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip accidental markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return None


def _render_proactive_agent_tab(patient_id: str, patient: dict,
                                  risk: dict, adherence: dict, trends: dict):
    """Render the Proactive AI Health Agent tab."""

    st.markdown("### 🤖 My Health Agent")
    st.markdown(
        '<p style="color:var(--text-secondary);margin-top:-0.5rem;">'
        'Your personal AI agent monitors your health around the clock '
        'and tells you what matters today — before you have to ask.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Cache key: regenerate once per patient per hour ───────────────────────
    cache_key   = f"proactive_agent_data_{patient_id}_{date.today().isoformat()}_{datetime.now().hour}"
    refresh_key = f"proactive_agent_refresh_{patient_id}"

    force_refresh = st.session_state.pop(refresh_key, False)

    if force_refresh or cache_key not in st.session_state:
        with st.spinner("🤖 Your health agent is reviewing your data..."):
            ctx    = _build_agent_context(patient_id, patient, risk, adherence, trends)
            result = _call_groq_agent(ctx)
            st.session_state[cache_key] = {"result": result, "ctx": ctx}

    cached     = st.session_state.get(cache_key, {})
    result     = cached.get("result")
    ctx        = cached.get("ctx", {})

    # ── Refresh button ────────────────────────────────────────────────────────
    col_title, col_refresh = st.columns([5, 1])
    with col_refresh:
        if st.button("🔄 Refresh", key=f"agent_refresh_{patient_id}",
                     use_container_width=True):
            # Clear all hourly cache keys for this patient
            for k in list(st.session_state.keys()):
                if k.startswith(f"proactive_agent_data_{patient_id}"):
                    del st.session_state[k]
            st.session_state[refresh_key] = True
            st.rerun()

    # ── Fallback if Groq failed ───────────────────────────────────────────────
    if not result:
        st.warning(
            "⚠️ Your health agent could not connect right now. "
            "Please check your API key or try refreshing."
        )
        return

    # ── BRIEFING BANNER ───────────────────────────────────────────────────────
    briefing   = result.get("briefing", "")
    time_icon  = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}.get(
        ctx.get("time_of_day", "morning"), "🌅"
    )

    st.markdown(f"""
    <div class="card" style="border-left:4px solid #A78BFA;
         background:rgba(124,58,237,0.08);margin-bottom:1.5rem;padding:1.2rem 1.4rem;">
        <div style="display:flex;align-items:flex-start;gap:0.9rem;">
            <span style="font-size:2rem;line-height:1;">{time_icon}</span>
            <div>
                <div style="font-weight:700;color:#A78BFA;font-size:0.78rem;
                     text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">
                    Agent Briefing
                </div>
                <div style="color:var(--text-primary);font-size:0.97rem;line-height:1.7;">
                    {briefing}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AGENT ACTIVITY SUMMARY (what the agent already did) ──────────────────
    activity_lines = []
    if ctx.get("consec_worsening"):
        activity_lines.append("✅ Detected worsening health trend — doctor alert sent")
    if ctx.get("unresolved_alerts", 0) > 0:
        activity_lines.append(f"✅ {ctx['unresolved_alerts']} active alert(s) flagged for your doctor")
    if ctx.get("risk_level") == "high":
        activity_lines.append("✅ High risk status detected — escalated to doctor dashboard")
    activity_lines.append(f"✅ Risk assessment run — current level: {ctx.get('risk_level','low').upper()}")
    activity_lines.append(f"✅ Medication adherence checked — {ctx.get('active_meds', 0)} active medication(s)")

    items_html = "".join(
        f'<div style="font-size:0.83rem;color:var(--text-secondary);'
        f'padding:0.25rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
        f'{line}</div>'
        for line in activity_lines
    )
    st.markdown(f"""
    <div class="card" style="margin-bottom:1.5rem;">
        <div style="font-weight:600;color:var(--text-primary);font-size:0.88rem;
             margin-bottom:0.6rem;">🔍 What your agent did while you were away</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

    # ── ACTION CARDS ─────────────────────────────────────────────────────────
    cards = result.get("cards", [])

    if not cards:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;
             border-left:4px solid #34D399;background:rgba(52,211,153,0.06);">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
            <div style="font-weight:700;color:#34D399;font-size:1rem;">All Clear</div>
            <div style="color:var(--text-muted);font-size:0.88rem;margin-top:0.4rem;">
                Your agent has reviewed everything. No actions needed right now.
                Keep taking your medications and completing your daily check-ins.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="font-weight:600;color:var(--text-primary);'
            'margin-bottom:0.8rem;">📋 Actions for you today</div>',
            unsafe_allow_html=True,
        )

        priority_colors = {
            "high":   {"border": "#F87171", "bg": "rgba(248,113,113,0.07)",
                       "badge_bg": "rgba(248,113,113,0.15)", "badge_text": "#F87171"},
            "medium": {"border": "#FBBF24", "bg": "rgba(251,191,36,0.07)",
                       "badge_bg": "rgba(251,191,36,0.15)", "badge_text": "#FBBF24"},
            "low":    {"border": "#34D399", "bg": "rgba(52,211,153,0.06)",
                       "badge_bg": "rgba(52,211,153,0.15)", "badge_text": "#34D399"},
        }

        for i, card in enumerate(cards[:3]):
            priority    = card.get("priority", "medium")
            cfg         = priority_colors.get(priority, priority_colors["medium"])
            icon        = card.get("icon", "💡")
            title       = card.get("title", "")
            message     = card.get("message", "")
            action_type = card.get("action_type", "dismiss")
            action_label= card.get("action_label", "Take Action")

            st.markdown(f"""
            <div class="card" style="border-left:4px solid {cfg['border']};
                 background:{cfg['bg']};margin-bottom:1rem;">
                <div style="display:flex;align-items:flex-start;
                     justify-content:space-between;gap:0.8rem;">
                    <div style="display:flex;align-items:flex-start;gap:0.8rem;flex:1;">
                        <span style="font-size:1.6rem;line-height:1.2;">{icon}</span>
                        <div>
                            <div style="display:flex;align-items:center;gap:0.5rem;
                                 margin-bottom:0.3rem;">
                                <span style="font-weight:700;color:var(--text-primary);
                                      font-size:0.97rem;">{title}</span>
                                <span style="font-size:0.72rem;padding:1px 8px;
                                      border-radius:10px;font-weight:600;
                                      background:{cfg['badge_bg']};
                                      color:{cfg['badge_text']};">
                                    {priority.upper()}
                                </span>
                            </div>
                            <div style="color:var(--text-secondary);font-size:0.85rem;
                                 line-height:1.6;">{message}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Action button per card ────────────────────────────────────────
            _render_card_action(
                patient_id=patient_id,
                patient=patient,
                action_type=action_type,
                action_label=action_label,
                card_index=i,
            )
            st.markdown("<div style='margin-bottom:0.5rem;'></div>",
                        unsafe_allow_html=True)

    # ── SLOT BOOKING FLOW (shown below cards when triggered) ─────────────────
    _render_agent_booking_flow(patient_id, patient)

    # ── TRACK PROGRESS SECTION ────────────────────────────────────────────────
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-weight:700;color:var(--text-primary);font-size:1rem;'
        'margin-bottom:0.8rem;">📊 Track Progress</div>',
        unsafe_allow_html=True,
    )

    trend_toggle_key = f"agent_show_trends_{patient_id}"
    btn_label = "🔼 Hide Trends" if st.session_state.get(trend_toggle_key) else "📈 View Trends"
    if st.button(btn_label, key=f"agent_trend_btn_{patient_id}"):
        st.session_state[trend_toggle_key] = not st.session_state.get(trend_toggle_key, False)
        st.rerun()

    if st.session_state.get(trend_toggle_key):
        responses = _cached_mcq_responses(patient_id, limit=30)
        if not responses:
            st.info("No health check-in data yet. Complete your daily check-ins to see trends.")
        else:
            import plotly.graph_objects as go

            chart_responses = list(reversed(responses))
            dates    = [r["date"] for r in chart_responses]
            scores   = [r["total_score"] for r in chart_responses]
            statuses = [r["status"] for r in chart_responses]

            status_colors_map = {"Improving": "#34D399", "Stable": "#FBBF24", "Worsening": "#F87171"}
            marker_colors = [status_colors_map.get(s, "#A78BFA") for s in statuses]

            # Rolling 3-day average for the bold trend line (like the reference image)
            import statistics
            rolling_avg = []
            for i in range(len(scores)):
                window = scores[max(0, i - 2): i + 1]
                rolling_avg.append(statistics.mean(window))

            fig = go.Figure()

            # Shaded fill — positive zone green, negative zone red
            fig.add_trace(go.Scatter(
                x=dates, y=[max(s, 0) for s in scores],
                fill="tozeroy", fillcolor="rgba(52,211,153,0.10)",
                line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
            ))
            fig.add_trace(go.Scatter(
                x=dates, y=[min(s, 0) for s in scores],
                fill="tozeroy", fillcolor="rgba(248,113,113,0.10)",
                line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"
            ))

            # Raw daily score — thin salmon line (jagged, like the light line in reference)
            fig.add_trace(go.Scatter(
                x=dates, y=scores,
                mode="lines+markers",
                line=dict(color="rgba(251,146,100,0.65)", width=1.5, shape="spline", smoothing=0.4),
                marker=dict(size=6, color=marker_colors,
                            line=dict(color="#1a1a2e", width=1.5)),
                name="Daily Score",
                hovertemplate="<b>%{x}</b><br>Daily Score: %{y:+d}<extra></extra>"
            ))

            # Bold rolling average line — thick dark red (dominant line like reference)
            fig.add_trace(go.Scatter(
                x=dates, y=rolling_avg,
                mode="lines",
                line=dict(color="#C0392B", width=3.5, shape="spline", smoothing=0.7),
                name="3-Day Avg",
                hovertemplate="<b>%{x}</b><br>3-Day Avg: %{y:.1f}<extra></extra>"
            ))

            # Status icons above each daily point
            status_icons_map = {"Improving": "✅", "Stable": "⚠️", "Worsening": "❌"}
            for d, s, st_ in zip(dates, scores, statuses):
                fig.add_annotation(
                    x=d, y=s,
                    text=status_icons_map.get(st_, ""),
                    showarrow=False,
                    yshift=18, font=dict(size=11)
                )

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#A89FC8", size=12),
                margin=dict(l=10, r=10, t=20, b=10),
                height=320,
                xaxis=dict(
                    showgrid=False, zeroline=False,
                    tickfont=dict(size=11, color="#6B6080"),
                    title="Day"
                ),
                yaxis=dict(
                    showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                    zeroline=True, zerolinecolor="rgba(255,255,255,0.25)",
                    tickfont=dict(size=11, color="#6B6080"),
                    title="Condition Score"
                ),
                hoverlabel=dict(
                    bgcolor="#1E1B4B", bordercolor="#A78BFA",
                    font=dict(color="white", size=13)
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    font=dict(size=11, color="#A89FC8"),
                    bgcolor="rgba(0,0,0,0)"
                ),
            )

            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            st.markdown("""
            <div style="display:flex;gap:1.5rem;justify-content:center;margin:-0.5rem 0 1rem;flex-wrap:wrap;">
                <span style="color:#C0392B;font-size:0.82rem;">━━ 3-Day Trend</span>
                <span style="color:rgba(251,146,100,0.9);font-size:0.82rem;">━ Daily Score</span>
                <span style="color:#34D399;font-size:0.82rem;">✅ Improving</span>
                <span style="color:#FBBF24;font-size:0.82rem;">⚠️ Stable</span>
                <span style="color:#F87171;font-size:0.82rem;">❌ Worsening</span>
            </div>
            """, unsafe_allow_html=True)

    # ── LAST UPDATED footer ───────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:var(--text-muted);font-size:0.75rem;'
        f'margin-top:1.5rem;text-align:right;">'
        f'Agent last updated: {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 🧠  AI COPILOT — Pre-Appointment Brief Generator
# ══════════════════════════════════════════════════════════════════════════════

def _build_brief_context(patient_id: str, patient: dict,
                          risk: dict, adherence: dict, trends: dict) -> dict:
    """Collect all signals needed to generate the pre-appointment brief."""
    from data.database import get_all_medicines_for_patient

    responses     = _cached_mcq_responses(patient_id, limit=14)  # last 2 weeks
    prescriptions = _cached_prescriptions(patient_id)
    chat_history  = _cached_chat_history(patient_id, limit=30)
    bookings      = _cached_opd_bookings(patient_id)
    alerts        = _cached_patient_alerts(patient_id)

    # ── Next appointment ──────────────────────────────────────────────────────
    upcoming = None
    today_str = date.today().isoformat()
    for b in sorted(bookings, key=lambda x: x.get("slot_date", "")):
        if b.get("slot_date", "") >= today_str and b.get("status") not in ("cancelled",):
            upcoming = b
            break

    # ── MCQ trend summary ─────────────────────────────────────────────────────
    scores   = [r["total_score"]  for r in responses]
    statuses = [r["status"]       for r in responses]
    dates_r  = [r["date"]         for r in responses]

    # Extract reported symptoms from MCQ JSON
    all_symptoms = []
    for r in responses:
        try:
            resp_data = json.loads(r.get("responses_json") or "{}")
            for q_data in resp_data.values():
                if isinstance(q_data, dict):
                    sym = q_data.get("symptoms") or q_data.get("answer") or ""
                    if sym and isinstance(sym, str) and len(sym) > 3:
                        all_symptoms.append(sym)
        except Exception:
            pass

    # Extract side-effects
    all_side_effects = []
    for r in responses:
        try:
            se = json.loads(r.get("side_effects") or "[]")
            if isinstance(se, list):
                all_side_effects.extend(se)
        except Exception:
            pass

    # ── Adherence misses ──────────────────────────────────────────────────────
    missed_dates = []
    for r in responses:
        adh = (r.get("adherence_status") or "").lower()
        if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
            missed_dates.append(r["date"])

    # ── Trend direction ───────────────────────────────────────────────────────
    if len(scores) >= 4:
        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2)
        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
        overall_dir = "improving" if second_half > first_half else ("worsening" if second_half < first_half else "stable")
    else:
        overall_dir = trends.get("trend", "stable")

    # ── Unresolved alerts ─────────────────────────────────────────────────────
    unresolved = [a for a in alerts if not a.get("resolved")]

    # ── Recent patient-reported concerns from chat ────────────────────────────
    user_msgs = [h["content"] for h in chat_history if h.get("role") == "user"][-8:]

    return {
        "name":            patient.get("name", ""),
        "age":             patient.get("age", ""),
        "disease":         patient.get("disease", ""),
        "doctor_name":     patient.get("doctor_name", "Your Doctor"),
        "risk_level":      risk.get("level", "low"),
        "risk_score":      risk.get("score", 0),
        "active_meds":     adherence.get("active_medications", 0),
        "med_list":        [
            f"{m.get('name', m.get('medicine_name', 'Unknown'))} ({m.get('dosage','')})"
            for p in prescriptions[:6]
            for m in (p.get("medicines") or [p])[:2]
        ],
        "trend":           overall_dir,
        "scores":          scores,
        "statuses":        statuses,
        "dates":           dates_r,
        "symptoms":        list(set(all_symptoms))[:10],
        "side_effects":    list(set(all_side_effects))[:8],
        "missed_dates":    missed_dates,
        "unresolved_alerts": len(unresolved),
        "upcoming_appt":   upcoming,
        "user_concerns":   user_msgs,
        "today":           today_str,
        "checkin_count":   len(responses),
    }


def _call_brief_generator(ctx: dict) -> dict | None:
    """
    Multi-step agentic brief generator.
    Step 1 — Symptom NLP: extract & cluster key symptoms from raw data.
    Step 2 — Trend analysis: interpret the score trajectory.
    Step 3 — Brief synthesis: produce the final structured brief.
    Returns a rich dict with all sections for rendering.
    """
    from core.config import GROQ_API_KEY, GROQ_MODEL
    if not GROQ_API_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json",
    }
    url = "https://api.groq.com/openai/v1/chat/completions"

    def _groq(system: str, user: str, max_tokens: int = 800, temp: float = 0.3) -> str:
        try:
            r = requests.post(url, headers=headers, json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "max_tokens":  max_tokens,
                "temperature": temp,
            }, timeout=25)
            raw = r.json()["choices"][0]["message"]["content"].strip()
            return raw.replace("```json", "").replace("```", "").strip()
        except Exception:
            return ""

    # ── STEP 1: Symptom & Concern NLP ────────────────────────────────────────
    symptom_system = """You are a medical NLP agent. Extract and cluster symptoms/concerns from patient data.
Respond ONLY with valid JSON, no markdown:
{
  "primary_complaints": ["list of top 3 distinct symptoms/concerns"],
  "side_effects_noted": ["list of side effects if any"],
  "red_flags": ["any urgent symptoms that need immediate attention"],
  "patient_sentiment": "positive | neutral | anxious | distressed"
}"""

    symptom_user = f"""Patient: {ctx['name']}, Condition: {ctx['disease']}
Reported symptoms from check-ins: {ctx['symptoms']}
Reported side effects: {ctx['side_effects']}
Recent chat messages: {ctx['user_concerns']}
Check-in statuses last 14 days: {ctx['statuses']}"""

    symptom_raw  = _groq(symptom_system, symptom_user, max_tokens=400)
    try:
        symptom_data = json.loads(symptom_raw)
    except Exception:
        symptom_data = {"primary_complaints": ctx["symptoms"][:3],
                        "side_effects_noted": ctx["side_effects"][:3],
                        "red_flags": [],
                        "patient_sentiment": "neutral"}

    # ── STEP 2: Trend Intelligence ────────────────────────────────────────────
    trend_system = """You are a clinical trend analysis AI. Analyse the patient's health score trajectory.
Respond ONLY with valid JSON, no markdown:
{
  "trajectory": "one sentence describing the overall trajectory",
  "best_period": "date range when patient was doing best",
  "worst_period": "date range when patient was doing worst",
  "pattern": "e.g. weekend dips, medication-related, gradual decline, steady recovery",
  "doctor_note": "one clinical observation the doctor should know"
}"""

    trend_user = f"""Patient: {ctx['name']}, Condition: {ctx['disease']}
Scores over last {ctx['checkin_count']} days (oldest→newest): {list(reversed(ctx['scores']))}
Dates: {list(reversed(ctx['dates']))}
Statuses: {list(reversed(ctx['statuses']))}
Missed medication dates: {ctx['missed_dates']}
Overall direction: {ctx['trend']}"""

    trend_raw = _groq(trend_system, trend_user, max_tokens=400)
    try:
        trend_data = json.loads(trend_raw)
    except Exception:
        trend_data = {"trajectory": f"Overall trend appears {ctx['trend']}.",
                      "best_period": "", "worst_period": "",
                      "pattern": "Insufficient data for pattern detection",
                      "doctor_note": ""}

    # ── STEP 3: Full Brief Synthesis ──────────────────────────────────────────
    brief_system = """You are an AI clinical brief writer for a healthcare app called MediCure.
You synthesise patient health data into a pre-appointment brief — a document the doctor reads before seeing the patient.

Write in clear, warm, clinical language. Be specific. No filler sentences.

Respond ONLY with valid JSON, no markdown fences:
{
  "headline": "one punchy sentence summarising the patient's status right now",
  "executive_summary": "3-4 sentences: who the patient is, what's been happening, what needs attention",
  "key_concerns": [
    {"concern": "...", "severity": "high|medium|low", "since": "approx date or 'ongoing'"}
  ],
  "medication_status": "2 sentences on medication adherence and any side effects",
  "questions_for_doctor": [
    "specific question the patient should ask or the doctor should address"
  ],
  "recommended_actions": [
    "specific action for the doctor to consider"
  ],
  "patient_message": "a warm 2-sentence message to the patient telling them what to expect in the appointment"
}"""

    brief_user = f"""PATIENT PROFILE:
Name: {ctx['name']} | Age: {ctx['age']} | Condition: {ctx['disease']}
Assigned Doctor: Dr. {ctx['doctor_name']}
Risk Level: {ctx['risk_level']} ({ctx['risk_score']}/100)
Active Medications: {ctx['active_meds']} — {', '.join(ctx['med_list']) or 'None listed'}

SYMPTOM ANALYSIS (from NLP agent):
Primary complaints: {symptom_data.get('primary_complaints', [])}
Side effects noted: {symptom_data.get('side_effects_noted', [])}
Red flags: {symptom_data.get('red_flags', [])}
Patient sentiment: {symptom_data.get('patient_sentiment', 'neutral')}

TREND ANALYSIS (from trend agent):
{trend_data.get('trajectory', '')}
Pattern observed: {trend_data.get('pattern', '')}
Clinical observation: {trend_data.get('doctor_note', '')}
Best period: {trend_data.get('best_period', '')}
Worst period: {trend_data.get('worst_period', '')}

ADHERENCE:
Missed medication dates in last 2 weeks: {ctx['missed_dates'] or 'None detected'}
Unresolved alerts: {ctx['unresolved_alerts']}

Upcoming appointment: {ctx['upcoming_appt'].get('slot_date','') + ' at ' + ctx['upcoming_appt'].get('start_time','') if ctx['upcoming_appt'] else 'Not scheduled'}
Today: {ctx['today']}"""

    brief_raw = _groq(brief_system, brief_user, max_tokens=900, temp=0.35)
    try:
        brief_data = json.loads(brief_raw)
    except Exception:
        brief_data = {
            "headline": f"{ctx['name']}'s health is {ctx['trend']} — see details below.",
            "executive_summary": f"{ctx['name']} has been monitored for {ctx['disease']}.",
            "key_concerns": [],
            "medication_status": f"{ctx['active_meds']} active medication(s).",
            "questions_for_doctor": [],
            "recommended_actions": [],
            "patient_message": "Your brief is ready. Bring it to your next appointment.",
        }

    return {
        "symptom_data": symptom_data,
        "trend_data":   trend_data,
        "brief":        brief_data,
        "ctx":          ctx,
    }


def _render_health_guardian_tab(patient_id: str, patient: dict):
    """Render the 🧬 Health Guardian sub-tab — autonomous background agent."""
    from agents.health_guardian import run_guardian

    st.markdown(
        '<p style="color:var(--text-secondary);margin-top:-0.5rem;">'
        'The <strong>Health Guardian</strong> runs silently every time you log in. '
        'It watches your <strong>cross-session patterns</strong>, reasons over weeks of data, '
        'and alerts your doctor automatically — no input needed.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Run the Guardian (cached per session so it doesn't re-run on every rerun) ──
    cache_key   = f"guardian_result_{patient_id}_{date.today().isoformat()}"
    refresh_key = f"guardian_refresh_{patient_id}"
    force       = st.session_state.pop(refresh_key, False)

    col_h, col_btn = st.columns([5, 1])
    with col_h:
        st.markdown(
            '<div style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">'
            '🧬 Health Guardian — Live Analysis</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("🔄 Re-run", key=f"guardian_rerun_{patient_id}", use_container_width=True):
            st.session_state.pop(cache_key, None)
            st.session_state[refresh_key] = True
            st.rerun()

    if force or cache_key not in st.session_state:
        prog = st.progress(0, text="👁️ Step 1/3 — Perceiving your health history...")
        prog.progress(30, text="🧠 Step 2/3 — Reasoning across sessions...")
        result = run_guardian(patient_id, patient)
        prog.progress(80, text="⚡ Step 3/3 — Executing actions...")
        prog.progress(100, text="✅ Guardian cycle complete.")
        prog.empty()
        st.session_state[cache_key] = result
    else:
        result = st.session_state[cache_key]

    reasoning = result.get("reasoning", {})
    actions   = result.get("actions", {})
    snapshot  = result.get("snapshot", {})
    findings  = reasoning.get("findings", [])
    ran_at    = result.get("ran_at", "")
    error     = result.get("error")

    # ── Error banner ─────────────────────────────────────────────────────────
    if error and "No GROQ_API_KEY" in str(error):
        st.warning("⚠️ Health Guardian requires a Groq API key. Configure it in your environment settings.")
        return

    # ── Status banner ─────────────────────────────────────────────────────────
    alerts_sent  = actions.get("alerts_sent", 0)
    appt_imminent = actions.get("appointment_imminent", False)
    status_color = "#F87171" if alerts_sent > 0 else "#34D399"
    status_icon  = "🚨" if alerts_sent > 0 else "✅"
    status_label = f"{alerts_sent} alert(s) sent to your doctor" if alerts_sent > 0 else "No immediate actions required"

    ran_fmt = ""
    try:
        ran_fmt = datetime.fromisoformat(ran_at).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        ran_fmt = ran_at

    st.markdown(f"""
    <div class="card" style="border-left:4px solid {status_color};
         background:rgba(52,211,153,0.04);margin-bottom:1.2rem;padding:1.2rem 1.4rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
            <div>
                <div style="font-size:0.72rem;font-weight:700;color:{status_color};
                     text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">
                    {status_icon} Guardian Status · Ran at {ran_fmt}
                </div>
                <div style="font-size:1rem;font-weight:600;color:var(--text-primary);">
                    {reasoning.get('overall_assessment', 'Analysis complete.')}
                </div>
            </div>
            <div style="background:rgba(167,139,250,0.12);border:1px solid rgba(167,139,250,0.3);
                 border-radius:8px;padding:0.4rem 0.8rem;font-size:0.8rem;color:#A78BFA;">
                {status_label}
            </div>
        </div>
        {"<div style='margin-top:0.7rem;padding:0.4rem 0.8rem;background:rgba(248,113,113,0.1);border-radius:6px;color:#F87171;font-size:0.82rem;font-weight:600;'>⚡ Appointment within 48 hours — all findings escalated to HIGH priority</div>" if appt_imminent else ""}
    </div>
    """, unsafe_allow_html=True)

    # ── Patient message ───────────────────────────────────────────────────────
    patient_msg = reasoning.get("patient_message", "")
    if patient_msg:
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #A78BFA;background:rgba(167,139,250,0.06);margin-bottom:1.2rem;">
            <div style="display:flex;align-items:flex-start;gap:0.8rem;">
                <span style="font-size:1.6rem;">🧬</span>
                <div>
                    <div style="font-weight:700;color:#A78BFA;font-size:0.75rem;
                         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.35rem;">
                        A note from your Health Guardian
                    </div>
                    <div style="color:var(--text-primary);font-size:0.92rem;line-height:1.7;">
                        {patient_msg}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Findings ─────────────────────────────────────────────────────────────
    if not findings:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">🟢</div>
            <div style="color:var(--text-primary);font-weight:600;font-size:0.95rem;">
                No cross-session patterns flagged today
            </div>
            <div style="color:var(--text-muted);font-size:0.82rem;margin-top:0.4rem;">
                The Guardian will continue monitoring every login
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="font-weight:700;color:var(--text-primary);font-size:0.88rem;'
            f'margin-bottom:0.8rem;">🔍 {len(findings)} Finding(s) Detected</div>',
            unsafe_allow_html=True,
        )

        severity_colors = {"high": "#F87171", "medium": "#FBBF24", "low": "#34D399"}
        type_icons = {
            "pattern":           "📊",
            "anomaly":           "⚠️",
            "silence":           "🔇",
            "escalation":        "🚨",
            "medication_effect": "💊",
        }
        action_labels = {
            "alert_doctor":  ("🔔 Alert sent to doctor", "#F87171"),
            "flag_in_brief": ("📋 Flagged in pre-appointment brief", "#FBBF24"),
            "monitor":       ("👁️ Monitoring — no action yet", "#A78BFA"),
            "none":          ("✅ No action required", "#34D399"),
        }

        for i, finding in enumerate(findings):
            sev       = finding.get("severity", "low")
            sev_color = severity_colors.get(sev, "#A78BFA")
            f_type    = finding.get("type", "pattern")
            f_icon    = type_icons.get(f_type, "🔍")
            action    = finding.get("action", "none")
            a_label, a_color = action_labels.get(action, ("", "#A78BFA"))
            chain     = finding.get("reasoning_chain", [])

            st.markdown(f"""
            <div class="card" style="border-left:4px solid {sev_color};margin-bottom:1rem;padding:1.2rem 1.4rem;">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;
                     flex-wrap:wrap;gap:0.5rem;margin-bottom:0.8rem;">
                    <div style="display:flex;align-items:center;gap:0.6rem;">
                        <span style="font-size:1.3rem;">{f_icon}</span>
                        <div>
                            <div style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">
                                {finding.get('title', 'Finding')}
                            </div>
                            <div style="font-size:0.72rem;color:{sev_color};font-weight:600;
                                 text-transform:uppercase;letter-spacing:0.07em;">
                                {sev} severity · {f_type.replace('_', ' ')}
                            </div>
                        </div>
                    </div>
                    <div style="background:rgba(0,0,0,0.15);border:1px solid {a_color}33;
                         border-radius:6px;padding:0.3rem 0.7rem;font-size:0.75rem;color:{a_color};">
                        {a_label}
                    </div>
                </div>

                <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.6;margin-bottom:1rem;">
                    {finding.get('description', '')}
                </div>

                <div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:0.8rem 1rem;">
                    <div style="font-size:0.72rem;font-weight:700;color:var(--text-muted);
                         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">
                        🧠 Reasoning Chain
                    </div>
                    {"".join([
                        f'<div style="display:flex;gap:0.6rem;padding:0.3rem 0;'
                        f'border-bottom:0.5px solid rgba(255,255,255,0.04);">'
                        f'<span style="color:#A78BFA;font-weight:700;min-width:1.4rem;font-size:0.8rem;">S{j+1}</span>'
                        f'<span style="color:var(--text-secondary);font-size:0.82rem;">{step}</span></div>'
                        for j, step in enumerate(chain)
                    ])}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Actions taken log ─────────────────────────────────────────────────────
    action_log = actions.get("action_log", [])
    if action_log:
        st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)
        with st.expander("📋 Actions Log — What the Guardian Did This Session"):
            for entry in action_log:
                act      = entry.get("action", "")
                finding  = entry.get("finding", "")
                sev      = entry.get("severity", "")
                ts       = entry.get("timestamp", "")
                escalated = entry.get("escalated", False)
                try:
                    ts = datetime.fromisoformat(ts).strftime("%I:%M:%S %p")
                except Exception:
                    pass

                icon = {"alert_sent": "🔔", "alert_failed": "❌", "flag_in_brief": "📋", "monitor": "👁️"}.get(act, "·")
                sev_color = severity_colors.get(sev, "#A78BFA")
                st.markdown(f"""
                <div style="display:flex;gap:0.8rem;padding:0.5rem 0;
                     border-bottom:0.5px solid rgba(255,255,255,0.05);align-items:flex-start;">
                    <span style="font-size:1rem;">{icon}</span>
                    <div style="flex:1;">
                        <div style="color:var(--text-primary);font-size:0.85rem;font-weight:600;">
                            {act.replace('_', ' ').title()} — {finding}
                        </div>
                        <div style="color:var(--text-muted);font-size:0.75rem;">
                            Severity: <span style="color:{sev_color};">{sev}</span>
                            {" · ⚡ Escalated (appt within 48h)" if escalated else ""}
                            · {ts}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Guardian metadata footer ──────────────────────────────────────────────
    checkins = snapshot.get("checkin_count", 0)
    days_silent = snapshot.get("days_silent", 0)
    st.markdown(f"""
    <div style="color:var(--text-muted);font-size:0.72rem;margin-top:1.2rem;
         display:flex;gap:1.5rem;flex-wrap:wrap;">
        <span>Sessions analysed: <strong>{checkins}</strong></span>
        <span>Days since last check-in: <strong>{days_silent}</strong></span>
        <span>Findings this cycle: <strong>{len(findings)}</strong></span>
        <span>Alerts sent: <strong>{actions.get('alerts_sent', 0)}</strong></span>
        <span>Loop: perceive → reason → act · {ran_fmt}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_ai_copilot_tab(patient_id: str, patient: dict,
                            risk: dict, adherence: dict, trends: dict):
    """Render the AI Copilot tab — two sub-tabs: Brief + Health Guardian (Option B)."""

    st.markdown("### 🧠 AI Copilot")
    st.markdown(
        '<p style="color:var(--text-secondary);margin-top:-0.5rem;">'
        'Two autonomous AI systems working for you — a <strong>Pre-Appointment Brief</strong> '
        'generator and a <strong>Health Guardian</strong> that watches your patterns 24/7.</p>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Option B: Two sub-tabs inside AI Copilot ─────────────────────────────
    sub_tab_brief, sub_tab_guardian = st.tabs([
        "📋 Pre-Appointment Brief",
        "🧬 Health Guardian",
    ])

    with sub_tab_brief:
        st.markdown(
            '<p style="color:var(--text-secondary);margin-top:0.5rem;">'
            'Your AI analyses <strong>14 days of health data</strong>, extracts symptoms, '
            'detects patterns, and generates a <strong>ready-to-use brief</strong> for your doctor — '
            'fully autonomous, no typing needed.</p>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        cache_key   = f"copilot_brief_{patient_id}_{date.today().isoformat()}"
        refresh_key = f"copilot_refresh_{patient_id}"
        force       = st.session_state.pop(refresh_key, False)

        # ── Generate / Refresh button ─────────────────────────────────────────
        col_h, col_btn = st.columns([5, 1])
        with col_h:
            st.markdown(
                '<div style="font-weight:700;color:var(--text-primary);font-size:0.95rem;">'
                '📋 Pre-Appointment Health Brief</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("🔄 Regenerate", key=f"copilot_regen_{patient_id}", use_container_width=True):
                st.session_state.pop(cache_key, None)
                st.session_state[refresh_key] = True
                st.rerun()

        # ── Run the 3-step agentic pipeline ──────────────────────────────────────
        if force or cache_key not in st.session_state:
            prog = st.progress(0, text="🔍 Step 1/3 — Collecting your health data...")
            ctx  = _build_brief_context(patient_id, patient, risk, adherence, trends)
            prog.progress(30, text="🧠 Step 2/3 — Analysing symptoms & trends...")
            result = _call_brief_generator(ctx)
            prog.progress(90, text="📝 Step 3/3 — Writing your brief...")
            prog.progress(100, text="✅ Brief ready!")
            prog.empty()
            if result:
                st.session_state[cache_key] = result
            else:
                st.error("⚠️ Could not generate brief — check your Groq API key in settings.")
                return

        data = st.session_state.get(cache_key)
        if not data:
            return

        brief   = data["brief"]
        sym     = data["symptom_data"]
        trend_d = data["trend_data"]
        ctx     = data["ctx"]

        # ── HEADLINE BANNER ───────────────────────────────────────────────────────
        risk_color = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}.get(
            ctx["risk_level"], "#A78BFA")
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {risk_color};
             background:rgba(167,139,250,0.06);margin-bottom:1.2rem;padding:1.2rem 1.4rem;">
            <div style="font-size:0.72rem;font-weight:700;color:{risk_color};
                 text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;">
                AI Brief · {ctx['today']} · Risk: {ctx['risk_level'].upper()}
            </div>
            <div style="font-size:1.05rem;font-weight:600;color:var(--text-primary);line-height:1.5;">
                {brief.get('headline','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="card" style="margin-bottom:1rem;">
            <div style="font-weight:700;color:var(--text-primary);font-size:0.88rem;
                 margin-bottom:0.6rem;">📄 Executive Summary</div>
            <div style="color:var(--text-secondary);font-size:0.9rem;line-height:1.75;">
                {brief.get('executive_summary','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── THREE COLUMNS: Concerns | Sentiment | Trend ───────────────────────────
        col1, col2, col3 = st.columns(3)

        severity_colors = {"high": "#F87171", "medium": "#FBBF24", "low": "#34D399"}
        with col1:
            concerns = brief.get("key_concerns", [])
            items_html = "".join([
                f'<div style="display:flex;align-items:flex-start;gap:0.5rem;'
                f'padding:0.4rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
                f'<span style="color:{severity_colors.get(c.get("severity","medium"),"#FBBF24")};'
                f'font-size:0.75rem;margin-top:2px;">●</span>'
                f'<div><div style="color:var(--text-primary);font-size:0.83rem;">{c.get("concern","")}</div>'
                f'<div style="color:var(--text-muted);font-size:0.72rem;">since {c.get("since","")}</div></div></div>'
                for c in concerns
            ]) if concerns else '<div style="color:var(--text-muted);font-size:0.82rem;">No major concerns flagged</div>'
            st.markdown(f"""
            <div class="card" style="height:100%;">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;margin-bottom:0.6rem;">
                    🩺 Key Concerns
                </div>
                {items_html}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            sentiment      = sym.get("patient_sentiment", "neutral")
            sent_color     = {"positive": "#34D399", "neutral": "#A78BFA",
                              "anxious": "#FBBF24", "distressed": "#F87171"}.get(sentiment, "#A78BFA")
            sent_icon      = {"positive": "😊", "neutral": "😐",
                              "anxious": "😟", "distressed": "😰"}.get(sentiment, "😐")
            red_flags      = sym.get("red_flags", [])
            flags_html     = "".join([
                f'<div style="color:#F87171;font-size:0.8rem;padding:0.2rem 0;">⚠️ {f}</div>'
                for f in red_flags
            ]) if red_flags else '<div style="color:#34D399;font-size:0.8rem;">✅ No red flags detected</div>'
            st.markdown(f"""
            <div class="card" style="height:100%;">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;margin-bottom:0.6rem;">
                    💬 Patient Sentiment
                </div>
                <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.8rem;">
                    <span style="font-size:1.8rem;">{sent_icon}</span>
                    <span style="color:{sent_color};font-weight:700;font-size:0.95rem;
                          text-transform:capitalize;">{sentiment}</span>
                </div>
                <div style="font-weight:600;color:var(--text-muted);font-size:0.75rem;
                     text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.4rem;">
                    Red Flags
                </div>
                {flags_html}
            </div>
            """, unsafe_allow_html=True)

        with col3:
            traj = trend_d.get("trajectory", "")
            pattern = trend_d.get("pattern", "")
            st.markdown(f"""
            <div class="card" style="height:100%;">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;margin-bottom:0.6rem;">
                    📈 Trend Intelligence
                </div>
                <div style="color:var(--text-secondary);font-size:0.82rem;line-height:1.6;margin-bottom:0.6rem;">
                    {traj}
                </div>
                <div style="color:var(--text-muted);font-size:0.75rem;font-style:italic;">
                    Pattern: {pattern}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        # ── MEDICATION STATUS ─────────────────────────────────────────────────────
        side_effects = sym.get("side_effects_noted", [])
        se_html = (
            " · ".join([f'<span style="color:#FBBF24;">{s}</span>' for s in side_effects])
            if side_effects else '<span style="color:#34D399;">None reported</span>'
        )
        missed = ctx.get("missed_dates", [])
        missed_html = (
            " · ".join([f'<span style="color:#F87171;">{d}</span>' for d in missed[:5]])
            if missed else '<span style="color:#34D399;">No missed doses detected</span>'
        )
        st.markdown(f"""
        <div class="card" style="margin-bottom:1rem;">
            <div style="font-weight:700;color:var(--text-primary);font-size:0.88rem;margin-bottom:0.7rem;">
                💊 Medication Status
            </div>
            <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.7;margin-bottom:0.6rem;">
                {brief.get('medication_status','')}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;margin-top:0.5rem;">
                <div>
                    <div style="color:var(--text-muted);font-size:0.72rem;text-transform:uppercase;
                         letter-spacing:0.06em;margin-bottom:0.3rem;">Side Effects Noted</div>
                    <div style="font-size:0.82rem;">{se_html}</div>
                </div>
                <div>
                    <div style="color:var(--text-muted);font-size:0.72rem;text-transform:uppercase;
                         letter-spacing:0.06em;margin-bottom:0.3rem;">Missed Doses</div>
                    <div style="font-size:0.82rem;">{missed_html}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── QUESTIONS FOR DOCTOR + RECOMMENDED ACTIONS (side by side) ────────────
        col_q, col_a = st.columns(2)

        with col_q:
            questions = brief.get("questions_for_doctor", [])
            q_items = "".join([
                f'<div style="display:flex;gap:0.6rem;padding:0.4rem 0;'
                f'border-bottom:0.5px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#A78BFA;font-weight:700;min-width:1.2rem;">Q{i+1}</span>'
                f'<span style="color:var(--text-secondary);font-size:0.83rem;">{q}</span></div>'
                for i, q in enumerate(questions)
            ]) if questions else '<div style="color:var(--text-muted);font-size:0.82rem;">No specific questions generated.</div>'
            st.markdown(f"""
            <div class="card">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.88rem;margin-bottom:0.6rem;">
                    ❓ Questions for Your Doctor
                </div>
                {q_items}
            </div>
            """, unsafe_allow_html=True)

        with col_a:
            actions = brief.get("recommended_actions", [])
            a_items = "".join([
                f'<div style="display:flex;gap:0.6rem;padding:0.4rem 0;'
                f'border-bottom:0.5px solid rgba(255,255,255,0.05);">'
                f'<span style="color:#34D399;font-size:0.9rem;">→</span>'
                f'<span style="color:var(--text-secondary);font-size:0.83rem;">{a}</span></div>'
                for a in actions
            ]) if actions else '<div style="color:var(--text-muted);font-size:0.82rem;">No additional actions recommended.</div>'
            st.markdown(f"""
            <div class="card">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.88rem;margin-bottom:0.6rem;">
                    ✅ Recommended Actions
                </div>
                {a_items}
            </div>
            """, unsafe_allow_html=True)

        # ── PATIENT MESSAGE ───────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="card" style="border-left:4px solid #34D399;
             background:rgba(52,211,153,0.05);margin-top:0.5rem;">
            <div style="display:flex;align-items:flex-start;gap:0.8rem;">
                <span style="font-size:1.8rem;">🤖</span>
                <div>
                    <div style="font-weight:700;color:#34D399;font-size:0.78rem;
                         text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">
                        A note from your AI
                    </div>
                    <div style="color:var(--text-primary);font-size:0.92rem;line-height:1.7;">
                        {brief.get('patient_message','')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── COPY-TO-CLIPBOARD plain text brief ───────────────────────────────────
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        with st.expander("📋 View Plain-Text Brief (copy for your doctor)"):
            concerns_text = "\n".join([
                f"  • {c.get('concern','')} [{c.get('severity','').upper()}] — since {c.get('since','')}"
                for c in brief.get("key_concerns", [])
            ]) or "  • None flagged"
            questions_text = "\n".join([f"  Q{i+1}. {q}" for i, q in enumerate(brief.get("questions_for_doctor", []))]) or "  • None"
            actions_text   = "\n".join([f"  • {a}" for a in brief.get("recommended_actions", [])]) or "  • None"
            missed_text    = ", ".join(missed) if missed else "None"
            se_text        = ", ".join(side_effects) if side_effects else "None"

            plain = f"""
    ╔══════════════════════════════════════════════════════╗
    ║         PRE-APPOINTMENT HEALTH BRIEF — MediCure AI   ║
    ╚══════════════════════════════════════════════════════╝

    Patient : {ctx['name']}  |  Age: {ctx['age']}  |  Condition: {ctx['disease']}
    Doctor  : Dr. {ctx['doctor_name']}
    Date    : {ctx['today']}  |  Risk: {ctx['risk_level'].upper()} ({ctx['risk_score']}/100)

    HEADLINE
    {brief.get('headline','')}

    EXECUTIVE SUMMARY
    {brief.get('executive_summary','')}

    KEY CONCERNS
    {concerns_text}

    MEDICATION STATUS
    {brief.get('medication_status','')}
    Missed Doses  : {missed_text}
    Side Effects  : {se_text}

    TREND INTELLIGENCE
    {trend_d.get('trajectory','')}
    Pattern: {trend_d.get('pattern','')}
    {('Clinical note: ' + trend_d.get('doctor_note','')) if trend_d.get('doctor_note') else ''}

    QUESTIONS FOR THE DOCTOR
    {questions_text}

    RECOMMENDED ACTIONS
    {actions_text}

    ──────────────────────────────────────────────────────
    Generated by MediCure AI Copilot · {datetime.now().strftime('%d %b %Y, %I:%M %p')}
            """.strip()
            st.code(plain, language=None)

        # ── Footer ────────────────────────────────────────────────────────────────
        st.markdown(
            f'<div style="color:var(--text-muted);font-size:0.72rem;'
            f'margin-top:1rem;text-align:right;">'
            f'Brief generated · {datetime.now().strftime("%d %b %Y, %I:%M %p")} · '
            f'3-step AI pipeline: NLP → Trend Analysis → Synthesis'
            f'</div>',
            unsafe_allow_html=True,
        )

    with sub_tab_guardian:
        _render_health_guardian_tab(patient_id, patient)


def _render_card_action(patient_id: str, patient: dict, action_type: str,
                         action_label: str, card_index: int):
    """Render the action button for a single card and handle its logic."""

    btn_key = f"agent_card_btn_{patient_id}_{card_index}"

    if action_type == "complete_checkin":
        if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
            st.info("👉 Head to the **🩺 Daily Health Check** tab to complete today's check-in.")

    elif action_type == "view_prescription":
        if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
            st.info("👉 Head to the **💊 My Prescriptions** tab to review your medications.")

    elif action_type == "book_appointment":
        book_trigger_key = f"agent_book_trigger_{patient_id}"
        if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
            # Fetch available slots on click — never before
            doctors   = get_available_opd_doctors()
            my_doc_id = patient.get("doctor_id")
            my_docs   = [d for d in doctors if d["doctor_id"] == my_doc_id] or doctors

            all_slots = []
            for doc in my_docs:
                dates = get_available_opd_dates_for_doctor(doc["doctor_id"])
                for d in dates[:3]:
                    slots = get_available_opd_slots(doc["doctor_id"], d)
                    for s in slots:
                        all_slots.append({
                            **s,
                            "doctor_name": doc["name"],
                            "doctor_id":   doc["doctor_id"],
                        })

            if not all_slots:
                st.warning(
                    "⚠️ No available slots right now. "
                    "Please check the **🖥️ Online OPD** tab or contact the clinic."
                )
            else:
                st.session_state[f"agent_slots_{patient_id}"]       = all_slots
                st.session_state[f"agent_booking_step_{patient_id}"] = "select"
                st.rerun()

    elif action_type == "dismiss":
        if st.button(f"→ {action_label}", key=btn_key, use_container_width=False):
            st.success("✅ Noted.")


def _render_agent_booking_flow(patient_id: str, patient: dict):
    """3-step booking flow triggered from an action card. Fully scoped to agent context."""

    step_key   = f"agent_booking_step_{patient_id}"
    slots_key  = f"agent_slots_{patient_id}"
    slot_key   = f"agent_chosen_slot_{patient_id}"
    doctor_key = f"agent_chosen_doctor_{patient_id}"

    step = st.session_state.get(step_key)
    if step is None:
        return

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-weight:600;color:var(--text-primary);'
        'margin-bottom:0.8rem;">📅 Book a Consultation</div>',
        unsafe_allow_html=True,
    )

    # ── Step: select slot ─────────────────────────────────────────────────────
    if step == "select":
        all_slots = st.session_state.get(slots_key, [])
        if not all_slots:
            st.warning("No slots loaded. Please try again.")
            st.session_state.pop(step_key, None)
            return

        slot_labels = [
            f"Dr. {s['doctor_name']}  —  {s['slot_date']}  {s['start_time']}–{s['end_time']}"
            for s in all_slots
        ]
        chosen_idx = st.selectbox(
            "Select a slot",
            options=range(len(slot_labels)),
            format_func=lambda i: slot_labels[i],
            key=f"agent_slot_select_{patient_id}",
            label_visibility="collapsed",
        )
        col_ok, col_cancel = st.columns([2, 1])
        with col_ok:
            if st.button("Confirm this slot →",
                         key=f"agent_confirm_slot_{patient_id}",
                         type="primary", use_container_width=True):
                chosen = all_slots[chosen_idx]
                st.session_state[slot_key]   = chosen
                st.session_state[doctor_key] = {
                    "name": chosen["doctor_name"],
                    "id":   chosen["doctor_id"],
                }
                st.session_state[step_key] = "confirm"
                st.rerun()
        with col_cancel:
            if st.button("Cancel", key=f"agent_cancel_slot_{patient_id}",
                         use_container_width=True):
                for k in (step_key, slots_key, slot_key, doctor_key):
                    st.session_state.pop(k, None)
                st.rerun()

    # ── Step: confirm booking ─────────────────────────────────────────────────
    elif step == "confirm":
        chosen_slot   = st.session_state.get(slot_key, {})
        chosen_doctor = st.session_state.get(doctor_key, {})

        st.markdown(f"""
        <div class="card" style="border:1px solid rgba(167,139,250,0.4);
             background:rgba(167,139,250,0.06);margin-bottom:0.8rem;">
            <div style="font-weight:600;color:var(--text-primary);margin-bottom:0.4rem;">
                📋 Confirm Booking
            </div>
            <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.9;">
                <strong>Doctor:</strong> Dr. {chosen_doctor.get('name', '')}<br>
                <strong>Date:</strong> {chosen_slot.get('slot_date', '')}<br>
                <strong>Time:</strong> {chosen_slot.get('start_time', '')} – {chosen_slot.get('end_time', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_yes, col_back = st.columns(2)
        with col_yes:
            if st.button("✅ Book Appointment",
                         key=f"agent_book_yes_{patient_id}",
                         type="primary", use_container_width=True):
                success = book_opd_slot(
                    slot_id=chosen_slot["id"],
                    patient_id=patient_id,
                    patient_name=patient.get("name", ""),
                )
                for k in (step_key, slots_key, slot_key, doctor_key):
                    st.session_state.pop(k, None)
                _cached_opd_bookings.clear()

                if success:
                    doctor_id = patient.get("doctor_id")
                    create_alert(
                        patient_id=patient_id,
                        alert_type="agent_opd_booked",
                        message=(
                            f"Patient booked an OPD slot via the Proactive Health Agent tab.\n"
                            f"Slot: Dr. {chosen_doctor.get('name','')} on "
                            f"{chosen_slot.get('slot_date','')} "
                            f"at {chosen_slot.get('start_time','')}."
                        ),
                        severity="low",
                        doctor_id=doctor_id,
                    )
                    st.success(
                        f"✅ Appointment booked with Dr. {chosen_doctor.get('name','')} "
                        f"on {chosen_slot.get('slot_date','')} "
                        f"at {chosen_slot.get('start_time','')}."
                    )
                else:
                    st.error(
                        "❌ That slot was just taken. "
                        "Please go to the **🖥️ Online OPD** tab to pick another."
                    )
                st.rerun()

        with col_back:
            if st.button("← Back", key=f"agent_book_back_{patient_id}",
                         use_container_width=True):
                st.session_state[step_key] = "select"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# 🧬  HEALTH COMMAND CENTER — Autonomous Multi-Step AI Agent
# ══════════════════════════════════════════════════════════════════════════════

def _build_command_center_context(patient_id: str, patient: dict,
                                   risk: dict, adherence: dict, trends: dict) -> dict:
    """Collect every signal needed for the autonomous agent loop."""
    from data.database import (
        get_mcq_responses, get_mcq_response_for_date,
        check_consecutive_worsening, get_patient_alerts,
        get_patient_opd_bookings, get_patient_prescriptions,
        get_all_medicines_for_patient, get_chat_history,
    )

    today_str   = date.today().isoformat()
    mcq_rows    = get_mcq_responses(patient_id, limit=14)
    bookings    = get_patient_opd_bookings(patient_id)
    alerts      = get_patient_alerts(patient_id)
    prescriptions = get_patient_prescriptions(patient_id)
    chat_history  = get_chat_history(patient_id, limit=20)

    # ── Scores & statuses ─────────────────────────────────────────────────────
    scores   = [r["total_score"] for r in mcq_rows]
    statuses = [r["status"]      for r in mcq_rows]
    dates_r  = [r["date"]        for r in mcq_rows]

    # ── Adherence flags ───────────────────────────────────────────────────────
    adherence_flags = [r.get("adherence_status", "") for r in mcq_rows[:7]]
    missed_dose_dates = []
    for r in mcq_rows:
        adh = (r.get("adherence_status") or "").lower()
        if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
            missed_dose_dates.append(r["date"])

    # ── Check-in status ───────────────────────────────────────────────────────
    checkin_done      = get_mcq_response_for_date(patient_id, today_str) is not None
    consec_worsening  = check_consecutive_worsening(patient_id, 2)
    consec_worsening3 = check_consecutive_worsening(patient_id, 3)

    # ── Appointments ──────────────────────────────────────────────────────────
    upcoming_appt = None
    days_until_appt = None
    for b in sorted(bookings, key=lambda x: x.get("slot_date", "")):
        if b.get("slot_date", "") >= today_str and b.get("status") not in ("cancelled",):
            upcoming_appt = b
            try:
                appt_date = date.fromisoformat(b["slot_date"])
                days_until_appt = (appt_date - date.today()).days
            except Exception:
                days_until_appt = None
            break

    # ── Alerts ────────────────────────────────────────────────────────────────
    unresolved_alerts = [a for a in alerts if not a.get("resolved")]
    high_alerts       = [a for a in unresolved_alerts if a.get("severity") == "high"]

    # ── Symptoms from MCQ responses ───────────────────────────────────────────
    all_symptoms = []
    for r in mcq_rows:
        try:
            resp_data = json.loads(r.get("responses_json") or "{}")
            for q_data in resp_data.values():
                if isinstance(q_data, dict):
                    sym = q_data.get("symptoms") or q_data.get("answer") or ""
                    if sym and isinstance(sym, str) and len(sym) > 3:
                        all_symptoms.append(sym)
        except Exception:
            pass

    # ── Side effects ──────────────────────────────────────────────────────────
    all_side_effects = []
    for r in mcq_rows:
        try:
            se = json.loads(r.get("side_effects") or "[]")
            if isinstance(se, list):
                all_side_effects.extend(se)
        except Exception:
            pass

    # ── Trend direction (14-day) ──────────────────────────────────────────────
    if len(scores) >= 4:
        half = len(scores) // 2
        first_h  = sum(scores[:half]) / half
        second_h = sum(scores[half:]) / (len(scores) - half)
        overall_dir = ("improving" if second_h > first_h
                       else "worsening" if second_h < first_h
                       else "stable")
    else:
        overall_dir = trends.get("trend", "stable")

    # ── Time of day ───────────────────────────────────────────────────────────
    hour = datetime.now().hour
    time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"

    # ── User concerns from chat ───────────────────────────────────────────────
    user_msgs = [h["content"] for h in chat_history if h.get("role") == "user"][-6:]

    # ── Med list ──────────────────────────────────────────────────────────────
    med_list = [
        f"{m.get('name', m.get('medicine_name', 'Unknown'))} ({m.get('dosage', '')})"
        for p in prescriptions[:4]
        for m in (p.get("medicines") or [p])[:2]
    ]

    return {
        # Patient info
        "name":               patient.get("name", ""),
        "age":                patient.get("age", ""),
        "disease":            patient.get("disease", ""),
        "doctor_name":        patient.get("doctor_name") or patient.get("doctor_id", "your doctor"),
        # Risk & health
        "risk_level":         risk.get("level", "low"),
        "risk_score":         risk.get("score", 0),
        "trend":              overall_dir,
        "active_meds":        adherence.get("active_medications", 0),
        "med_list":           med_list,
        # Check-ins
        "checkin_done":       checkin_done,
        "scores":             scores,
        "statuses":           statuses,
        "dates":              dates_r,
        "symptoms":           list(set(all_symptoms))[:8],
        "side_effects":       list(set(all_side_effects))[:6],
        # Alerts & worsening
        "consec_worsening":   consec_worsening,
        "consec_worsening3":  consec_worsening3,
        "missed_dose_dates":  missed_dose_dates,
        "unresolved_count":   len(unresolved_alerts),
        "high_alert_count":   len(high_alerts),
        # Appointment
        "upcoming_appt":      upcoming_appt,
        "days_until_appt":    days_until_appt,
        # Meta
        "today":              today_str,
        "time_of_day":        time_of_day,
        "user_concerns":      user_msgs,
        "checkin_count":      len(mcq_rows),
    }


def _run_autonomous_actions(patient_id: str, ctx: dict) -> list:
    """
    The agent's autonomous action loop.
    Evaluates conditions and writes real DB actions (alerts) where needed.
    Returns a timestamped log of everything it did.
    """
    from data.database import create_alert, check_consecutive_worsening, get_patient as _gp
    from core.config import GROQ_API_KEY
    try:
        from core.email_service import send_action_email as _send_email
        _email_ok = True
    except Exception:
        _email_ok = False

    log = []
    now_str = datetime.now().strftime("%I:%M %p")
    # Pull doctor_id from patient record so alerts appear on the doctor's Alert tab
    _pt = _gp(patient_id) or {}
    doctor_id      = _pt.get("doctor_id") or None
    patient_email  = _pt.get("email", "")
    patient_name   = ctx.get("name", "Patient")
    hospital_name  = "MediCure"

    def _try_email(action_type, subject, headline, body_html, details_rows, footer=""):
        if _email_ok and patient_email:
            try:
                _send_email(
                    action_type   = action_type,
                    patient_name  = patient_name,
                    patient_email = patient_email,
                    subject       = subject,
                    headline      = headline,
                    body_html     = body_html,
                    details_rows  = details_rows,
                    footer_note   = footer,
                    hospital_name = hospital_name,
                )
            except Exception:
                pass

    # ── Rule 1: 3 consecutive worsening → high-priority alert ─────────────────
    if ctx.get("consec_worsening3"):
        create_alert(
            patient_id=patient_id,
            alert_type="command_center_worsening",
            message=(
                f"Health Command Center detected 3 consecutive worsening check-ins for "
                f"{ctx['name']}. Immediate review recommended."
            ),
            severity="high",
            doctor_id=doctor_id,
        )
        _try_email(
            action_type  = "high_risk",
            subject      = f"⚠️ Health Alert — Worsening Trend Detected | {ctx.get('today','')}",
            headline     = "Your health has been declining for 3 consecutive check-ins",
            body_html    = (
                "Our autonomous health monitor has detected that your condition has been "
                "<strong>worsening for 3 consecutive check-ins</strong>. "
                "Your doctor has been notified. Please take your medications as prescribed "
                "and consider contacting the clinic if symptoms worsen."
            ),
            details_rows = [
                ("Patient",       patient_name),
                ("Condition",     ctx.get("disease", "N/A")),
                ("Risk Level",    ctx.get("risk_level", "N/A").upper()),
                ("Risk Score",    f"{ctx.get('risk_score', 0)}/100"),
                ("Trend",         ctx.get("trend", "N/A").upper()),
                ("Date",          ctx.get("today", "")),
            ],
            footer = "Your doctor has been automatically notified. Please do not ignore this alert.",
        )
        log.append({
            "time": now_str,
            "icon": "🚨",
            "color": "#F87171",
            "text": "3 consecutive worsening sessions detected — high-priority alert created for your doctor",
        })

    # ── Rule 2: 2 consecutive worsening → medium alert ────────────────────────
    elif ctx.get("consec_worsening"):
        create_alert(
            patient_id=patient_id,
            alert_type="command_center_worsening_2",
            message=(
                f"Health Command Center: {ctx['name']} has shown worsening health "
                f"for 2 consecutive check-ins. Monitor closely."
            ),
            severity="medium",
            doctor_id=doctor_id,
        )
        _try_email(
            action_type  = "worsening",
            subject      = f"⚠️ Health Monitoring Alert — {ctx.get('today','')}",
            headline     = "Your health check-ins show a worsening pattern",
            body_html    = (
                "Your health has been reported as worsening in your last 2 check-ins. "
                "Your doctor has been notified and is monitoring your progress. "
                "Please continue taking your medications and complete your daily check-ins."
            ),
            details_rows = [
                ("Patient",       patient_name),
                ("Condition",     ctx.get("disease", "N/A")),
                ("Current Trend", ctx.get("trend", "N/A").upper()),
                ("Risk Level",    ctx.get("risk_level", "N/A").upper()),
                ("Date",          ctx.get("today", "")),
            ],
            footer = "Complete today's check-in to keep your doctor updated.",
        )
        log.append({
            "time": now_str,
            "icon": "⚠️",
            "color": "#FBBF24",
            "text": "Worsening trend for 2 sessions — monitoring alert sent to doctor",
        })

    # ── Rule 3: Risk crossed to high → escalation alert ───────────────────────
    if ctx.get("risk_level") == "high":
        create_alert(
            patient_id=patient_id,
            alert_type="command_center_high_risk",
            message=(
                f"Risk score for {ctx['name']} is {ctx['risk_score']}/100 (HIGH). "
                f"Condition: {ctx['disease']}. Immediate attention required."
            ),
            severity="high",
            doctor_id=doctor_id,
        )
        _try_email(
            action_type  = "high_risk",
            subject      = f"🔴 High Risk Alert — Immediate Attention Required | {ctx.get('today','')}",
            headline     = f"Your health risk score has reached HIGH ({ctx.get('risk_score',0)}/100)",
            body_html    = (
                f"Your current health risk score is <strong>{ctx.get('risk_score',0)}/100 (HIGH)</strong>. "
                "This means your recent health data indicates a need for immediate medical attention. "
                "Please contact your doctor or visit the clinic as soon as possible."
            ),
            details_rows = [
                ("Patient",       patient_name),
                ("Condition",     ctx.get("disease", "N/A")),
                ("Risk Score",    f"{ctx.get('risk_score', 0)}/100"),
                ("Risk Level",    "HIGH ⚠️"),
                ("Active Meds",   str(ctx.get("active_meds", 0))),
                ("Date",          ctx.get("today", "")),
            ],
            footer = "Please seek medical attention promptly. Your doctor has been notified.",
        )
        log.append({
            "time": now_str,
            "icon": "🔴",
            "color": "#F87171",
            "text": f"High risk score ({ctx['risk_score']}/100) — escalation alert raised",
        })

    # ── Rule 4: Missed 2+ doses this week → adherence alert ───────────────────
    if len(ctx.get("missed_dose_dates", [])) >= 2:
        create_alert(
            patient_id=patient_id,
            alert_type="command_center_missed_doses",
            message=(
                f"{ctx['name']} missed medication on: "
                f"{', '.join(ctx['missed_dose_dates'][:3])}. "
                f"Adherence follow-up needed."
            ),
            severity="medium",
            doctor_id=doctor_id,
        )
        _try_email(
            action_type  = "missed_doses",
            subject      = f"💊 Medication Reminder — Missed Doses Detected | {ctx.get('today','')}",
            headline     = "You have missed medication doses this week",
            body_html    = (
                "Our system has detected that you may have missed taking your medication on "
                f"<strong>{len(ctx.get('missed_dose_dates',[]))} day(s)</strong> this week. "
                "Consistent adherence is essential for your recovery. "
                "Please resume your medication schedule as prescribed by your doctor."
            ),
            details_rows = [
                ("Patient",        patient_name),
                ("Condition",      ctx.get("disease", "N/A")),
                ("Missed On",      ", ".join(ctx.get("missed_dose_dates", [])[:3])),
                ("Active Meds",    str(ctx.get("active_meds", 0))),
                ("Date",           ctx.get("today", "")),
            ],
            footer = "If you are experiencing side effects, contact your doctor before stopping medication.",
        )
        log.append({
            "time": now_str,
            "icon": "💊",
            "color": "#FBBF24",
            "text": f"Missed doses on {len(ctx['missed_dose_dates'])} day(s) — adherence alert logged",
        })

    # ── Rule 5: Appointment in ≤ 2 days → pre-visit brief flagged ─────────────
    days = ctx.get("days_until_appt")
    if days is not None and days <= 2:
        log.append({
            "time": now_str,
            "icon": "📋",
            "color": "#A78BFA",
            "text": f"Appointment in {days} day(s) — pre-visit brief auto-generated below",
        })

    # ── Rule 6: Groq API missing → warn ───────────────────────────────────────
    if not GROQ_API_KEY:
        log.append({
            "time": now_str,
            "icon": "⚙️",
            "color": "#6B7280",
            "text": "AI briefing unavailable — GROQ_API_KEY not configured",
        })

    # ── Always log the routine checks ─────────────────────────────────────────
    log.append({
        "time": now_str,
        "icon": "✅",
        "color": "#34D399",
        "text": f"Risk assessment complete — current level: {ctx['risk_level'].upper()} ({ctx['risk_score']}/100)",
    })
    log.append({
        "time": now_str,
        "icon": "✅",
        "color": "#34D399",
        "text": f"Medication adherence checked — {ctx['active_meds']} active medication(s) on record",
    })
    if ctx.get("checkin_done"):
        log.append({
            "time": now_str,
            "icon": "✅",
            "color": "#34D399",
            "text": "Today's health check-in received and processed",
        })
    else:
        log.append({
            "time": now_str,
            "icon": "🔔",
            "color": "#FBBF24",
            "text": "Today's health check-in not yet completed — reminder queued",
        })

    return log


def _call_command_center_groq(ctx: dict) -> dict | None:
    """
    Single Groq call that returns:
      - morning_brief: personalised 2-3 sentence daily summary
      - missions: list of active agent missions with status
      - pre_visit_brief: structured doctor brief (only if appointment ≤ 7 days away)
      - suggested_questions: questions to ask the doctor
    """
    from core.config import GROQ_API_KEY, GROQ_MODEL
    if not GROQ_API_KEY:
        return None

    appt = ctx.get("upcoming_appt")
    days = ctx.get("days_until_appt")
    appt_str = (
        f"{appt.get('slot_date','')} at {appt.get('start_time','')}"
        if appt else "None scheduled"
    )
    include_brief = appt is not None and days is not None and days <= 7

    system_prompt = """You are an autonomous AI health agent embedded in a medical app called MediCure.
You run silently in the background and produce a structured daily health intelligence report for the patient.

Rules:
- Address the patient by first name only
- Use plain language — no clinical jargon, no "risk score", no "MCQ", no "consecutive worsening"
- Be warm, specific, and direct
- Never say "based on your data" or "I have analysed" — just state things naturally
- For missions: reflect what the agent is genuinely watching right now
- For pre_visit_brief: only include if include_pre_visit_brief is true in the context

Respond ONLY with valid JSON — no markdown fences, no extra text:
{
  "morning_brief": "2-3 sentences personalised daily summary",
  "missions": [
    {
      "status": "active | watching | complete",
      "icon": "single emoji",
      "title": "short mission name max 5 words",
      "detail": "1 sentence what the agent is tracking"
    }
  ],
  "pre_visit_brief": {
    "headline": "one sentence summary for the doctor",
    "executive_summary": "2-3 sentences covering condition, trend, key concerns",
    "key_concerns": ["concern 1", "concern 2"],
    "suggested_questions": ["question 1", "question 2", "question 3"],
    "medication_notes": "1 sentence on adherence and any side effects"
  }
}

Always include 3-5 missions. Only include pre_visit_brief key when include_pre_visit_brief is true."""

    user_prompt = f"""Patient: {ctx['name']}, age {ctx['age']}, condition: {ctx['disease']}
Doctor: Dr. {ctx['doctor_name']}
Time of day: {ctx['time_of_day']}
Today: {ctx['today']}

Health trend (14 days): {ctx['trend']}
Risk level: {ctx['risk_level']} ({ctx['risk_score']}/100)
Active medications: {ctx['active_meds']} — {', '.join(ctx['med_list'][:4]) or 'none listed'}

Last 5 check-in statuses: {ctx['statuses'][:5]}
Last 5 scores: {ctx['scores'][:5]}
Today's check-in done: {ctx['checkin_done']}
Health declining for 2+ sessions: {ctx['consec_worsening']}
Health declining for 3+ sessions: {ctx['consec_worsening3']}

Missed dose dates this week: {ctx['missed_dose_dates'][:3] or 'none'}
Unresolved alerts: {ctx['unresolved_count']}
High-severity alerts: {ctx['high_alert_count']}

Reported symptoms (recent): {ctx['symptoms'][:5] or 'none'}
Side effects reported: {ctx['side_effects'][:4] or 'none'}
Recent patient concerns: {ctx['user_concerns'][-3:] or 'none'}

Upcoming appointment: {appt_str}
Days until appointment: {days if days is not None else 'N/A'}
include_pre_visit_brief: {include_brief}"""

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                "max_tokens":  900,
                "temperature": 0.4,
            },
            timeout=25,
        )
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception:
        return None


def _render_health_command_center(patient_id: str, patient: dict,
                                   risk: dict, adherence: dict, trends: dict):
    """
    🧬 Health Command Center — Autonomous multi-step AI agent tab.

    On every open it:
      1. Collects full patient context
      2. Runs autonomous DB actions (creates alerts where thresholds are breached)
      3. Calls Groq for morning brief + missions + pre-visit brief
      4. Renders: Header → Morning Brief → Active Missions → Pre-Visit Brief → Actions Log
    Cache: regenerated once per patient per hour.
    """

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:0.3rem;">
        <span style="font-size:1.45rem;font-weight:800;
              background:linear-gradient(135deg,#A78BFA,#60A5FA);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            🧬 Health Command Center
        </span>
    </div>
    <p style="color:var(--text-secondary);margin-top:-0.2rem;margin-bottom:1rem;font-size:0.93rem;">
        Your autonomous AI agent — reads your health data, acts on your behalf,
        and gives you a complete picture before you even scroll.
    </p>
    """, unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Cache key: regenerate once per patient per hour ───────────────────────
    hour_key     = f"hcc_{patient_id}_{date.today().isoformat()}_{datetime.now().hour}"
    refresh_key  = f"hcc_refresh_{patient_id}"
    force        = st.session_state.pop(refresh_key, False)

    if force or hour_key not in st.session_state:
        prog = st.progress(0, text="🔍 Step 1 / 3 — Reading your health data...")
        ctx  = _build_command_center_context(patient_id, patient, risk, adherence, trends)

        prog.progress(30, text="⚙️ Step 2 / 3 — Running autonomous checks & actions...")
        actions_log = _run_autonomous_actions(patient_id, ctx)

        prog.progress(60, text="🧠 Step 3 / 3 — Generating your daily intelligence brief...")
        ai_result = _call_command_center_groq(ctx)

        prog.progress(100, text="✅ Command Center ready!")
        prog.empty()

        st.session_state[hour_key] = {
            "ctx":         ctx,
            "actions_log": actions_log,
            "ai_result":   ai_result,
        }

    cached      = st.session_state[hour_key]
    ctx         = cached["ctx"]
    actions_log = cached["actions_log"]
    ai_result   = cached.get("ai_result")

    # ── Refresh button (top-right) ────────────────────────────────────────────
    _, col_btn = st.columns([6, 1])
    with col_btn:
        if st.button("🔄 Refresh", key=f"hcc_refresh_btn_{patient_id}",
                     use_container_width=True):
            for k in list(st.session_state.keys()):
                if k.startswith(f"hcc_{patient_id}"):
                    del st.session_state[k]
            st.session_state[refresh_key] = True
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — MORNING BRIEF
    # ═══════════════════════════════════════════════════════════════════════════
    time_icon = {"morning": "🌅", "afternoon": "☀️", "evening": "🌙"}.get(
        ctx.get("time_of_day", "morning"), "🌅"
    )
    risk_color = {"low": "#34D399", "medium": "#FBBF24", "high": "#F87171"}.get(
        ctx["risk_level"], "#A78BFA"
    )

    briefing_text = (
        ai_result.get("morning_brief", "")
        if ai_result
        else (
            f"Good {ctx['time_of_day']}, {ctx['name'].split()[0]}. "
            f"Your current health trend is <strong>{ctx['trend']}</strong> and your "
            f"risk level is <strong>{ctx['risk_level'].upper()}</strong>. "
            + ("Please complete today's health check-in." if not ctx["checkin_done"] else
               "Today's check-in is complete — keep it up!")
        )
    )

    st.markdown(f"""
    <div class="card" style="border-left:4px solid {risk_color};
         background:rgba(124,58,237,0.07);margin-bottom:1.4rem;padding:1.3rem 1.5rem;">
        <div style="display:flex;align-items:flex-start;gap:1rem;">
            <span style="font-size:2.2rem;line-height:1;">{time_icon}</span>
            <div style="flex:1;">
                <div style="font-weight:700;color:{risk_color};font-size:0.75rem;
                     text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.4rem;">
                    Agent Morning Brief · {ctx['today']} · Risk: {ctx['risk_level'].upper()}
                </div>
                <div style="color:var(--text-primary);font-size:1rem;line-height:1.75;">
                    {briefing_text}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — ACTIVE MISSIONS PANEL
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown(
        '<div style="font-weight:700;color:var(--text-primary);font-size:1rem;'
        'margin-bottom:0.8rem;">📡 Active Agent Missions</div>',
        unsafe_allow_html=True,
    )

    missions = (ai_result or {}).get("missions") or []

    # Fallback missions if Groq failed
    if not missions:
        missions = [
            {"status": "active",    "icon": "🔍", "title": "Risk monitoring",
             "detail": f"Tracking risk score — currently {ctx['risk_score']}/100 ({ctx['risk_level'].upper()})"},
            {"status": "active",    "icon": "💊", "title": "Adherence watch",
             "detail": f"Monitoring {ctx['active_meds']} medication(s) for missed doses"},
            {"status": "watching",  "icon": "📈", "title": "Trend detection",
             "detail": f"14-day health trend is {ctx['trend']}"},
            {"status": "active",    "icon": "🔔", "title": "Alert surveillance",
             "detail": f"{ctx['unresolved_count']} unresolved alert(s) being tracked"},
        ]
        if ctx.get("upcoming_appt"):
            days = ctx.get("days_until_appt")
            missions.append({
                "status": "active", "icon": "📋", "title": "Pre-visit brief",
                "detail": f"Appointment in {days} day(s) — brief auto-generated",
            })

    status_cfg = {
        "active":   {"color": "#34D399", "bg": "rgba(52,211,153,0.12)",  "label": "ACTIVE"},
        "watching": {"color": "#FBBF24", "bg": "rgba(251,191,36,0.12)",  "label": "WATCHING"},
        "complete": {"color": "#60A5FA", "bg": "rgba(96,165,250,0.12)",  "label": "COMPLETE"},
    }

    cols = st.columns(min(len(missions), 3))
    for i, mission in enumerate(missions[:6]):
        col = cols[i % 3]
        s   = mission.get("status", "active")
        cfg = status_cfg.get(s, status_cfg["active"])
        with col:
            st.markdown(f"""
            <div class="card" style="padding:0.9rem 1rem;margin-bottom:0.8rem;
                 border-top:3px solid {cfg['color']};">
                <div style="display:flex;align-items:center;justify-content:space-between;
                     margin-bottom:0.4rem;">
                    <span style="font-size:1.4rem;">{mission.get('icon','🤖')}</span>
                    <span style="font-size:0.67rem;font-weight:700;letter-spacing:0.08em;
                          padding:2px 8px;border-radius:10px;
                          background:{cfg['bg']};color:{cfg['color']};">
                        {cfg['label']}
                    </span>
                </div>
                <div style="font-weight:700;color:var(--text-primary);
                     font-size:0.85rem;margin-bottom:0.3rem;">
                    {mission.get('title','')}
                </div>
                <div style="color:var(--text-muted);font-size:0.78rem;line-height:1.5;">
                    {mission.get('detail','')}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — PRE-VISIT DOCTOR BRIEF (only when appointment ≤ 7 days)
    # ═══════════════════════════════════════════════════════════════════════════
    days      = ctx.get("days_until_appt")
    appt_data = ctx.get("upcoming_appt")
    pvb       = (ai_result or {}).get("pre_visit_brief")

    if appt_data and days is not None and days <= 7 and pvb:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        urgency_color = "#F87171" if days == 0 else "#FBBF24" if days <= 1 else "#A78BFA"
        day_label     = "Today" if days == 0 else "Tomorrow" if days == 1 else f"In {days} days"

        st.markdown(
            f'<div style="font-weight:700;color:var(--text-primary);font-size:1rem;'
            f'margin-bottom:0.8rem;">📋 Pre-Visit Doctor Brief '
            f'<span style="font-size:0.78rem;font-weight:600;'
            f'color:{urgency_color};margin-left:0.5rem;">● Appointment {day_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Headline banner
        st.markdown(f"""
        <div class="card" style="border-left:4px solid {urgency_color};
             background:rgba(167,139,250,0.06);margin-bottom:1rem;padding:1.1rem 1.3rem;">
            <div style="font-size:0.72rem;font-weight:700;color:{urgency_color};
                 text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.3rem;">
                Auto-Generated Brief · {ctx['today']}
            </div>
            <div style="font-size:1rem;font-weight:600;color:var(--text-primary);
                 line-height:1.5;">
                {pvb.get('headline', '')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            # Executive Summary
            st.markdown(f"""
            <div class="card" style="margin-bottom:0.8rem;">
                <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;
                     margin-bottom:0.6rem;">📄 Summary for Dr. {ctx['doctor_name']}</div>
                <div style="color:var(--text-secondary);font-size:0.88rem;line-height:1.7;">
                    {pvb.get('executive_summary', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Medication notes
            med_note = pvb.get("medication_notes", "")
            if med_note:
                st.markdown(f"""
                <div class="card" style="margin-bottom:0.8rem;">
                    <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;
                         margin-bottom:0.5rem;">💊 Medication Notes</div>
                    <div style="color:var(--text-secondary);font-size:0.85rem;line-height:1.6;">
                        {med_note}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_right:
            # Key concerns
            concerns = pvb.get("key_concerns", [])
            if concerns:
                concerns_html = "".join([
                    f'<div style="display:flex;align-items:flex-start;gap:0.5rem;'
                    f'padding:0.35rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
                    f'<span style="color:#F87171;font-size:0.75rem;margin-top:3px;">●</span>'
                    f'<div style="color:var(--text-secondary);font-size:0.84rem;">{c}</div>'
                    f'</div>'
                    for c in concerns
                ])
                st.markdown(f"""
                <div class="card" style="margin-bottom:0.8rem;">
                    <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;
                         margin-bottom:0.5rem;">🩺 Key Concerns to Raise</div>
                    {concerns_html}
                </div>
                """, unsafe_allow_html=True)

            # Suggested questions
            questions = pvb.get("suggested_questions", [])
            if questions:
                q_html = "".join([
                    f'<div style="display:flex;align-items:flex-start;gap:0.5rem;'
                    f'padding:0.35rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
                    f'<span style="color:#A78BFA;font-size:0.8rem;font-weight:700;'
                    f'min-width:18px;">Q{idx+1}</span>'
                    f'<div style="color:var(--text-secondary);font-size:0.84rem;">{q}</div>'
                    f'</div>'
                    for idx, q in enumerate(questions[:4])
                ])
                st.markdown(f"""
                <div class="card">
                    <div style="font-weight:700;color:var(--text-primary);font-size:0.85rem;
                         margin-bottom:0.5rem;">💬 Questions to Ask Your Doctor</div>
                    {q_html}
                </div>
                """, unsafe_allow_html=True)

    elif appt_data and days is not None and days <= 7 and not pvb:
        # Groq failed but appointment is near — show static fallback
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.info(
            f"📋 You have an appointment in {days} day(s). "
            "Pre-visit brief could not be generated — check your Groq API key."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — AUTONOMOUS ACTIONS LOG
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-weight:700;color:var(--text-primary);font-size:1rem;'
        'margin-bottom:0.8rem;">🗂️ Autonomous Actions Log</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="color:var(--text-muted);font-size:0.82rem;margin-top:-0.5rem;'
        'margin-bottom:0.9rem;">Everything the agent did on your behalf this session.</p>',
        unsafe_allow_html=True,
    )

    if not actions_log:
        st.markdown("""
        <div class="card" style="text-align:center;padding:1.5rem;">
            <div style="font-size:2rem;margin-bottom:0.4rem;">✅</div>
            <div style="font-weight:600;color:#34D399;">All checks passed</div>
            <div style="color:var(--text-muted);font-size:0.85rem;margin-top:0.3rem;">
                No autonomous actions were needed this session.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        log_items_html = "".join([
            f'<div style="display:flex;align-items:flex-start;gap:0.75rem;'
            f'padding:0.55rem 0;border-bottom:0.5px solid rgba(255,255,255,0.05);">'
            f'<span style="font-size:1.1rem;line-height:1.4;">{entry["icon"]}</span>'
            f'<div style="flex:1;">'
            f'<div style="color:var(--text-secondary);font-size:0.85rem;line-height:1.5;">'
            f'{entry["text"]}</div>'
            f'</div>'
            f'<span style="font-size:0.73rem;color:var(--text-muted);'
            f'white-space:nowrap;margin-left:0.5rem;">{entry["time"]}</span>'
            f'</div>'
            for entry in actions_log
        ])
        st.markdown(f"""
        <div class="card" style="padding:0.8rem 1.2rem;">
            {log_items_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="color:var(--text-muted);font-size:0.73rem;'
        f'margin-top:1.2rem;text-align:right;">'
        f'Command Center last run: {datetime.now().strftime("%d %b %Y, %I:%M %p")}'
        f'</div>',
        unsafe_allow_html=True,
    )
