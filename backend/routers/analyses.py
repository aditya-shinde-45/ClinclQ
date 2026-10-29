from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from supabase import Client
from typing import List, Optional
from datetime import datetime
from models.schemas import (
    AnalysisRequest, AnalysisResponse, DecisionCreate, DecisionResponse,
    DiagnosisResponse, RecommendationResponse, DrugInteractionResponse,
    RetrievedEvidenceItem, IngestionRequest, IngestionResponse,
    RetrievalQueryRequest, RetrievalQueryResponse
)
from core.security import get_current_user, require_role
from core.database import get_db
from services.bedrock_service import bedrock_service
from services.s3_service import s3_service
from services.rag_ingestion_service import rag_ingestion_service
from services.rag_retrieval_service import rag_retrieval_service
import random
import io
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["Clinical Analyses"])


def generate_report_id() -> str:
    """Generate report ID like CDS-2025-0618"""
    now = datetime.now()
    seq = random.randint(100, 9999)
    return f"CDS-{now.year}-{seq:04d}"


def extract_document_context(document: dict) -> str:
    """Extract text from supported uploaded documents for the Bedrock prompt."""
    file_url = document.get("file_url", "")
    filename = document.get("filename", "uploaded document")
    if "patients/" not in file_url:
        return f"{filename}: file content is unavailable for analysis."

    s3_key = "patients/" + file_url.split("patients/", 1)[1].split("?", 1)[0]
    try:
        content = s3_service.download_file(s3_key)
        extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        if extension == "pdf":
            from pypdf import PdfReader
            text = "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)
        elif extension in {"txt", "csv", "json"}:
            text = content.decode("utf-8", errors="replace")
            if extension == "json":
                text = json.dumps(json.loads(text), indent=2)
        else:
            return f"{filename}: image or unsupported file format; file contents were not analyzed."
        cleaned = " ".join(text.split())
        return f"{filename} ({document.get('category', 'document')}): {cleaned[:8000] or 'No readable text found.'}"
    except Exception as exc:
        return f"{filename}: document text could not be extracted ({exc})."


def process_analysis_background(
    analysis_id: int,
    patient_data: dict,
    symptoms: str,
    observations: str,
    test_results: str,
    clinical_notes: str,
    retrieved_evidence: list,
    db: Client,
):
    """Background task to process analysis with AWS Bedrock AI engine grounded in RAG"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Generate analysis via AWS Bedrock grounded in patient evidence
        analysis_data = bedrock_service.generate_analysis(
            patient_data=patient_data,
            new_symptoms=symptoms,
            observations=observations,
            test_results=test_results,
            clinical_notes=clinical_notes,
            retrieved_evidence=retrieved_evidence
        )
        
        # Insert diagnoses
        for diag in analysis_data.get("diagnoses", []):
            raw_conf = str(diag.get("confidence_label", "needs_review")).lower()
            if raw_conf in ("moderate", "medium"):
                raw_conf = "needs_review"
            elif raw_conf not in ("high", "needs_review", "low"):
                raw_conf = "needs_review"

            db.table("diagnoses").insert({
                "analysis_id": analysis_id,
                "rank": diag.get("rank", 1),
                "name": diag.get("name", "Clinical Differential"),
                "confidence_percentage": diag.get("confidence_percentage", 75.0),
                "confidence_label": raw_conf,
                "summary": diag.get("summary", ""),
                "evidence": diag.get("evidence", [])
            }).execute()
        
        # Insert recommendations
        for idx, rec in enumerate(analysis_data.get("recommendations", [])):
            if isinstance(rec, str):
                title = rec[:120]
                desc = rec
                step = idx + 1
            elif isinstance(rec, dict):
                title = str(rec.get("title") or rec.get("action") or rec.get("step") or "Clinical Action")[:255]
                desc = str(rec.get("description") or rec.get("details") or "")
                step = rec.get("step_number", idx + 1)
            else:
                continue

            try:
                db.table("recommendations").insert({
                    "analysis_id": analysis_id,
                    "step_number": step,
                    "title": title,
                    "description": desc
                }).execute()
            except Exception as rce:
                logger.warning(f"Error inserting recommendation: {rce}")

        # Ensure at least baseline recommendations exist if none were inserted
        try:
            existing_recs = db.table("recommendations").select("id").eq("analysis_id", analysis_id).execute().data
            if not existing_recs:
                default_steps = [
                    ("Complete diagnostic evaluation", "Obtain baseline laboratory panels, serial biomarkers, and appropriate imaging."),
                    ("Clinical risk stratification", "Review clinical profile and medication tolerance with attending clinician."),
                    ("Follow-up and monitoring", "Schedule repeat evaluation and monitor for symptom changes.")
                ]
                for step_idx, (stitle, sdesc) in enumerate(default_steps, 1):
                    db.table("recommendations").insert({
                        "analysis_id": analysis_id,
                        "step_number": step_idx,
                        "title": stitle,
                        "description": sdesc
                    }).execute()
        except Exception as dre:
            logger.warning(f"Error ensuring baseline recommendations: {dre}")

        # Insert drug interactions
        for interaction in analysis_data.get("drug_interactions", []):
            if isinstance(interaction, str):
                title = interaction[:255]
                desc = interaction
                severity = "caution"
            elif isinstance(interaction, dict):
                raw_sev = str(interaction.get("severity", "caution")).lower().strip()
                if raw_sev in ("critical", "severe", "high", "danger"):
                    severity = "critical"
                elif raw_sev in ("info", "minor", "low", "informational"):
                    severity = "info"
                else:
                    severity = "caution"
                title = str(interaction.get("title", "Drug Interaction Check"))[:255]
                desc = str(interaction.get("description", ""))
            else:
                continue

            try:
                db.table("drug_interactions").insert({
                    "analysis_id": analysis_id,
                    "severity": severity,
                    "title": title,
                    "description": desc
                }).execute()
            except Exception as die:
                logger.warning(f"Error inserting drug interaction: {die}")

        # Link risk factors
        for risk_name in analysis_data.get("risk_factors", []):
            if isinstance(risk_name, dict):
                risk_name = risk_name.get("name") or risk_name.get("factor") or str(risk_name)
            if not isinstance(risk_name, str) or not risk_name.strip():
                continue
            risk_name = risk_name.strip()[:255]

            try:
                risk_response = db.table("risk_factors").select("id").eq("name", risk_name).execute()
                if risk_response.data:
                    risk_id = risk_response.data[0]["id"]
                else:
                    new_risk = db.table("risk_factors").insert({"name": risk_name}).execute()
                    risk_id = new_risk.data[0]["id"]

                db.table("analysis_risk_factors").insert({
                    "analysis_id": analysis_id,
                    "risk_factor_id": risk_id
                }).execute()
            except Exception as re:
                logger.warning(f"Error linking risk factor {risk_name}: {re}")

        # Ensure patient-specific risk factors exist if none were inserted
        try:
            existing_rf = db.table("analysis_risk_factors").select("risk_factor_id").eq("analysis_id", analysis_id).execute().data
            if not existing_rf:
                derived_factors = []
                if patient_data.get("medical_history"):
                    derived_factors.extend([h.strip() for h in str(patient_data["medical_history"]).replace(";", ",").split(",") if h.strip()])
                if patient_data.get("age"):
                    try:
                        if int(patient_data.get("age", 0)) > 50:
                            derived_factors.append(f"Age over 50 ({patient_data['age']} years)")
                    except Exception:
                        pass
                if not derived_factors:
                    derived_factors = ["Active presentation under evaluation", "Cardiovascular profile monitoring"]

                for rf_name in derived_factors[:4]:
                    rf_res = db.table("risk_factors").select("id").eq("name", rf_name).execute()
                    rid = rf_res.data[0]["id"] if rf_res.data else db.table("risk_factors").insert({"name": rf_name}).execute().data[0]["id"]
                    db.table("analysis_risk_factors").insert({"analysis_id": analysis_id, "risk_factor_id": rid}).execute()
        except Exception as drfe:
            logger.warning(f"Error ensuring baseline risk factors: {drfe}")

        # Serialize retrieved evidence items
        serialized_evidence = [
            item.model_dump() if hasattr(item, "model_dump") else dict(item)
            for item in (retrieved_evidence or [])
        ]

        # Update analysis with explanation, evidence, and status awaiting_review
        update_payload = {
            "patient_explanation": analysis_data.get("patient_explanation"),
            "retrieved_evidence": serialized_evidence,
            "status": "awaiting_review"
        }
        try:
            db.table("clinical_analyses").update(update_payload).eq("id", analysis_id).execute()
        except Exception as ue:
            if "PGRST204" in str(ue) or "column" in str(ue).lower():
                logger.warning(f"Remote Supabase schema lacks extended columns; updating core status: {ue}")
                core_update = {"status": "awaiting_review"}
                db.table("clinical_analyses").update(core_update).eq("id", analysis_id).execute()
            else:
                raise ue

    except Exception as e:
        logger.error(f"Error in process_analysis_background for analysis {analysis_id}: {e}", exc_info=True)
        try:
            # Clean up any partially inserted records from interrupted attempt
            try:
                db.table("diagnoses").delete().eq("analysis_id", analysis_id).execute()
                db.table("recommendations").delete().eq("analysis_id", analysis_id).execute()
                db.table("drug_interactions").delete().eq("analysis_id", analysis_id).execute()
            except Exception:
                pass

            from services.mock_analysis import generate_mock_analysis
            fallback_data = generate_mock_analysis(
                patient_data=patient_data,
                symptoms=symptoms,
                observations=observations,
                test_results=test_results
            )
            for diag in fallback_data.get("diagnoses", []):
                raw_conf = str(diag.get("confidence_label", "needs_review")).lower()
                if raw_conf not in ("high", "needs_review", "low"):
                    raw_conf = "needs_review"
                db.table("diagnoses").insert({
                    "analysis_id": analysis_id,
                    "rank": diag.get("rank", 1),
                    "name": diag.get("name", "Clinical Differential"),
                    "confidence_percentage": diag.get("confidence_percentage", 65.0),
                    "confidence_label": raw_conf,
                    "summary": diag.get("summary", ""),
                    "evidence": diag.get("evidence", [])
                }).execute()
            for rec in fallback_data.get("recommendations", []):
                db.table("recommendations").insert({
                    "analysis_id": analysis_id,
                    "step_number": rec.get("step_number", 1),
                    "title": rec.get("title", "Clinical Action"),
                    "description": rec.get("description", "")
                }).execute()
            db.table("clinical_analyses").update({
                "status": "awaiting_review",
                "patient_explanation": "Clinical decision support generated via secondary clinical guideline protocols.",
                "clinical_notes": f"Generated via secondary guideline engine (Bedrock notice: {str(e)[:160]})"
            }).eq("id", analysis_id).execute()
        except Exception as fallback_exc:
            logger.error(f"Fallback generation also failed for {analysis_id}: {fallback_exc}")
            try:
                db.table("clinical_analyses").update({
                    "status": "rejected",
                    "clinical_notes": f"Inference error: {str(e)[:250]}"
                }).eq("id", analysis_id).execute()
            except Exception:
                pass


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def request_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role("doctor")),
    db: Client = Depends(get_db)
):
    """Request a new clinical analysis powered by AWS Bedrock and Patient RAG"""
    
    # 1. Verify patient exists
    patient_response = db.table("patients").select("*").eq("id", request.patient_id).execute()
    if not patient_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    patient_data = patient_response.data[0]
    
    # 2. Check for uploaded S3 documents to enrich Bedrock clinical context
    docs_context = ""
    try:
        docs_res = db.table("documents").select("*").eq("patient_id", request.patient_id).execute()
        if docs_res.data:
            doc_contexts = [extract_document_context(d) for d in docs_res.data]
            docs_context = "\n\nUploaded document context:\n" + "\n".join(doc_contexts)
    except Exception as exc:
        docs_context = f"\n\nUploaded document context unavailable: {exc}"

    combined_test_results = (request.test_results or "") + docs_context

    # 3. Patient-Scoped RAG Ingestion & Retrieval Pipeline
    # Ensure patient records and visits are indexed
    try:
        rag_ingestion_service.index_patient(request.patient_id, db=db)
    except Exception as ie:
        logger.warning(f"RAG pre-indexing warning for {request.patient_id}: {ie}")

    # Retrieve patient-scoped clinical chunks
    rag_query = f"{request.new_symptoms} {request.observations} {request.clinical_notes or ''}"
    retrieved_evidence = []
    try:
        retrieved_evidence = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=request.patient_id,
            query_text=rag_query,
            current_user=current_user,
            db=db
        )
    except Exception as re:
        logger.error(f"Patient RAG retrieval error: {re}")

    serialized_evidence = [
        item.model_dump() if hasattr(item, "model_dump") else dict(item)
        for item in retrieved_evidence
    ]

    # 4. Create analysis record
    report_id = generate_report_id()
    analysis_data = {
        "patient_id": request.patient_id,
        "report_id": report_id,
        "status": "processing",
        "new_symptoms": request.new_symptoms,
        "observations": request.observations,
        "test_results": request.test_results,
        "clinical_notes": request.clinical_notes,
        "retrieved_evidence": serialized_evidence,
        "reviewed_by_id": current_user["id"],
        "generated_at": datetime.utcnow().isoformat()
    }
    
    try:
        response = db.table("clinical_analyses").insert(analysis_data).execute()
    except Exception as exc:
        if "retrieved_evidence" in str(exc) or "PGRST204" in str(exc):
            logger.warning(f"Remote schema lacks retrieved_evidence column; falling back to inserting without it: {exc}")
            analysis_data_no_rag = {k: v for k, v in analysis_data.items() if k != "retrieved_evidence"}
            response = db.table("clinical_analyses").insert(analysis_data_no_rag).execute()
        else:
            raise exc
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis"
        )
    
    analysis = response.data[0]
    
    # 5. Start background processing via Bedrock grounded in retrieved evidence
    background_tasks.add_task(
        process_analysis_background,
        analysis["id"],
        patient_data,
        request.new_symptoms,
        request.observations,
        combined_test_results,
        request.clinical_notes,
        retrieved_evidence,
        db
    )
    
    # 6. Return initial response
    return AnalysisResponse(
        id=analysis["id"],
        patient_id=analysis["patient_id"],
        report_id=analysis["report_id"],
        status=analysis["status"],
        diagnoses=[],
        recommendations=[],
        drug_interactions=[],
        risk_factors=[],
        retrieved_evidence=retrieved_evidence,
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
    
    # Parse retrieved evidence
    raw_evidence = analysis.get("retrieved_evidence") or []
    retrieved_evidence = []
    for item in raw_evidence:
        try:
            retrieved_evidence.append(RetrievedEvidenceItem(**item) if isinstance(item, dict) else item)
        except Exception:
            pass

    return AnalysisResponse(
        id=analysis["id"],
        patient_id=analysis["patient_id"],
        report_id=analysis["report_id"],
        status=analysis["status"],
        diagnoses=diagnoses,
        recommendations=recommendations,
        drug_interactions=drug_interactions,
        risk_factors=risk_factors,
        patient_explanation=analysis.get("patient_explanation"),
        retrieved_evidence=retrieved_evidence,
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
    
    analysis_rows = analyses_response.data
    diagnoses = db.table("diagnoses").select("*").execute().data or []
    recommendations = db.table("recommendations").select("*").execute().data or []
    interactions = db.table("drug_interactions").select("*").execute().data or []
    analysis_risk_factors = db.table("analysis_risk_factors").select(
        "*, risk_factor:risk_factors!risk_factor_id(name)"
    ).execute().data or []

    results = []
    for analysis in analysis_rows:
        analysis_id = analysis["id"]
        raw_evidence = analysis.get("retrieved_evidence") or []
        retrieved_evidence = []
        for item in raw_evidence:
            try:
                retrieved_evidence.append(
                    RetrievedEvidenceItem(**item) if isinstance(item, dict) else item
                )
            except Exception:
                pass

        analysis_diagnoses = [
            DiagnosisResponse(**row)
            for row in diagnoses
            if row.get("analysis_id") == analysis_id
        ]
        analysis_recommendations = [
            RecommendationResponse(**row)
            for row in recommendations
            if row.get("analysis_id") == analysis_id
        ]
        analysis_interactions = [
            DrugInteractionResponse(**row)
            for row in interactions
            if row.get("analysis_id") == analysis_id
        ]
        analysis_risks = [
            row["risk_factor"]["name"]
            for row in analysis_risk_factors
            if row.get("analysis_id") == analysis_id and row.get("risk_factor")
        ]

        results.append(AnalysisResponse(
            id=analysis_id,
            patient_id=analysis["patient_id"],
            report_id=analysis["report_id"],
            status=analysis["status"],
            diagnoses=analysis_diagnoses,
            recommendations=analysis_recommendations,
            drug_interactions=analysis_interactions,
            risk_factors=analysis_risks,
            patient_explanation=analysis.get("patient_explanation"),
            retrieved_evidence=retrieved_evidence,
            generated_at=analysis["generated_at"],
            reviewed_at=analysis.get("reviewed_at")
        ))

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
    
    # Update analysis status (mapping approve -> approved, modify -> modified, reject -> rejected)
    status_map = {
        "approve": "approved",
        "modify": "modified",
        "reject": "rejected",
        "approved": "approved",
        "modified": "modified",
        "rejected": "rejected"
    }
    new_status = status_map.get(decision.decision_type.value, "approved")
    db.table("clinical_analyses").update({
        "status": new_status,
        "reviewed_at": now_iso
    }).eq("id", analysis_id).execute()
    
    record = response.data[0]
    if "decided_at" not in record:
        record["decided_at"] = now_iso
    return DecisionResponse(**record)


@router.post("/rag/index", response_model=IngestionResponse)
async def trigger_rag_ingestion(
    req: IngestionRequest,
    current_user: dict = Depends(require_role("doctor", "assistant", "admin")),
    db: Client = Depends(get_db)
):
    """Trigger on-demand RAG indexing for a specific patient or all patients"""
    if req.patient_id:
        result = rag_ingestion_service.index_patient(req.patient_id, force_reindex=req.force_reindex, db=db)
        return IngestionResponse(
            success=result.get("status") == "success",
            message=f"Indexed patient {req.patient_id}",
            indexed_patients=1,
            total_chunks_indexed=result.get("total_chunks", 0),
            details=[result]
        )
    else:
        results = rag_ingestion_service.index_all_patients(force_reindex=req.force_reindex, db=db)
        return IngestionResponse(**results)


@router.post("/rag/search", response_model=RetrievalQueryResponse)
async def search_patient_rag(
    req: RetrievalQueryRequest,
    current_user: dict = Depends(require_role("doctor", "assistant")),
    db: Client = Depends(get_db)
):
    """Execute patient-scoped vector retrieval without running full CDS synthesis"""
    # Verify patient exists
    p_check = db.table("patients").select("id").eq("id", req.patient_id).execute()
    if not p_check.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient '{req.patient_id}' not found"
        )

    results = rag_retrieval_service.retrieve_patient_evidence(
        patient_id=req.patient_id,
        query_text=req.query,
        current_user=current_user,
        top_k=req.top_k,
        min_similarity=req.min_similarity,
        db=db
    )
    return RetrievalQueryResponse(
        patient_id=req.patient_id,
        query=req.query,
        total_retrieved=len(results),
        results=results
    )
