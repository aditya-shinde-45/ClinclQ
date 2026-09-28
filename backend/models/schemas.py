from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    DOCTOR = "doctor"
    ASSISTANT = "assistant"
    ADMIN = "admin"


class UserStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVATED = "deactivated"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitType(str, Enum):
    CLINICAL_NOTE = "clinical_note"
    DOCTOR_NOTE = "doctor_note"
    LAB_RESULT = "lab_result"
    AI_ANALYSIS = "ai_analysis"
    PROCEDURE = "procedure"


class AnalysisStatus(str, Enum):
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"


class DecisionType(str, Enum):
    APPROVE = "approve"
    MODIFY = "modify"
    REJECT = "reject"


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    department: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    id: int
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Patient schemas
class PatientBase(BaseModel):
    full_name: str
    date_of_birth: str
    gender: str
    contact_number: Optional[str] = None
    reason_for_visit: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    past_treatments: Optional[str] = None


class PatientCreate(PatientBase):
    mrn: str
    assigned_doctor_id: Optional[int] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    contact_number: Optional[str] = None
    reason_for_visit: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    past_treatments: Optional[str] = None
    assigned_doctor_id: Optional[int] = None


class PatientResponse(PatientBase):
    id: str
    mrn: str
    age: Optional[int] = None
    assigned_doctor_id: Optional[int] = None
    last_visit: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatientDetailResponse(PatientResponse):
    assigned_doctor: Optional[UserResponse] = None


# Appointment schemas
class AppointmentBase(BaseModel):
    appointment_time: datetime
    reason: str


class AppointmentCreate(AppointmentBase):
    patient_id: str
    doctor_id: int


class AppointmentUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None


class AppointmentResponse(AppointmentBase):
    id: int
    patient_id: str
    doctor_id: int
    status: AppointmentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class AppointmentWithPatient(AppointmentResponse):
    patient_name: str


# Visit/Timeline schemas
class VisitCreate(BaseModel):
    patient_id: str
    title: str
    body: str
    type: VisitType
    created_by_id: Optional[int] = None


class VisitResponse(BaseModel):
    id: int
    patient_id: str
    visit_date: datetime
    title: str
    body: str
    type: VisitType
    created_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Clinical Analysis schemas
class DiagnosisResponse(BaseModel):
    rank: int
    name: str
    confidence_percentage: float
    confidence_label: str
    summary: str
    evidence: List[str]


class RecommendationResponse(BaseModel):
    step_number: int
    title: str
    description: str


class DrugInteractionResponse(BaseModel):
    severity: str
    title: str
    description: str


class AnalysisRequest(BaseModel):
    patient_id: str
    new_symptoms: str
    observations: str
    test_results: Optional[str] = None
    clinical_notes: Optional[str] = None


class AnalysisResponse(BaseModel):
    id: int
    patient_id: str
    report_id: str
    status: AnalysisStatus
    diagnoses: List[DiagnosisResponse]
    recommendations: List[RecommendationResponse]
    drug_interactions: List[DrugInteractionResponse]
    risk_factors: List[str]
    generated_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Clinical Decision schemas
class DecisionCreate(BaseModel):
    analysis_id: int
    decision_type: DecisionType
    clinician_notes: Optional[str] = None
    attestation_confirmed: bool = True


class DecisionResponse(BaseModel):
    id: int
    analysis_id: int
    decision_type: DecisionType
    clinician_notes: Optional[str] = None
    attestation_confirmed: bool
    decided_by_id: int
    decided_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentUploadResponse(BaseModel):
    id: int
    patient_id: str
    filename: str
    file_type: str
    category: str
    file_url: str
    uploaded_at: datetime
    uploaded_by_id: int

    class Config:
        from_attributes = True


# Knowledge Source schemas (Admin)
class KnowledgeSourceResponse(BaseModel):
    id: int
    name: str
    type: str
    version: str
    status: str
    last_synchronized: datetime

    class Config:
        from_attributes = True


# System metrics (Admin)
class SystemMetrics(BaseModel):
    active_users: int
    total_users: int
    total_patients: int
    total_analyses: int
    total_appointments: int
    analyses_today: int
    knowledge_sources: int
    service_availability: float
