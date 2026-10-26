#!/usr/bin/env python3
"""
ClinIQ - Reproducible, Idempotent Kaggle Hospital Dataset Importer.
Imports verified fields from 'backend/dataset/archive/hospital data analysis.csv'
into ClinIQ patients and visits tables.

Usage:
  python backend/scripts/import_kaggle_dataset.py [--dry-run] [--limit N] [--index-rag]
"""

import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Ensure backend root is on Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from core.database import get_db


DATASET_PATH = BACKEND_DIR / "dataset" / "archive" / "hospital data analysis.csv"

EXPECTED_COLUMNS = [
    "Patient_ID", "Age", "Gender", "Condition", "Procedure",
    "Cost", "Length_of_Stay", "Readmission", "Outcome", "Satisfaction"
]


def calculate_dob_from_age(age_years: int) -> str:
    """Derive approximate date of birth from age string."""
    current_year = datetime.now().year
    birth_year = current_year - age_years
    return f"{birth_year:04d}-01-01"


def validate_row(row: dict) -> tuple[bool, str]:
    """Validate data integrity for an incoming CSV record."""
    required_fields = EXPECTED_COLUMNS
    for field in required_fields:
        if field not in row or not str(row[field]).strip():
            return False, f"Missing required column: {field}"

    try:
        pid = int(row["Patient_ID"])
        if pid <= 0:
            return False, f"Invalid Patient_ID: {pid}"
    except ValueError:
        return False, f"Patient_ID is not an integer: {row['Patient_ID']}"

    try:
        age = int(row["Age"])
        if age < 0 or age > 130:
            return False, f"Age out of bounds: {age}"
    except ValueError:
        return False, f"Age is not an integer: {row['Age']}"

    try:
        float(row["Cost"])
        int(row["Length_of_Stay"])
        int(row["Satisfaction"])
    except ValueError as e:
        return False, f"Numeric parsing error: {e}"

    return True, "Valid"


def import_dataset(dry_run: bool = False, limit: int = None, index_rag: bool = False) -> dict:
    print("=" * 65)
    print("CLINIQ - KAGGLE HOSPITAL DATASET IMPORTER")
    print("=" * 65)
    print(f"Dataset Source : {DATASET_PATH}")
    print(f"Dry Run Mode   : {dry_run}")
    print(f"Row Limit      : {limit if limit else 'ALL (984 rows)'}")
    print("=" * 65)

    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        return {"success": False, "error": "Dataset file missing"}

    db = get_db()

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    total_rows = len(all_rows)
    print(f"Loaded {total_rows} rows from CSV.")

    if limit and limit > 0:
        target_rows = all_rows[:limit]
    else:
        target_rows = all_rows

    imported_patients = 0
    skipped_existing = 0
    rejected_rows = []
    imported_visits = 0

    # Ensure a default doctor exists for assignment
    default_doctor_id = 1
    doc_res = db.table("users").select("id").eq("role", "doctor").limit(1).execute()
    if doc_res.data:
        default_doctor_id = doc_res.data[0]["id"]

    for idx, row in enumerate(target_rows, 1):
        is_valid, validation_msg = validate_row(row)
        if not is_valid:
            rejected_rows.append({"index": idx, "row": row, "reason": validation_msg})
            continue

        raw_pid = int(row["Patient_ID"])
        clq_id = f"CLQ-HOSP-{raw_pid:04d}"
        mrn = f"MRN-HOSP-{raw_pid:04d}"
        age = int(row["Age"])
        dob = calculate_dob_from_age(age)
        gender = row["Gender"].strip().capitalize()
        condition = row["Condition"].strip()
        procedure = row["Procedure"].strip()
        cost = float(row["Cost"])
        los = int(row["Length_of_Stay"])
        readmission = row["Readmission"].strip()
        outcome = row["Outcome"].strip()
        satisfaction = int(row["Satisfaction"])

        # Check if patient already exists (idempotency by unique ID & MRN)
        existing = db.table("patients").select("id").eq("id", clq_id).execute()
        if existing.data:
            skipped_existing += 1
            continue

        patient_record = {
            "id": clq_id,
            "mrn": mrn,
            "full_name": f"Demo Patient #{raw_pid}",
            "date_of_birth": dob,
            "gender": gender,
            "contact_number": "+91-5555555555",
            "reason_for_visit": condition,
            "medical_history": f"Diagnosed with {condition}",
            "allergies": "No known allergies documented in demo dataset",
            "current_medications": None,
            "past_treatments": f"Inpatient procedure: {procedure} (Hospital Stay: {los} days, Outcome: {outcome})",
            "assigned_doctor_id": default_doctor_id,
        }

        # Visit entry capturing all verified procedure & hospital telemetry
        visit_body = (
            f"Hospital Inpatient Admission for {condition}.\n"
            f"- Clinical Procedure: {procedure}\n"
            f"- Length of Hospital Stay: {los} days\n"
            f"- Procedure / Care Cost: ${cost:,.2f}\n"
            f"- 30-Day Readmission: {readmission}\n"
            f"- Discharge Outcome: {outcome}\n"
            f"- Patient Satisfaction Score: {satisfaction}/5\n"
            f"[Source: Kaggle Hospital Demonstration Dataset (Record #{raw_pid})]"
        )

        visit_record = {
            "patient_id": clq_id,
            "title": f"Inpatient Record — {condition}",
            "body": visit_body,
            "type": "procedure",
            "created_by_id": default_doctor_id,
            "visit_date": (datetime.utcnow() - timedelta(days=idx % 365)).isoformat(),
        }

        if dry_run:
            imported_patients += 1
            imported_visits += 1
            continue

        try:
            # Insert patient
            p_res = db.table("patients").insert(patient_record).execute()
            if p_res.data:
                imported_patients += 1

            # Insert visit
            v_res = db.table("visits").insert(visit_record).execute()
            if v_res.data:
                imported_visits += 1

        except Exception as e:
            rejected_rows.append({"index": idx, "row": row, "reason": str(e)})

    print("\n" + "=" * 65)
    print("IMPORT RESULTS SUMMARY")
    print("=" * 65)
    print(f"Total Processed   : {len(target_rows)}")
    print(f"Patients Imported : {imported_patients}")
    print(f"Visits Imported   : {imported_visits}")
    print(f"Skipped (Exists)  : {skipped_existing}")
    print(f"Rejected Rows     : {len(rejected_rows)}")
    if rejected_rows:
        print("\nSample Rejected Rows:")
        for r in rejected_rows[:5]:
            print(f"  - Row {r['index']}: {r['reason']}")
    print("=" * 65)

    # Optional RAG indexing trigger
    if index_rag and not dry_run:
        print("\nTriggering RAG Indexing for registered patients...")
        from services.rag_ingestion_service import rag_ingestion_service
        ingest_res = rag_ingestion_service.index_all_patients()
        print(f"RAG Indexing Finished: {ingest_res['total_chunks_indexed']} chunks created across {ingest_res['indexed_patients']} patients.")

    return {
        "success": True,
        "processed": len(target_rows),
        "imported_patients": imported_patients,
        "imported_visits": imported_visits,
        "skipped_existing": skipped_existing,
        "rejected_rows": len(rejected_rows),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Kaggle Hospital Dataset into ClinIQ")
    parser.add_argument("--dry-run", action="store_true", help="Validate and simulate without writing to database")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to import")
    parser.add_argument("--index-rag", action="store_true", help="Automatically generate RAG chunks and vector embeddings")

    args = parser.parse_args()
    import_dataset(dry_run=args.dry_run, limit=args.limit, index_rag=args.index_rag)
