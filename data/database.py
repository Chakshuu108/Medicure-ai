import sqlite3
import json
import uuid
import hashlib
from datetime import datetime
import os

# DB path: use /tmp on Streamlit Cloud so data survives reruns within the same
# deployment session. Falls back to local data/ dir for local development.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
os.makedirs(_DATA_DIR, exist_ok=True)

# Prefer /tmp (persists across Streamlit reruns, survives in cloud deployments)
_TMP_DB = "/tmp/medicore_healthcare.db"
_LOCAL_DB = os.path.join(_DATA_DIR, "healthcare.db")

# If local DB has data (local dev), use it. Otherwise use /tmp for cloud.
def _pick_db_path():
    import shutil
    # If running locally and local DB has tables, use it
    if os.path.exists(_LOCAL_DB) and os.path.getsize(_LOCAL_DB) > 8192:
        return _LOCAL_DB
    # Copy local DB to /tmp if /tmp is empty (first deploy)
    if not os.path.exists(_TMP_DB) or os.path.getsize(_TMP_DB) < 8192:
        if os.path.exists(_LOCAL_DB):
            shutil.copy2(_LOCAL_DB, _TMP_DB)
    return _TMP_DB

DB_PATH = _pick_db_path()


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS hospitals (
            hospital_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            address TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            website TEXT DEFAULT '',
            city TEXT DEFAULT '',
            pincode TEXT DEFAULT '',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS doctors (
            doctor_id TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            specialization TEXT,
            gender TEXT DEFAULT 'Not specified',
            doctor_code TEXT DEFAULT '',
            created_at TEXT,
            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id),
            UNIQUE(email, hospital_id)
        );

        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            hospital_id TEXT NOT NULL,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            contact TEXT,
            disease TEXT,
            visit_date TEXT,
            created_at TEXT,
            risk_score INTEGER DEFAULT 0,
            risk_level TEXT DEFAULT 'low'
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            doctor_id TEXT,
            doctor_notes TEXT,
            created_at TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS medicines (
            id TEXT PRIMARY KEY,
            prescription_id TEXT,
            name TEXT,
            dosage TEXT,
            duration_days INTEGER,
            timing TEXT,
            start_date TEXT,
            FOREIGN KEY(prescription_id) REFERENCES prescriptions(id)
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            doctor_id TEXT,
            alert_type TEXT,
            message TEXT,
            severity TEXT,
            created_at TEXT,
            resolved INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS adherence_logs (
            id TEXT PRIMARY KEY,
            patient_id TEXT,
            medicine_id TEXT,
            taken INTEGER,
            scheduled_time TEXT,
            logged_at TEXT
        );

        CREATE TABLE IF NOT EXISTS receptionists (
            receptionist_id TEXT PRIMARY KEY,
            hospital_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id),
            UNIQUE(email, hospital_id)
        );
    """)
    conn.commit()

    # Migrate: add gender + doctor_code columns to existing doctors tables

    # Migrate: add hospital profile columns
    hosp_cols = {row[1] for row in c.execute("PRAGMA table_info(hospitals)")}
    for col, typedef in [
        ("address",  "TEXT DEFAULT ''"),
        ("phone",    "TEXT DEFAULT ''"),
        ("website",  "TEXT DEFAULT ''"),
        ("city",     "TEXT DEFAULT ''"),
        ("pincode",  "TEXT DEFAULT ''"),
    ]:
        if col not in hosp_cols:
            c.execute(f"ALTER TABLE hospitals ADD COLUMN {col} {typedef}")

    # Migrate: add email column to existing patients table
    patient_cols = {row[1] for row in c.execute("PRAGMA table_info(patients)")}
    if "email" not in patient_cols:
        c.execute("ALTER TABLE patients ADD COLUMN email TEXT DEFAULT ''")

    # Migrate: add vitals columns to patients
    for col, typedef in [
        ("blood_group", "TEXT DEFAULT ''"),
        ("weight_kg", "REAL"),
        ("temperature_c", "REAL"),
        ("blood_pressure", "TEXT DEFAULT ''"),
        ("pulse_bpm", "INTEGER"),
        ("oxygen_spo2", "REAL"),
        ("height_cm", "REAL"),
        ("address", "TEXT DEFAULT ''"),
    ]:
        if col not in patient_cols:
            c.execute(f"ALTER TABLE patients ADD COLUMN {col} {typedef}")

    existing_cols = {row[1] for row in c.execute("PRAGMA table_info(doctors)")}
    if "gender" not in existing_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN gender TEXT DEFAULT 'Not specified'")
    if "doctor_code" not in existing_cols:
        c.execute("ALTER TABLE doctors ADD COLUMN doctor_code TEXT DEFAULT ''")
    conn.commit()
    conn.close()
    # Init OPD tables
    init_opd_tables()


# ── Hospital Auth ─────────────────────────────────────────────────────────────

def register_hospital(name, email, password, address="", phone="", website="", city="", pincode=""):
    hospital_id = "HOSP-" + str(uuid.uuid4())[:8].upper()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO hospitals (hospital_id, name, email, password_hash, address, phone, website, city, pincode, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (hospital_id, name, email, _hash_password(password), address, phone, website, city, pincode, datetime.now().isoformat())
        )
        conn.commit()
        return hospital_id, None
    except sqlite3.IntegrityError:
        return None, "Email already registered."
    finally:
        conn.close()


def login_hospital(email, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM hospitals WHERE email=? AND password_hash=?",
        (email, _hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_hospital(hospital_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM hospitals WHERE hospital_id=?", (hospital_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_hospitals():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM hospitals ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_hospital_profile(hospital_id, address="", phone="", website="", city="", pincode=""):
    conn = get_conn()
    conn.execute(
        "UPDATE hospitals SET address=?, phone=?, website=?, city=?, pincode=? WHERE hospital_id=?",
        (address, phone, website, city, pincode, hospital_id)
    )
    conn.commit()
    conn.close()


# ── Doctor Code Generation ────────────────────────────────────────────────────

def _generate_doctor_code(name: str, hospital_id: str) -> str:
    """
    Generate a unique 3-character uppercase code from the doctor's name.
    Takes the first 3 consonants in order; pads with other letters if needed.
    Ensures uniqueness within the hospital.

    Examples: Chakshu → CHK  |  Rahul → RHL
    """
    VOWELS = set("AEIOU")
    letters = [c.upper() for c in name if c.isalpha()]
    consonants = [c for c in letters if c not in VOWELS]

    if len(consonants) >= 3:
        base = "".join(consonants[:3])
    elif letters:
        code_chars = list(consonants)
        for c in letters:
            if c not in code_chars:
                code_chars.append(c)
            if len(code_chars) >= 3:
                break
        if len(code_chars) < 3:
            code_chars = letters[:3]
            while len(code_chars) < 3:
                code_chars.append("X")
        base = "".join(code_chars[:3])
    else:
        base = "UNK"

    # Ensure uniqueness within hospital
    conn = get_conn()
    existing_codes = {
        r[0] for r in conn.execute(
            "SELECT doctor_code FROM doctors WHERE hospital_id=?", (hospital_id,)
        ).fetchall() if r[0]
    }
    conn.close()

    code = base
    suffix = 1
    while code in existing_codes:
        code = base[:2] + str(suffix)
        suffix += 1

    return code


def _make_doctor_initials(name):
    parts = name.strip().split()
    initials = "".join(p[0].upper() for p in parts if p)
    return initials[:4]


def register_doctor(hospital_id, name, email, password, specialization="General", gender="Not specified"):
    """Register a doctor. Returns (doctor_id, doctor_code, error)."""
    doctor_code = _generate_doctor_code(name, hospital_id)
    initials = _make_doctor_initials(name)
    suffix = str(uuid.uuid4())[:4].upper()
    doctor_id = f"DR-{initials}-{suffix}"
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO doctors (doctor_id, hospital_id, name, email, password_hash, specialization, gender, doctor_code, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (doctor_id, hospital_id, name, email, _hash_password(password),
             specialization, gender, doctor_code, datetime.now().isoformat())
        )
        conn.commit()
        return doctor_id, doctor_code, None
    except sqlite3.IntegrityError:
        return None, None, "Email already registered under this hospital."
    finally:
        conn.close()


def login_doctor(hospital_id, email, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM doctors WHERE hospital_id=? AND email=? AND password_hash=?",
        (hospital_id, email, _hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctor(doctor_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM doctors WHERE doctor_id=?", (doctor_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_doctors_by_hospital(hospital_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM doctors WHERE hospital_id=?", (hospital_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Receptionist Auth ─────────────────────────────────────────────────────────

def register_receptionist(hospital_id, name, email, password):
    rid = "REC-" + str(uuid.uuid4())[:8].upper()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO receptionists (receptionist_id, hospital_id, name, email, password_hash, created_at) VALUES (?,?,?,?,?,?)",
            (rid, hospital_id, name, email, _hash_password(password), datetime.now().isoformat())
        )
        conn.commit()
        return rid, None
    except sqlite3.IntegrityError:
        return None, "Email already registered for this hospital."
    finally:
        conn.close()


def login_receptionist(hospital_id, email, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM receptionists WHERE hospital_id=? AND email=? AND password_hash=?",
        (hospital_id, email, _hash_password(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_receptionists_by_hospital(hospital_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM receptionists WHERE hospital_id=?", (hospital_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Patient Management ────────────────────────────────────────────────────────

def _generate_patient_id(visit_date: str) -> str:
    """
    Format: PAT-YYYYMMDD-XXXX
    Simple, unique, never conflicts with doctor codes.
    Example: PAT-20260413-0001
    """
    date_str = visit_date.replace("-", "")
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    conn.close()
    serial = str(count + 1).zfill(4)
    return f"PAT-{date_str}-{serial}"


def create_patient(doctor_id, hospital_id, doctor_name, name, age, gender, contact, email, disease, visit_date,
                   blood_group=None, weight_kg=None, temperature_c=None, blood_pressure=None,
                   pulse_bpm=None, oxygen_spo2=None, height_cm=None, address=None):
    # Generate patient ID from patient's OWN name (not doctor code)
    pid = _generate_patient_id(visit_date)
    conn = get_conn()
    conn.execute(
        """INSERT INTO patients (id, doctor_id, hospital_id, name, age, gender, contact, email, disease, visit_date, created_at,
            blood_group, weight_kg, temperature_c, blood_pressure, pulse_bpm, oxygen_spo2, height_cm, address)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, doctor_id, hospital_id, name, age, gender, contact, email or '', disease, visit_date, datetime.now().isoformat(),
         blood_group or '', weight_kg, temperature_c, blood_pressure or '', pulse_bpm, oxygen_spo2, height_cm, address or '')
    )
    conn.commit()
    conn.close()
    return pid


def get_patient(patient_id):
    conn = get_conn()
    # Normalise to uppercase and also try exact match for safety
    pid = patient_id.strip().upper() if patient_id else ""
    row = conn.execute(
        "SELECT * FROM patients WHERE UPPER(id)=?", (pid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_patients():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM patients ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patients_by_doctor(doctor_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM patients WHERE doctor_id=? ORDER BY created_at DESC", (doctor_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patients_by_doctor_and_date(doctor_id, visit_date):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM patients WHERE doctor_id=? AND visit_date=? ORDER BY created_at ASC",
        (doctor_id, visit_date)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_patients_by_date(doctor_id, visit_date):
    conn = get_conn()
    patient_rows = conn.execute(
        "SELECT id FROM patients WHERE doctor_id=? AND visit_date=?", (doctor_id, visit_date)
    ).fetchall()
    patient_ids = [r["id"] for r in patient_rows]
    for pid in patient_ids:
        pres = conn.execute("SELECT id FROM prescriptions WHERE patient_id=?", (pid,)).fetchall()
        for pr in pres:
            conn.execute("DELETE FROM medicines WHERE prescription_id=?", (pr["id"],))
        conn.execute("DELETE FROM prescriptions WHERE patient_id=?", (pid,))
        conn.execute("DELETE FROM alerts WHERE patient_id=?", (pid,))
        conn.execute("DELETE FROM chat_history WHERE patient_id=?", (pid,))
    conn.execute(
        "DELETE FROM patients WHERE doctor_id=? AND visit_date=?", (doctor_id, visit_date)
    )
    conn.commit()
    conn.close()
    return len(patient_ids)


def update_patient_risk(patient_id, score, level):
    conn = get_conn()
    conn.execute("UPDATE patients SET risk_score=?, risk_level=? WHERE id=?", (score, level, patient_id))
    conn.commit()
    conn.close()


# ── Prescriptions ─────────────────────────────────────────────────────────────

def create_prescription(patient_id, medicines_data, doctor_notes="", doctor_id=None):
    prid = str(uuid.uuid4())
    conn = get_conn()
    conn.execute(
        "INSERT INTO prescriptions (id, patient_id, doctor_id, doctor_notes, created_at) VALUES (?,?,?,?,?)",
        (prid, patient_id, doctor_id, doctor_notes, datetime.now().isoformat())
    )
    for med in medicines_data:
        mid = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO medicines (id, prescription_id, name, dosage, duration_days, timing, start_date) VALUES (?,?,?,?,?,?,?)",
            (mid, prid, med["name"], med["dosage"], med["duration_days"], med["timing"],
             med.get("start_date", datetime.now().date().isoformat()))
        )
    conn.commit()
    conn.close()
    return prid


def get_patient_prescriptions(patient_id):
    conn = get_conn()
    prescriptions = conn.execute(
        "SELECT * FROM prescriptions WHERE patient_id=? ORDER BY created_at DESC", (patient_id,)
    ).fetchall()
    result = []
    for p in prescriptions:
        pd = dict(p)
        meds = conn.execute("SELECT * FROM medicines WHERE prescription_id=?", (p["id"],)).fetchall()
        pd["medicines"] = [dict(m) for m in meds]
        result.append(pd)
    conn.close()
    return result


def get_all_medicines_for_patient(patient_id):
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.* FROM medicines m
        JOIN prescriptions p ON m.prescription_id = p.id
        WHERE p.patient_id=?
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Chat ──────────────────────────────────────────────────────────────────────

def save_chat_message(patient_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_history (id, patient_id, role, content, timestamp) VALUES (?,?,?,?,?)",
        (str(uuid.uuid4()), patient_id, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_chat_history(patient_id, limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_history WHERE patient_id=? ORDER BY timestamp DESC LIMIT ?",
        (patient_id, limit)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))


# ── Alerts ────────────────────────────────────────────────────────────────────

def create_alert(patient_id, alert_type, message, severity="medium", doctor_id=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO alerts (id, patient_id, doctor_id, alert_type, message, severity, created_at) VALUES (?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), patient_id, doctor_id, alert_type, message, severity, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_alerts(resolved=False, doctor_id=None):
    conn = get_conn()
    if doctor_id:
        rows = conn.execute(
            "SELECT a.*, p.name as patient_name FROM alerts a JOIN patients p ON a.patient_id=p.id WHERE a.resolved=? AND a.doctor_id=? ORDER BY a.created_at DESC",
            (1 if resolved else 0, doctor_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT a.*, p.name as patient_name FROM alerts a JOIN patients p ON a.patient_id=p.id WHERE a.resolved=? ORDER BY a.created_at DESC",
            (1 if resolved else 0,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patient_alerts(patient_id, resolved=None):
    """Fetch all alerts for a specific patient (patient-facing Alerts tab)."""
    conn = get_conn()
    if resolved is None:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE patient_id=? ORDER BY created_at DESC",
            (patient_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE patient_id=? AND resolved=? ORDER BY created_at DESC",
            (patient_id, 1 if resolved else 0)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id):
    conn = get_conn()
    conn.execute("UPDATE alerts SET resolved=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()


# ── MCQ / Daily Health Check ──────────────────────────────────────────────────

def save_mcq_set(patient_id, doctor_id, questions_json, date_str):
    """Store a generated MCQ set for a patient on a given date."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_sets (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            questions_json TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT
        )
    """)
    conn.execute("DELETE FROM mcq_sets WHERE patient_id=? AND date=?", (patient_id, date_str))
    mid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO mcq_sets (id, patient_id, doctor_id, questions_json, date, created_at) VALUES (?,?,?,?,?,?)",
        (mid, patient_id, doctor_id, questions_json, date_str, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return mid


def get_mcq_set(patient_id, date_str):
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_sets (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            questions_json TEXT NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT
        )
    """)
    row = conn.execute(
        "SELECT * FROM mcq_sets WHERE patient_id=? AND date=?", (patient_id, date_str)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_mcq_response(patient_id, doctor_id, date_str, responses_json, total_score, status, side_effects, adherence_status):
    """Store a patient's daily MCQ submission."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_responses (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            date TEXT NOT NULL,
            responses_json TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            side_effects TEXT,
            adherence_status TEXT,
            submitted_at TEXT
        )
    """)
    rid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO mcq_responses (id, patient_id, doctor_id, date, responses_json, total_score, status, side_effects, adherence_status, submitted_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (rid, patient_id, doctor_id, date_str, responses_json, total_score, status,
         side_effects, adherence_status, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return rid


def get_mcq_responses(patient_id, limit=30):
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_responses (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            date TEXT NOT NULL,
            responses_json TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            side_effects TEXT,
            adherence_status TEXT,
            submitted_at TEXT
        )
    """)
    rows = conn.execute(
        "SELECT * FROM mcq_responses WHERE patient_id=? ORDER BY submitted_at DESC LIMIT ?",
        (patient_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_mcq_response_for_date(patient_id, date_str):
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_responses (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            date TEXT NOT NULL,
            responses_json TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            side_effects TEXT,
            adherence_status TEXT,
            submitted_at TEXT
        )
    """)
    row = conn.execute(
        "SELECT * FROM mcq_responses WHERE patient_id=? AND date=? ORDER BY submitted_at DESC LIMIT 1",
        (patient_id, date_str)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_mcq_responses_for_doctor(doctor_id, status_filter=None):
    """Get all patient MCQ responses under this doctor, optionally filtered by status."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mcq_responses (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor_id TEXT,
            date TEXT NOT NULL,
            responses_json TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            status TEXT NOT NULL,
            side_effects TEXT,
            adherence_status TEXT,
            submitted_at TEXT
        )
    """)
    if status_filter and status_filter != "All":
        rows = conn.execute(
            "SELECT r.*, p.name as patient_name, p.disease FROM mcq_responses r JOIN patients p ON r.patient_id=p.id WHERE r.doctor_id=? AND r.status=? ORDER BY r.submitted_at DESC",
            (doctor_id, status_filter)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT r.*, p.name as patient_name, p.disease FROM mcq_responses r JOIN patients p ON r.patient_id=p.id WHERE r.doctor_id=? ORDER BY r.submitted_at DESC",
            (doctor_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_consecutive_worsening(patient_id, n=2):
    """Return True if last n responses are all Worsening."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT status FROM mcq_responses WHERE patient_id=? ORDER BY submitted_at DESC LIMIT ?",
            (patient_id, n)
        ).fetchall()
    except Exception:
        conn.close()
        return False
    conn.close()
    statuses = [r["status"] for r in rows]
    return len(statuses) == n and all(s == "Worsening" for s in statuses)


# ═══════════════════════════════════════════════════════════════════════════════
# Online OPD — Slot Management
# ═══════════════════════════════════════════════════════════════════════════════

def init_opd_tables():
    """Create OPD tables. Called from init_db."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS opd_slots (
            id TEXT PRIMARY KEY,
            doctor_id TEXT NOT NULL,
            slot_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_booked INTEGER DEFAULT 0,
            booked_by_patient_id TEXT,
            patient_name TEXT,
            patient_visited INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
        );
    """)
    conn.commit()
    conn.close()


def create_opd_slots(doctor_id: str, slot_date: str, start_time: str,
                     num_slots: int, slot_duration_minutes: int = 17):
    """Delete existing unbooked slots for that day, then create fresh slots."""
    from datetime import datetime, timedelta
    conn = get_conn()
    # Remove only unbooked slots so we don't wipe confirmed bookings
    conn.execute(
        "DELETE FROM opd_slots WHERE doctor_id=? AND slot_date=? AND is_booked=0",
        (doctor_id, slot_date)
    )
    base = datetime.strptime(start_time, "%H:%M")
    for i in range(num_slots):
        slot_start = (base + timedelta(minutes=i * slot_duration_minutes)).strftime("%H:%M")
        slot_end   = (base + timedelta(minutes=(i + 1) * slot_duration_minutes)).strftime("%H:%M")
        slot_id = f"OPD-{doctor_id[:6]}-{slot_date.replace('-','')}-{i+1:03d}"
        conn.execute(
            """INSERT OR IGNORE INTO opd_slots
               (id, doctor_id, slot_date, start_time, end_time, is_booked, patient_visited, created_at)
               VALUES (?,?,?,?,?,0,0,?)""",
            (slot_id, doctor_id, slot_date, slot_start, slot_end, datetime.now().isoformat())
        )
    conn.commit()
    conn.close()


def get_opd_slots(doctor_id: str, slot_date: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM opd_slots WHERE doctor_id=? AND slot_date=? ORDER BY start_time",
        (doctor_id, slot_date)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_opd_slots_for_doctor(doctor_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM opd_slots WHERE doctor_id=? ORDER BY slot_date, start_time",
        (doctor_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def book_opd_slot(slot_id: str, patient_id: str, patient_name: str = "") -> bool:
    """Book a slot for a patient. Returns True on success, False if already taken."""
    conn = get_conn()
    row = conn.execute("SELECT is_booked FROM opd_slots WHERE id=?", (slot_id,)).fetchone()
    if not row or row["is_booked"]:
        conn.close()
        return False
    conn.execute(
        "UPDATE opd_slots SET is_booked=1, booked_by_patient_id=?, patient_name=? WHERE id=?",
        (patient_id, patient_name, slot_id)
    )
    conn.commit()
    conn.close()
    return True


def cancel_opd_booking(slot_id: str, patient_id: str) -> bool:
    """Cancel a booking — only the booking patient can cancel."""
    conn = get_conn()
    row = conn.execute(
        "SELECT booked_by_patient_id FROM opd_slots WHERE id=?", (slot_id,)
    ).fetchone()
    if not row or row["booked_by_patient_id"] != patient_id:
        conn.close()
        return False
    conn.execute(
        "UPDATE opd_slots SET is_booked=0, booked_by_patient_id=NULL, patient_name=NULL WHERE id=?",
        (slot_id,)
    )
    conn.commit()
    conn.close()
    return True


def mark_patient_visited(slot_id: str, visited: bool):
    conn = get_conn()
    conn.execute("UPDATE opd_slots SET patient_visited=? WHERE id=?", (1 if visited else 0, slot_id))
    conn.commit()
    conn.close()


def get_patient_opd_bookings(patient_id: str):
    conn = get_conn()
    rows = conn.execute(
        """SELECT s.*, d.name AS doctor_name, d.specialization
           FROM opd_slots s
           JOIN doctors d ON s.doctor_id = d.doctor_id
           WHERE s.booked_by_patient_id=?
           ORDER BY s.slot_date, s.start_time""",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_available_opd_doctors():
    """Return doctors who have unbooked slots from today onwards."""
    from datetime import date
    conn = get_conn()
    today = date.today().isoformat()
    rows = conn.execute(
        """SELECT DISTINCT d.doctor_id, d.name, d.specialization, d.doctor_code
           FROM doctors d
           JOIN opd_slots s ON d.doctor_id = s.doctor_id
           WHERE s.slot_date >= ? AND s.is_booked = 0
           ORDER BY d.name""",
        (today,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_available_opd_dates_for_doctor(doctor_id: str):
    """Return distinct dates that have ≥1 unbooked slot."""
    from datetime import date
    conn = get_conn()
    today = date.today().isoformat()
    rows = conn.execute(
        """SELECT DISTINCT slot_date FROM opd_slots
           WHERE doctor_id=? AND slot_date >= ? AND is_booked=0
           ORDER BY slot_date""",
        (doctor_id, today)
    ).fetchall()
    conn.close()
    return [r["slot_date"] for r in rows]


def get_available_opd_slots(doctor_id: str, slot_date: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM opd_slots WHERE doctor_id=? AND slot_date=? AND is_booked=0 ORDER BY start_time",
        (doctor_id, slot_date)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_patient_has_booking(patient_id: str, doctor_id: str, slot_date: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM opd_slots WHERE booked_by_patient_id=? AND doctor_id=? AND slot_date=?",
        (patient_id, doctor_id, slot_date)
    ).fetchone()
    conn.close()
    return row is not None


# ── Meet Summaries ────────────────────────────────────────────────────────────

def save_meet_summary(slot_id: str, doctor_id: str, patient_id: str,
                      transcript: str, summary_json: str):
    """Save or replace a consultation summary after an online meeting."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            transcript TEXT,
            summary_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("DELETE FROM meet_summaries WHERE slot_id=?", (slot_id,))
    conn.execute("""
        INSERT INTO meet_summaries (slot_id, doctor_id, patient_id, transcript, summary_json)
        VALUES (?, ?, ?, ?, ?)
    """, (slot_id, doctor_id, patient_id, transcript, summary_json))
    conn.commit()
    conn.close()


def get_meet_summary(slot_id: str) -> dict | None:
    """Fetch the summary for a given slot, or None if not yet generated."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            transcript TEXT,
            summary_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    row = conn.execute(
        "SELECT * FROM meet_summaries WHERE slot_id=? ORDER BY id DESC LIMIT 1",
        (slot_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_patient_meet_summaries(patient_id: str) -> list:
    """Return all summaries for a patient, newest first."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            transcript TEXT,
            summary_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    rows = conn.execute(
        "SELECT * FROM meet_summaries WHERE patient_id=? ORDER BY id DESC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_doctor_meet_summaries(doctor_id: str) -> list:
    """Return all summaries for a doctor, newest first."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            patient_id TEXT NOT NULL,
            transcript TEXT,
            summary_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    rows = conn.execute(
        "SELECT * FROM meet_summaries WHERE doctor_id=? ORDER BY id DESC",
        (doctor_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_doctor_meet_summaries_enriched(doctor_id: str) -> list:
    """Return doctor summaries joined with OPD slot and patient details."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*,
               s.slot_date, s.start_time, s.end_time,
               COALESCE(s.patient_name, p.name, m.patient_id) AS patient_name
        FROM meet_summaries m
        LEFT JOIN opd_slots s ON m.slot_id = s.id
        LEFT JOIN patients p ON m.patient_id = p.id
        WHERE m.doctor_id=?
        ORDER BY m.id DESC
    """, (doctor_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_patient_meet_summaries_enriched(patient_id: str) -> list:
    """Return patient summaries joined with OPD slot and doctor details."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT m.*,
               s.slot_date, s.start_time, s.end_time,
               d.name AS doctor_name, d.specialization
        FROM meet_summaries m
        LEFT JOIN opd_slots s ON m.slot_id = s.id
        LEFT JOIN doctors d ON m.doctor_id = d.doctor_id
        WHERE m.patient_id=?
        ORDER BY m.id DESC
    """, (patient_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Meet Transcript Lines ─────────────────────────────────────────────────────

def _ensure_transcript_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS meet_transcript_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_name TEXT NOT NULL,
            speaker_label TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp_ms INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)


def save_transcript_line(room_name: str, speaker_label: str, text: str, timestamp_ms: int):
    """Save a single transcribed sentence with its timestamp."""
    conn = get_conn()
    _ensure_transcript_table(conn)
    conn.execute(
        "INSERT INTO meet_transcript_lines (room_name, speaker_label, text, timestamp_ms) VALUES (?,?,?,?)",
        (room_name, speaker_label, text, timestamp_ms)
    )
    conn.commit()
    conn.close()


def get_transcript_lines(room_name: str) -> list:
    """Return all transcript lines for a room sorted by timestamp_ms."""
    conn = get_conn()
    _ensure_transcript_table(conn)
    rows = conn.execute(
        "SELECT * FROM meet_transcript_lines WHERE room_name=? ORDER BY timestamp_ms ASC",
        (room_name,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_transcript_lines(room_name: str):
    """Clear transcript lines for a room after summary is saved."""
    conn = get_conn()
    _ensure_transcript_table(conn)
    conn.execute("DELETE FROM meet_transcript_lines WHERE room_name=?", (room_name,))
    conn.commit()
    conn.close()
