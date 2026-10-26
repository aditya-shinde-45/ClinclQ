import sys
import io
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from main import app
from services.s3_service import s3_service
from services.bedrock_service import bedrock_service

client = TestClient(app)

def run_tests():
    print("=" * 65)
    print("CLINIQ API & AWS INFRASTRUCTURE (S3 + BEDROCK) VERIFICATION SUITE")
    print("=" * 65)

    # 1. Health & AWS Status Check
    print("\n[TEST 1] GET /health & /aws/status")
    health_resp = client.get("/health")
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print("Health response:", health_data)
    assert health_data["status"] == "healthy"
    assert health_data["aws"]["s3"]["configured"] is True
    assert health_data["aws"]["bedrock"]["configured"] is True

    aws_resp = client.get("/aws/status")
    assert aws_resp.status_code == 200, f"AWS status failed: {aws_resp.text}"
    aws_data = aws_resp.json()
    print("AWS Status:", aws_data)
    assert aws_data["s3"]["status"] == "operational"
    assert aws_data["bedrock"]["status"] == "operational"
    print("PASS: Health & AWS operational status verified.")

    # 2. Authentication Login (Doctor)
    print("\n[TEST 2] POST /auth/login (as Doctor)")
    login_resp = client.post(
        "/auth/login",
        json={"email": "parth.chavan@cliniq.org", "password": "clinical-access"}
    )
    if login_resp.status_code != 200:
        # Fallback to default seed doctor
        login_resp = client.post(
            "/auth/login",
            json={"email": "maya.patel@northlake.org", "password": "clinical-access"}
        )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    auth_data = login_resp.json()
    token = auth_data["access_token"]
    user_info = auth_data["user"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"PASS: Authenticated as {user_info['full_name']} (Role: {user_info['role']})")

    # 3. AWS S3 Document Upload
    patient_id = "CLQ-10482"
    print(f"\n[TEST 3] POST /documents/upload (Uploading to AWS S3 for {patient_id})")
    test_pdf_content = b"%PDF-1.4 1 0 obj << /Title (ClinIQ Lab Report) >> endobj xref 0 1 trailer << /Size 1 >> startxref 99 %%EOF"
    upload_file = ("cardiac_biomarkers.pdf", io.BytesIO(test_pdf_content), "application/pdf")
    
    upload_resp = client.post(
        f"/documents/upload?patient_id={patient_id}&category=lab",
        headers=headers,
        files={"file": upload_file}
    )
    assert upload_resp.status_code == 201, f"Document upload failed: {upload_resp.text}"
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    file_url = doc_data["file_url"]
    print(f"PASS: Document uploaded to S3 successfully!")
    print(f"  - Document ID: {doc_id}")
    print(f"  - Filename:    {doc_data['filename']}")
    print(f"  - Category:    {doc_data['category']}")
    print(f"  - S3 URL:      {file_url[:80]}...")

    # 4. AWS S3 Presigned URL Verification
    print(f"\n[TEST 4] GET /documents/patient/{patient_id}")
    docs_resp = client.get(f"/documents/patient/{patient_id}", headers=headers)
    assert docs_resp.status_code == 200, f"Get documents failed: {docs_resp.text}"
    patient_docs = docs_resp.json()
    uploaded_doc = next((d for d in patient_docs if d["id"] == doc_id), None)
    assert uploaded_doc is not None, "Uploaded document not found in patient list"
    assert "https://" in uploaded_doc["file_url"] and "s3" in uploaded_doc["file_url"]
    print("PASS: Verified document list returns active AWS S3 Presigned URLs.")

    # 5. AWS Bedrock Clinical Analysis Request (Llama 3 70B)
    print(f"\n[TEST 5] POST /analyses (Triggering Bedrock Llama 3 70B Inference)")
    analysis_payload = {
        "patient_id": patient_id,
        "new_symptoms": "Exertional retrosternal pressure radiating to jaw, relieved by sublingual nitroglycerin",
        "observations": "BP 138/86, HR 78 bpm regular, S4 gallop heard on cardiac auscultation",
        "test_results": "Resting ECG showed 1mm horizontal ST depression in V4-V6. Troponin-I: 0.02 ng/mL (normal)",
        "clinical_notes": "Urgent outpatient evaluation for recurrent angina pectoris."
    }
    create_analysis_resp = client.post("/analyses", json=analysis_payload, headers=headers)
    assert create_analysis_resp.status_code == 201, f"Analysis request failed: {create_analysis_resp.text}"
    created_analysis = create_analysis_resp.json()
    analysis_id = created_analysis["id"]
    report_id = created_analysis["report_id"]
    print(f"PASS: Created analysis job (ID: {analysis_id}, Report: {report_id})")

    # 6. Wait for and Verify Bedrock Output
    print(f"\n[TEST 6] GET /analyses/{analysis_id} (Verifying Bedrock generated report)")
    # Poll until background processing completes
    max_wait = 35
    start_time = time.time()
    completed_analysis = None
    while time.time() - start_time < max_wait:
        poll_resp = client.get(f"/analyses/{analysis_id}", headers=headers)
        assert poll_resp.status_code == 200
        data = poll_resp.json()
        if data["status"] in ["awaiting_review", "approved", "completed"]:
            completed_analysis = data
            break
        time.sleep(1)

    assert completed_analysis is not None, f"Analysis did not finish within {max_wait}s"
    diagnoses = completed_analysis.get("diagnoses", [])
    recommendations = completed_analysis.get("recommendations", [])
    drug_interactions = completed_analysis.get("drug_interactions", [])
    risk_factors = completed_analysis.get("risk_factors", [])

    print(f"PASS: Bedrock generated completed analysis (Status: {completed_analysis['status']})")
    print(f"  - Total Diagnoses:       {len(diagnoses)}")
    for d in diagnoses:
        print(f"    * Rank {d['rank']}: {d['name']} ({d['confidence_percentage']}%, {d['confidence_label']})")
        print(f"      Summary: {d['summary']}")
    print(f"  - Total Recommendations: {len(recommendations)}")
    for r in recommendations:
        print(f"    * Step {r['step_number']}: {r['title']}")
    print(f"  - Risk Factors:          {risk_factors}")
    print(f"  - Drug Interactions:     {len(drug_interactions)} detected")

    # 7. Record Clinical Decision
    print(f"\n[TEST 7] POST /analyses/{analysis_id}/decision (Doctor approval)")
    decision_payload = {
        "analysis_id": analysis_id,
        "decision_type": "approve",
        "notes": "Agree with Meta Llama 3 70B assessment. Proceeding with coronary CT angiography."
    }
    decision_resp = client.post(f"/analyses/{analysis_id}/decision", json=decision_payload, headers=headers)
    assert decision_resp.status_code == 201, f"Decision recording failed: {decision_resp.text}"
    decision_data = decision_resp.json()
    print(f"PASS: Recorded decision #{decision_data['id']} (Type: {decision_data['decision_type']})")

    # 8. S3 Document Deletion
    print(f"\n[TEST 8] DELETE /documents/{doc_id} (Cleanup from S3 and Database)")
    del_resp = client.delete(f"/documents/{doc_id}", headers=headers)
    assert del_resp.status_code == 204, f"Delete failed: {del_resp.text}"
    print(f"PASS: Document {doc_id} deleted successfully from AWS S3 and database.")

    print("\n" + "=" * 65)
    print("ALL API & AWS S3 / BEDROCK TESTS PASSED SUCCESSFULLY! (8/8)")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
