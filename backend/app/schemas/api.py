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
    website: str = ""
    pincode: str = ""


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
    age: int = Field(ge=0, le=130)
    gender: str
    contact: str = Field(min_length=1)
    email: str = ""
    disease: str = ""
    visit_date: str = ""
    doctor_id: str
    blood_group: str = Field(min_length=1)
    weight_kg: float = Field(gt=0, le=500)
    height_cm: float = Field(gt=0, le=300)
    temperature_c: float = Field(gt=0, le=50)
    pulse_bpm: int = Field(gt=0, le=300)
    oxygen_spo2: float = Field(gt=0, le=100)
    blood_pressure: str = Field(min_length=3, max_length=20)
    address: str = ""


class MedicineCreate(BaseModel):
    name: str
    disease: str = ""
    dosage: str
    duration_days: int = Field(ge=1, le=365)
    frequency_pattern: str = "daily"
    times_per_day: int = Field(ge=1, le=6, default=1)


class PrescriptionCreate(BaseModel):
    patient_id: str
    disease: str = ""
    doctor_notes: str = ""
    medicines: list[MedicineCreate]


class MedicineScheduleUpdate(BaseModel):
    start_date: str
    start_time: str
    dose_times: list[str] | None = None


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
