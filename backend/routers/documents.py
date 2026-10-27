from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from supabase import Client
from typing import List
from models.schemas import DocumentUploadResponse
from core.security import get_current_user, require_role
from core.database import get_db
from core.config import settings
from services.s3_service import s3_service
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    patient_id: str,
    category: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Upload a document for a patient to AWS S3"""
    
    # Verify patient exists
    patient_response = db.table("patients").select("id").eq("id", patient_id).execute()
    if not patient_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Validate category
    valid_categories = ["lab", "imaging", "clinical_note", "prescription", "external", "general"]
    if category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    s3_key = f"patients/{patient_id}/{uuid.uuid4()}.{file_extension}"
    
    # Upload to AWS S3 (with server-side encryption & fallback)
    try:
        s3_service.upload_file(file_content, s3_key, file.content_type or "application/octet-stream")
        file_url = s3_service.get_document_url(s3_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )
    
    # Create document record
    now_iso = datetime.utcnow().isoformat()
    document_data = {
        "patient_id": patient_id,
        "filename": file.filename,
        "file_type": file.content_type or "application/octet-stream",
        "category": category,
        "file_url": file_url,
        "uploaded_by_id": current_user["id"],
        "uploaded_at": now_iso
    }
    
    response = db.table("documents").insert(document_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create document record"
        )
    
    record = response.data[0]
    if "uploaded_at" not in record:
        record["uploaded_at"] = now_iso
    return DocumentUploadResponse(**record)


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
    
    docs = []
    for doc in response.data:
        file_url = doc.get("file_url", "")
        if "patients/" in file_url:
            try:
                key_part = "patients/" + file_url.split("patients/")[-1].split("?")[0]
                doc["file_url"] = s3_service.get_document_url(key_part, expires_in=86400)
            except Exception:
                pass
        if not doc.get("uploaded_at"):
            doc["uploaded_at"] = doc.get("created_at") or datetime.utcnow().isoformat()
        if isinstance(doc.get("uploaded_by_id"), str) and doc["uploaded_by_id"].isdigit():
            doc["uploaded_by_id"] = int(doc["uploaded_by_id"])
        docs.append(DocumentUploadResponse(**doc))
        
    return docs


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Delete a document from S3 and database"""
    
    # Get document to find file path
    doc_response = db.table("documents").select("*").eq("id", document_id).execute()
    
    if not doc_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document = doc_response.data[0]
    file_url = document.get("file_url", "")
    
    # Delete from AWS S3
    if "patients/" in file_url:
        try:
            s3_key = "patients/" + file_url.split("patients/")[-1].split("?")[0]
            s3_service.delete_file(s3_key)
        except Exception:
            pass
    elif "/patient-documents/" in file_url:
        try:
            file_path = file_url.split("/patient-documents/")[-1]
            if hasattr(db, "storage"):
                db.storage.from_("patient-documents").remove([file_path])
        except Exception:
            pass
    
    # Delete database record
    db.table("documents").delete().eq("id", document_id).execute()

    # Clean up associated vector chunks from vector store
    try:
        from services.rag_ingestion_service import resolve_chunk_db
        chunk_db = resolve_chunk_db(db)
        chunk_db.table("patient_record_chunks").delete().eq("source_type", "document").eq("source_id", str(document_id)).execute()
    except Exception as ce:
        logger.warning(f"Warning cleaning up vector chunks for document {document_id}: {ce}")
    
    return None
