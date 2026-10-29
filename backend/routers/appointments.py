from fastapi import APIRouter, HTTPException, status, Depends
from supabase import Client
from typing import List
from datetime import datetime, timedelta
from models.schemas import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentWithPatient
)
from core.security import get_current_user, require_role
from core.database import get_db

router = APIRouter(prefix="/appointments", tags=["Appointments"])


async def list_appointments(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db),
    start: datetime | None = None,
    end: datetime | None = None,
):
    query = db.table("appointments").select(
        "*, patient:patients!patient_id(full_name)"
    )
    if start:
        query = query.gte("appointment_time", start.isoformat())
    if end:
        query = query.lt("appointment_time", end.isoformat())
    
    if current_user["role"] == "doctor":
        query = query.eq("doctor_id", current_user["id"])
    
    response = query.order("appointment_time").execute()
    
    appointments = []
    for appt in response.data:
        appt_dict = dict(appt)
        if appt_dict.get("patient"):
            appt_dict["patient_name"] = appt_dict["patient"]["full_name"]
            appt_dict.pop("patient")
        appointments.append(AppointmentWithPatient(**appt_dict))
    
    return appointments


@router.get("/today", response_model=List[AppointmentWithPatient])
async def get_todays_appointments(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get appointments scheduled for today."""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return await list_appointments(current_user, db, today_start, today_start + timedelta(days=1))


@router.get("/upcoming", response_model=List[AppointmentWithPatient])
async def get_upcoming_appointments(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get appointments scheduled from tomorrow onward."""
    tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return await list_appointments(current_user, db, tomorrow)


@router.get("/all", response_model=List[AppointmentWithPatient])
async def get_all_appointments(
    current_user: dict = Depends(require_role("assistant", "doctor")),
    db: Client = Depends(get_db)
):
    """Get all appointments for appointment management."""
    return await list_appointments(current_user, db)


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate,
    current_user: dict = Depends(require_role("assistant", "doctor")),
    db: Client = Depends(get_db)
):
    """Create a new appointment"""
    
    appointment_data = appointment.model_dump(mode="json")
    
    response = db.table("appointments").insert(appointment_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create appointment"
        )
    
    return AppointmentResponse(**response.data[0])


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_update: AppointmentUpdate,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Update appointment details or status"""
    
    update_data = appointment_update.model_dump(mode="json", exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    response = db.table("appointments").update(update_data).eq("id", appointment_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return AppointmentResponse(**response.data[0])


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: int,
    current_user: dict = Depends(require_role("assistant")),
    db: Client = Depends(get_db)
):
    """Permanently delete an appointment. Only clinic assistants may delete."""
    
    existing = db.table("appointments").select("id").eq("id", appointment_id).execute()
    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )

    db.table("appointments").delete().eq("id", appointment_id).execute()

    return None
