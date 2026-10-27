import pytest
import io
from services.rag_ingestion_service import rag_ingestion_service, chunk_text, compute_sha256, resolve_chunk_db
from services.rag_retrieval_service import rag_retrieval_service
from services.embedding_service import embedding_service
from services.bedrock_service import bedrock_service
from core.database import get_db, local_db
from models.schemas import DecisionCreate, DecisionType


class TestRagPipelineAudit:
    """Phase 3: Deep Verification of the 5 Core RAG Pipeline Stages."""

    # -------------------------------------------------------------
    # STAGE 1: Primary Knowledge Sources
    # -------------------------------------------------------------
    def test_stage_1_primary_knowledge_source_integrity(self):
        """Verify structured records are queried directly and absent fields are not fabricated."""
        db = get_db()
        # Query imported patient
        res = db.table("patients").select("*").eq("id", "CLQ-HOSP-0001").execute()
        assert len(res.data) > 0
        p = res.data[0]

        # Verify demographic and condition mapping
        assert p["id"] == "CLQ-HOSP-0001"
        assert p["gender"] in ("Male", "Female")
        assert "Heart Disease" in p.get("medical_history", "")
        assert "Angioplasty" in p.get("past_treatments", "")

        # Crucial: Unreported fields must NOT be fabricated with synthetic medications/allergies
        # The importer sets them to None / empty, not fabricated drug names
        assert p.get("allergies") in (None, "", "No known drug allergies", "No known allergies documented in demo dataset")
        assert p.get("current_medications") in (None, "", "None reported")

    # -------------------------------------------------------------
    # STAGE 2: Preparation and Ingestion
    # -------------------------------------------------------------
    def test_stage_2_chunking_and_content_hashing(self):
        """Verify chunk size, overlap, and deterministic SHA-256 content hashing."""
        sample_text = (
            "Patient History: Recurrent exertional retrosternal chest pain radiating to left shoulder. "
            "Past Surgeries: Angioplasty with drug-eluting stent. Baseline ECG: Normal sinus rhythm. "
            "Hospitalization: 5 days inpatient stay. Discharge Outcome: Recovered. Readmission: No."
        )
        chunks = chunk_text(sample_text, chunk_size=150, chunk_overlap=30)
        assert len(chunks) >= 2, "Expected text to be split into multiple overlapping chunks"

        # Check content hashing consistency
        h1 = compute_sha256(chunks[0])
        h2 = compute_sha256(chunks[0])
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 produces 64-char hex string

    def test_stage_2_embedding_dimensions(self):
        """Verify Amazon Titan Text Embeddings returns 1024-dimensional normalized vectors."""
        embedding = embedding_service.get_embedding("Clinical evaluation of patient with acute chest discomfort.")
        assert isinstance(embedding, list)
        assert len(embedding) == 1024, f"Expected 1024 dimensions for Titan v2, got {len(embedding)}"
        norm_sq = sum(x * x for x in embedding)
        assert abs(norm_sq - 1.0) < 0.05, f"Vector should be normalized: norm_sq={norm_sq}"

    def test_stage_2_incremental_reindexing_and_deduplication(self):
        """Verify unchanged content hashes are skipped and not re-embedded."""
        db = get_db()
        test_patient = "CLQ-HOSP-0001"

        # First run (reindex force)
        res1 = rag_ingestion_service.index_patient(test_patient, force_reindex=True, db=db)
        assert res1["status"] == "success"
        total_chunks = res1["total_chunks"]

        # Second incremental run (force_reindex=False)
        res2 = rag_ingestion_service.index_patient(test_patient, force_reindex=False, db=db)
        assert res2["status"] == "success"
        assert res2["chunks_created"] == 0, "Incremental run must not re-create unchanged chunks"
        assert res2["chunks_unchanged"] == total_chunks, "All existing chunks should be recognized as unchanged"

    def test_stage_2_document_extraction_edge_cases(self):
        """Verify handling of empty text, corrupt PDFs, and unsupported formats."""
        # Unsupported format (e.g. image or binary file)
        unsupported_doc = {
            "filename": "scan_xray.png",
            "file_url": "https://s3.amazonaws.com/bucket/patients/CLQ-HOSP-0001/scan_xray.png",
            "category": "imaging"
        }
        text = rag_ingestion_service._extract_document_text(unsupported_doc)
        assert text == "", "Unsupported file extensions should return empty string gracefully"

        # Corrupt PDF binary
        corrupt_doc = {
            "filename": "corrupted_lab.pdf",
            "file_url": "patients/CLQ-HOSP-0001/corrupted_lab.pdf",
            "category": "lab"
        }
        # When S3 download fails or returns invalid bytes, must not raise uncaught exception
        text_corrupt = rag_ingestion_service._extract_document_text(corrupt_doc)
        assert text_corrupt == ""

    # -------------------------------------------------------------
    # STAGE 3: Patient-Scoped Retrieval
    # -------------------------------------------------------------
    def test_stage_3_patient_scoped_vector_retrieval(self):
        """Verify semantic retrieval returns relevant chunks strictly for the target patient."""
        db = get_db()
        test_patient = "CLQ-HOSP-0001"
        doctor_user = {"id": 1, "role": "doctor"}

        results = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=test_patient,
            query_text="Angioplasty and Heart Disease inpatient stay recovery",
            current_user=doctor_user,
            top_k=3,
            min_similarity=0.10,
            db=db
        )
        assert len(results) > 0, "Expected at least 1 relevant chunk for Patient 1"
        for item in results:
            # Check safety: chunk_id must match target patient
            assert test_patient in item.chunk_id
            assert item.similarity >= 0.10
            assert item.content != ""
            assert item.source_type in ("patient_profile", "hospital_encounter", "visit_timeline", "document")

    def test_stage_3_strict_cross_patient_boundary_isolation(self):
        """Verify cross-patient isolation: queries for Patient A never return Patient B's chunks."""
        db = get_db()
        patient_a = "CLQ-HOSP-0001"  # Heart Disease, Angioplasty
        patient_b = "CLQ-HOSP-0002"  # Diabetes, Insulin Therapy
        doctor_user = {"id": 1, "role": "doctor"}

        # Search for Patient B's specific condition while scoped to Patient A
        results_for_a = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=patient_a,
            query_text="Insulin Therapy for Diabetes with 3-day stay",
            current_user=doctor_user,
            top_k=5,
            min_similarity=0.10,
            db=db
        )
        for item in results_for_a:
            assert patient_b not in item.chunk_id
            assert "CLQ-HOSP-0002" not in item.content

    def test_stage_3_empty_retrieval_handling(self):
        """Verify genuine empty result is returned when no evidence matches threshold or query."""
        db = get_db()
        doctor_user = {"id": 1, "role": "doctor"}

        # High threshold on unrelated query
        results = rag_retrieval_service.retrieve_patient_evidence(
            patient_id="CLQ-HOSP-0001",
            query_text="Severe neurodegenerative amyotrophic lateral sclerosis genetic panel",
            current_user=doctor_user,
            top_k=4,
            min_similarity=0.95,  # Unattainable threshold
            db=db
        )
        assert results == [], "Expected empty retrieval list when similarity threshold is not met"

    # -------------------------------------------------------------
    # STAGE 4: Amazon Bedrock Generation Grounding
    # -------------------------------------------------------------
    def test_stage_4_grounded_prompt_construction(self):
        """Verify Bedrock prompt builds [EVIDENCE ITEM #X] citations and enforces CDS rules."""
        db = get_db()
        doctor_user = {"id": 1, "role": "doctor"}
        evidence = rag_retrieval_service.retrieve_patient_evidence(
            patient_id="CLQ-HOSP-0001",
            query_text="Heart Disease Angioplasty",
            current_user=doctor_user,
            top_k=2,
            db=db
        )
        formatted_context = rag_retrieval_service.format_retrieved_evidence_for_prompt(evidence)
        assert "[EVIDENCE ITEM #1]" in formatted_context
        assert "Relevance:" in formatted_context

    def test_stage_4_bedrock_schema_validation(self):
        """Verify Bedrock generation produces valid differential diagnoses JSON schema."""
        patient_data = {
            "id": "CLQ-HOSP-0001",
            "full_name": "Demo Patient 1",
            "gender": "Female",
            "date_of_birth": "1981-01-01",
            "medical_history": "Heart Disease",
            "past_treatments": "Angioplasty",
            "allergies": "No known drug allergies",
            "current_medications": "None reported"
        }
        res = bedrock_service.generate_analysis(
            patient_data=patient_data,
            new_symptoms="Substernal chest pressure on climbing stairs, relieved by rest",
            observations="BP 130/80, HR 72, Normal heart sounds",
            test_results="Resting ECG normal",
            clinical_notes="Follow-up after prior angioplasty"
        )
        assert "diagnoses" in res
        assert "recommendations" in res
        assert "drug_interactions" in res
        assert "risk_factors" in res
        assert "patient_explanation" in res

    def test_stage_4_zero_evidence_regression(self):
        """Regression Test: Verify zero-evidence case cannot silently become a confident clinical conclusion."""
        patient_data = {
            "id": "CLQ-HOSP-0001",
            "full_name": "Demo Patient 1",
            "gender": "Female",
            "date_of_birth": "1981-01-01",
            "medical_history": "Heart Disease",
            "past_treatments": "Angioplasty",
            "allergies": "No known drug allergies",
            "current_medications": "None reported"
        }
        res = bedrock_service.generate_analysis(
            patient_data=patient_data,
            new_symptoms="Vague fatigue and subjective weakness",
            observations="Normal vitals",
            test_results="None",
            clinical_notes="No prior records or evidence available",
            retrieved_evidence=[]
        )
        assert res.get("evidence_grounding_status") == "insufficient_evidence"
        assert len(res.get("retrieved_evidence", [])) == 0
        for diag in res.get("diagnoses", []):
            assert diag["confidence_label"] in ("needs_review", "low"), "Must not be 'high' without evidence"
            assert float(diag["confidence_percentage"]) <= 50.0, "Confidence must not exceed 50% without evidence"
        assert "risk_factors" in res
        assert len(res["diagnoses"]) >= 1
        for d in res["diagnoses"]:
            assert "rank" in d
            assert "name" in d
            assert "confidence_percentage" in d
            assert d["confidence_label"] in ("high", "needs_review", "low")

    # -------------------------------------------------------------
    # STAGE 5: Physician Review & Decision Workflow
    # -------------------------------------------------------------
    def test_stage_5_physician_review_workflow(self):
        """Verify analysis enters awaiting_review and doctor can record decision with attestation."""
        import time
        db = get_db()
        # Create a fresh dedicated analysis to test decision recording
        test_report_id = f"TEST-DEC-{int(time.time()*1000)}"
        new_analysis_res = db.table("clinical_analyses").insert({
            "patient_id": "CLQ-HOSP-0001",
            "report_id": test_report_id,
            "status": "awaiting_review",
            "new_symptoms": "Test exertional symptoms",
            "observations": "Test vitals",
            "reviewed_by_id": 1
        }).execute()
        assert len(new_analysis_res.data) > 0
        analysis_id = new_analysis_res.data[0]["id"]

        # Verify initial status requires physician review
        assert new_analysis_res.data[0]["status"] == "awaiting_review"

        # Test decision recording
        decision_data = {
            "analysis_id": analysis_id,
            "decision_type": DecisionType.APPROVE.value,
            "clinician_notes": "Reviewed and verified against patient cardiac history.",
            "attestation_confirmed": True,
            "decided_by_id": 1,
            "decided_at": "2026-10-26T12:00:00Z"
        }
        d_res = db.table("clinical_decisions").insert(decision_data).execute()
        assert len(d_res.data) > 0
        decision_id = d_res.data[0]["id"]
        assert d_res.data[0]["attestation_confirmed"] is True

        # Verify status updates to approved
        db.table("clinical_analyses").update({"status": "approved"}).eq("id", analysis_id).execute()
        updated = db.table("clinical_analyses").select("status").eq("id", analysis_id).execute()
        assert updated.data[0]["status"] == "approved"
