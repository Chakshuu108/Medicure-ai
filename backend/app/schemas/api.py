from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str
    hospital_id: str | None = None
    extra: dict = Field(default_factory=dict)


class LoginRequest(BaseModel):
    email: str
    password: str


class PatientLoginRequest(BaseModel):
    patient_code: str


class PatientGoogleLoginRequest(BaseModel):
    patient_code: str
    code: str


class HospitalRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    address: str = ""
    phone: str = ""
    city: str = ""


class DoctorCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    specialization: str = "General Medicine"
    gender: str = "Not specified"


class ReceptionistCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class PatientCreate(BaseModel):
    name: str
    age: int
    gender: str
    contact: str = ""
    email: str = ""
    disease: str = ""
    visit_date: str = ""
    doctor_id: str
    blood_group: str = ""
    weight_kg: float | None = None
    blood_pressure: str = ""


class MedicineCreate(BaseModel):
    name: str
    dosage: str
    duration_days: int = 7
    timing: str = "morning"


class PrescriptionCreate(BaseModel):
    patient_id: str
    doctor_notes: str = ""
    medicines: list[MedicineCreate]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    triage: str | None = None
    action_taken: str | None = None
    run_id: str | None = None
    agents_run: list[str] = []


class SessionInitRequest(BaseModel):
    google_access_token: str | None = None


class MCQSubmit(BaseModel):
    responses: dict
    total_score: int
    status: str
    side_effects: list[str] = []
    adherence_status: str = ""


class OPDSlotCreate(BaseModel):
    slot_date: str
    count: int = 5
    duration_minutes: int = 10


class BookSlotRequest(BaseModel):
    slot_id: str


class MeetSummaryCreate(BaseModel):
    booking_id: str
    transcript: str = ""


class TranscriptLineCreate(BaseModel):
    booking_id: str
    speaker_label: str
    text: str
    timestamp_ms: int = 0


class DemoCredentials(BaseModel):
    role: str
    email_or_code: str
    password: str | None = None
    description: str
