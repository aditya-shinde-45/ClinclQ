from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from supabase import Client
from typing import List
from models.schemas import DocumentUploadResponse
from core.security import get_current_user, require_role
from core.database import get_db
from core.config import settings
import uuid

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    patient_id: str,
    category: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Upload a document for a patient"""
    
    # Verify patient exists
    patient_response = db.table("patients").select("id").eq("id", patient_id).execute()
    if not patient_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate category
    valid_categories = ["lab", "imaging", "clinical_note", "prescription", "external"]
    if category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{patient_id}/{uuid.uuid4()}.{file_extension}"
    
    # Upload to Supabase Storage
    try:
        storage_response = db.storage.from_("patient-documents").upload(
            unique_filename,
            file_content,
            {"content-type": file.content_type}
        )
        
        # Get public URL
        file_url = db.storage.from_("patient-documents").get_public_url(unique_filename)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )
    
    # Create document record
    document_data = {
        "patient_id": patient_id,
        "filename": file.filename,
        "file_type": file.content_type or "application/octet-stream",
        "category": category,
        "file_url": file_url,
        "uploaded_by_id": current_user["id"]
    }
    
    response = db.table("documents").insert(document_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document record"
        )
    
    return DocumentUploadResponse(**response.data[0])


@router.get("/patient/{patient_id}", response_model=List[DocumentUploadResponse])
async def get_patient_documents(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get all documents for a patient"""
    
    response = db.table("documents").select("*").eq(
        "patient_id", patient_id
    ).order("uploaded_at", desc=True).execute()
    
    return [DocumentUploadResponse(**doc) for doc in response.data]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Delete a document"""
    
    # Get document to find file path
    doc_response = db.table("documents").select("*").eq("id", document_id).execute()
    
    if not doc_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document = doc_response.data[0]
    
    # Extract file path from URL
    file_path = document["file_url"].split("/patient-documents/")[-1]
    
    # Delete from storage
    try:
        db.storage.from_("patient-documents").remove([file_path])
    except Exception as e:
        # Continue even if storage deletion fails
        pass
    
    # Delete database record
    db.table("documents").delete().eq("id", document_id).execute()
    
    return None
