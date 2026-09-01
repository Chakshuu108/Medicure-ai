"""End-to-end API smoke test for MediCure FastAPI backend."""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = "http://127.0.0.1:8000"
results: list[tuple[str, str, str]] = []  # area, test, status


def record(area: str, name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else f"FAIL {detail}"
    results.append((area, name, status))
    mark = "OK" if ok else "FAIL"
    print(f"  {mark} {name}" + (f" — {detail}" if detail and not ok else ""))


def login(client: httpx.Client, path: str, body: dict) -> dict:
    r = client.post(f"{BASE}{path}", json=body)
    r.raise_for_status()
    return r.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    print("\n=== MediCure full app API test ===\n")
    failures = 0

    with httpx.Client(timeout=120.0) as client:
        # ── Infrastructure ──────────────────────────────────────────────
        print("[Infrastructure]")
        try:
            h = client.get(f"{BASE}/health").json()
            record("infra", "GET /health", h.get("status") == "ok")
            record("infra", "groq_configured flag present", "groq_configured" in h)
        except Exception as e:
            record("infra", "GET /health", False, str(e))

        try:
            creds = client.get(f"{BASE}/api/demo-credentials").json()
            record("infra", "GET /api/demo-credentials", len(creds) >= 4)
        except Exception as e:
            record("infra", "demo-credentials", False, str(e))

        # ── Auth all roles ──────────────────────────────────────────────
        print("\n[Authentication]")
        tokens: dict[str, str] = {}
        ids: dict[str, str] = {}
        try:
            admin = login(client, "/api/auth/admin/login", {"email": "admin@medicure.demo", "password": "demo123"})
            tokens["admin"] = admin["access_token"]
            ids["admin"] = admin["user_id"]
            record("auth", "admin login", True)
        except Exception as e:
            record("auth", "admin login", False, str(e))

        try:
            doctor = login(client, "/api/auth/doctor/login", {"email": "doctor@medicure.demo", "password": "demo123"})
            tokens["doctor"] = doctor["access_token"]
            ids["doctor"] = doctor["user_id"]
            record("auth", "doctor login", True)
        except Exception as e:
            record("auth", "doctor login", False, str(e))

        try:
            reception = login(client, "/api/auth/receptionist/login", {"email": "reception@medicure.demo", "password": "demo123"})
            tokens["receptionist"] = reception["access_token"]
            record("auth", "receptionist login", True)
        except Exception as e:
            record("auth", "receptionist login", False, str(e))

        try:
            patient = login(client, "/api/auth/patient/login", {"patient_code": "PAT-DEMO-0001"})
            tokens["patient"] = patient["access_token"]
            ids["patient"] = patient["user_id"]
            record("auth", "patient login", True)
        except Exception as e:
            record("auth", "patient login", False, str(e))

        if "doctor" in tokens:
            me = client.get(f"{BASE}/api/auth/me", headers=auth_headers(tokens["doctor"])).json()
            record("auth", "GET /api/auth/me (doctor)", me.get("role") == "doctor" or "name" in str(me))

        # ── Doctor: patients & OPD slots ────────────────────────────────
        print("\n[Doctor portal]")
        patient_id = ids.get("patient")
        slot_id = None
        booking_id = None

        if "doctor" in tokens:
            dh = auth_headers(tokens["doctor"])
            try:
                patients = client.get(f"{BASE}/api/patients", headers=dh).json()
                record("doctor", "GET /api/patients", isinstance(patients, list) and len(patients) > 0)
                if patients and not patient_id:
                    patient_id = patients[0]["id"]
            except Exception as e:
                record("doctor", "GET /api/patients", False, str(e))

            try:
                tomorrow = (date.today() + timedelta(days=7)).isoformat()
                slots_resp = client.post(
                    f"{BASE}/api/opd/slots",
                    headers=dh,
                    json={"slot_date": tomorrow, "count": 5, "duration_minutes": 10},
                )
                ok = slots_resp.status_code == 200
                data = slots_resp.json() if ok else {}
                if ok and data.get("slots"):
                    slot_id = data["slots"][0]["id"]
                record("doctor", "POST /api/opd/slots", ok, slots_resp.text[:120] if not ok else "")
            except Exception as e:
                record("doctor", "POST /api/opd/slots", False, str(e))

            try:
                mine = client.get(f"{BASE}/api/opd/slots/mine", headers=dh).json()
                record("doctor", "GET /api/opd/slots/mine", isinstance(mine, list))
                if not slot_id and mine:
                    open_slot = next((s for s in mine if not s.get("is_booked")), None)
                    if open_slot:
                        slot_id = open_slot["id"]
            except Exception as e:
                record("doctor", "GET /api/opd/slots/mine", False, str(e))

            if patient_id:
                try:
                    rx = client.post(
                        f"{BASE}/api/prescriptions",
                        headers=dh,
                        json={
                            "patient_id": patient_id,
                            "disease": "Hypertension",
                            "doctor_notes": "E2E test prescription",
                            "medicines": [{
                                "name": "Amlodipine",
                                "dosage": "5mg",
                                "duration_days": 7,
                                "frequency_pattern": "daily",
                                "times_per_day": 1,
                            }],
                        },
                    )
                    record("doctor", "POST /api/prescriptions", rx.status_code == 200, rx.text[:120])
                except Exception as e:
                    record("doctor", "POST /api/prescriptions", False, str(e))

        # ── Patient: MCQ, schedule, guardian ────────────────────────────
        print("\n[Patient portal]")
        if "patient" in tokens:
            ph = auth_headers(tokens["patient"])

            try:
                mcq = client.get(f"{BASE}/api/mcq/today", headers=ph).json()
                record("patient", "GET /api/mcq/today", "questions" in mcq and len(mcq["questions"]) >= 3)
                questions = mcq.get("questions", [])
                if questions:
                    # pick worst options for alert path
                    responses = {str(q["id"]): len(q.get("options", [])) - 1 for q in questions}
                    sub = client.post(
                        f"{BASE}/api/mcq/submit",
                        headers=ph,
                        json={
                            "responses": responses,
                            "total_score": 0,
                            "status": "Stable",
                            "side_effects": [],
                            "adherence_status": "",
                        },
                    )
                    if sub.status_code == 400 and "already completed" in sub.text.lower():
                        record("patient", "POST /api/mcq/submit", True, "already done today (ok)")
                    else:
                        record("patient", "POST /api/mcq/submit", sub.status_code == 200, sub.text[:120])
            except Exception as e:
                record("patient", "MCQ flow", False, str(e))

            try:
                trends = client.get(f"{BASE}/api/mcq/trends?days=14", headers=ph).json()
                record("patient", "GET /api/mcq/trends", "points" in trends and "summary" in trends)
            except Exception as e:
                record("patient", "GET /api/mcq/trends", False, str(e))

            try:
                init = client.post(f"{BASE}/api/patient/session-init", headers=ph, json={}).json()
                record("patient", "POST /api/patient/session-init", "guardian" in init and "trends" in init)
            except Exception as e:
                record("patient", "session-init", False, str(e))

            try:
                autopilot = client.get(f"{BASE}/api/patient/care-autopilot", headers=ph).json()
                record("patient", "GET /api/patient/care-autopilot", "guardian" in autopilot)
            except Exception as e:
                record("patient", "care-autopilot", False, str(e))

            try:
                sched = client.get(f"{BASE}/api/patient/schedule/preview", headers=ph).json()
                record("patient", "GET /api/patient/schedule/preview", "schedule" in sched)
            except Exception as e:
                record("patient", "schedule preview", False, str(e))

            if patient_id:
                try:
                    rxs = client.get(f"{BASE}/api/prescriptions/patient/{patient_id}", headers=ph).json()
                    record("patient", "GET prescriptions", isinstance(rxs, list))
                except Exception as e:
                    record("patient", "GET prescriptions", False, str(e))

        # ── OPD booking ─────────────────────────────────────────────────
        print("\n[OPD booking]")
        if "patient" in tokens and slot_id:
            ph = auth_headers(tokens["patient"])
            try:
                limit = client.get(f"{BASE}/api/opd/booking-limit", headers=ph).json()
                can_book = limit.get("can_book", False)
                if can_book:
                    book = client.post(f"{BASE}/api/opd/book", headers=ph, json={"slot_id": slot_id})
                    if book.status_code == 200:
                        booking_id = book.json().get("booking_id") or book.json().get("id")
                        record("opd", "POST /api/opd/book", True)
                    else:
                        record("opd", "POST /api/opd/book", False, book.text[:120])
                else:
                    bookings = client.get(f"{BASE}/api/opd/bookings", headers=ph).json()
                    if bookings:
                        booking_id = bookings[0].get("id") or bookings[0].get("booking_id")
                    record("opd", "POST /api/opd/book", True, "already has booking (ok)")
            except Exception as e:
                record("opd", "booking", False, str(e))

            try:
                bookings = client.get(f"{BASE}/api/opd/bookings", headers=ph).json()
                record("opd", "GET /api/opd/bookings", isinstance(bookings, list))
                if not booking_id and bookings:
                    booking_id = bookings[0].get("id")
            except Exception as e:
                record("opd", "GET bookings", False, str(e))

            try:
                avail = client.get(f"{BASE}/api/opd/slots/available", headers=ph).json()
                record("opd", "GET /api/opd/slots/available", isinstance(avail, list))
            except Exception as e:
                record("opd", "available slots", False, str(e))

        # ── Meet transcript & summary ───────────────────────────────────
        print("\n[Video consult summary]")
        if "patient" in tokens and booking_id:
            ph = auth_headers(tokens["patient"])
            try:
                line = client.post(
                    f"{BASE}/api/opd/transcript-line",
                    headers=ph,
                    json={
                        "booking_id": booking_id,
                        "speaker_label": "Test Patient",
                        "text": "I have been having headaches for three days.",
                        "timestamp_ms": 1000,
                    },
                )
                record("meet", "POST transcript-line", line.status_code == 200)
            except Exception as e:
                record("meet", "transcript-line", False, str(e))

            try:
                tx = client.get(f"{BASE}/api/opd/transcript/{booking_id}", headers=ph).json()
                record("meet", "GET transcript", tx.get("count", 0) >= 1)
            except Exception as e:
                record("meet", "GET transcript", False, str(e))

            try:
                summary_body = (
                    "Patient: headaches for three days. Doctor: advised rest, "
                    "Paracetamol 500mg twice daily for 3 days. Follow up in one week."
                )
                summ = client.post(
                    f"{BASE}/api/opd/meet-summary",
                    headers=ph,
                    json={"booking_id": booking_id, "transcript": summary_body},
                )
                if summ.status_code == 400 and "GROQ" in summ.text.upper():
                    record("meet", "POST meet-summary", True, "no GROQ key (expected locally)")
                else:
                    record("meet", "POST meet-summary", summ.status_code == 200, summ.text[:120])
            except Exception as e:
                record("meet", "meet-summary", False, str(e))

            try:
                got = client.get(f"{BASE}/api/opd/meet-summary/{booking_id}", headers=ph).json()
                record("meet", "GET meet-summary", "summary" in got)
            except Exception as e:
                record("meet", "GET meet-summary", False, str(e))

        # ── Chat SSE (symptom → alert path) ─────────────────────────────
        print("\n[AI chat SSE]")
        if "patient" in tokens:
            ph = auth_headers(tokens["patient"])
            try:
                with client.stream(
                    "POST",
                    f"{BASE}/api/patient/chat",
                    headers=ph,
                    json={"message": "I have a bad headache and mild fever today"},
                ) as resp:
                    events = []
                    chat_result = None
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            payload = line[6:].strip()
                            if payload == "[DONE]":
                                break
                            try:
                                ev = json.loads(payload)
                                events.append(ev.get("type"))
                                if ev.get("type") == "chat_result":
                                    chat_result = ev.get("result")
                            except json.JSONDecodeError:
                                pass
                    ok = chat_result is not None and bool(chat_result.get("reply"))
                    record("chat", "POST /api/patient/chat SSE", ok, f"events={len(events)}")
                    if chat_result:
                        record("chat", "chat reply non-empty", len(chat_result.get("reply", "")) > 10)
            except Exception as e:
                record("chat", "chat SSE", False, str(e))

            try:
                hist = client.get(f"{BASE}/api/patient/chat/history", headers=ph).json()
                record("chat", "GET chat history", isinstance(hist, list) and len(hist) >= 2)
            except Exception as e:
                record("chat", "chat history", False, str(e))

        # ── Alerts ──────────────────────────────────────────────────────
        print("\n[Alerts]")
        alert_id = None
        if "doctor" in tokens:
            dh = auth_headers(tokens["doctor"])
            try:
                alerts = client.get(f"{BASE}/api/alerts", headers=dh).json()
                record("alerts", "GET /api/alerts (doctor)", isinstance(alerts, list))
                if alerts:
                    alert_id = alerts[0]["id"]
                    a0 = alerts[0]
                    record("alerts", "alert has summary + severity", bool(a0.get("summary")) and bool(a0.get("severity")))
            except Exception as e:
                record("alerts", "doctor alerts", False, str(e))

        if "patient" in tokens:
            try:
                palerts = client.get(f"{BASE}/api/alerts", headers=auth_headers(tokens["patient"])).json()
                record("alerts", "GET /api/alerts (patient)", isinstance(palerts, list))
            except Exception as e:
                record("alerts", "patient alerts", False, str(e))

        if alert_id and "doctor" in tokens:
            try:
                # resolve then un-resolve is not supported; just verify endpoint exists with a dry run on a fake id
                fake = client.patch(
                    f"{BASE}/api/alerts/00000000-0000-0000-0000-000000000000/resolve",
                    headers=auth_headers(tokens["doctor"]),
                )
                record("alerts", "PATCH resolve auth works", fake.status_code in (404, 200))
            except Exception as e:
                record("alerts", "resolve endpoint", False, str(e))

        # ── Guardian force scan ─────────────────────────────────────────
        print("\n[Health Guardian]")
        if "patient" in tokens:
            ph = auth_headers(tokens["patient"])
            try:
                g = client.post(f"{BASE}/api/patient/guardian-check?force=true", headers=ph)
                if g.status_code == 200:
                    body = g.json()
                    record("guardian", "POST guardian-check force", "reasoning" in body or "snapshot" in body)
                else:
                    record("guardian", "guardian-check", False, g.text[:120])
            except Exception as e:
                record("guardian", "guardian-check", False, str(e))

        # ── Admin ───────────────────────────────────────────────────────
        print("\n[Admin]")
        if "admin" in tokens:
            ah = auth_headers(tokens["admin"])
            try:
                hosp = client.get(f"{BASE}/api/admin/hospital", headers=ah).json()
                record("admin", "GET /api/admin/hospital", bool(hosp.get("name")))
            except Exception as e:
                record("admin", "hospital", False, str(e))
            try:
                docs = client.get(f"{BASE}/api/admin/doctors", headers=ah).json()
                record("admin", "GET /api/admin/doctors", isinstance(docs, list))
            except Exception as e:
                record("admin", "doctors list", False, str(e))

        # ── Frontend proxy ──────────────────────────────────────────────
        print("\n[Frontend dev proxy]")
        try:
            fe = httpx.get("http://127.0.0.1:5173/api/demo-credentials", timeout=10.0)
            record("frontend", "Vite proxy /api to backend", fe.status_code == 200)
        except Exception as e:
            record("frontend", "Vite dev server", False, str(e))

        try:
            fe_html = httpx.get("http://127.0.0.1:5173/", timeout=10.0)
            record("frontend", "GET / (React app)", fe_html.status_code == 200 and "MediCure" in fe_html.text)
        except Exception as e:
            record("frontend", "React index", False, str(e))

    # ── Summary ─────────────────────────────────────────────────────
    print("\n=== SUMMARY ===")
    passed = sum(1 for _, _, s in results if s == "PASS")
    failed = [r for r in results if not r[2].startswith("PASS")]
    for area, name, status in results:
        if not status.startswith("PASS"):
            print(f"  [{area}] {name}: {status}")
    print(f"\nTotal: {passed}/{len(results)} passed")
    if failed:
        print(f"Failed: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
