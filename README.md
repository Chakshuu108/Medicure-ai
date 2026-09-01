# MediCure — How the system actually works

This document is an **interview-oriented walkthrough of the running product**: the React portal (`frontend/`) talking to the FastAPI API (`backend/`), PostgreSQL tables in `backend/app/models/entities.py`, LangGraph in `backend/app/agents/graph/workflow.py`, and the clinical services that write rows the doctor later reads.

It does not describe how to install the project. It describes **what calls what, when, where data is stored, and how that becomes UI**.

The live doctor/patient portals used in this repo are **not** the Streamlit app. Streamlit (`app.py`, `ui/`, `agents/`, SQLite in `data/database.py`) is a parallel older surface. Everything below is the FastAPI + React path unless a section says otherwise.

---

## 1. System shape (who talks to whom)

```
Browser (React)
  AuthContext  → JWT in localStorage
  pages/*      → api.ts fetch()
       │
       │  Authorization: Bearer <JWT>
       ▼
FastAPI (backend/app/main.py)
  routers: auth, clinical, schedule, admin
  Depends(get_current_user) → decode JWT → load Hospital|Doctor|Receptionist|Patient
  Depends(get_db) → AsyncSession; COMMIT at end of successful request
       │
       ├── LangGraph workflow (chat only)
       ├── services (alerts, MCQ, guardian, OPD, email, meet)
       └── SQLAlchemy models → PostgreSQL
```

There is **no WebSocket and no server push** to the doctor Alerts tab. An alert becomes visible when the doctor (or the layout header) **GETs `/api/alerts`**. Until that request, the row can already exist in `alerts` and the doctor may already have an email, but the tab has not painted it.

On API startup (`lifespan` in `backend/app/main.py`): tables are created, schema patches run, then `start_proactive_scheduler()` starts a background loop that can create guardian/silence alerts **without anyone logged in**.

---

## 2. How a user becomes a “caller” (data entering the system)

### 2.1 Identity

| Role | Login endpoint | Token `sub` | Token `role` |
|------|----------------|-------------|--------------|
| Hospital admin | `POST /api/auth/admin/login` or register | `hospitals.id` | `admin` |
| Doctor | `POST /api/auth/doctor/login` | `doctors.id` | `doctor` |
| Receptionist | `POST /api/auth/receptionist/login` | `receptionists.id` | `receptionist` |
| Patient | `POST /api/auth/patient/login` (`patient_code`) or Google login | `patients.id` | `patient` |

`create_access_token` in `backend/app/core/security.py` encodes JWT (HS256). Every later `api.*` call in `frontend/src/lib/api.ts` attaches that token.

`get_current_user` loads the ORM row and returns `{ role, user, user_id, hospital_id }`. Role gates are `require_roles(...)`.

Patients are **created by receptionist/admin**, not by self-signup in the React portal. `POST /api/admin/patients` writes `patients` with `doctor_id`, `hospital_id`, `patient_code`, demographics, `disease`, vitals, `risk_score` default `0`, `risk_level` default `"low"`.

The patient is permanently tied to **one doctor** via `patients.doctor_id`. That foreign key is how later alerts find the doctor portal.

### 2.2 Frontend routing after login

`frontend/src/App.tsx`: `/patient`, `/doctor`, `/admin`, `/receptionist` behind `ProtectedRoute`. Dashboards are tab UIs (`PatientDashboard`, `DoctorDashboard`, …), not separate URLs per tab.

---

## 3. The complete chat pipeline (patient types a message → reply + possible alert)

This is the main **multi-agent** path. It is the only place LangGraph runs in the React app.

### 3.1 User action

Patient tab **AI Assistant** → `ChatPanel`. On first mount: `GET /api/patient/chat/history` (last 50 `chat_messages` for that patient). On send: `streamChat(message)` in `frontend/src/lib/api.ts`.

### 3.2 HTTP call

`POST /api/patient/chat` with `{ message }` (`backend/app/api/routes/clinical.py`).

The handler does **not** wait and return JSON. It:

1. Builds `AgentEventEmitter` and `AgentWorkflowService(db)`.
2. Subscribes an asyncio queue to the emitter.
3. Starts `service.run_chat(patient_id, message, emitter)` as a background task **on the same request**.
4. Returns `StreamingResponse` (`text/event-stream`): events while the graph runs, then `{ type: chat_result, result }`, then `[DONE]`.

The floating **AI Processing** widget (`AgentActivityPanel`) is fed those SSE events through `AgentActivityContext` (`startActivity` / `addEvent` / `endActivity` in `ChatPanel`).

### 3.3 `AgentWorkflowService.run_chat`

File: `backend/app/services/agent_service.py`.

1. Inserts `agent_runs` row: `workflow_type="chat"`, `status="running"`, `patient_id`, empty `events`.
2. Loads last 20 `chat_messages` into LangChain `HumanMessage` / `AIMessage` list.
3. `build_workflow(db, emitter)` compiles LangGraph (`backend/app/agents/graph/workflow.py`).
4. `workflow.ainvoke(initial_state)` with `user_message`, `patient_id`, flags all false, `workflow_type="chat"`.
5. On success: writes **two** `chat_messages` (user + assistant), optional `agent_memory` (`memory_type="episodic"`), sets `agent_runs.status="completed"`, stores `events` + `result` JSON (`reply`, `triage`, `action_taken`, `agents_run`).
6. Request ends → `get_db` **commits**. Chat, alerts created inside tools, risk updates, bookings from tools — all commit together.

### 3.4 Orchestrator: what runs next

`orchestrator_node` does **keyword routing on the raw user string** (lowercase). Groq is required; if `GROQ_API_KEY` is missing it jumps to synthesizer with a config error.

| Flag / route | Trigger words in the message | First specialist node |
|--------------|------------------------------|------------------------|
| `needs_scheduling` | book, appointment, schedule, slot, cancel, opd | `scheduling_agent` |
| else default | — | `conversation_agent` |
| `needs_risk` | pain, symptom, fever, chest, breath, dizzy, hurt, sick, worse, headache, heart, attack, emergency, stroke, unconscious | (after conversation) `risk_agent` |
| `needs_health` | adherence, missed, medicine, dose, taking, medication, pill, forgot | (after risk, if also set) `health_agent` |
| `needs_alerting` | **same as `needs_risk`** | eventually `alerting_agent` |
| `needs_guardian` | only if `workflow_type == "guardian_check"` | `guardian_agent` |
| `needs_intelligence` | only if `workflow_type == "health_analysis"` | `intelligence_agent` |

The React chat always uses `workflow_type="chat"`. So **Health Guardian node and Health Intelligence node inside LangGraph are not used by the patient chat UI**. Guardian in the product is `guardian_service.run_guardian` (separate function), described later.

Graph edges: every specialist sets `next_agent`, then `route_after_agent` sends them there or to `synthesizer`. Synthesizer → `END`.

Typical **symptom** path:

`orchestrator` → `conversation_agent` → `risk_agent` → (`health_agent` only if med words) → `alerting_agent` if `needs_alerting` → `synthesizer`.

Typical **booking** path:

`orchestrator` → `scheduling_agent` → `synthesizer` (no alerting unless the message also matched risk words).

Greetings (`hi`, `hello`, …) short-circuit inside `conversation_node` to a canned reply and skip tools.

### 3.5 Tools (how agents touch the database)

`create_tools(db, patient_id)` in `backend/app/agents/tools/patient_tools.py` returns this **fixed list** (indexes matter in workflow.py):

| Index | Tool | Reads / writes |
|-------|------|----------------|
| 0 | `get_patient_context` | `patients` |
| 1 | `get_prescriptions` | `prescriptions` + `medicines` |
| 2 | `get_chat_history` | `chat_messages` |
| 3 | `get_active_alerts` | unresolved `alerts` |
| 4 | `search_available_slots` | unbooked `opd_slots` |
| 5 | `book_appointment` | `opd_slots.is_booked`, insert `opd_bookings` |
| 6 | `cancel_appointment` | booking status, slot `is_booked=False` |
| 7 | `create_alert` | `create_clinical_alert(...)` |
| 8 | `update_risk_score` | `patients.risk_score`, `patients.risk_level` |

LLM (Groq `ChatGroq`, model from settings, default `llama-3.3-70b-versatile`) may call tools; `ToolNode` executes them on the **same** `AsyncSession`.

### 3.6 What the user sees

SSE `chat_result.result.reply` is appended as an assistant bubble. History on next visit comes from `chat_messages`, not from `agent_runs`.

---

## 4. Alerts — the interview question in full

**Question:** “When the alert becomes high, how does it go to the Alert tab in the doctor portal?”

**Short accurate answer:** Severity is a **column on an `alerts` row**. Nothing “pushes” high alerts to the tab. The doctor UI **queries** open alerts that belong to that doctor’s patients. High is a display style on that JSON. Email may fire at insert time, independently of the tab.

### 4.1 There is one write path that matters

Almost every doctor-visible alert goes through:

`create_clinical_alert` in `backend/app/services/alert_service.py`.

That function:

1. `normalize_severity`: maps `urgent` / `critical` / `emergency` → `severe`; otherwise `high` / `medium` / `low` / default `medium`.
2. If `alert_type` is in `PATIENT_ONLY_ALERT_TYPES` (`missed_mcq_reminder` only), it will **not** email the doctor (`notify_doctor=False`). That type is also filtered out of GET `/api/alerts` via `is_doctor_facing`.
3. If `doctor_id` is missing, it copies `patient.doctor_id`.
4. **Dedup:** `find_recent_open_alert` looks for an **unresolved** row with same `patient_id` + `alert_type` inside a time window (e.g. `mcq_health_check` 24h, `emergency` 2h, `patient_reported_symptoms` 6h, Guardian pattern 24h). If found, it **does not insert a second row**; it may raise severity and append message text.
5. Else: `db.add(Alert(...))` → table `alerts` (`patient_id`, `doctor_id`, `alert_type`, `message`, `severity`, `resolved=False`, `created_at`).
6. If `notify_doctor` and the doctor has `email`: schedules `send_doctor_clinical_alert_email` (SMTP, not awaited on the HTTP path). Email is **not** how the Alerts tab fills.

`create_alert` tool and `create_chat_symptom_alert` both call this function.

### 4.2 How severity becomes “high” (or severe)

Severity is **chosen by the creator**, then normalized. It is **not** automatically copied from `patients.risk_level`.

| Source | How severity is chosen | `alert_type` |
|--------|------------------------|--------------|
| Chat keyword rules `classify_chat_urgency` | heart/chest/stroke/unconscious… → `severe`; “severe pain” / 911 → `high`; fever/headache/pain/… → `medium` | `emergency` or `patient_reported_symptoms` |
| Chat `TRIAGE_VERDICT: URGENT` fallback in alerting_node | `severe` | `emergency` |
| Alerting LLM tool `create_alert` | whatever the model passes (`low\|medium\|high\|severe`) | whatever the model passes |
| Daily MCQ submit | `medium` if `total_score >= -3`, else **`high`** | `mcq_health_check` |
| Health Guardian `_act` | finding `severity`, bumped to `high` if OPD appointment is within 48 hours | `Health Guardian — Pattern Detected` |
| Silence scan | `high` if silent ≥ 5 days, else `medium` | `Health Guardian — Missed Check-ins` |
| Risk agent | updates **patient** `risk_score` / `risk_level` only; **does not create an alert by itself** | — |

So “when the alert becomes high” in this codebase usually means: **the writer passed `severity="high"`** (or normalized to `high`), and that string is stored on the row. Risk going high on the patient card is a **different field** (`patients.risk_level`), shown on the doctor Patients tab as a badge. It does not insert an `alerts` row unless some other path also calls `create_clinical_alert`.

### 4.3 Chat → alerting_agent → doctor inbox (end-to-end)

User types e.g. “I have chest pain”.

1. Orchestrator sets `needs_risk=True`, `needs_alerting=True`, first node conversation.
2. Conversation may include `TRIAGE_VERDICT: URGENT` in the model text (stripped from the user-facing reply by `_clean_reply_for_user`).
3. Risk agent may call `update_risk_score` → `patients.risk_level` / `risk_score` change (Patients list later shows the badge).
4. `alerting_node`:
   - First: `classify_chat_urgency(user_message)` — **rule-based, no LLM**. If any keyword list matches, `create_chat_symptom_alert` → `create_clinical_alert` with that severity/type.
   - Else if conversation triage was `URGENT`: tool `create_alert` with `emergency` / `severe`.
   - Else: Groq with tools `get_active_alerts` + `create_alert`; may create another row if the model calls the tool.
5. Commit → `alerts` row with `doctor_id = patient.doctor_id`.
6. Optional SMTP to `doctors.email`.
7. **Doctor still sees nothing until fetch.**

Doctor:

1. Opens `/doctor` → `DashboardLayout` `useEffect` → `api.getAlerts()` → header badge count (`alerts.filter(a => !a.resolved).length`).
2. Clicks **Alerts** tab → `DoctorDashboard` `useEffect` when `tab === 'alerts'` → `api.getAlerts()` → `setAlerts` → `<AlertsList role="doctor" />`.

`GET /api/alerts` (`clinical.py`):

1. If role doctor: `collapse_duplicate_open_alerts(db, doctor_id=...)` — unresolved extras with same `(patient_id, alert_type, calendar day)` get `resolved=True`.
2. Query `Alert` **join** `Patient` where `Alert.doctor_id == current doctor` **OR** `Patient.doctor_id == current doctor`.
3. `Alert.resolved == False`, newest first, limit 50.
4. Drop types in `PATIENT_ONLY_ALERT_TYPES`.
5. `serialize_alert`: adds `summary` from `build_alert_summary` (plain-English template + first sentence of `message` + patient name), `severity_label`, `alert_type_label`, `patient_name`.

`AlertsList` renders `summary` (not raw `message` as the title), badge from `severity` (`high`/`severe` → red / `danger`), **Mark done** → `PATCH /api/alerts/{id}/resolve` sets `resolved=True`, then GET again.

That is the entire “how it appears in the Alert tab” mechanism: **shared PostgreSQL row + HTTP GET on tab/header load**.

### 4.4 Patient Alerts tab

Same `GET /api/alerts` with `role=patient` filters `Alert.patient_id == me`, collapse by patient, unresolved only. `AlertsList` without resolve. Copy says the doctor has been notified.

---

## 5. Daily health check (MCQ) — data in, score, alert, UI

### 5.1 Questions

Patient **Health Check** tab: `GET /api/mcq/today` → `generate_today_mcqs`.

- If `mcq_sets` already has a row for `(patient_id, today’s date)` → return cached questions.
- Else: latest prescription med names, last 3 `mcq_responses` as context, Groq JSON of 5 questions or `_fallback_mcqs`, insert `mcq_sets`.

### 5.2 Submit

`POST /api/mcq/submit` with option indexes.

1. Reject if `mcq_responses` already exists for today.
2. Recompute `total_score` from stored questions (`compute_total_score`).
3. `compute_status`: score `> 0` Improving, `== 0` Stable, `< 0` **Worsening**.
4. Insert `mcq_responses` (JSON answers, score, status, adherence, side effects).
5. **If `total_score < 0` or status Worsening:** `create_clinical_alert` type `mcq_health_check`. Severity **high** when score `< -3`, else medium. Message includes status, score, adherence. Patient worsening email is fire-and-forget if `patient.email` is set.
6. **Does not** call `run_guardian` on submit (Guardian is not blocking this request).
7. Response JSON: score, status, `get_feedback(status)` for the green/yellow/red card on the patient page.

Doctor Alerts tab: same GET as above; summary template for this type is *“Daily health check showed a concerning result.”* plus the first sentence of the stored message.

Trends: `GET /api/mcq/trends` fills missing calendar days as `missed: true` in a points array (used by charts / Guardian).

---

## 6. Health Guardian (the service, not the LangGraph node)

### 6.1 When it runs

| Trigger | Call | `force` |
|---------|------|---------|
| Patient login session | `POST /api/patient/session-init` → `run_guardian(..., force=False)` | cached if an `agent_runs` row for `guardian_daily` already completed **today** |
| Care Autopilot / Guardian tab load | `GET /api/patient/care-autopilot` → `run_guardian(force=False)` | same cache |
| Patient “scan now” | `POST /api/patient/guardian-check?force=true` | always recomputes |
| Background scheduler | every `max(3600, guardian_scan_interval_hours * 3600)` seconds (default 24h), after `guardian_startup_delay_seconds` (default 60s) | `run_proactive_scan_all` → per patient `run_guardian(..., workflow_type="guardian_proactive", force=False)` |

Cache: `_get_cached_today` reads latest completed `agent_runs` for that `workflow_type` whose `started_at.date() == today`.

### 6.2 Perceive → reason → act

`run_guardian` in `backend/app/services/guardian_service.py`:

1. `_perceive`: last 30 MCQ responses, last 50 alerts, prescriptions, bookings, day-of-week score buckets, missed-med dates from `adherence_status` text, `already_flagged` = first 60 chars of existing Guardian alerts, days since last check-in, risk fields.
2. `_reason`: Groq JSON findings (`action`: `alert_doctor` | `flag_in_brief` | `monitor` | `none`, `severity`).
3. `_act`: collects `alert_doctor` findings with severity medium/high/severe; **one** combined `create_clinical_alert` (`Health Guardian — Pattern Detected`) unless title already in `already_flagged`. Appointment within 48h forces severity `high`.
4. Stores full payload on `agent_runs.result`.
5. Patient UI (`HealthGuardianPanel`) reads that JSON (findings, trends, `alerts_sent`).

### 6.3 Silence (no login)

`proactive_monitor_service._handle_silence_alert`: if `days_silent >= guardian_silence_alert_days` (default 2) and not already flagged in `agent_memory` (`proactive_silence_alert` + today’s date), creates Missed Check-ins alert and optional patient nudge email.

Missed MCQ **reminders** (`reminder_service.process_missed_mcq_reminders`) email the **patient** and optional Google Calendar; they are **not** doctor alerts (`missed_mcq_reminder` is patient-only if ever used as alert type). Session-init shows a banner from `missed_dates`.

---

## 7. Prescriptions and medication schedule

Doctor **Prescriptions** tab: `POST /api/prescriptions` inserts `prescriptions` + `medicines`, and if diagnosis is set, writes `patients.disease`.

Patient **Schedule & Prescriptions**: `GET /api/prescriptions/patient/{id}`. Patient sets `start_date` / `start_time` via `PATCH /api/patient/medicines/{id}/schedule` (`schedule.py`). `get_schedule_preview` expands dose times for the Care Autopilot / schedule UI. Optional `POST /api/patient/schedule/sync-calendar` uses stored Google refresh token.

MCQ generation and Guardian perceive **read** these medicines; they do not write prescriptions.

---

## 8. OPD booking, video room, transcript, summary

### 8.1 Slots

Doctor **OPD Management**: `POST /api/opd/slots` creates **5** consecutive 10-minute `opd_slots` for that doctor/date.

Room name is **not stored**. `slot_room_name(slot_id)` in `meet_service.py` is `MediCure-` + first 20 hex chars of the slot UUID without dashes. Doctor and patient compute the **same string** from the same slot id.

### 8.2 Book

Patient OPD tab or scheduling agent: `POST /api/opd/book`. `ensure_patient_can_book` enforces **one active booking**. Writes `opd_bookings`, sets `opd_slots.is_booked=True`. Booking confirmation email if patient email is set.

Chat booking uses the same tables via `book_appointment` or `smart_book_from_context` in `opd_booking_service`.

### 8.3 Call and speech

`VideoCallPanel`: Join requests mic then **stops tracks**, starts **browser SpeechRecognition in the parent page**, embeds Jitsi External API (anonymous hosts such as `meet.ffmuc.net`, not `meet.jit.si` moderator login). Each final phrase: `POST /api/opd/transcript-line` → `meet_transcript_lines`. Poll `GET /api/opd/transcript/{booking_id}` so the other party’s lines can appear.

End call: local + remote lines into a textarea. Generate: `POST /api/opd/meet-summary` with transcript (or DB lines if body too short). `generate_meet_summary` calls Groq, upserts `meet_summaries`, deletes transcript lines.

Both portals **Consultation Summaries** tab: `GET /api/opd/meet-summaries` filtered by `patient_id` or `doctor_id` on `meet_summaries`.

---

## 9. How processed data is shown (read path cheat sheet)

| UI | When it loads | API | Tables |
|----|---------------|-----|--------|
| Header alert badge | every dashboard mount | `GET /api/alerts` | `alerts` |
| Doctor Alerts tab | `tab === 'alerts'` | same | `alerts` + patient names |
| Doctor Patients | mount + after Rx | `GET /api/patients` | `patients` (`risk_level` badge) |
| Chat history | ChatPanel mount | `GET /api/patient/chat/history` | `chat_messages` |
| Chat reply | send | SSE `POST /api/patient/chat` | writes chat + maybe alerts + maybe risk + maybe bookings |
| Health check form | health tab | `GET /api/mcq/today` | `mcq_sets` |
| Health check result | submit | `POST /api/mcq/submit` | `mcq_responses` + maybe `alerts` |
| Trend chart | health tab / session-init | `GET /api/mcq/trends` | `mcq_responses` |
| Guardian panel | guardian tab | `GET /api/patient/care-autopilot` | `agent_runs`, MCQ, alerts, bookings |
| OPD lists | opd tab | slots/bookings endpoints | `opd_slots`, `opd_bookings` |
| Summaries | summaries tab | `GET /api/opd/meet-summaries` | `meet_summaries` |

Doctor Patients list **does not** subscribe to alerts. Risk badge updates only after a request that wrote `patients.risk_*` (typically risk agent during symptom chat) and a **refetch** of `/api/patients`.

---

## 10. Interview-style questions and answers (from this codebase)

### “Walk me through a patient saying they have a headache until the doctor sees it.”

1. `ChatPanel.send` → `POST /api/patient/chat` SSE.  
2. Orchestrator: “headache” ∈ `needs_risk` ⇒ `needs_alerting`. Conversation Groq (+ tools if needed).  
3. Risk agent may `update_risk_score`.  
4. Alerting: `classify_chat_urgency` matches `"headache"` in the mild/medium keyword tuple → `create_chat_symptom_alert` → `alerts` row type `patient_reported_symptoms`, severity `medium` (unless a stronger rule matched first — first matching rule wins, heart/chest is earlier in the list).  
5. Commit. Optional doctor email.  
6. Doctor opens Alerts or already had layout fetch: `GET /api/alerts` join on `patients.doctor_id` → `AlertsList` card with `build_alert_summary` (“Patient reported symptoms…”).

### “If risk is high, is that the same as a high alert?”

No. `patients.risk_level` is updated by `update_risk_score`. `alerts.severity` is set only when `create_clinical_alert` runs. A patient can be high-risk on the Patients tab with **zero** open alerts, or have a high MCQ alert while risk_level is still `low`.

### “How does high MCQ score-alert get to the doctor?”

Submit computes score. If Worsening and score `< -3`, `severity="high"`, type `mcq_health_check`. Same GET `/api/alerts` as chat. UI badge uses `LEVEL_STYLES.high = 'danger'`.

### “Is the doctor notified in real time?”

Email can go out immediately (async task). The Alerts **tab** updates on **next GET** (navigation, refresh, switching to Alerts). No live channel.

### “Who is the alerting agent?”

In chat: LangGraph node `alerting_node`. For MCQ/Guardian/silence: **no** LangGraph node; Python services call `create_clinical_alert` directly.

### “Where is conversation memory?”

Short-term: last 20 messages loaded into the graph. Persisted: `chat_messages`. Episodic snippet: `agent_memory`. Tool `get_chat_history` can re-read DB during a turn.

### “What does the synthesizer do?”

Picks `final_reply` already set by a specialist, or last AIMessage. Strips `TRIAGE_VERDICT`. Emits `final_response` SSE. Does not write alerts.

### “Can two agents create two alerts for one message?”

Yes in principle: keyword path creates one; if that path did not fire, the LLM tool path may. Dedup collapses **same type** in the time window. Different types (e.g. emergency vs guardian) can coexist until daily collapse on GET.

### “What is LangGraph vs Guardian service?”

LangGraph = chat (and unused-from-UI `workflow_type` guardian_check / health_analysis on `AgentWorkflowService`). Production Guardian UI = `run_guardian` perceive/reason/act + `agent_runs` with `guardian_daily` / `guardian_proactive`.

### “How are agent events shown without blocking the reply?”

Same HTTP response: SSE multiplex. Workflow task runs concurrently with the event loop that `yield`s queue items. Frontend `streamChat` parses `data: ` lines until `chat_result`.

---

## 11. Persistence map (tables the portal actually uses)

Defined in `backend/app/models/entities.py`:

`hospitals`, `doctors`, `receptionists`, `patients`, `prescriptions`, `medicines`, `chat_messages`, `alerts`, `mcq_sets`, `mcq_responses`, `opd_slots`, `opd_bookings`, `meet_summaries`, `meet_transcript_lines`, `agent_runs`, `agent_memory`.

Commit boundary: `get_db` in `backend/app/database.py` commits if the request handler returns without exception.

---

## 12. One diagram: action → write → doctor Alert tab

```
Patient UI action
    │
    ├─ Chat (symptoms) ─► POST /api/patient/chat
    │                         LangGraph alerting_node
    │                         classify_chat_urgency and/or create_alert tool
    │
    ├─ MCQ submit (worsening) ─► POST /api/mcq/submit
    │                         create_clinical_alert(mcq_health_check, high|medium)
    │
    ├─ Guardian scan ─► run_guardian._act
    │                         create_clinical_alert(Pattern Detected)
    │
    └─ Scheduler / silence ─► _handle_silence_alert
                              create_clinical_alert(Missed Check-ins)
            │
            ▼
    create_clinical_alert → INSERT/UPDATE alerts
            │                 optional SMTP to doctors.email
            ▼
    PostgreSQL  (patient_id, doctor_id, severity, alert_type, resolved=false)
            │
            │  later, independent HTTP
            ▼
    Doctor: GET /api/alerts
            collapse duplicates, unresolved only, serialize summary
            ▼
    DoctorDashboard Alerts tab + header badge
            ▼
    PATCH /api/alerts/{id}/resolve  → resolved=true  → disappears from list
```

That is the complete implemented workflow from user action to the doctor Alert tab.
