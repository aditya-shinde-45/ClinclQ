from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from supabase import Client
from typing import List
from datetime import datetime
from models.schemas import (
    AnalysisRequest, AnalysisResponse, DecisionCreate, DecisionResponse,
    DiagnosisResponse, RecommendationResponse, DrugInteractionResponse
)
from core.security import get_current_user, require_role
from core.database import get_db
from services.bedrock_service import bedrock_service
import random

router = APIRouter(prefix="/analyses", tags=["Clinical Analyses"])


def generate_report_id() -> str:
    """Generate report ID like CDS-2025-0618"""
    now = datetime.now()
    seq = random.randint(100, 9999)
    return f"CDS-{now.year}-{seq:04d}"


def process_analysis_background(analysis_id: int, patient_data: dict, symptoms: str, observations: str, test_results: str, db: Client):
    """Background task to process analysis with AWS Bedrock AI engine"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Generate analysis via AWS Bedrock (or graceful fallback)
        mock_data = bedrock_service.generate_analysis(
            patient_data=patient_data,
            new_symptoms=symptoms,
            observations=observations,
            test_results=test_results
        )
        
        # Insert diagnoses
        for diag in mock_data.get("diagnoses", []):
            db.table("diagnoses").insert({
                "analysis_id": analysis_id,
                "rank": diag.get("rank", 1),
                "name": diag.get("name", "Clinical Differential"),
                "confidence_percentage": diag.get("confidence_percentage", 75.0),
                "confidence_label": diag.get("confidence_label", "moderate"),
                "summary": diag.get("summary", ""),
                "evidence": diag.get("evidence", [])
            }).execute()
        
        # Insert recommendations
        for rec in mock_data.get("recommendations", []):
            db.table("recommendations").insert({
                "analysis_id": analysis_id,
                "step_number": rec.get("step_number", 1),
                "title": rec.get("title", "Clinical Action"),
                "description": rec.get("description", "")
            }).execute()
        
        # Insert drug interactions
        for interaction in mock_data.get("drug_interactions", []):
            db.table("drug_interactions").insert({
                "analysis_id": analysis_id,
                "severity": interaction.get("severity", "moderate"),
                "title": interaction.get("title", "Drug Interaction Check"),
                "description": interaction.get("description", "")
            }).execute()
        
        # Link risk factors
        for risk_name in mock_data.get("risk_factors", []):
            try:
                # Get or create risk factor
                risk_response = db.table("risk_factors").select("id").eq("name", risk_name).execute()
                if risk_response.data:
                    risk_id = risk_response.data[0]["id"]
                else:
                    new_risk = db.table("risk_factors").insert({"name": risk_name}).execute()
                    risk_id = new_risk.data[0]["id"]
                
                # Link to analysis
                db.table("analysis_risk_factors").insert({
                    "analysis_id": analysis_id,
                    "risk_factor_id": risk_id
                }).execute()
            except Exception as re:
                logger.warning(f"Error linking risk factor {risk_name}: {re}")
        
        # Update status to awaiting_review
        db.table("clinical_analyses").update({
            "status": "awaiting_review"
        }).eq("id", analysis_id).execute()

    except Exception as e:
        logger.error(f"Error in process_analysis_background for analysis {analysis_id}: {e}", exc_info=True)
        # Ensure analysis status is updated so UI doesn't hang in processing
        db.table("clinical_analyses").update({
            "status": "awaiting_review"
        }).eq("id", analysis_id).execute()


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("doctor")),
    db: Client = Depends(get_db)
):
    """Request a new clinical analysis powered by AWS Bedrock"""
    
    # Get patient data
    patient_response = db.table("patients").select("*").eq("id", request.patient_id).execute()
    if not patient_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient_data = patient_response.data[0]
    
    # Check for uploaded S3 documents to enrich Bedrock clinical context
    docs_context = ""
    try:
        docs_res = db.table("documents").select("filename, category, uploaded_at").eq("patient_id", request.patient_id).execute()
        if docs_res.data:
            doc_summaries = [f"{d.get('filename')} ({d.get('category')})" for d in docs_res.data]
            docs_context = f" | Attached S3 Documents: {', '.join(doc_summaries)}"
    except Exception:
        docs_context = ""

    combined_test_results = (request.test_results or "") + docs_context

    # Create analysis record
    report_id = generate_report_id()
    analysis_data = {
        "patient_id": request.patient_id,
        "report_id": report_id,
        "status": "processing",
        "new_symptoms": request.new_symptoms,
        "observations": request.observations,
        "test_results": request.test_results,
        "clinical_notes": request.clinical_notes,
        "reviewed_by_id": current_user["id"],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    response = db.table("clinical_analyses").insert(analysis_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis"
        )
    
    analysis = response.data[0]
    
    # Start background processing via Bedrock
    background_tasks.add_task(
        process_analysis_background,
        analysis["id"],
        patient_data,
        request.new_symptoms,
        request.observations,
        combined_test_results,
        db
    )
    
    # Return initial response
    return AnalysisResponse(
        id=analysis["id"],
        patient_id=analysis["patient_id"],
        report_id=analysis["report_id"],
        status=analysis["status"],
        diagnoses=[],
        recommendations=[],
        drug_interactions=[],
        risk_factors=[],
        generated_at=analysis.get("generated_at", datetime.utcnow()),
        reviewed_at=None
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get analysis details with all related data"""
    
    # Get analysis
    analysis_response = db.table("clinical_analyses").select("*").eq("id", analysis_id).execute()
    if not analysis_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    analysis = analysis_response.data[0]
    
    # Get diagnoses
    diagnoses_response = db.table("diagnoses").select("*").eq(
        "analysis_id", analysis_id
    ).order("rank").execute()
    diagnoses = [DiagnosisResponse(**d) for d in diagnoses_response.data]
    
    # Get recommendations
    recs_response = db.table("recommendations").select("*").eq(
        "analysis_id", analysis_id
    ).order("step_number").execute()
    recommendations = [RecommendationResponse(**r) for r in recs_response.data]
    
    # Get drug interactions
    interactions_response = db.table("drug_interactions").select("*").eq(
        "analysis_id", analysis_id
    ).execute()
    drug_interactions = [DrugInteractionResponse(**i) for i in interactions_response.data]
    
    # Get risk factors
    risk_response = db.table("analysis_risk_factors").select(
        "risk_factor:risk_factors!risk_factor_id(name)"
    ).eq("analysis_id", analysis_id).execute()
    risk_factors = [r["risk_factor"]["name"] for r in risk_response.data if r.get("risk_factor")]
    
    return AnalysisResponse(
        id=analysis["id"],
        patient_id=analysis["patient_id"],
        report_id=analysis["report_id"],
        status=analysis["status"],
        diagnoses=diagnoses,
        recommendations=recommendations,
        drug_interactions=drug_interactions,
        risk_factors=risk_factors,
        generated_at=analysis["generated_at"],
        reviewed_at=analysis.get("reviewed_at")
    )


@router.get("/patient/{patient_id}", response_model=List[AnalysisResponse])
async def get_patient_analyses(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Get all analyses for a patient"""
    
    analyses_response = db.table("clinical_analyses").select("*").eq(
        "patient_id", patient_id
    ).order("generated_at", desc=True).execute()
    
    results = []
    for analysis in analyses_response.data:
        # Get full analysis with related data
        full_analysis = await get_analysis(analysis["id"], current_user, db)
        results.append(full_analysis)
    
    return results


@router.post("/{analysis_id}/decision", response_model=DecisionResponse, status_code=status.HTTP_201_CREATED)
async def record_decision(
    analysis_id: int,
    decision: DecisionCreate,
    current_user: dict = Depends(require_role("doctor")),
    db: Client = Depends(get_db)
):
    """Record a clinical decision on an analysis"""
    
    # Verify analysis exists
    analysis_response = db.table("clinical_analyses").select("*").eq("id", analysis_id).execute()
    if not analysis_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Create decision
    now_iso = datetime.utcnow().isoformat()
    decision_data = decision.model_dump()
    decision_data["decided_by_id"] = current_user["id"]
    decision_data["decided_at"] = now_iso
    
    response = db.table("clinical_decisions").insert(decision_data).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record decision"
        )
    
    # Update analysis status
    new_status = decision.decision_type.value  # approve, modify, or reject
    db.table("clinical_analyses").update({
        "status": new_status,
        "reviewed_at": now_iso
    }).eq("id", analysis_id).execute()
    
    record = response.data[0]
    if "decided_at" not in record:
        record["decided_at"] = now_iso
    return DecisionResponse(**record)
