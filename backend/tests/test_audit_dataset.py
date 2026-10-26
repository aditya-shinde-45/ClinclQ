import os
import csv
import pytest
from pathlib import Path
from scripts.import_kaggle_dataset import (
    DATASET_PATH,
    EXPECTED_COLUMNS,
    validate_row,
    import_dataset
)
from core.database import get_db, local_db


class TestDatasetAudit:
    """Phase 2: Comprehensive Dataset and Importer Pipeline Verification."""

    def test_file_exists_and_path_handling(self):
        """Verify the exact dataset path with spaces is parsed and resolved correctly."""
        assert DATASET_PATH.exists(), f"Dataset file does not exist at {DATASET_PATH}"
        assert "hospital data analysis.csv" in str(DATASET_PATH)
        assert os.path.isfile(DATASET_PATH)

    def test_row_and_column_counts(self):
        """Verify the Kaggle dataset contains exactly 984 rows and 10 expected columns."""
        with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames
            rows = list(reader)

        assert len(columns) == 10, f"Expected 10 columns, found {len(columns)}: {columns}"
        assert set(columns) == set(EXPECTED_COLUMNS)
        assert len(rows) == 984, f"Expected exactly 984 data rows, found {len(rows)}"

    def test_data_types_and_no_missing_values(self):
        """Verify no missing/null values and check data types of fields."""
        with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        pids = set()
        for idx, row in enumerate(rows):
            # Check for non-empty fields
            for col in EXPECTED_COLUMNS:
                val = row.get(col)
                assert val is not None and str(val).strip() != "", f"Empty value found at row {idx}, col {col}"

            # Check Patient_ID is positive integer
            pid_int = int(row["Patient_ID"])
            assert pid_int > 0
            pids.add(pid_int)

            # Check Age range
            age = int(row["Age"])
            assert 0 < age <= 120, f"Invalid age {age} at row {idx}"

            # Check Gender
            assert row["Gender"] in ("Male", "Female"), f"Unexpected gender {row['Gender']} at row {idx}"

            # Check Cost is numeric
            cost = float(row["Cost"])
            assert cost >= 0

            # Check Length of stay
            los = int(row["Length_of_Stay"])
            assert los >= 0

            # Check Readmission is Yes/No
            assert row["Readmission"] in ("Yes", "No")

            # Check Outcome is Recovered/Stable
            assert row["Outcome"] in ("Recovered", "Stable")

        assert len(pids) == 984, "All 984 records must have distinct Patient_IDs"

    def test_validation_logic_rejects_invalid_rows(self):
        """Verify that malformed or incomplete rows are rejected by validate_row."""
        # Missing field
        invalid_row_1 = {
            "Patient_ID": "1001",
            "Age": "45",
            "Gender": "Male",
            "Condition": "",  # Empty condition
            "Procedure": "Surgery",
            "Cost": "1000",
            "Length_of_Stay": "2",
            "Readmission": "No",
            "Outcome": "Recovered",
            "Satisfaction": "5"
        }
        valid_1, err_1 = validate_row(invalid_row_1)
        assert not valid_1
        assert "Missing required column" in err_1

        # Non-numeric Age
        invalid_row_2 = dict(invalid_row_1, Condition="Hypertension", Age="forty")
        valid_2, err_2 = validate_row(invalid_row_2)
        assert not valid_2
        assert "Age is not an integer" in err_2

        # Non-numeric Cost
        invalid_row_3 = dict(invalid_row_1, Condition="Hypertension", Cost="expensive")
        valid_3, err_3 = validate_row(invalid_row_3)
        assert not valid_3
        assert "Numeric parsing error" in err_3

    def test_dry_run_does_not_mutate_database(self):
        """Verify dry-run mode processes records without mutating database state."""
        db = get_db()
        p_count_before = len(db.table("patients").select("id").execute().data or [])

        result = import_dataset(dry_run=True, limit=15)
        assert result["success"] is True
        assert result["processed"] == 15
        assert result["rejected_rows"] == 0

        p_count_after = len(db.table("patients").select("id").execute().data or [])
        assert p_count_before == p_count_after, "Dry run must not insert records into patients"

    def test_demo_provenance_tagging(self):
        """Verify imported patients carry explicit demonstration provenance tags."""
        db = get_db()
        res = db.table("patients").select("*").ilike("id", "CLQ-HOSP-%").limit(5).execute()
        demo_patients = res.data or []
        assert len(demo_patients) > 0, "Expected imported demo patients with CLQ-HOSP- prefix"

        for p in demo_patients:
            assert p["full_name"].startswith("Demo Patient #")
            assert p["id"].startswith("CLQ-HOSP-")
            assert p["mrn"].startswith("MRN-HOSP-")
            assert "demo dataset" in (p.get("allergies") or "")

    def test_existing_patients_never_overwritten(self):
        """Verify that existing clinical patients (e.g. CLQ-10482) are untouched."""
        db = get_db()
        res = db.table("patients").select("*").eq("id", "CLQ-10482").execute()
        assert len(res.data) > 0, "Baseline patient CLQ-10482 must exist"
        patient = res.data[0]

        # Verify baseline properties are intact
        assert patient["full_name"] == "Sunita Jadhav"
        assert patient["gender"] == "Female"
        assert "coronary artery disease" in (patient.get("medical_history") or "").lower()
