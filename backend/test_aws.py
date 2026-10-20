import sys
import uuid
import json
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from services.s3_service import s3_service
from services.bedrock_service import bedrock_service

print("=" * 60)
print("1. TESTING AWS S3 INTEGRATION")
print("=" * 60)
print(f"Bucket:     {s3_service.bucket}")
print(f"Region:     {s3_service.region}")
print(f"Configured: {s3_service.is_configured}")

s3_ok = False
test_key = f"diagnostics-test/{uuid.uuid4()}.txt"
test_content = b"ClinIQ Medical Health Records S3 Validation 2026"

try:
    # 1. Put Object
    print("\n[Step 1] Uploading test file to S3...")
    result_key = s3_service.upload_file(test_content, test_key, "text/plain")
    if result_key.startswith("local/"):
        print(f"FAILED: S3 upload fell back to local storage ({result_key})")
    else:
        print(f"SUCCESS: Uploaded to S3 Key: {result_key}")
        
        # 2. Presigned URL
        print("\n[Step 2] Generating pre-signed download URL...")
        presigned_url = s3_service.get_document_url(result_key, expires_in=600)
        print(f"SUCCESS: Presigned URL generated:\n{presigned_url[:110]}...")

        # 3. Read Verification
        print("\n[Step 3] Verifying object retrieval from S3...")
        response = s3_service.s3_client.get_object(Bucket=s3_service.bucket, Key=result_key)
        downloaded = response["Body"].read()
        assert downloaded == test_content, "Content mismatch!"
        print(f"SUCCESS: Verified content integrity ({len(downloaded)} bytes matches).")

        # 4. Clean up
        print("\n[Step 4] Deleting test object from S3...")
        deleted = s3_service.delete_file(result_key)
        print(f"SUCCESS: Cleanup completed (deleted={deleted}).")
        s3_ok = True

except Exception as err:
    print(f"S3 Encountered Error: {type(err).__name__}: {err}")

print("\n" + "=" * 60)
print("2. TESTING AWS BEDROCK INTEGRATION (Llama 3 70B Instruct)")
print("=" * 60)
print(f"Model ID:   {bedrock_service.model_id}")
print(f"Region:     {bedrock_service.region}")
print(f"Configured: {bedrock_service.is_configured}")

bedrock_ok = False
try:
    sample_patient = {
        "full_name": "Sarah Connor",
        "age": 46,
        "gender": "Female",
        "medical_history": "Asthma, Migraine",
        "allergies": "Aspirin",
        "current_medications": "Albuterol inhaler PRN, Sumatriptan",
        "past_treatments": "None"
    }

    print("\nSending clinical inference prompt to AWS Bedrock Converse API...")
    analysis = bedrock_service.generate_analysis(
        patient_data=sample_patient,
        new_symptoms="Acute shortness of breath, wheezing unrelieved by 4 puffs albuterol",
        observations="RR 28/min, SpO2 91% on room air, diffuse expiratory wheezes, accessory muscle use",
        test_results="Peak expiratory flow 45% of personal best"
    )

    diagnoses = analysis.get("diagnoses", [])
    recommendations = analysis.get("recommendations", [])
    drug_interactions = analysis.get("drug_interactions", [])
    risk_factors = analysis.get("risk_factors", [])

    print(f"\nSUCCESS: Received structured CDS response from Bedrock!")
    print(f"Diagnoses found ({len(diagnoses)}):")
    for d in diagnoses:
        print(f"  - Rank {d.get('rank')}: {d.get('name')} | Confidence: {d.get('confidence_percentage')}% ({d.get('confidence_label')})")
        print(f"    Rationale: {d.get('summary')}")

    print(f"\nRecommendations found ({len(recommendations)}):")
    for r in recommendations:
        print(f"  - Step {r.get('step_number')}: {r.get('title')}")

    print(f"\nRisk Factors: {risk_factors}")
    print(f"Drug Interactions: {len(drug_interactions)} detected")
    bedrock_ok = True

except Exception as err:
    print(f"Bedrock Encountered Error: {type(err).__name__}: {err}")

print("\n" + "=" * 60)
print("SUMMARY RESULTS")
print("=" * 60)
print(f"AWS S3 Bucket Integration:    {'WORKING (PASS)' if s3_ok else 'FAILED'}")
print(f"AWS Bedrock Model Inference: {'WORKING (PASS)' if bedrock_ok else 'FAILED'}")
print("=" * 60)
