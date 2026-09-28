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


@router.get("/today", response_model=List[AppointmentWithPatient])
async def get_todays_appointments(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get today's appointments for the current doctor"""
    
    # Get start and end of today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # If doctor, filter by their ID
    query = db.table("appointments").select(
        "*, patient:patients!patient_id(full_name)"
    ).gte("appointment_time", today_start.isoformat()).lt(
        "appointment_time", today_end.isoformat()
    )
    
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


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment: AppointmentCreate,
    current_user: dict = Depends(require_role("assistant", "doctor")),
    db: Client = Depends(get_db)
):
    """Create a new appointment"""
    
    appointment_data = appointment.model_dump()
    
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
    
    update_data = appointment_update.model_dump(exclude_unset=True)
    
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
async def cancel_appointment(
    appointment_id: int,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Cancel an appointment"""
    
    response = db.table("appointments").update(
        {"status": "cancelled"}
    ).eq("id", appointment_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
    
    return None
