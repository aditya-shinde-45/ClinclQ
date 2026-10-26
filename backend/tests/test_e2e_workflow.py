import pytest
import time
from fastapi.testclient import TestClient
from main import app
from core.database import get_db


class TestEndToEndWorkflow:
    """Phase 6 & 8: End-to-End Application & Physician Review Workflow."""

    @classmethod
    def setup_class(cls):
        cls.client = TestClient(app)
        cls.db = get_db()

    def test_complete_doctor_analysis_workflow(self):
        """
        Executes complete end-to-end clinical journey:
        Login -> Patient Lookup -> RAG Search -> Request Analysis -> Poll -> Physician Approval
        """
        # 1. Doctor Login
        login_resp = self.client.post("/auth/login", json={
            "email": "parth.chavan@cliniq.org",
            "password": "clinical-access"
        })
        if login_resp.status_code != 200:
            login_resp = self.client.post("/auth/login", json={
                "email": "maya.patel@northlake.org",
                "password": "clinical-access"
            })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Patient Detail Lookup
        patient_id = "CLQ-HOSP-0001"
        p_resp = self.client.get(f"/patients/{patient_id}", headers=headers)
        assert p_resp.status_code == 200
        patient = p_resp.json()
        assert patient["id"] == patient_id
        assert "Heart Disease" in patient.get("medical_history", "")

        # 3. Patient-Scoped RAG Vector Search
        search_resp = self.client.post("/analyses/rag/search", json={
            "patient_id": patient_id,
            "query": "Angioplasty and coronary heart disease recovery",
            "top_k": 3
        }, headers=headers)
        assert search_resp.status_code == 200
        rag_data = search_resp.json()
        assert rag_data["patient_id"] == patient_id
        assert len(rag_data["results"]) > 0

        # 4. Request Clinical Analysis (Grounded in Patient Evidence)
        analysis_req_payload = {
            "patient_id": patient_id,
            "new_symptoms": "Exertional chest tightness radiating to jaw, relieved by rest",
            "observations": "BP 132/84, HR 76, S4 gallop, clear lungs",
            "test_results": "Resting 12-lead ECG shows non-specific ST depression",
            "clinical_notes": "Patient with history of heart disease and prior angioplasty"
        }
        create_resp = self.client.post("/analyses", json=analysis_req_payload, headers=headers)
        assert create_resp.status_code == 201, f"Create analysis failed: {create_resp.text}"
        created = create_resp.json()
        analysis_id = created["id"]
        report_id = created["report_id"]
        assert created["status"] in ("processing", "awaiting_review")

        # 5. Poll for Bedrock Inference Completion
        max_wait = 35
        start_time = time.time()
        final_analysis = None

        while time.time() - start_time < max_wait:
            poll_resp = self.client.get(f"/analyses/{analysis_id}", headers=headers)
            assert poll_resp.status_code == 200
            data = poll_resp.json()
            if data["status"] in ("awaiting_review", "approved", "completed"):
                final_analysis = data
                break
            time.sleep(1.5)

        assert final_analysis is not None, f"Analysis {analysis_id} did not finish within {max_wait}s"
        assert final_analysis["status"] == "awaiting_review"
        assert len(final_analysis.get("diagnoses", [])) >= 1
        assert len(final_analysis.get("recommendations", [])) >= 1

        # 6. Physician Decision Review & Attestation
        decision_payload = {
            "analysis_id": analysis_id,
            "decision_type": "approve",
            "clinician_notes": "Clinical differential verified. Correlates with prior angioplasty history.",
            "attestation_confirmed": True
        }
        decision_resp = self.client.post(
            f"/analyses/{analysis_id}/decision",
            json=decision_payload,
            headers=headers
        )
        assert decision_resp.status_code == 201, f"Record decision failed: {decision_resp.text}"
        decision = decision_resp.json()
        assert decision["decision_type"] == "approve"
        assert decision["attestation_confirmed"] is True

        # 7. Verify Status Transition to Approved
        verified_resp = self.client.get(f"/analyses/{analysis_id}", headers=headers)
        assert verified_resp.status_code == 200
        assert verified_resp.json()["status"] == "approved"
