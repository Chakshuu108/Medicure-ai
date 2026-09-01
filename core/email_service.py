"""
Email Service — OPD Registration Receipt
Generates a professional PDF receipt exactly matching the hospital's letterhead
and emails it to the patient.

Credentials are loaded from Streamlit Secrets (st.secrets) via core/config.py.
"""

import io
import smtplib
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── SMTP config — loaded from Streamlit Secrets via config.py ─────────────────
from core.config import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME
)


# ── Colour palette (clean, formal — matches reference receipt) ────────────────
NAVY        = colors.HexColor("#0A2342")
NAVY_MID    = colors.HexColor("#1A3A5C")
TEAL        = colors.HexColor("#006B75")
TEAL_LIGHT  = colors.HexColor("#E0F2F4")
GREY_LIGHT  = colors.HexColor("#F5F7FA")
GREY_MID    = colors.HexColor("#D1D5DB")
GREY_TEXT   = colors.HexColor("#6B7280")
TEXT        = colors.HexColor("#1F2937")
SUCCESS     = colors.HexColor("#065F46")
SUCCESS_BG  = colors.HexColor("#D1FAE5")
WHITE       = colors.white
BLACK       = colors.black


def _fmt_date(date_str):
    """Convert YYYY-MM-DD to '09 April 2026'."""
    try:
        return datetime.strptime(str(date_str), "%Y-%m-%d").strftime("%d %B %Y")
    except Exception:
        return str(date_str)


def _build_pdf(patient_data: dict) -> bytes:
    """
    Build an OPD registration receipt PDF and return as bytes.

    patient_data keys:
        patient_id, name, age, gender, contact, email, disease,
        visit_date, doctor_name, doctor_dept, hospital_name,
        hospital_address, hospital_city, hospital_pincode,
        hospital_phone, hospital_email, hospital_website,
        blood_group, weight_kg, height_cm, temperature_c,
        blood_pressure, pulse_bpm, oxygen_spo2, address,
        token_number, consultation_type
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=12*mm,  bottomMargin=12*mm,
    )

    W = A4[0] - 36*mm   # usable width
    styles = getSampleStyleSheet()

    def ps(name, base="Normal", **kw):
        return ParagraphStyle(name, parent=styles[base], **kw)

    # ── Styles ────────────────────────────────────────────────────────────────
    hosp_name_s  = ps("HN",  fontSize=18, leading=22, textColor=WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)
    hosp_addr_s  = ps("HA",  fontSize=8,  leading=11, textColor=colors.HexColor("#C7E8EC"),
                       fontName="Helvetica", alignment=TA_CENTER)
    doc_title_s  = ps("DT",  fontSize=11, leading=14, textColor=WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)
    doc_sub_s    = ps("DS",  fontSize=8,  leading=10, textColor=colors.HexColor("#B0D8DF"),
                       fontName="Helvetica", alignment=TA_CENTER)

    sec_head_s   = ps("SH",  fontSize=8,  leading=11, textColor=NAVY,
                       fontName="Helvetica-Bold", spaceAfter=2)
    lbl_s        = ps("LBL", fontSize=8.5, leading=12, textColor=GREY_TEXT,
                       fontName="Helvetica")
    val_s        = ps("VAL", fontSize=9,  leading=12, textColor=TEXT,
                       fontName="Helvetica-Bold")
    pid_lbl_s    = ps("PL",  fontSize=8,  leading=11, textColor=TEAL,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)
    pid_val_s    = ps("PV",  fontSize=20, leading=24, textColor=NAVY,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)
    status_s     = ps("ST",  fontSize=10, leading=13, textColor=SUCCESS,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)
    note_s       = ps("NT",  fontSize=8,  leading=12, textColor=TEXT,
                       fontName="Helvetica")
    footer_s     = ps("FT",  fontSize=7.5, leading=11, textColor=GREY_TEXT,
                       fontName="Helvetica", alignment=TA_CENTER)
    badge_lbl_s  = ps("BL",  fontSize=7.5, leading=10, textColor=GREY_TEXT,
                       fontName="Helvetica", alignment=TA_CENTER)
    badge_val_s  = ps("BV",  fontSize=9,  leading=12, textColor=NAVY,
                       fontName="Helvetica-Bold", alignment=TA_CENTER)

    story = []

    # ──────────────────────────────────────────────────────────────────────────
    # HEADER — Hospital letterhead (top dark band, exactly like the sample)
    # ──────────────────────────────────────────────────────────────────────────
    hosp_name    = patient_data.get("hospital_name", "Hospital")
    hosp_addr    = patient_data.get("hospital_address", "")
    hosp_city    = patient_data.get("hospital_city", "")
    hosp_pin     = patient_data.get("hospital_pincode", "")
    hosp_phone   = patient_data.get("hospital_phone", "")
    hosp_email   = patient_data.get("hospital_email", "")
    hosp_website = patient_data.get("hospital_website", "")

    # Build address line
    addr_parts = []
    if hosp_addr:
        addr_parts.append(hosp_addr)
    if hosp_city and hosp_pin:
        addr_parts.append(f"{hosp_city} — {hosp_pin}")
    elif hosp_city:
        addr_parts.append(hosp_city)
    addr_line = ", ".join(addr_parts)

    # Contact line
    contact_parts = []
    if hosp_phone:
        contact_parts.append(f"Tel: {hosp_phone}")
    if hosp_email:
        contact_parts.append(f"Email: {hosp_email}")
    if hosp_website:
        contact_parts.append(hosp_website)
    contact_line = "  |  ".join(contact_parts)

    header_rows = [[Paragraph(hosp_name, hosp_name_s)]]
    if addr_line:
        header_rows.append([Paragraph(addr_line, hosp_addr_s)])
    if contact_line:
        header_rows.append([Paragraph(contact_line, hosp_addr_s)])
    header_rows.append([Paragraph("OPD REGISTRATION RECEIPT", doc_title_s)])
    header_rows.append([Paragraph("Outpatient Department  ·  This is a computer-generated document", doc_sub_s)])

    banner = Table(header_rows, colWidths=[W])
    banner.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        # Extra padding for hospital name row
        ("TOPPADDING",   (0, 0), (-1, 0), 10),
        # Slightly different bg for receipt title row
        ("BACKGROUND",   (0, -2), (-1, -1), NAVY_MID),
    ]))
    story.append(banner)
    story.append(Spacer(1, 4*mm))

    # ── Receipt meta row (Receipt No. / Visit Date / Generated On / Status) ──
    receipt_no   = f"RCP-{patient_data['patient_id']}"
    visit_date_f = _fmt_date(patient_data.get("visit_date", ""))
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    meta_data = [[
        Paragraph("Receipt No.", badge_lbl_s),
        Paragraph("Visit Date", badge_lbl_s),
        Paragraph("Generated On", badge_lbl_s),
        Paragraph("Status", badge_lbl_s),
    ],[
        Paragraph(receipt_no, badge_val_s),
        Paragraph(visit_date_f, badge_val_s),
        Paragraph(generated_at, badge_val_s),
        Paragraph("Confirmed", ps("ST2", fontSize=9, fontName="Helvetica-Bold",
                                  textColor=SUCCESS, alignment=TA_CENTER)),
    ]]
    meta_tbl = Table(meta_data, colWidths=[W*0.30, W*0.20, W*0.28, W*0.22])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), GREY_LIGHT),
        ("BOX",          (0, 0), (-1, -1), 0.5, GREY_MID),
        ("LINEAFTER",    (0, 0), (-2, -1), 0.5, GREY_MID),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_tbl)
    story.append(Spacer(1, 4*mm))

    # ── Patient ID highlight box ──────────────────────────────────────────────
    pid_tbl = Table([
        [Paragraph("PATIENT IDENTIFICATION NUMBER", pid_lbl_s)],
        [Paragraph(patient_data["patient_id"], pid_val_s)],
        [Paragraph("Please quote this number at all future visits", badge_lbl_s)],
    ], colWidths=[W])
    pid_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), TEAL_LIGHT),
        ("BOX",          (0, 0), (-1, -1), 1.5, TEAL),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story.append(pid_tbl)
    story.append(Spacer(1, 5*mm))

    # ── Section helper ────────────────────────────────────────────────────────
    def section(title, rows_2col):
        """Two-column key-value table under a section heading."""
        story.append(Paragraph(title, sec_head_s))
        story.append(HRFlowable(width=W, thickness=0.75, color=NAVY, spaceAfter=2))

        # Pair rows into 4-column layout (label, value, label, value)
        table_data = []
        for i in range(0, len(rows_2col), 2):
            left  = rows_2col[i]
            right = rows_2col[i+1] if i+1 < len(rows_2col) else ("", "")
            table_data.append([
                Paragraph(left[0],  lbl_s),
                Paragraph(str(left[1])  if left[1]  else "—", val_s),
                Paragraph(right[0], lbl_s),
                Paragraph(str(right[1]) if right[1] else "—", val_s),
            ])

        t = Table(table_data, colWidths=[W*0.18, W*0.32, W*0.18, W*0.32])
        t.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, GREY_LIGHT]),
            ("LINEBELOW",    (0, 0), (-1, -2), 0.25, GREY_MID),
        ]))
        story.append(t)
        story.append(Spacer(1, 4*mm))

    # ── Patient Information ───────────────────────────────────────────────────
    section("PATIENT INFORMATION", [
        ("Full Name",       patient_data.get("name")),
        ("Age / Gender",    f"{patient_data.get('age', '')} Years / {patient_data.get('gender', '')}"),
        ("Contact Number",  patient_data.get("contact")),
        ("Email Address",   patient_data.get("email")),
        ("Blood Group",     patient_data.get("blood_group")),
        ("Address",         patient_data.get("address")),
    ])

    # ── Consultation Details ──────────────────────────────────────────────────
    dept = patient_data.get("doctor_dept") or "General Medicine"
    token = patient_data.get("token_number") or "—"
    consult_type = patient_data.get("consultation_type") or "OPD — Outpatient"
    section("CONSULTATION DETAILS", [
        ("Attending Doctor", f"Dr. {patient_data.get('doctor_name', '')}"),
        ("Department",       dept),
        ("Primary Complaint",patient_data.get("disease")),
        ("Visit Date",       visit_date_f),
        ("Consultation Type",consult_type),
        ("Token Number",     token),
    ])

    # ── Vitals ────────────────────────────────────────────────────────────────
    vitals = []
    if patient_data.get("weight_kg"):
        vitals.append(("Weight",        f"{patient_data['weight_kg']} kg"))
    if patient_data.get("height_cm"):
        vitals.append(("Height",        f"{patient_data['height_cm']} cm"))
    if patient_data.get("temperature_c"):
        vitals.append(("Temperature",   f"{patient_data['temperature_c']} °C"))
    if patient_data.get("blood_pressure"):
        vitals.append(("Blood Pressure",patient_data["blood_pressure"]))
    if patient_data.get("pulse_bpm"):
        vitals.append(("Pulse Rate",    f"{patient_data['pulse_bpm']} bpm"))
    if patient_data.get("oxygen_spo2"):
        vitals.append(("SpO₂",          f"{patient_data['oxygen_spo2']} %"))

    if vitals:
        section("VITALS RECORDED AT REGISTRATION", vitals)

    # ── Important note ────────────────────────────────────────────────────────
    note_tbl = Table([[Paragraph(
        f"Important: Please carry this receipt along with a valid government-issued photo identity "
        f"document when visiting the hospital. Your Patient ID (<b>{patient_data['patient_id']}</b>) "
        f"is required for all future consultations, prescription collections, investigations, and "
        f"online OPD bookings. This receipt is valid for the visit date mentioned above only.",
        note_s
    )]], colWidths=[W])
    note_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",          (0, 0), (-1, -1), 0.75, colors.HexColor("#D97706")),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(note_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Signature row ─────────────────────────────────────────────────────────
    sig_data = [[
        Paragraph("_______________________________<br/>Receptionist / Registration Officer<br/>"
                  f"<b>{hosp_name}</b>", ps("SIG1", fontSize=8, fontName="Helvetica",
                  textColor=TEXT, leading=13)),
        Paragraph("_______________________________<br/>Authorised Signatory<br/>"
                  f"<b>Medical Superintendent</b>", ps("SIG2", fontSize=8, fontName="Helvetica",
                  textColor=TEXT, leading=13, alignment=TA_RIGHT)),
    ]]
    sig_tbl = Table(sig_data, colWidths=[W*0.5, W*0.5])
    sig_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 5*mm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.5, color=GREY_MID))
    story.append(Spacer(1, 2*mm))
    footer_parts = [hosp_name]
    if addr_line:
        footer_parts.append(addr_line)
    footer_line1 = "  ·  ".join(footer_parts)
    footer_line2_parts = []
    if hosp_phone:
        footer_line2_parts.append(f"Tel: {hosp_phone}")
    if hosp_email:
        footer_line2_parts.append(f"Email: {hosp_email}")
    if hosp_website:
        footer_line2_parts.append(hosp_website)
    footer_line2 = "  ·  ".join(footer_line2_parts)

    footer_text = footer_line1
    if footer_line2:
        footer_text += f"<br/>{footer_line2}"
    footer_text += "<br/>This is a system-generated document and does not require a physical signature to be valid."
    story.append(Paragraph(footer_text, footer_s))

    doc.build(story)
    return buf.getvalue()


def _html_email_body(patient_data: dict) -> str:
    """Responsive HTML email body with full hospital details."""
    name         = patient_data.get("name", "Patient")
    pid          = patient_data.get("patient_id", "")
    doctor       = patient_data.get("doctor_name", "")
    dept         = patient_data.get("doctor_dept") or "General Medicine"
    hospital     = patient_data.get("hospital_name", "")
    hosp_addr    = patient_data.get("hospital_address", "")
    hosp_city    = patient_data.get("hospital_city", "")
    hosp_pin     = patient_data.get("hospital_pincode", "")
    hosp_phone   = patient_data.get("hospital_phone", "")
    hosp_email   = patient_data.get("hospital_email", "")
    hosp_website = patient_data.get("hospital_website", "")
    disease      = patient_data.get("disease", "")
    visit        = _fmt_date(patient_data.get("visit_date", ""))
    token        = patient_data.get("token_number") or "—"
    consult_type = patient_data.get("consultation_type") or "OPD — Outpatient"

    addr_parts = [p for p in [hosp_addr, hosp_city] if p]
    if hosp_pin:
        addr_parts.append(hosp_pin)
    addr_line = ", ".join(addr_parts)

    contact_parts = []
    if hosp_phone:
        contact_parts.append(f"Tel: {hosp_phone}")
    if hosp_email:
        contact_parts.append(f"Email: {hosp_email}")
    if hosp_website:
        contact_parts.append(hosp_website)
    contact_line = "  |  ".join(contact_parts)

    def row(label, value, alt=False):
        bg = "#F9FAFB" if alt else "#FFFFFF"
        return f"""<tr style="background:{bg};">
          <td style="padding:9px 12px;color:#6B7280;font-size:13px;border-bottom:1px solid #F3F4F6;width:38%;">{label}</td>
          <td style="padding:9px 12px;color:#111827;font-size:13px;font-weight:600;border-bottom:1px solid #F3F4F6;">{value or "—"}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;padding:20px 0;">
  <tr><td align="center">
  <table width="580" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:10px;overflow:hidden;border:1px solid #E5E7EB;">

    <!-- Header -->
    <tr><td style="background:#0A2342;padding:20px 28px 14px;text-align:center;">
      <div style="color:#fff;font-size:22px;font-weight:700;">{hospital}</div>
      {f'<div style="color:#9BB5CC;font-size:11px;margin-top:3px;">{addr_line}</div>' if addr_line else ""}
      {f'<div style="color:#7A99B8;font-size:11px;margin-top:2px;">{contact_line}</div>' if contact_line else ""}
      <div style="background:#1A3A5C;margin:10px -28px -14px;padding:7px 28px;">
        <span style="color:#fff;font-size:13px;font-weight:600;letter-spacing:0.5px;">OPD REGISTRATION RECEIPT</span>
      </div>
    </td></tr>

    <!-- Body -->
    <tr><td style="padding:24px 28px 20px;">
      <p style="margin:0 0 6px;color:#374151;font-size:15px;">Dear <strong>{name}</strong>,</p>
      <p style="margin:0 0 20px;color:#6B7280;font-size:13px;line-height:1.6;">
        Your OPD registration has been confirmed at <strong>{hospital}</strong>.
        Your receipt PDF is attached to this email for your records.
      </p>

      <!-- Patient ID box -->
      <table width="100%" cellpadding="14" cellspacing="0"
             style="background:#E0F2F4;border:2px solid #006B75;border-radius:8px;margin-bottom:20px;">
        <tr><td align="center">
          <div style="color:#006B75;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px;">Patient Identification Number</div>
          <div style="color:#0A2342;font-size:28px;font-weight:700;letter-spacing:3px;">{pid}</div>
          <div style="color:#2D7A84;font-size:11px;margin-top:4px;">Quote this number at all future visits</div>
        </td></tr>
      </table>

      <!-- Details -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px;border:1px solid #E5E7EB;border-radius:6px;overflow:hidden;">
        {row("Attending Doctor", f"Dr. {doctor}", True)}
        {row("Department", dept)}
        {row("Primary Complaint", disease, True)}
        {row("Visit Date", visit)}
        {row("Consultation Type", consult_type, True)}
        {row("Token Number", token)}
      </table>

      <!-- Note -->
      <table width="100%" cellpadding="10" cellspacing="0"
             style="background:#FFFBEB;border:1px solid #D97706;border-radius:6px;margin-bottom:18px;">
        <tr><td>
          <p style="margin:0;color:#92400E;font-size:12px;line-height:1.6;">
            ⚠ Please carry this email (or the attached PDF) along with a valid government-issued
            photo ID when visiting the hospital. Your Patient ID is required for all consultations,
            prescriptions, investigations, and OPD slot bookings.
          </p>
        </td></tr>
      </table>

      <p style="margin:0;color:#6B7280;font-size:12px;">
        For queries, contact the Registration Desk.
      </p>
    </td></tr>

    <!-- Footer -->
    <tr><td style="background:#F9FAFB;padding:12px 28px;text-align:center;border-top:1px solid #E5E7EB;">
      <p style="margin:0;color:#9CA3AF;font-size:11px;">
        {hospital}{f' · {addr_line}' if addr_line else ''}<br>
        {contact_line if contact_line else ''}<br>
        This is a system-generated email. Please do not reply.
      </p>
    </td></tr>

  </table>
  </td></tr>
  </table>
</body>
</html>"""


def send_registration_email(patient_data: dict) -> tuple[bool, str]:
    """
    Generate PDF receipt and email it to the patient.
    Returns (success: bool, message: str)
    """
    recipient = (patient_data.get("email") or "").strip()
    if not recipient:
        return False, "No email address provided."

    if not SMTP_USER or not SMTP_PASSWORD:
        return False, (
            "SMTP credentials not configured. "
            "Set SMTP_USER and SMTP_PASSWORD environment variables."
        )

    try:
        pdf_bytes = _build_pdf(patient_data)

        hosp = patient_data.get("hospital_name", "Hospital")
        subject = (
            f"OPD Registration Confirmed — Patient ID: {patient_data.get('patient_id', '')} | {hosp}"
        )

        plain = (
            f"Dear {patient_data.get('name','Patient')},\n\n"
            f"Your OPD registration is confirmed.\n"
            f"Patient ID : {patient_data.get('patient_id','')}\n"
            f"Doctor     : Dr. {patient_data.get('doctor_name','')}\n"
            f"Department : {patient_data.get('doctor_dept','')}\n"
            f"Hospital   : {patient_data.get('hospital_name','')}\n"
            f"Visit Date : {patient_data.get('visit_date','')}\n\n"
            f"Please carry your Patient ID for all future visits.\n\n"
            f"— {hosp}"
        )

        # Outer: mixed (body + attachment)
        outer = MIMEMultipart("mixed")
        outer["Subject"] = subject
        outer["From"]    = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        outer["To"]      = recipient

        # Inner: alternative (plain + html)
        inner = MIMEMultipart("alternative")
        inner.attach(MIMEText(plain, "plain"))
        inner.attach(MIMEText(_html_email_body(patient_data), "html"))
        outer.attach(inner)

        # PDF attachment
        attachment = MIMEBase("application", "pdf")
        attachment.set_payload(pdf_bytes)
        encoders.encode_base64(attachment)
        fname = f"OPD_Receipt_{patient_data.get('patient_id','')}.pdf"
        attachment.add_header("Content-Disposition", "attachment", filename=fname)
        outer.attach(attachment)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, recipient, outer.as_string())

        return True, f"Receipt emailed to {recipient}"

    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed. Check SMTP_USER / SMTP_PASSWORD."
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception:
        return False, f"Email failed: {traceback.format_exc()}"


# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONAL ACTION EMAILS
# Covers: booking, cancellation, high-risk alert, worsening trend, missed doses
# ══════════════════════════════════════════════════════════════════════════════

_ACTION_STYLES = {
    "booking": {
        "color":      "#0A2342",
        "accent":     "#006B75",
        "icon":       "✅",
        "badge_bg":   "#D1FAE5",
        "badge_text": "#065F46",
        "badge":      "CONFIRMED",
    },
    "cancellation": {
        "color":      "#7C2D12",
        "accent":     "#DC2626",
        "icon":       "❌",
        "badge_bg":   "#FEE2E2",
        "badge_text": "#991B1B",
        "badge":      "CANCELLED",
    },
    "high_risk": {
        "color":      "#7C2D12",
        "accent":     "#DC2626",
        "icon":       "🚨",
        "badge_bg":   "#FEE2E2",
        "badge_text": "#991B1B",
        "badge":      "HIGH RISK ALERT",
    },
    "worsening": {
        "color":      "#78350F",
        "accent":     "#D97706",
        "icon":       "⚠️",
        "badge_bg":   "#FEF3C7",
        "badge_text": "#92400E",
        "badge":      "HEALTH ALERT",
    },
    "missed_doses": {
        "color":      "#1E40AF",
        "accent":     "#3B82F6",
        "icon":       "💊",
        "badge_bg":   "#DBEAFE",
        "badge_text": "#1E40AF",
        "badge":      "MEDICATION REMINDER",
    },
    "prescription": {
        "color":      "#064E3B",
        "accent":     "#059669",
        "icon":       "💊",
        "badge_bg":   "#D1FAE5",
        "badge_text": "#065F46",
        "badge":      "NEW PRESCRIPTION",
    },
}


def _action_html_email(
    action_type: str,
    patient_name: str,
    subject_line: str,
    headline: str,
    body_html: str,
    details_rows: list,        # list of (label, value) tuples
    footer_note: str = "",
    hospital_name: str = "MediCure",
) -> str:
    """Build a clean, responsive HTML transactional email for any action."""

    style = _ACTION_STYLES.get(action_type, _ACTION_STYLES["booking"])
    color      = style["color"]
    accent     = style["accent"]
    icon       = style["icon"]
    badge_bg   = style["badge_bg"]
    badge_text = style["badge_text"]
    badge      = style["badge"]

    rows_html = ""
    for label, value in details_rows:
        rows_html += f"""
        <tr>
          <td style="padding:8px 12px;color:#6B7280;font-size:13px;
                     border-bottom:1px solid #F3F4F6;white-space:nowrap;
                     font-weight:500;">{label}</td>
          <td style="padding:8px 12px;color:#111827;font-size:13px;
                     border-bottom:1px solid #F3F4F6;font-weight:600;">{value}</td>
        </tr>"""

    details_block = f"""
    <table style="width:100%;border-collapse:collapse;background:#F9FAFB;
                  border-radius:8px;margin-top:16px;">
      {rows_html}
    </table>""" if rows_html else ""

    footer_block = f"""
    <p style="font-size:12px;color:#9CA3AF;margin-top:24px;
              border-top:1px solid #E5E7EB;padding-top:16px;">
      {footer_note}
    </p>""" if footer_note else ""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td align="center" style="padding:32px 16px;">
<table width="600" cellpadding="0" cellspacing="0"
       style="background:#FFFFFF;border-radius:12px;
              box-shadow:0 1px 4px rgba(0,0,0,0.08);overflow:hidden;">

  <!-- Header -->
  <tr>
    <td style="background:{color};padding:28px 32px;">
      <table width="100%">
        <tr>
          <td>
            <div style="font-size:22px;font-weight:700;color:#FFFFFF;
                        letter-spacing:0.5px;">{hospital_name}</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.65);
                        margin-top:3px;letter-spacing:0.4px;">
              Patient Health Platform
            </div>
          </td>
          <td align="right">
            <span style="background:{badge_bg};color:{badge_text};
                         font-size:11px;font-weight:700;letter-spacing:0.8px;
                         padding:5px 12px;border-radius:20px;">
              {badge}
            </span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Icon + Headline -->
  <tr>
    <td style="padding:28px 32px 8px;">
      <div style="font-size:36px;margin-bottom:12px;">{icon}</div>
      <h2 style="margin:0 0 8px;font-size:20px;color:{color};
                 font-weight:700;line-height:1.3;">{headline}</h2>
      <p style="margin:0;font-size:14px;color:#6B7280;line-height:1.6;">
        Dear <strong style="color:#111827;">{patient_name}</strong>,
      </p>
    </td>
  </tr>

  <!-- Body -->
  <tr>
    <td style="padding:8px 32px 0;">
      <div style="font-size:14px;color:#374151;line-height:1.8;">
        {body_html}
      </div>
      {details_block}
    </td>
  </tr>

  <!-- Footer -->
  <tr>
    <td style="padding:16px 32px 28px;">
      {footer_block}
      <p style="font-size:11px;color:#D1D5DB;margin-top:20px;margin-bottom:0;">
        This is an automated notification from {hospital_name}.
        Please do not reply to this email.
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def send_action_email(
    action_type: str,
    patient_name: str,
    patient_email: str,
    subject: str,
    headline: str,
    body_html: str,
    details_rows: list = None,
    footer_note: str = "",
    hospital_name: str = "MediCure",
) -> tuple[bool, str]:
    """
    Send a transactional HTML email for any patient-facing action.

    action_type: 'booking' | 'cancellation' | 'high_risk' |
                 'worsening' | 'missed_doses' | 'prescription'
    details_rows: list of (label, value) pairs shown as a table
    Returns (success, message).
    """
    recipient = (patient_email or "").strip()
    if not recipient:
        return False, "No email address on file."
    if not SMTP_USER or not SMTP_PASSWORD:
        return False, "SMTP credentials not configured."

    try:
        html_body = _action_html_email(
            action_type=action_type,
            patient_name=patient_name,
            subject_line=subject,
            headline=headline,
            body_html=body_html,
            details_rows=details_rows or [],
            footer_note=footer_note,
            hospital_name=hospital_name,
        )

        plain = f"Dear {patient_name},\n\n{headline}\n\n{footer_note}\n\n— {hospital_name}"

        outer = MIMEMultipart("alternative")
        outer["Subject"] = subject
        outer["From"]    = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        outer["To"]      = recipient

        outer.attach(MIMEText(plain,     "plain"))
        outer.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASSWORD)
            srv.sendmail(SMTP_USER, [recipient], outer.as_string())

        return True, "Email sent."
    except Exception as exc:
        return False, f"Email error: {exc}"
