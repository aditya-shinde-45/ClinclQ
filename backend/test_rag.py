#!/usr/bin/env python3
"""
ClinIQ - Comprehensive Automated RAG Verification Suite.
Validates:
1. CSV dataset inspection & idempotent import
2. Sliding-window chunking & SHA-256 content hashing
3. Amazon Bedrock Titan Text Embeddings v2 (1024 dimensions)
4. Vector insertion, indexing, and deduplication
5. Strict patient-scoped boundary filtering (Patient Isolation)
6. Empty retrieval handling
7. End-to-end RAG grounded Bedrock generation & physician review
"""

import sys
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from core.database import get_db
from core.config import settings
from services.embedding_service import embedding_service
from services.rag_ingestion_service import rag_ingestion_service, chunk_text, compute_sha256
from services.rag_retrieval_service import rag_retrieval_service
from services.bedrock_service import bedrock_service
from scripts.import_kaggle_dataset import import_dataset, DATASET_PATH, validate_row


class TestClinIqRagPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 65)
        print("RUNNING CLINIQ RAG & PATIENT KNOWLEDGE PIPELINE TEST SUITE")
        print("=" * 65)
        cls.db = get_db()

    def test_01_csv_dataset_inspection(self):
        """Verify Kaggle hospital dataset exists, format is intact, and validation succeeds."""
        print("\n[TEST 1] CSV Dataset Integrity & Validation")
        self.assertTrue(DATASET_PATH.exists(), f"Dataset file missing at {DATASET_PATH}")
        
        # Test dry-run import on sample
        result = import_dataset(dry_run=True, limit=10)
        self.assertTrue(result["success"])
        self.assertEqual(result["processed"], 10)
        self.assertEqual(result["rejected_rows"], 0)
        print("  -> PASSED: CSV schema valid, 10 sample records verified without rejections.")

    def test_02_idempotent_dataset_import(self):
        """Verify importing records writes to database and subsequent runs are idempotent."""
        print("\n[TEST 2] Idempotent Dataset Import")
        # Import first 5 demo records for testing
        res1 = import_dataset(dry_run=False, limit=5)
        self.assertTrue(res1["success"])
        
        # Immediate second import with same limit must skip all existing
        res2 = import_dataset(dry_run=False, limit=5)
        self.assertTrue(res2["success"])
        self.assertEqual(res2["imported_patients"], 0, "Second import must not create duplicate patients!")
        self.assertEqual(res2["skipped_existing"], 5, "Second import must detect existing patients!")
        print("  -> PASSED: Idempotency confirmed. Existing demo records skipped without duplication.")

    def test_03_text_chunking_and_hashing(self):
        """Verify text chunking respects chunk size, overlap, and produces consistent hashes."""
        print("\n[TEST 3] Chunking & Content Hashing")
        sample_text = (
            "Patient is a 55-year-old female presenting with exertional chest pain. "
            "History of hypertension and coronary artery disease. "
            "Current medications include Amlodipine 5mg and Aspirin 81mg. "
            "Previous angioplasty completed with stable clinical recovery. "
            "Discharged in good condition with follow-up scheduled."
        )
        chunks = chunk_text(sample_text, chunk_size=100, chunk_overlap=20)
        self.assertGreater(len(chunks), 1, "Chunking should produce multiple chunks for text > 100 chars")
        
        # Verify SHA-256 consistency
        hash1 = compute_sha256(chunks[0])
        hash2 = compute_sha256(chunks[0])
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)
        print(f"  -> PASSED: Produced {len(chunks)} overlapping chunks. SHA-256 consistency confirmed.")

    def test_04_bedrock_titan_embeddings(self):
        """Verify Amazon Titan Embeddings v2 returns 1024-dimensional normalized vectors."""
        print("\n[TEST 4] Bedrock Titan Text Embeddings Generation")
        test_phrase = "Cardiac catheterization showing patent coronary stents."
        embedding = embedding_service.get_embedding(test_phrase)
        
        self.assertIsInstance(embedding, list)
        self.assertEqual(len(embedding), 1024, f"Expected 1024 dimensions, got {len(embedding)}")
        # Check normalization (sum of squares ~= 1.0)
        norm_sq = sum(x * x for x in embedding)
        self.assertAlmostEqual(norm_sq, 1.0, places=2)
        print(f"  -> PASSED: Bedrock Titan embedding returned {len(embedding)} dimensions (Normalized).")

    def test_05_patient_indexing_and_deduplication(self):
        """Verify RAG indexing creates chunks and skips unchanged hashes."""
        print("\n[TEST 5] Ingestion Pipeline & Incremental Deduplication")
        test_patient_id = "CLQ-HOSP-0001"
        
        # First index run
        res1 = rag_ingestion_service.index_patient(test_patient_id, force_reindex=True, db=self.db)
        self.assertEqual(res1["status"], "success")
        self.assertGreater(res1["total_chunks"], 0)
        total_active_chunks = res1["total_chunks"]
        
        # Second index run without changes: chunks_created should be 0, unchanged should match total_active_chunks
        res2 = rag_ingestion_service.index_patient(test_patient_id, force_reindex=False, db=self.db)
        self.assertEqual(res2["status"], "success")
        self.assertEqual(res2["chunks_created"], 0, "Incremental run must not re-embed unchanged chunks")
        self.assertEqual(res2["chunks_unchanged"], total_active_chunks)
        print(f"  -> PASSED: Indexed {total_active_chunks} chunks; incremental run skipped {res2['chunks_unchanged']} identical hashes.")

    def test_06_strict_patient_isolation(self):
        """CRITICAL: Verify patient-scoped retrieval strictly isolates Patient A from Patient B."""
        print("\n[TEST 6] Strict Patient Boundary Isolation (Zero Cross-Patient Leakage)")
        patient_a = "CLQ-HOSP-0001"
        patient_b = "CLQ-HOSP-0002"
        
        # Ensure both patients are indexed
        rag_ingestion_service.index_patient(patient_a, db=self.db)
        rag_ingestion_service.index_patient(patient_b, db=self.db)
        
        # Query specifically for Patient A's condition
        retrieved_for_a = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=patient_a,
            query_text="Heart disease angioplasty recovery hospital stay",
            current_user={"id": 1, "role": "doctor"},
            db=self.db
        )
        
        # Assert ALL returned chunks belong exclusively to Patient A
        self.assertGreater(len(retrieved_for_a), 0, "Patient A should have matching chunks")
        for chunk in retrieved_for_a:
            self.assertTrue(chunk.chunk_id.startswith(f"chunk_{patient_a}"), f"Leaked chunk {chunk.chunk_id}!")
        
        # Query for Patient B using Patient A's symptoms
        retrieved_for_b = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=patient_b,
            query_text="Heart disease angioplasty recovery",
            current_user={"id": 1, "role": "doctor"},
            db=self.db
        )
        for chunk in retrieved_for_b:
            self.assertTrue(chunk.chunk_id.startswith(f"chunk_{patient_b}"), f"Cross-contamination detected in Patient B!")
            self.assertFalse(chunk.chunk_id.startswith(f"chunk_{patient_a}"), f"Patient A data leaked to Patient B!")

        print(f"  -> PASSED: Verified 100% boundary isolation. Zero cross-patient leakage detected.")

    def test_07_empty_retrieval_handling(self):
        """Verify querying non-existent patient or empty query returns empty list safely."""
        print("\n[TEST 7] Empty Retrieval & Edge-Case Safety")
        empty_res = rag_retrieval_service.retrieve_patient_evidence(
            patient_id="CLQ-NONEXISTENT-9999",
            query_text="unrelated medical condition query",
            current_user={"id": 1, "role": "doctor"},
            db=self.db
        )
        self.assertEqual(empty_res, [], "Non-existent patient must return empty list without exception")
        
        blank_query_res = rag_retrieval_service.retrieve_patient_evidence(
            patient_id="CLQ-HOSP-0001",
            query_text="   ",
            current_user={"id": 1, "role": "doctor"},
            db=self.db
        )
        self.assertEqual(blank_query_res, [], "Blank query must return empty list")
        print("  -> PASSED: Graceful empty retrieval handling verified.")

    def test_08_bedrock_generation_grounded_in_rag(self):
        """Verify AWS Bedrock Llama 3 70B synthesis accepts retrieved evidence and returns valid schema."""
        print("\n[TEST 8] Bedrock Llama 3 70B Generation Grounded in RAG Evidence")
        patient_id = "CLQ-HOSP-0001"
        p_res = self.db.table("patients").select("*").eq("id", patient_id).execute()
        patient_data = p_res.data[0]

        evidence = rag_retrieval_service.retrieve_patient_evidence(
            patient_id=patient_id,
            query_text="Chest pain, recurrent dyspnea",
            current_user={"id": 1, "role": "doctor"},
            db=self.db
        )

        analysis = bedrock_service.generate_analysis(
            patient_data=patient_data,
            new_symptoms="Exertional tightness and shortness of breath for 3 days",
            observations="BP 138/88 mmHg, HR 76 regular, no peripheral edema",
            test_results="Resting ECG shows normal sinus rhythm without acute ST elevations",
            clinical_notes="Evaluate for recurrent angina vs heart disease exacerbation",
            retrieved_evidence=evidence
        )

        self.assertIn("diagnoses", analysis)
        self.assertGreater(len(analysis["diagnoses"]), 0)
        self.assertIn("recommendations", analysis)
        self.assertIn("risk_factors", analysis)
        self.assertIn("patient_explanation", analysis)
        self.assertIn("retrieved_evidence", analysis)
        self.assertEqual(len(analysis["retrieved_evidence"]), len(evidence))

        leading_diag = analysis["diagnoses"][0]
        print(f"  -> PASSED: Bedrock generated leading diagnosis: '{leading_diag['name']}' ({leading_diag['confidence_percentage']}%)")
        print(f"  -> Grounded in {len(analysis['retrieved_evidence'])} retrieved patient evidence items.")


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestClinIqRagPipeline)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
