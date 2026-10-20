# ClinIQ — AI Clinical Decision Support System

ClinIQ is a full-stack clinical decision support (CDS) web application built for healthcare practitioners. It pairs an intuitive React 19 + TypeScript frontend with a high-performance FastAPI backend, powered by **AWS Bedrock (Meta Llama 3 70B Instruct)** for real-time differential diagnoses and **AWS S3** with server-side AES256 encryption for patient document management.

---

## 🌟 Key Features

* **AI Clinical Decision Support Engine**: Uses **Meta Llama 3 70B Instruct** on **AWS Bedrock** to synthesize evidence-grounded differential diagnoses, guideline-directed next steps, drug-drug safety screens, and patient-specific risk factor stratification.
* **Encrypted Medical Document Storage**: Secure document uploading to **AWS S3** (`AES256` server-side encryption) with dynamic, expiring pre-signed URLs (AWS SigV4) for imaging and lab reports.
* **Patient Context Synthesis**: Seamlessly injects patient history, current medications, vital signs, and attached S3 medical records directly into LLM clinical prompts.
* **Physician Sign-Off & Governance**: Full audit trail allowing board-certified clinicians to review, approve, modify, or reject AI-generated clinical suggestions.
* **Role-Based Access Control**: Separate workflows for **Doctors**, **Assistants**, and **Admins** with JWT authentication and bcrypt password hashing.
* **Zero-Downtime Resilience**: Hybrid database layer supporting live cloud Supabase or autonomous local database fallback with automatic DNS detection.

---

## 🏗️ Architecture & Project Structure

```
.
├── frontend/                     # React 19 + Vite + Tailwind CSS v4
│   ├── src/
│   │   ├── App.tsx               # Main application component & dashboards
│   │   ├── api.ts                # REST API client & auth handlers
│   │   ├── config.ts             # Environment configuration
│   │   ├── main.tsx              # React entry point
│   │   └── index.css             # Tailwind v4 design system
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── backend/                      # FastAPI Python Application
│   ├── core/
│   │   ├── config.py             # Pydantic environment configuration
│   │   ├── database.py           # Database connection & fallback engine
│   │   ├── mock_db.py            # Resilient local JSON database
│   │   └── security.py           # JWT tokens & bcrypt password hashing
│   ├── models/
│   │   └── schemas.py            # Pydantic data validation schemas
│   ├── routers/
│   │   ├── auth.py               # Authentication & login
│   │   ├── patients.py           # Patient demographics & timeline
│   │   ├── appointments.py       # Clinical appointment booking
│   │   ├── analyses.py           # AWS Bedrock CDS generation & decisions
│   │   ├── documents.py          # AWS S3 file upload & presigned URLs
│   │   └── admin.py              # User management & system metrics
│   ├── services/
│   │   ├── bedrock_service.py    # AWS Bedrock Converse API (Llama 3 70B)
│   │   ├── s3_service.py         # AWS S3 AES256 storage & presigned URLs
│   │   └── mock_analysis.py      # Clinical fallback inference generator
│   ├── create_user.py            # CLI user generation tool
│   ├── test_api_aws.py           # End-to-end 8-point API verification suite
│   ├── test_aws.py               # Direct AWS S3 & Bedrock diagnostic probe
│   ├── local_db.json             # Seeded clinical database
│   ├── main.py                   # FastAPI application entry point
│   └── requirements.txt          # Python dependencies (boto3, fastapi, etc.)
│
├── start-all.bat                 # One-click launcher for Frontend & Backend
├── start-backend.bat             # Launcher for FastAPI server (Port 8000)
├── start-frontend.bat            # Launcher for Vite dev server (Port 5173)
├── USERS_AND_WORKFLOW.md         # Credentials, user directory & test guide
└── README.md                     # This file
```

---

## 🚀 Quick Start

### 1. Prerequisites
* **Node.js** (v18+) & **npm** or **pnpm**
* **Python** (3.10+) with `venv`

### 2. Launching the Application
You can start both servers simultaneously on Windows using the batch script:
```powershell
.\start-all.bat
```

Or run each in its own terminal:

**Terminal 1 (Backend):**
```powershell
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```powershell
cd frontend
npm run dev
```

* **Frontend UI**: [http://localhost:5173](http://localhost:5173)
* **Backend API**: [http://localhost:8000](http://localhost:8000)
* **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **AWS Status Monitor**: [http://localhost:8000/aws/status](http://localhost:8000/aws/status)

---

## 🔐 Credentials & Testing Workflow

For full credentials, testing scenarios, and sample inputs, see:
👉 **[USERS_AND_WORKFLOW.md](USERS_AND_WORKFLOW.md)**

### Quick Login Credentials (Password for all: `clinical-access`)
* **Doctor**: `parth.chavan@cliniq.org`
* **Assistant**: `jamie.rivera@northlake.org`
* **Admin**: `admin@northlake.org`

---

## ☁️ AWS Configuration

The backend is configured in `backend/.env` with:

```env
# AWS Configuration (India - ap-south-1 Mumbai)
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=ap-south-1
AWS_S3_BUCKET_NAME=cliniq-app-storage-2026-unique
AWS_BEDROCK_MODEL_ID=meta.llama3-70b-instruct-v1:0
```

### Supported AWS Services:
1. **Amazon Bedrock**:
   * Model: `meta.llama3-70b-instruct-v1:0` (Meta Llama 3 70B Instruct)
   * API: `converse()` operation with structured schema enforcement
2. **Amazon Simple Storage Service (S3)**:
   * Bucket: `cliniq-app-storage-2026-unique`
   * Server-Side Encryption: `AES256`
   * Access: Secure temporary presigned URLs (`generate_presigned_url`)

---

## 🧪 Automated Testing

### 1. Run the Full 8-Point API & AWS Verification Suite:
```powershell
cd backend
.\venv\Scripts\python.exe test_api_aws.py
```
This tests:
1. Health & AWS infrastructure status (`/health`, `/aws/status`)
2. Doctor login & JWT token issuance (`/auth/login`)
3. S3 document upload with AES256 encryption (`/documents/upload`)
4. Dynamic AWS presigned URL generation (`/documents/patient/{id}`)
5. Real-time Llama 3 70B Bedrock inference (`/analyses`)
6. Verification of generated differential diagnoses, recommendations, and drug checks
7. Clinical decision recording and approval (`/analyses/{id}/decision`)
8. S3 document deletion and database cleanup (`/documents/{id}`)

### 2. Run Direct AWS Probe Test:
```powershell
cd backend
.\venv\Scripts\python.exe test_aws.py
```

### 3. Create Custom Test Users:
```powershell
cd backend
.\venv\Scripts\python.exe create_user.py --email "doctor@hospital.org" --name "Dr. Name" --role "doctor" --password "yourpassword"
```

---

## 📜 License
Developed for ClinIQ Clinical Decision Support Systems. Internal Clinical Research & Healthcare Use.
