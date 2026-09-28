from fastapi import APIRouter, HTTPException, status, Depends
from supabase import Client
from typing import List
from models.schemas import (
    UserResponse, UserCreate, UserUpdate, KnowledgeSourceResponse, SystemMetrics
)
from core.security import get_current_user, require_role, get_password_hash
from core.database import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """List all users (admin only)"""
    
    response = db.table("users").select("*").order("created_at", desc=True).execute()
    
    # Remove password hashes
    users = []
    for user in response.data:
        user.pop("password_hash", None)
        users.append(UserResponse(**user))
    
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """Create a new user (admin only)"""
    
    # Check if email already exists
    existing = db.table("users").select("id").eq("email", user.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    user_data = user.model_dump()
    user_data["password_hash"] = get_password_hash(user_data.pop("password"))
    
    response = db.table("users").insert(user_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    user_response = response.data[0]
    user_response.pop("password_hash", None)
    
    return UserResponse(**user_response)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """Update user details (admin only)"""
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    response = db.table("users").update(update_data).eq("id", user_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_response = response.data[0]
    user_response.pop("password_hash", None)
    
    return UserResponse(**user_response)


@router.get("/knowledge-sources", response_model=List[KnowledgeSourceResponse])
async def list_knowledge_sources(
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """List all knowledge sources (admin only)"""
    
    response = db.table("knowledge_sources").select("*").order("last_synchronized", desc=True).execute()
    
    return [KnowledgeSourceResponse(**source) for source in response.data]


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """Get system metrics (admin only)"""
    
    # Count active users
    active_users_response = db.table("users").select("id", count="exact").eq("status", "active").execute()
    active_users = active_users_response.count or 0

    # Count total users
    total_users_response = db.table("users").select("id", count="exact").execute()
    total_users = total_users_response.count or 0

    # Count total patients
    total_patients_response = db.table("patients").select("id", count="exact").execute()
    total_patients = total_patients_response.count or 0

    # Count total appointments
    total_appointments_response = db.table("appointments").select("id", count="exact").execute()
    total_appointments = total_appointments_response.count or 0

    # Count total analyses
    total_analyses_response = db.table("clinical_analyses").select("id", count="exact").execute()
    total_analyses = total_analyses_response.count or 0

    # Count analyses today
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    analyses_response = db.table("clinical_analyses").select("id", count="exact").gte(
        "generated_at", today_start.isoformat()
    ).execute()
    analyses_today = analyses_response.count or 0
    
    # Count knowledge sources
    sources_response = db.table("knowledge_sources").select("id", count="exact").execute()
    knowledge_sources = sources_response.count or 0
    
    return SystemMetrics(
        active_users=active_users,
        total_users=total_users,
        total_patients=total_patients,
        total_analyses=total_analyses,
        total_appointments=total_appointments,
        analyses_today=analyses_today,
        knowledge_sources=knowledge_sources,
        service_availability=99.98
    )


@router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    current_user: dict = Depends(require_role("admin")),
    db: Client = Depends(get_db)
):
    """Get recent audit log entries (admin only)"""
    
    response = db.table("audit_log").select(
        "*, user:users!user_id(full_name, email)"
    ).order("timestamp", desc=True).limit(limit).execute()
    
    return response.data
