import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"
    PATIENT = "patient"


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hospital_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    website: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    pincode: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    doctors: Mapped[list["Doctor"]] = relationship(back_populates="hospital")
    receptionists: Mapped[list["Receptionist"]] = relationship(back_populates="hospital")
    patients: Mapped[list["Patient"]] = relationship(back_populates="hospital")


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hospital_id: Mapped[str] = mapped_column(ForeignKey("hospitals.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    specialization: Mapped[str] = mapped_column(String(255), default="General Medicine")
    gender: Mapped[str] = mapped_column(String(50), default="Not specified")
    doctor_code: Mapped[str] = mapped_column(String(10), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hospital: Mapped["Hospital"] = relationship(back_populates="doctors")
    patients: Mapped[list["Patient"]] = relationship(back_populates="doctor")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="doctor")


class Receptionist(Base):
    __tablename__ = "receptionists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hospital_id: Mapped[str] = mapped_column(ForeignKey("hospitals.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hospital: Mapped["Hospital"] = relationship(back_populates="receptionists")


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    hospital_id: Mapped[str] = mapped_column(ForeignKey("hospitals.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(50))
    contact: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), default="")
    disease: Mapped[str] = mapped_column(Text, default="")
    visit_date: Mapped[str | None] = mapped_column(String(20))
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    blood_group: Mapped[str] = mapped_column(String(10), default="")
    weight_kg: Mapped[float | None] = mapped_column(Float)
    temperature_c: Mapped[float | None] = mapped_column(Float)
    blood_pressure: Mapped[str] = mapped_column(String(20), default="")
    pulse_bpm: Mapped[int | None] = mapped_column(Integer)
    oxygen_spo2: Mapped[float | None] = mapped_column(Float)
    height_cm: Mapped[float | None] = mapped_column(Float)
    address: Mapped[str] = mapped_column(Text, default="")
    google_email: Mapped[str] = mapped_column(String(255), default="")
    google_refresh_token: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    doctor: Mapped["Doctor"] = relationship(back_populates="patients")
    hospital: Mapped["Hospital"] = relationship(back_populates="patients")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="patient")
    chat_messages: Mapped[list["ChatMessage"]] = relationship(back_populates="patient")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="patient")
    mcq_responses: Mapped[list["MCQResponse"]] = relationship(back_populates="patient")
    opd_bookings: Mapped[list["OPDBooking"]] = relationship(back_populates="patient")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="patient")


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    doctor_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="prescriptions")
    doctor: Mapped["Doctor"] = relationship(back_populates="prescriptions")
    medicines: Mapped[list["Medicine"]] = relationship(back_populates="prescription", cascade="all, delete-orphan")


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    prescription_id: Mapped[str] = mapped_column(ForeignKey("prescriptions.id"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), default="")
    duration_days: Mapped[int] = mapped_column(Integer, default=7)
    timing: Mapped[str] = mapped_column(String(100), default="morning")
    start_date: Mapped[str] = mapped_column(String(20), default="")

    prescription: Mapped["Prescription"] = relationship(back_populates="medicines")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="chat_messages")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str | None] = mapped_column(ForeignKey("doctors.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="low")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="alerts")


class MCQSet(Base):
    __tablename__ = "mcq_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    date: Mapped[str] = mapped_column(String(20), index=True)
    questions_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MCQResponse(Base):
    __tablename__ = "mcq_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    date: Mapped[str] = mapped_column(String(20), index=True)
    responses_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="Stable")
    side_effects: Mapped[list] = mapped_column(JSONB, default=list)
    adherence_status: Mapped[str] = mapped_column(String(100), default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    patient: Mapped["Patient"] = relationship(back_populates="mcq_responses")


class OPDSlot(Base):
    __tablename__ = "opd_slots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"), index=True)
    slot_date: Mapped[str] = mapped_column(String(20), index=True)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False)
    patient_visited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["OPDBooking | None"] = relationship(back_populates="slot", uselist=False)


class OPDBooking(Base):
    __tablename__ = "opd_bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    slot_id: Mapped[str] = mapped_column(ForeignKey("opd_slots.id"), unique=True, index=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    patient_name: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    slot: Mapped["OPDSlot"] = relationship(back_populates="booking")
    patient: Mapped["Patient"] = relationship(back_populates="opd_bookings")
    meet_summary: Mapped["MeetSummary | None"] = relationship(back_populates="booking", uselist=False)


class MeetSummary(Base):
    __tablename__ = "meet_summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(ForeignKey("opd_bookings.id"), unique=True)
    doctor_id: Mapped[str] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    transcript: Mapped[str] = mapped_column(Text, default="")
    summary_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    booking: Mapped["OPDBooking"] = relationship(back_populates="meet_summary")


class MeetTranscriptLine(Base):
    """Live consultation transcript lines captured during a video call."""

    __tablename__ = "meet_transcript_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    booking_id: Mapped[str] = mapped_column(ForeignKey("opd_bookings.id"), index=True)
    speaker_label: Mapped[str] = mapped_column(String(255), default="")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_ms: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentRun(Base):
    """Persistent log of agent workflow executions."""

    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str | None] = mapped_column(ForeignKey("patients.id"), index=True)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running")
    events: Mapped[list] = mapped_column(JSONB, default=list)
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    patient: Mapped["Patient | None"] = relationship(back_populates="agent_runs")


class AgentMemory(Base):
    """Long-term episodic memory for agents."""

    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"), index=True)
    memory_type: Mapped[str] = mapped_column(String(50), default="episodic")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
