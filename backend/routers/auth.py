from fastapi import APIRouter, HTTPException, status, Depends
from supabase import Client
from models.schemas import LoginRequest, LoginResponse, UserResponse
from core.security import verify_password, create_access_token
from core.database import get_db
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, db: Client = Depends(get_db)):
    """Authenticate user and return JWT token"""
    
    # Query user by email
    response = db.table("users").select("*").eq("email", credentials.email).execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    user = response.data[0]
    
    # Check if account is active
    if user["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user["id"], "role": user["role"], "email": user["email"]}
    )
    
    # Remove password hash from response
    user.pop("password_hash", None)
    
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(**user)
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Successfully logged out"}
