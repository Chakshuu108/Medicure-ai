# import requests
# from datetime import datetime, date, timedelta
# from data.database import get_patient, get_patient_prescriptions
# from core.config import GOOGLE_CALENDAR_API_KEY

# TIMING_MAP = {
#     "morning": "08:00",
#     "afternoon": "13:00",
#     "evening": "18:00",
#     "night": "21:00",
#     "before bed": "22:00",
#     "twice daily": "08:00",
#     "thrice daily": "08:00",
#     "with meals": "08:00",
#     "empty stomach": "07:00",
# }

# class SchedulingAgent:
#     def __init__(self):
#         self.calendar_base = "https://www.googleapis.com/calendar/v3"
#         self.api_key = GOOGLE_CALENDAR_API_KEY

#     def _parse_timing(self, timing_str):
#         timing_lower = timing_str.lower()
#         for key, val in TIMING_MAP.items():
#             if key in timing_lower:
#                 return val
#         return "08:00"

#     def _build_events(self, medicine, patient_name):
#         events = []
#         start_date = datetime.fromisoformat(medicine["start_date"]).date() if medicine.get("start_date") else date.today()
#         duration = int(medicine.get("duration_days", 7))
#         timing = self._parse_timing(medicine.get("timing", "morning"))
        
#         is_twice = "twice" in medicine.get("timing", "").lower()
#         is_thrice = "thrice" in medicine.get("timing", "").lower() or "3 times" in medicine.get("timing", "").lower()
        
#         dose_times = [timing]
#         if is_twice:
#             dose_times = ["08:00", "20:00"]
#         elif is_thrice:
#             dose_times = ["08:00", "14:00", "20:00"]
        
#         for day_offset in range(duration):
#             current_date = start_date + timedelta(days=day_offset)
#             for t in dose_times:
#                 hour, minute = map(int, t.split(":"))
#                 start_dt = datetime(current_date.year, current_date.month, current_date.day, hour, minute)
#                 end_dt = start_dt + timedelta(minutes=15)
#                 events.append({
#                     "summary": f"💊 {medicine['name']} - {medicine['dosage']}",
#                     "description": f"Medication for {patient_name}\nTiming: {medicine['timing']}\nDosage: {medicine['dosage']}",
#                     "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
#                     "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
#                     "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]}
#                 })
#         return events

#     def schedule_for_patient(self, patient_id, calendar_id="primary"):
#         patient = get_patient(patient_id)
#         if not patient:
#             return {"success": False, "message": "Patient not found", "events_created": 0}
        
#         prescriptions = get_patient_prescriptions(patient_id)
#         if not prescriptions:
#             return {"success": False, "message": "No prescriptions found", "events_created": 0}
        
#         all_events = []
#         for prescription in prescriptions[:1]:
#             for medicine in prescription.get("medicines", []):
#                 events = self._build_events(medicine, patient["name"])
#                 all_events.extend(events[:7])
        
#         created = 0
#         errors = []
        
#         for event in all_events:
#             try:
#                 url = f"{self.calendar_base}/calendars/{calendar_id}/events?key={self.api_key}"
#                 response = requests.post(url, json=event, headers={"Content-Type": "application/json"})
#                 if response.status_code in [200, 201]:
#                     created += 1
#                 else:
#                     errors.append(response.json().get("error", {}).get("message", "Unknown error"))
#             except Exception as e:
#                 errors.append(str(e))
        
#         if created > 0:
#             return {"success": True, "message": f"Created {created} calendar events", "events_created": created}
#         else:
#             sample_events = [{"date": e["start"]["dateTime"][:10], "time": e["start"]["dateTime"][11:16], "medicine": e["summary"]} for e in all_events[:5]]
#             return {
#                 "success": False,
#                 "message": f"Calendar API not authorized (key may need OAuth). Showing schedule preview.",
#                 "events_created": 0,
#                 "preview": sample_events,
#                 "errors": errors[:3]
#             }

#     def get_schedule_preview(self, patient_id):
#         patient = get_patient(patient_id)
#         prescriptions = get_patient_prescriptions(patient_id)
#         if not prescriptions or not patient:
#             return []
        
#         schedule = []
#         for prescription in prescriptions[:1]:
#             for medicine in prescription.get("medicines", []):
#                 events = self._build_events(medicine, patient["name"])
#                 for e in events[:14]:
#                     schedule.append({
#                         "date": e["start"]["dateTime"][:10],
#                         "time": e["start"]["dateTime"][11:16],
#                         "medicine": medicine["name"],
#                         "dosage": medicine["dosage"],
#                         "timing": medicine["timing"]
#                     })
        
#         schedule.sort(key=lambda x: (x["date"], x["time"]))
#         return schedule



import requests
from datetime import datetime, date, timedelta
from data.database import get_patient, get_patient_prescriptions
from core.config import (
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_TOKEN_URI,
    GOOGLE_REDIRECT_URI,
    GOOGLE_AUTH_URI,
    GOOGLE_SCOPES,
)

TIMING_MAP = {
    "morning": "08:00",
    "afternoon": "13:00",
    "evening": "18:00",
    "night": "21:00",
    "before bed": "22:00",
    "twice daily": "08:00",
    "thrice daily": "08:00",
    "with meals": "08:00",
    "empty stomach": "07:00",
}

CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"


def get_auth_url():
    """Return the Google OAuth2 consent URL the user must visit."""
    import streamlit as st
    from urllib.parse import urlencode

    # Read directly from st.secrets as fallback in case config.py BOM stripping fails
    try:
        client_id = st.secrets["GOOGLE_OAUTH_CLIENT_ID"].strip()
    except Exception:
        client_id = GOOGLE_OAUTH_CLIENT_ID

    try:
        redirect_uri = st.secrets["GOOGLE_REDIRECT_URI"].strip()
    except Exception:
        redirect_uri = GOOGLE_REDIRECT_URI

    try:
        scopes = st.secrets["GOOGLE_SCOPES"].strip()
    except Exception:
        scopes = GOOGLE_SCOPES

    try:
        auth_uri = st.secrets["GOOGLE_AUTH_URI"].strip()
    except Exception:
        auth_uri = GOOGLE_AUTH_URI

    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "access_type": "offline",
        "prompt": "consent",
    })
    return f"{auth_uri}?{params}"


def exchange_code_for_tokens(auth_code: str) -> dict:
    """Exchange the one-time auth code for access + refresh tokens."""
    resp = requests.post(GOOGLE_TOKEN_URI, data={
        "code": auth_code,
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    })
    return resp.json()


def refresh_access_token(refresh_token: str):
    """Use refresh token to get a new access token silently."""
    resp = requests.post(GOOGLE_TOKEN_URI, data={
        "refresh_token": refresh_token,
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
        "grant_type": "refresh_token",
    })
    return resp.json().get("access_token")


class SchedulingAgent:
    def __init__(self):
        pass

    def _parse_timing(self, timing_str):
        timing_lower = timing_str.lower()
        for key, val in TIMING_MAP.items():
            if key in timing_lower:
                return val
        return "08:00"

    def _build_events(self, medicine, patient_name):
        events = []
        start_date = datetime.fromisoformat(medicine["start_date"]).date() if medicine.get("start_date") else date.today()
        duration = int(medicine.get("duration_days", 7))
        timing = self._parse_timing(medicine.get("timing", "morning"))

        is_twice = "twice" in medicine.get("timing", "").lower()
        is_thrice = "thrice" in medicine.get("timing", "").lower() or "3 times" in medicine.get("timing", "").lower()

        dose_times = [timing]
        if is_twice:
            dose_times = ["08:00", "20:00"]
        elif is_thrice:
            dose_times = ["08:00", "14:00", "20:00"]

        for day_offset in range(duration):
            current_date = start_date + timedelta(days=day_offset)
            for t in dose_times:
                hour, minute = map(int, t.split(":"))
                start_dt = datetime(current_date.year, current_date.month, current_date.day, hour, minute)
                end_dt = start_dt + timedelta(minutes=15)
                events.append({
                    "summary": f"💊 {medicine['name']} - {medicine['dosage']}",
                    "description": f"Medication for {patient_name}\nTiming: {medicine['timing']}\nDosage: {medicine['dosage']}",
                    "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                    "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                    "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]}
                })
        return events

    def schedule_for_patient(self, patient_id, access_token: str, calendar_id="primary"):
        """Push medication events to Google Calendar using a valid OAuth access token."""
        patient = get_patient(patient_id)
        if not patient:
            return {"success": False, "message": "Patient not found", "events_created": 0}

        prescriptions = get_patient_prescriptions(patient_id)
        if not prescriptions:
            return {"success": False, "message": "No prescriptions found", "events_created": 0}

        all_events = []
        for prescription in prescriptions[:1]:
            for medicine in prescription.get("medicines", []):
                events = self._build_events(medicine, patient["name"])
                all_events.extend(events[:7])

        created = 0
        errors = []
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        for event in all_events:
            try:
                url = f"{CALENDAR_BASE}/calendars/{calendar_id}/events"
                response = requests.post(url, json=event, headers=headers)
                if response.status_code in [200, 201]:
                    created += 1
                else:
                    err_msg = response.json().get("error", {}).get("message", "Unknown error")
                    errors.append(err_msg)
            except Exception as e:
                errors.append(str(e))

        if created > 0:
            return {
                "success": True,
                "message": f"✅ {created} medication reminder(s) added to your Google Calendar!",
                "events_created": created,
            }
        else:
            return {
                "success": False,
                "message": "Failed to create calendar events.",
                "events_created": 0,
                "errors": errors[:3],
            }

    def get_schedule_preview(self, patient_id):
        patient = get_patient(patient_id)
        prescriptions = get_patient_prescriptions(patient_id)
        if not prescriptions or not patient:
            return []

        schedule = []
        for prescription in prescriptions[:1]:
            for medicine in prescription.get("medicines", []):
                events = self._build_events(medicine, patient["name"])
                for e in events[:14]:
                    schedule.append({
                        "date": e["start"]["dateTime"][:10],
                        "time": e["start"]["dateTime"][11:16],
                        "medicine": medicine["name"],
                        "dosage": medicine["dosage"],
                        "timing": medicine["timing"]
                    })

        schedule.sort(key=lambda x: (x["date"], x["time"]))
        return schedule
