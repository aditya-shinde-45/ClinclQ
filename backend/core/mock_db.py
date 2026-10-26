import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

LOCAL_DB_FILE = Path(__file__).resolve().parent.parent / "local_db.json"

DEFAULT_SEED_USERS = [
    {
        "id": 1,
        "email": "maya.patel@northlake.org",
        "password_hash": "$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm",
        "full_name": "Dr. Priya Deshmukh",
        "role": "doctor",
        "department": "Cardiology",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "email": "jamie.rivera@northlake.org",
        "password_hash": "$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm",
        "full_name": "Aditya Kulkarni",
        "role": "assistant",
        "department": "Cardiology",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 3,
        "email": "jon.bell@northlake.org",
        "password_hash": "$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm",
        "full_name": "Dr. Rajesh Joshi",
        "role": "doctor",
        "department": "Internal Medicine",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 4,
        "email": "admin@northlake.org",
        "password_hash": "$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm",
        "full_name": "Sneha Patil",
        "role": "admin",
        "department": None,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 5,
        "email": "parth.chavan@cliniq.org",
        "password_hash": "$2b$12$2Uy6hrUPun4oasHrneF2vux0WBVd55Spj.rjfjBtAw7LJyuftNmuW",
        "full_name": "Dr. Parth Chavan",
        "role": "doctor",
        "department": "Cardiology",
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
]

DEFAULT_SEED_PATIENTS = [
    {
        "id": "CLQ-10482",
        "mrn": "MRN-883104",
        "full_name": "Sunita Jadhav",
        "date_of_birth": "1967-09-12",
        "gender": "Female",
        "contact_number": "+91-9876543210",
        "reason_for_visit": "Dyspnea and chest pressure",
        "medical_history": "Hypertension; stable coronary artery disease; hyperlipidemia",
        "allergies": "Penicillin — severe urticaria",
        "current_medications": "Amlodipine 5 mg; Atorvastatin 40 mg; Aspirin 81 mg",
        "past_treatments": "Cardiac rehabilitation, completed Aug 2024",
        "assigned_doctor_id": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "CLQ-10479",
        "mrn": "MRN-881092",
        "full_name": "Ramesh Bhosale",
        "date_of_birth": "1958-03-22",
        "gender": "Male",
        "contact_number": "+91-9876543211",
        "reason_for_visit": "Post-operative review",
        "medical_history": "Type 2 diabetes; previous MI",
        "allergies": "None known",
        "current_medications": "Metformin 500mg; Lisinopril 10mg",
        "past_treatments": "CABG surgery Nov 2024",
        "assigned_doctor_id": 1,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "CLQ-10491",
        "mrn": "MRN-883891",
        "full_name": "Manjusha Pawar",
        "date_of_birth": "1971-07-08",
        "gender": "Female",
        "contact_number": "+91-9876543212",
        "reason_for_visit": "Medication follow-up",
        "medical_history": "Hypothyroidism; osteoarthritis",
        "allergies": "Sulfa drugs",
        "current_medications": "Levothyroxine 75mcg; Ibuprofen as needed",
        "past_treatments": None,
        "assigned_doctor_id": 3,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": "CLQ-10496",
        "mrn": "MRN-884201",
        "full_name": "Anand Kale",
        "date_of_birth": "1965-11-15",
        "gender": "Male",
        "contact_number": "+91-9876543213",
        "reason_for_visit": "Abnormal lab review",
        "medical_history": "Chronic kidney disease stage 3",
        "allergies": "None known",
        "current_medications": "Losartan 50mg",
        "past_treatments": None,
        "assigned_doctor_id": 3,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
]

today_base = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
DEFAULT_SEED_APPOINTMENTS = [
    {
        "id": 1,
        "patient_id": "CLQ-10479",
        "doctor_id": 1,
        "appointment_time": (today_base + timedelta(minutes=30)).isoformat(),
        "reason": "Post-operative review",
        "status": "checked_in",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "patient_id": "CLQ-10482",
        "doctor_id": 1,
        "appointment_time": (today_base + timedelta(hours=1, minutes=15)).isoformat(),
        "reason": "Dyspnea and chest pressure",
        "status": "in_progress",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 3,
        "patient_id": "CLQ-10491",
        "doctor_id": 1,
        "appointment_time": (today_base + timedelta(hours=2)).isoformat(),
        "reason": "Medication follow-up",
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    {
        "id": 4,
        "patient_id": "CLQ-10496",
        "doctor_id": 1,
        "appointment_time": (today_base + timedelta(hours=3, minutes=30)).isoformat(),
        "reason": "Abnormal lab review",
        "status": "scheduled",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
]

DEFAULT_SEED_VISITS = [
    {
        "id": 1,
        "patient_id": "CLQ-10482",
        "title": "Current visit opened",
        "body": "Persistent dyspnea on exertion and intermittent chest pressure reported.",
        "type": "clinical_note",
        "visit_date": datetime.utcnow().isoformat(),
        "created_by_id": 1,
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "patient_id": "CLQ-10482",
        "title": "Cardiology follow-up",
        "body": "Ejection fraction stable at 52%. Continue current medications.",
        "type": "doctor_note",
        "visit_date": (datetime.utcnow() - timedelta(days=35)).isoformat(),
        "created_by_id": 1,
        "created_at": (datetime.utcnow() - timedelta(days=35)).isoformat()
    },
    {
        "id": 3,
        "patient_id": "CLQ-10482",
        "title": "Complete blood count",
        "body": "Hemoglobin 11.2 g/dL, mildly below reference range.",
        "type": "lab_result",
        "visit_date": (datetime.utcnow() - timedelta(days=138)).isoformat(),
        "created_by_id": None,
        "created_at": (datetime.utcnow() - timedelta(days=138)).isoformat()
    }
]

DEFAULT_SEED_KNOWLEDGE_SOURCES = [
    {
        "id": 1,
        "name": "ACC/AHA Clinical Guidelines",
        "type": "guideline_library",
        "version": "2025.06",
        "status": "current",
        "last_synchronized": datetime.utcnow().isoformat()
    },
    {
        "id": 2,
        "name": "Northlake Formulary",
        "type": "local_formulary",
        "version": "v42.8",
        "status": "current",
        "last_synchronized": (datetime.utcnow() - timedelta(hours=2)).isoformat()
    },
    {
        "id": 3,
        "name": "DrugBank Clinical",
        "type": "drug_data",
        "version": "2025-Q2",
        "status": "current",
        "last_synchronized": (datetime.utcnow() - timedelta(days=2)).isoformat()
    },
    {
        "id": 4,
        "name": "NICE Guidance",
        "type": "guideline_library",
        "version": "2025.05",
        "status": "update_pending",
        "last_synchronized": (datetime.utcnow() - timedelta(days=17)).isoformat()
    }
]

DEFAULT_SEED_RISK_FACTORS = [
    {"id": 1, "name": "Known coronary artery disease"},
    {"id": 2, "name": "Hypertension"},
    {"id": 3, "name": "Hyperlipidemia"},
    {"id": 4, "name": "Age over 55"},
    {"id": 5, "name": "Type 2 diabetes"},
    {"id": 6, "name": "Previous MI"},
    {"id": 7, "name": "Chronic kidney disease"},
    {"id": 8, "name": "Smoking history"}
]


class MockResponse:
    def __init__(self, data: Any, count: Optional[int] = None):
        self.data = data
        self.count = count if count is not None else (len(data) if isinstance(data, list) else 1)


class MockStorageBucket:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    def upload(self, path: str, file_content: bytes, file_options: dict = None):
        return {"path": path, "id": path}

    def get_public_url(self, path: str) -> str:
        return f"/uploads/{self.bucket_name}/{path}"


class MockStorage:
    def __init__(self):
        self.buckets = {}

    def from_(self, bucket_name: str):
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = MockStorageBucket(bucket_name)
        return self.buckets[bucket_name]


class MockQueryBuilder:
    def __init__(self, table_name: str, db: "LocalDatabase"):
        self.table_name = table_name
        self.db = db
        self.filters = []
        self.selected_columns = "*"
        self.count_mode = None
        self.order_col = None
        self.order_desc = False
        self.limit_val = None
        self.action = "select"
        self.payload = None

    def select(self, columns: str = "*", count: Optional[str] = None):
        self.selected_columns = columns
        self.count_mode = count
        self.action = "select"
        return self

    def insert(self, data: Any):
        self.action = "insert"
        self.payload = data
        return self

    def upsert(self, data: Any, on_conflict: str = None):
        self.action = "upsert"
        self.payload = data
        self.on_conflict = on_conflict
        return self

    def update(self, data: Any):
        self.action = "update"
        self.payload = data
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, col: str, val: Any):
        self.filters.append(("eq", col, val))
        return self

    def neq(self, col: str, val: Any):
        self.filters.append(("neq", col, val))
        return self

    def gte(self, col: str, val: Any):
        self.filters.append(("gte", col, val))
        return self

    def lte(self, col: str, val: Any):
        self.filters.append(("lte", col, val))
        return self

    def gt(self, col: str, val: Any):
        self.filters.append(("gt", col, val))
        return self

    def lt(self, col: str, val: Any):
        self.filters.append(("lt", col, val))
        return self

    def ilike(self, col: str, pattern: str):
        self.filters.append(("ilike", col, pattern))
        return self

    def order(self, col: str, desc: bool = False):
        self.order_col = col
        self.order_desc = desc
        return self

    def limit(self, count: int):
        self.limit_val = count
        return self

    def execute(self) -> MockResponse:
        table_data = self.db.get_table(self.table_name)

        if self.action == "insert":
            inserted = self.db.insert_row(self.table_name, self.payload)
            return MockResponse(inserted if isinstance(inserted, list) else [inserted])

        if self.action == "upsert":
            payload_items = self.payload if isinstance(self.payload, list) else [self.payload]
            conflict_col = self.on_conflict or "chunk_id"
            res = []
            for item in payload_items:
                key_val = item.get(conflict_col)
                existing_idx = None
                if key_val is not None:
                    for i, r in enumerate(table_data):
                        if str(r.get(conflict_col)) == str(key_val):
                            existing_idx = i
                            break
                if existing_idx is not None:
                    table_data[existing_idx].update(item)
                    table_data[existing_idx]["updated_at"] = datetime.utcnow().isoformat()
                    res.append(dict(table_data[existing_idx]))
                else:
                    res.append(self.db.insert_single(table_data, item))
            self.db.save()
            return MockResponse(res)

        # Filter rows
        matched = []
        matched_indices = []
        for idx, row in enumerate(table_data):
            match = True
            for ftype, col, val in self.filters:
                row_val = row.get(col)
                if ftype == "eq":
                    if str(row_val) != str(val):
                        match = False
                        break
                elif ftype == "neq":
                    if str(row_val) == str(val):
                        match = False
                        break
                elif ftype == "gte":
                    if row_val is None or str(row_val) < str(val):
                        match = False
                        break
                elif ftype == "lte":
                    if row_val is None or str(row_val) > str(val):
                        match = False
                        break
                elif ftype == "gt":
                    if row_val is None or str(row_val) <= str(val):
                        match = False
                        break
                elif ftype == "lt":
                    if row_val is None or str(row_val) >= str(val):
                        match = False
                        break
                elif ftype == "ilike":
                    clean_pattern = str(val).replace("%", "").lower()
                    if clean_pattern and (row_val is None or clean_pattern not in str(row_val).lower()):
                        match = False
                        break
            if match:
                matched.append(dict(row))
                matched_indices.append(idx)

        if self.action == "update":
            updated_rows = []
            for idx in matched_indices:
                row = table_data[idx]
                row.update(self.payload)
                row["updated_at"] = datetime.utcnow().isoformat()
                updated_rows.append(dict(row))
            self.db.save()
            return MockResponse(updated_rows)

        if self.action == "delete":
            for idx in sorted(matched_indices, reverse=True):
                del table_data[idx]
            self.db.save()
            return MockResponse({"success": True})

        # Selection & Joins
        results = matched

        # Handle join expansions
        for r in results:
            if "patient:patients!patient_id" in self.selected_columns:
                p_id = r.get("patient_id")
                patient = next((p for p in self.db.get_table("patients") if p.get("id") == p_id), None)
                if patient:
                    r["patient"] = {"full_name": patient.get("full_name")}
            if "assigned_doctor:users!assigned_doctor_id" in self.selected_columns:
                doc_id = r.get("assigned_doctor_id")
                doctor = next((u for u in self.db.get_table("users") if str(u.get("id")) == str(doc_id)), None)
                if doctor:
                    doc_copy = dict(doctor)
                    doc_copy.pop("password_hash", None)
                    r["assigned_doctor"] = doc_copy
            if "risk_factor:risk_factors!risk_factor_id" in self.selected_columns:
                rf_id = r.get("risk_factor_id")
                rf = next((x for x in self.db.get_table("risk_factors") if str(x.get("id")) == str(rf_id)), None)
                if rf:
                    r["risk_factor"] = {"name": rf.get("name")}

        # Ordering
        if self.order_col:
            def sort_key(item):
                val = item.get(self.order_col)
                return ("" if val is None else str(val))
            results.sort(key=sort_key, reverse=self.order_desc)

        # Limit
        if self.limit_val is not None:
            results = results[:self.limit_val]

        total_count = len(matched)
        return MockResponse(results, count=total_count)


class LocalDatabase:
    def __init__(self):
        self.storage = MockStorage()
        self.data: Dict[str, List[Dict[str, Any]]] = {}
        self.load()

    def load(self):
        if LOCAL_DB_FILE.exists():
            try:
                with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    return
            except Exception:
                pass
        
        # Populate defaults
        self.data = {
            "users": list(DEFAULT_SEED_USERS),
            "patients": list(DEFAULT_SEED_PATIENTS),
            "appointments": list(DEFAULT_SEED_APPOINTMENTS),
            "visits": list(DEFAULT_SEED_VISITS),
            "knowledge_sources": list(DEFAULT_SEED_KNOWLEDGE_SOURCES),
            "risk_factors": list(DEFAULT_SEED_RISK_FACTORS),
            "clinical_analyses": [],
            "diagnoses": [],
            "recommendations": [],
            "drug_interactions": [],
            "analysis_risk_factors": [],
            "clinical_decisions": [],
            "documents": [],
            "patient_record_chunks": []
        }
        self.save()

    def save(self):
        try:
            with open(LOCAL_DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print("Error saving local db:", e)

    def get_table(self, name: str) -> List[Dict[str, Any]]:
        self.load()
        if name not in self.data:
            self.data[name] = []
        return self.data[name]

    def insert_row(self, table_name: str, payload: Any):
        table = self.get_table(table_name)
        if isinstance(payload, list):
            res = []
            for item in payload:
                res.append(self.insert_single(table, item))
            self.save()
            return res
        else:
            res = self.insert_single(table, payload)
            self.save()
            return res

    def insert_single(self, table: List[Dict[str, Any]], item: Dict[str, Any]) -> Dict[str, Any]:
        row = dict(item)
        if "id" not in row:
            existing_ids = [r["id"] for r in table if isinstance(r.get("id"), int)]
            row["id"] = (max(existing_ids) + 1) if existing_ids else 1
        now = datetime.utcnow().isoformat()
        if "created_at" not in row:
            row["created_at"] = now
        if "updated_at" not in row:
            row["updated_at"] = now
        table.append(row)
        return row

    def table(self, table_name: str) -> MockQueryBuilder:
        return MockQueryBuilder(table_name, self)

    def rpc(self, function_name: str, params: dict = None):
        """Simulate Supabase stored procedures such as match_patient_record_chunks"""
        class MockRpcCaller:
            def __init__(self, db, fn_name, fn_params):
                self.db = db
                self.fn_name = fn_name
                self.fn_params = fn_params or {}

            def execute(self):
                if self.fn_name == "match_patient_record_chunks":
                    query_emb = self.fn_params.get("query_embedding", [])
                    target_pid = str(self.fn_params.get("target_patient_id", ""))
                    threshold = float(self.fn_params.get("match_threshold", 0.0))
                    limit = int(self.fn_params.get("match_count", 5))

                    chunks = self.db.get_table("patient_record_chunks")
                    matched = []
                    try:
                        import numpy as np
                        q_vec = np.array(query_emb, dtype=np.float32)
                        q_norm = float(np.linalg.norm(q_vec))
                    except Exception:
                        q_vec = None
                        q_norm = 0.0

                    for c in chunks:
                        if str(c.get("patient_id")) != target_pid:
                            continue
                        c_emb = c.get("embedding", [])
                        if not c_emb or len(c_emb) != len(query_emb):
                            continue

                        if q_vec is not None and q_norm > 0:
                            c_vec = np.array(c_emb, dtype=np.float32)
                            c_norm = float(np.linalg.norm(c_vec))
                            if c_norm > 0:
                                sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                            else:
                                sim = 0.0
                        else:
                            sim = 0.5

                        if sim >= threshold:
                            matched.append({
                                "id": c.get("id"),
                                "chunk_id": c.get("chunk_id"),
                                "patient_id": c.get("patient_id"),
                                "source_type": c.get("source_type"),
                                "source_id": c.get("source_id"),
                                "content": c.get("content"),
                                "metadata": c.get("metadata", {}),
                                "similarity": round(sim, 4)
                            })

                    matched.sort(key=lambda x: x["similarity"], reverse=True)
                    return MockResponse(matched[:limit])

                return MockResponse([])

        return MockRpcCaller(self, function_name, params)
