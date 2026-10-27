# ClinIQ — Complete End-to-End Setup Guide

This guide contains everything needed to set up, configure, import the clinical dataset, and run the **ClinIQ** Clinical Decision Support (CDS) application from scratch.

---

## 📋 1. Prerequisites

Before starting, ensure the following software is installed on your computer:

| Requirement | Recommended Version | Download Link | Purpose |
| :--- | :--- | :--- | :--- |
| **Python** | `3.10` to `3.12` | [python.org](https://www.python.org/downloads/) | FastAPI backend, RAG pipeline, and dataset importer |
| **Node.js** | `v18+` or `v20+` (LTS) | [nodejs.org](https://nodejs.org/) | Vite / React frontend web application |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) | Version control |
| **Supabase** | Free Cloud Project | [supabase.com](https://supabase.com/) | PostgreSQL database & vector embeddings store |
| **AWS Account** | Active with IAM credentials | [aws.amazon.com](https://aws.amazon.com/) | Bedrock LLM (`ap-south-1`) & S3 document storage |

> **Note on Python on Windows:** Make sure to check the box **"Add python.exe to PATH"** during Python installation.

---

## 🗄️ 2. Database Setup (Supabase)

ClinIQ uses a Supabase PostgreSQL instance with pgvector for clinical document retrieval.

1. Log into [supabase.com](https://supabase.com) and click **"New Project"**.
2. Give your project a name (e.g. `cliniq-hospital-db`), choose region **Mumbai (`ap-south-1`)** or closest to you, and set a database password.
3. Once initialized (1–2 minutes), navigate to the **SQL Editor** tab from the left sidebar.

### Step 2.1: Execute Schema DDL
* Open [`backend/schema.sql`](file:///c:/Users/Parth%20Chavan/Desktop/projects/ClinclQ/backend/schema.sql).
* Copy the full file content, paste it into the Supabase SQL Editor, and click **Run**.
* *Creates:* `users`, `patients`, `visits`, `medical_documents`, `clinical_analyses`, `diagnoses`, `recommendations`, `drug_interactions`, `risk_factors`, `analysis_risk_factors`, `clinical_decisions`, `appointments`, and `patient_embeddings`.

### Step 2.2: Seed Demo Users & Patients
* Open [`backend/seed_data.sql`](file:///c:/Users/Parth%20Chavan/Desktop/projects/ClinclQ/backend/seed_data.sql).
* Copy the full content, paste into the Supabase SQL Editor, and click **Run**.
* *Seeds:* Staff accounts (Doctor, Assistant, Admin) and patient **Sunita Jadhav** (`CLQ-10482`).

---

## ⚙️ 3. Backend Setup

### Step 3.1: Open Terminal in Backend
```powershell
cd ClinclQ\backend
```

### Step 3.2: Create and Activate Virtual Environment
* **On Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\activate
  ```
* **On macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3.3: Install Python Packages
```bash
pip install -r requirements.txt
```

### Step 3.4: Configure Backend Environment Variables
Create the `.env` file from the example:
* **Windows:**
  ```powershell
  copy .env.example .env
  ```
* **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

Edit `backend/.env` with your actual credentials:
```env
# Supabase (Settings > API in your Supabase Dashboard)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_public_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# JWT Security
JWT_SECRET_KEY=hospital-clinclq-secret-key-32-chars-minimum!
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:8443","http://localhost:5173","http://localhost:3000","http://127.0.0.1:8443","http://127.0.0.1:5173"]

# AWS Infrastructure (ap-south-1 Mumbai)
AWS_ACCESS_KEY_ID=AKIA...your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
AWS_S3_BUCKET_NAME=cliniq-app-storage-2026-unique
AWS_BEDROCK_MODEL_ID=meta.llama3-70b-instruct-v1:0
AWS_BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

---

## 📊 4. Import Dataset & Generate RAG Embeddings

ClinIQ includes a hospital Kaggle dataset located in `backend/dataset/archive/hospital data analysis.csv`.

To import the clinical records and generate vector embeddings with Amazon Titan:

Make sure the backend virtual environment is active, then run from the **project root**:
```powershell
# Windows
.\backend\venv\Scripts\python.exe backend\scripts\import_kaggle_dataset.py --index-rag

# macOS / Linux
python3 backend/scripts/import_kaggle_dataset.py --index-rag
```

**What this step performs:**
1. Validates each inpatient record (diagnoses, angioplasty/CT procedures, stay lengths, outcomes).
2. Inserts verified patient and visit records into Supabase.
3. Uses Amazon Titan Embeddings v2 (`amazon.titan-embed-text-v2:0`) to create 1024-dimensional semantic vectors and stores them in `patient_embeddings` for RAG lookup.

---

## 💻 5. Frontend Setup

### Step 5.1: Open a Second Terminal
```powershell
cd ClinclQ\frontend
```

### Step 5.2: Install NPM Dependencies
```bash
npm install
```

### Step 5.3: Configure Frontend Environment Variables
* **Windows:**
  ```powershell
  copy .env.example .env
  ```
* **macOS / Linux:**
  ```bash
  cp .env.example .env
  ```

Ensure `frontend/.env` contains:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🚀 6. Running the Application

### Option A: One-Click Startup (Windows)
From the project root:
```powershell
.\start-all.bat
```
*This starts both the FastAPI server and the Vite dev server in separate terminal windows.*

---

### Option B: Running in Independent Terminals

#### Terminal 1 — Backend (Port 8000):
```powershell
cd ClinclQ\backend
.\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
* **API Server:** [http://localhost:8000](http://localhost:8000)
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **AWS Health Status:** [http://localhost:8000/aws/status](http://localhost:8000/aws/status)

#### Terminal 2 — Frontend (Port 8443):
```powershell
cd ClinclQ\frontend
npm run dev
```
* **Web Application:** [http://localhost:8443](http://localhost:8443) *(or [http://localhost:5173](http://localhost:5173))*

---

## 🔑 7. Verified Demo Accounts

Every demo user account uses the standard password: **`clinical-access`**

| Role | Name | Email (Username) | Password | Permissions & Features |
| :--- | :--- | :--- | :--- | :--- |
| **Doctor (Primary)** | Dr. Parth Chavan | `parth.chavan@cliniq.org` | `clinical-access` | **Full Clinical Access**: Request Bedrock CDS analysis, review differential diagnoses, sign off decisions. |
| **Doctor (Secondary)** | Dr. Priya Deshmukh | `maya.patel@northlake.org` | `clinical-access` | Cardiology review and patient chart consults. |
| **Assistant** | Aditya Kulkarni | `jamie.rivera@northlake.org` | `clinical-access` | **Front Desk**: Patient intake, appointment scheduling, S3 document uploads. |
| **Admin** | Sneha Patil | `admin@northlake.org` | `clinical-access` | System metrics, user accounts management, audit logs. |

> **Ready-to-Use Test Data:** For realistic clinical presentations that cite the Kaggle dataset and test Bedrock CDS, refer to [`SAMPLE_PATIENT_TEST_CASES.md`](./SAMPLE_PATIENT_TEST_CASES.md).

---

## 🧪 8. Automatic Verification Suite

You can verify the entire setup, Supabase database, S3 uploads, and AWS Bedrock Llama 3 70B inference by running the included automated test suite:

```powershell
.\backend\venv\Scripts\python.exe backend\test_api_aws.py
```

Expected output:
```text
[TEST 1] GET /health & /aws/status           --> PASS (Bedrock & S3 operational)
[TEST 2] POST /auth/login                     --> PASS (Dr. Parth Chavan authenticated)
[TEST 3] POST /documents/upload               --> PASS (S3 AES256 upload verified)
[TEST 4] GET /documents/patient/CLQ-10482     --> PASS (Presigned S3 URL verified)
[TEST 5] POST /analyses                       --> PASS (Bedrock Llama 3 70B inference)
[TEST 6] GET /analyses/{id}                   --> PASS (Differential report generated)
[TEST 7] POST /analyses/{id}/decision          --> PASS (Physician approval recorded)
[TEST 8] DELETE /documents/{id}               --> PASS (S3 cleanup)
=================================================================
ALL API & AWS S3 / BEDROCK TESTS PASSED SUCCESSFULLY! (8/8)
=================================================================
```

---

## 💡 9. Troubleshooting & FAQ

* **Issue: `InvalidSignatureException: Signature expired` from AWS**
  * *Cause:* Local PC clock is out of sync with internet time.
  * *Fix:* The backend automatically calibrates clock skew via `backend/core/aws_time_sync.py` upon startup. No manual action is required.
* **Issue: CORS error in browser**
  * *Cause:* Frontend is running on a port not listed in `backend/.env`.
  * *Fix:* Verify that `CORS_ORIGINS` in `backend/.env` includes `http://localhost:8443` and `http://localhost:5173`.
* **Issue: Adding a custom doctor or staff account**
  * *Fix:* Run from the project root:
    ```powershell
    .\backend\venv\Scripts\python.exe backend\create_user.py --email "dr.name@hospital.org" --name "Dr. Full Name" --role "doctor" --password "hospital123"
    ```
