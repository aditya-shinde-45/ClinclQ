import pytest
from core.database import get_db, local_db
from services.rag_ingestion_service import resolve_chunk_db


class TestDatabaseConsistencyAudit:
    """Phase 7: Database Integrity, Foreign Key Consistency, and Orphan Auditing."""

    def test_patient_foreign_keys_and_identifiers(self):
        """Verify all visits, documents, and analyses reference existing patients."""
        db = get_db()
        patients_res = db.table("patients").select("id").execute()
        valid_patient_ids = set(p["id"] for p in (patients_res.data or []))
        assert len(valid_patient_ids) > 0

        # Check visits
        visits_res = db.table("visits").select("id, patient_id").execute()
        for v in (visits_res.data or []):
            pid = v.get("patient_id")
            assert pid in valid_patient_ids, f"Orphaned visit {v.get('id')} references non-existent patient {pid}"

        # Check documents
        docs_res = db.table("documents").select("id, patient_id").execute()
        for d in (docs_res.data or []):
            pid = d.get("patient_id")
            assert pid in valid_patient_ids, f"Orphaned document {d.get('id')} references non-existent patient {pid}"

        # Check analyses
        analyses_res = db.table("clinical_analyses").select("id, patient_id").execute()
        for a in (analyses_res.data or []):
            pid = a.get("patient_id")
            assert pid in valid_patient_ids, f"Orphaned analysis {a.get('id')} references non-existent patient {pid}"

    def test_chunk_table_orphans_and_integrity(self):
        """Verify all vector chunks reference valid patients and contain non-empty embeddings."""
        db = get_db()
        chunk_db = resolve_chunk_db(db)
        patients_res = db.table("patients").select("id").execute()
        valid_patient_ids = set(p["id"] for p in (patients_res.data or []))

        chunks_res = chunk_db.table("patient_record_chunks").select("chunk_id, patient_id, content, embedding").execute()
        chunks = chunks_res.data or []
        assert len(chunks) > 0, "Expected indexed chunks in vector store"

        for c in chunks:
            # 1. Patient reference must be valid
            pid = c.get("patient_id")
            assert pid in valid_patient_ids, f"Orphaned chunk {c.get('chunk_id')} points to non-existent patient {pid}"

            # 2. Content must be non-empty
            assert c.get("content") and len(c["content"].strip()) > 0

            # 3. Embedding must have 1024 dimensions
            emb = c.get("embedding", [])
            assert len(emb) == 1024, f"Chunk {c.get('chunk_id')} has invalid embedding dimension: {len(emb)}"

    def test_clinical_analysis_status_constraints(self):
        """Verify all analyses conform to the strict status enum constraint."""
        db = get_db()
        valid_statuses = {"processing", "awaiting_review", "approved", "modified", "rejected"}
        analyses_res = db.table("clinical_analyses").select("id, status, report_id").execute()

        for a in (analyses_res.data or []):
            status = a.get("status")
            assert status in valid_statuses, f"Analysis {a.get('id')} ({a.get('report_id')}) has invalid status '{status}'"

    def test_diagnosis_and_recommendation_links(self):
        """Verify all differential diagnoses link to an existing clinical_analysis."""
        db = get_db()
        analyses_res = db.table("clinical_analyses").select("id").execute()
        valid_analysis_ids = set(a["id"] for a in (analyses_res.data or []))

        # Diagnoses
        diag_res = db.table("diagnoses").select("id, analysis_id, confidence_label").execute()
        for d in (diag_res.data or []):
            aid = d.get("analysis_id")
            assert aid in valid_analysis_ids, f"Diagnosis {d.get('id')} has invalid analysis_id {aid}"
            assert d.get("confidence_label") in ("high", "needs_review", "low")

        # Recommendations
        rec_res = db.table("recommendations").select("id, analysis_id").execute()
        for r in (rec_res.data or []):
            aid = r.get("analysis_id")
            assert aid in valid_analysis_ids, f"Recommendation {r.get('id')} has invalid analysis_id {aid}"
