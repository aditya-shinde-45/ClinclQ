from fastapi import APIRouter, HTTPException, status, Depends, Query
from supabase import Client
from typing import List, Optional
from models.schemas import (
    PatientCreate, PatientUpdate, PatientResponse, PatientDetailResponse,
    VisitResponse, AppointmentWithPatient
)
from core.security import get_current_user, require_role
from core.database import get_db
import random
import string

router = APIRouter(prefix="/patients", tags=["Patients"])


def calculate_age(date_of_birth: str) -> int:
    """Calculate age from date of birth string"""
    from datetime import datetime
    dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
    today = datetime.now()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def add_age_to_patient(patient_data: dict) -> dict:
    """Add calculated age and last visit date to patient data"""
    if patient_data.get("date_of_birth"):
        patient_data["age"] = calculate_age(patient_data["date_of_birth"])
    return patient_data


def add_last_visit(db: Client, patient_data: dict) -> dict:
    """Add last visit date to patient data"""
    visits = db.table("visits").select("visit_date").eq(
        "patient_id", patient_data["id"]
    ).order("visit_date", desc=True).limit(1).execute()
    
    if visits.data:
        visit_date = visits.data[0]["visit_date"]
        # Format as a readable date string
        from datetime import datetime
        dt = datetime.fromisoformat(visit_date.replace('Z', '+00:00'))
        patient_data["last_visit"] = dt.strftime("%d %b %Y")
    else:
        patient_data["last_visit"] = None
    
    return patient_data


def generate_patient_id() -> str:
    """Generate a unique patient ID like CLQ-10482"""
    number = random.randint(10000, 99999)
    return f"CLQ-{number}"


@router.get("/doctors", response_model=List[dict])
async def get_doctors(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get list of active doctors (accessible to all authenticated users)"""
    response = db.table("users").select("id, full_name, department").eq("role", "doctor").eq("status", "active").execute()
    return response.data


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    current_user: dict = Depends(require_role("assistant", "doctor")),
    db: Client = Depends(get_db)
):
    """Register a new patient"""
    
    # Generate patient ID
    patient_id = generate_patient_id()
    
    # Check if MRN already exists
    existing = db.table("patients").select("id").eq("mrn", patient.mrn).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MRN already exists"
        )
    
    # Calculate age from date_of_birth
    from datetime import datetime
    dob = datetime.strptime(patient.date_of_birth, "%Y-%m-%d")
    
    # Create patient record
    patient_data = patient.model_dump()
    patient_data["id"] = patient_id
    
    response = db.table("patients").insert(patient_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient"
        )
    
    result = add_age_to_patient(response.data[0])
    return PatientResponse(**result)


@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    q: Optional[str] = Query(None, description="Search by ID, MRN, or name"),
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Search for patients - returns all patients if no query provided"""
    
    # If no query, return all patients
    if not q or q.strip() == "":
        response = db.table("patients").select("*").order("created_at", desc=True).limit(50).execute()
        return [PatientResponse(**add_last_visit(db, add_age_to_patient(p))) for p in response.data]
    
    # Search in multiple fields
    query = db.table("patients").select("*")
    
    # Try exact match on ID or MRN first
    response = query.or_(f"id.eq.{q},mrn.eq.{q}").execute()
    
    if response.data:
        return [PatientResponse(**add_last_visit(db, add_age_to_patient(p))) for p in response.data]
    
    # Otherwise search by name (case-insensitive)
    response = db.table("patients").select("*").ilike("full_name", f"%{q}%").execute()
    
    return [PatientResponse(**add_last_visit(db, add_age_to_patient(p))) for p in response.data]


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get patient details with assigned doctor info"""
    
    response = db.table("patients").select(
        "*, assigned_doctor:users!assigned_doctor_id(*)"
    ).eq("id", patient_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient_data = response.data[0]
    
    # Remove password_hash if doctor info is present
    if patient_data.get("assigned_doctor"):
        patient_data["assigned_doctor"].pop("password_hash", None)
    
    # Add calculated age and last visit
    patient_data = add_age_to_patient(patient_data)
    patient_data = add_last_visit(db, patient_data)
    
    return PatientDetailResponse(**patient_data)


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Update patient information"""
    
    update_data = patient_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    response = db.table("patients").update(update_data).eq("id", patient_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    result = add_age_to_patient(response.data[0])
    return PatientResponse(**result)


@router.get("/{patient_id}/timeline", response_model=List[VisitResponse])
async def get_patient_timeline(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get patient visit history/timeline"""
    
    response = db.table("visits").select("*").eq(
        "patient_id", patient_id
    ).order("visit_date", desc=True).execute()
    
    return [VisitResponse(**visit) for visit in response.data]


@router.get("/{patient_id}/appointments", response_model=List[AppointmentWithPatient])
async def get_patient_appointments(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get patient appointments"""
    
    response = db.table("appointments").select(
        "*, patient:patients!patient_id(full_name)"
    ).eq("patient_id", patient_id).order("appointment_time", desc=False).execute()
    
    appointments = []
    for appt in response.data:
        appt_dict = dict(appt)
        if appt_dict.get("patient"):
            appt_dict["patient_name"] = appt_dict["patient"]["full_name"]
            appt_dict.pop("patient")
        appointments.append(AppointmentWithPatient(**appt_dict))
    
    return appointments
