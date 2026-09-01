"""SMTP transactional emails for patient reminders and alerts."""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings


def _is_configured() -> bool:
    s = get_settings()
    return bool(s.smtp_user and s.smtp_password)


def _send_sync(to_email: str, subject: str, html_body: str, plain_body: str) -> tuple[bool, str]:
    s = get_settings()
    if not to_email.strip():
        return False, "No email address"
    if not _is_configured():
        return False, "SMTP not configured"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{s.smtp_from_name} <{s.smtp_user}>"
        msg["To"] = to_email
        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.smtp_user, [to_email], msg.as_string())
        return True, "Email sent"
    except Exception as exc:
        return False, str(exc)


async def send_email(to_email: str, subject: str, html_body: str, plain_body: str = "") -> tuple[bool, str]:
    plain = plain_body or subject
    return await asyncio.to_thread(_send_sync, to_email, subject, html_body, plain)


async def send_missed_checkin_email(patient_name: str, patient_email: str, missed_date: str) -> tuple[bool, str]:
    subject = f"MediCure — Missed health check-in for {missed_date}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#4F46E5;">Daily Health Check Reminder</h2>
      <p>Dear <strong>{patient_name}</strong>,</p>
      <p>We noticed you missed your daily health check-in on <strong>{missed_date}</strong>.</p>
      <p>Please log in to MediCure and complete today's Health Check so your doctor and Health Guardian can monitor your progress.</p>
      <p style="color:#6B7280;font-size:13px;">A calendar reminder has also been added if you connected Google Calendar.</p>
    </div>"""
    return await send_email(patient_email, subject, html)


async def send_booking_confirmation_email(
    patient_name: str, patient_email: str, slot_date: str, start_time: str, doctor_name: str,
) -> tuple[bool, str]:
    subject = f"MediCure — OPD appointment confirmed for {slot_date}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#059669;">Appointment Confirmed</h2>
      <p>Dear <strong>{patient_name}</strong>,</p>
      <p>Your OPD appointment with <strong>{doctor_name}</strong> is confirmed.</p>
      <ul><li>Date: {slot_date}</li><li>Time: {start_time}</li></ul>
    </div>"""
    return await send_email(patient_email, subject, html)


async def send_worsening_alert_email(
    patient_name: str, patient_email: str, status: str, total_score: int,
) -> tuple[bool, str]:
    subject = f"MediCure — Health check alert: {status}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#DC2626;">Health Status Alert</h2>
      <p>Dear <strong>{patient_name}</strong>,</p>
      <p>Your recent daily health check shows a status of <strong>{status}</strong> (score: {total_score}).</p>
      <p>Please log in to MediCure and review your symptoms. If you feel unwell, contact your doctor or seek medical care.</p>
      <p style="color:#6B7280;font-size:13px;">Your doctor has been notified through the MediCure alerts system.</p>
    </div>"""
    plain = f"Dear {patient_name},\n\nYour health check status is {status} (score {total_score}). Please review in MediCure."
    return await send_email(patient_email, subject, html, plain)


async def send_proactive_wellness_nudge(
    patient_name: str, patient_email: str, days_silent: int,
) -> tuple[bool, str]:
    subject = f"MediCure — We miss your daily health check-in"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#7C3AED;">Health Guardian noticed you've been away</h2>
      <p>Dear <strong>{patient_name}</strong>,</p>
      <p>Our proactive Health Guardian has not seen a daily check-in from you in
         <strong>{days_silent} day(s)</strong>.</p>
      <p>Please log in to MediCure and complete your daily health check so your doctor
         can stay informed about your condition.</p>
      <p style="color:#6B7280;font-size:13px;">Your doctor has been notified if this silence continues.</p>
    </div>"""
    plain = (
        f"Dear {patient_name},\n\nYou have not checked in for {days_silent} days. "
        "Please log in to MediCure and complete your daily health check."
    )
    return await send_email(patient_email, subject, html, plain)


async def send_doctor_clinical_alert_email(
    *,
    doctor_name: str,
    doctor_email: str,
    patient_name: str,
    patient_code: str,
    disease: str,
    alert_type: str,
    severity: str,
    summary: str,
    full_message: str,
) -> tuple[bool, str]:
    sev = (severity or "medium").upper()
    sev_color = {"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#059669"}.get(sev, "#4F46E5")
    subject = f"MediCure — [{sev}] Patient alert: {patient_name}"
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:{sev_color};">Clinical Alert — {sev}</h2>
      <p>Dear <strong>Dr. {doctor_name}</strong>,</p>
      <p style="background:#F8FAFC;padding:12px;border-radius:8px;border-left:4px solid {sev_color};">
        <strong>Summary:</strong> {summary}
      </p>
      <table style="width:100%;margin:16px 0;font-size:14px;">
        <tr><td style="color:#64748B;padding:4px 0;">Patient</td><td><strong>{patient_name}</strong> ({patient_code})</td></tr>
        <tr><td style="color:#64748B;padding:4px 0;">Condition</td><td>{disease}</td></tr>
        <tr><td style="color:#64748B;padding:4px 0;">Alert type</td><td>{alert_type}</td></tr>
        <tr><td style="color:#64748B;padding:4px 0;">Severity</td><td><strong style="color:{sev_color}">{sev}</strong></td></tr>
      </table>
      <p style="font-size:14px;color:#334155;white-space:pre-wrap;">{full_message}</p>
      <p style="font-size:12px;color:#94A3B8;margin-top:24px;">Log in to MediCure Doctor Portal → Alerts to review and resolve.</p>
    </div>"""
    plain = f"Dr. {doctor_name},\n\n{summary}\n\nPatient: {patient_name} ({patient_code})\n{full_message}"
    return await send_email(doctor_email, subject, html, plain)
