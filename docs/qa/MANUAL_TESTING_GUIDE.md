# ClinIQ — Comprehensive Manual Testing Guide

This guide provides step-by-step manual testing instructions for the **ClinIQ** Clinical Decision Support (CDS) application, following the patient-centric RAG architecture.

---

## 1. System Setup & Startup

### Prerequisites
- Python 3.12 (virtual environment at `backend/venv`)
- Node.js 20+ & npm
- Valid AWS credentials configured in `backend/.env` for Amazon Bedrock (`ap-south-1`) and Amazon S3

### Starting the Servers

#### Method A: One-Click Startup (Recommended)
From the repository root in PowerShell:
```powershell
.\start-all.bat
```

#### Method B: Independent Server Windows
* **Terminal 1 (Backend API):**
  ```powershell
  cd "C:\Users\Parth Chavan\Desktop\projects\ClinclQ"
  .\start-backend.bat
  ```
  *Listens at: `http://localhost:8000`*
* **Terminal 2 (Frontend UI):**
  ```powershell
  cd "C:\Users\Parth Chavan\Desktop\projects\ClinclQ"
  .\start-frontend.bat
  ```
  *Listens at: `http://localhost:8443` (or `http://localhost:5173`)*

### Service Endpoints
| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | `http://localhost:8443` | Main clinical user interface |
| **Backend REST API** | `http://localhost:8000` | FastAPI server |
| **API Documentation** | `http://localhost:8000/docs` | Interactive Swagger UI |
| **AWS Infrastructure Status** | `http://localhost:8000/aws/status` | Live Bedrock & S3 operational probe |
| **System Health Check** | `http://localhost:8000/health` | Service health status |

---

## 2. Authentication & Demo Account Directory

ClinIQ uses email-based JWT authentication (`POST /auth/login`). Passwords are encrypted with `bcrypt`.

> **Note on Credentials:** Passwords are kept in the local-only configuration file `demo_credentials.local.json` (gitignored). Refer to that file for live passwords.

### Available Verified Accounts

| Role | Name | Email (Login Identifier) | Purpose in Testing |
| :--- | :--- | :--- | :--- |
| **Doctor** *(Primary)* | Dr. Parth Chavan | `parth.chavan@cliniq.org` | Full clinical access, Bedrock CDS analyses, differential diagnosis reviews, physician approval sign-off. |
| **Doctor** *(Secondary)* | Dr. Priya Deshmukh | `maya.patel@northlake.org` | Cardiology consultations, patient review, decision attestation. |
| **Assistant** | Aditya Kulkarni | `jamie.rivera@northlake.org` | Patient intake, appointment booking, S3 document uploads. **Blocked from doctor analyses**. |
| **Administrator** | Sneha Patil | `admin@northlake.org` | System metrics, user accounts management, CDS usage audit log. |
| **Deactivated Account** | Kavita Sharma | `morgan.scott@northlake.org` | Negative security testing: verifies `HTTP 403 Forbidden` response for deactivated accounts. |

---

## 3. Verified Demonstration Patients

Use these three real records currently indexed in Supabase and the vector store:

### Patient A: Sunita Jadhav (`CLQ-10482`)
- **Display Name**: Sunita Jadhav (MRN: `MRN-883104`)
- **Demographics**: 59-year-old Female (DOB: `1967-09-12`)
- **Known Medical History**: Hypertension; stable coronary artery disease; hyperlipidemia.
- **Documented Allergies**: Penicillin (severe urticaria).
- **Current Medications**: Amlodipine 5 mg, Atorvastatin 40 mg, Aspirin 81 mg.
- **Encounters & Documents**: 4 visits + 5 uploaded lab documents.
- **Expected RAG Evidence**: Chart profile and cardiology timeline chunks detailing chest pressure and dyspnea on exertion.
- **Isolation Check**: Does NOT have a stroke history or appendectomy.

### Patient B: Demo Patient #1 (`CLQ-HOSP-0001`)
- **Display Name**: Demo Patient #1 (MRN: `MRN-HOSP-0001`)
- **Demographics**: 45-year-old Female (DOB: `1981-01-01`)
- **Source Facts**: Admitted for Heart Disease; underwent Inpatient Angioplasty; 5-day hospital stay; care cost $15,000; discharged recovered; 30-day readmission: No.
- **Expected RAG Evidence**: Chunks `chunk_CLQ-HOSP-0001_profile_0` and `chunk_CLQ-HOSP-0001_visit_5_0` citing Angioplasty and Heart Disease telemetry.
- **Isolation Check**: Does NOT take Amlodipine (Patient A) and has NO stroke history (Patient C).

### Patient C: Demo Patient #4 (`CLQ-HOSP-0004`)
- **Display Name**: Demo Patient #4 (MRN: `MRN-HOSP-0004`)
- **Demographics**: 56-year-old Male (DOB: `1970-01-01`)
- **Source Facts**: Admitted for Stroke; underwent Inpatient CT Scan and Medication; 7-day hospital stay; care cost $10,000; **30-Day Readmission: YES**; discharge outcome: Stable.
- **Expected RAG Evidence**: Chunk `chunk_CLQ-HOSP-0004_visit_4_0` detailing 30-day stroke readmission and inpatient care.
- **Isolation Check**: Does NOT have Angioplasty (Patient B) and has NO Penicillin allergy (Patient A).

---

## 4. Step-by-Step Manual Test Execution

### Test Scenario 1: Authentication & Session Management
1. Open `http://localhost:8443` in your browser.
2. Enter email `parth.chavan@cliniq.org` with an intentionally wrong password (`wrong123`).
   * **Expected**: Login fails with clear error: *"Incorrect email or password"*. User remains unauthenticated.
3. Enter email `morgan.scott@northlake.org` with the valid demo password.
   * **Expected**: Login fails with: *"Account is deactivated"* (HTTP 403).
4. Enter email `parth.chavan@cliniq.org` with the valid demo password from `demo_credentials.local.json`.
   * **Expected**: Successful login. Dashboard loads, displaying current active doctor badge and navigation tabs.
5. Click **Logout**.
   * **Expected**: Session token is cleared from `localStorage`. User is returned to login screen. Refreshing the browser preserves the logged-out state.

---

### Test Scenario 2: Patient Lookup & RAG Clinical Profile Inspection
1. Log in as Doctor (`parth.chavan@cliniq.org`).
2. In the patient search box, type `Sunita` or `CLQ-10482`.
3. Click on **Sunita Jadhav**.
   * **Expected**: Profile loads with:
     - Age, Gender (Female), MRN (`MRN-883104`)
     - Known medical history: Hypertension, stable CAD, hyperlipidemia
     - Documented Allergy: *Penicillin — severe urticaria*
     - Active medications: *Amlodipine 5 mg, Atorvastatin 40 mg, Aspirin 81 mg*
     - Historical timeline of visits
4. Search for `CLQ-HOSP-0004`.
   * **Expected**: Shows Demo Patient #4 with Stroke diagnosis, 7-day stay, and 30-day readmission flag.

---

### Test Scenario 3: End-to-End AI Analysis & Evidence Grounding (AWS Bedrock)
1. In patient **Sunita Jadhav** (`CLQ-10482`), click **"Request Analysis"** / **"New Clinical Analysis"**.
2. Fill in the clinical evaluation inputs:
   * **Symptoms / Chief Complaint**:
     ```text
     Substernal chest tightness radiating to the left arm and jaw, occurring with exertion, relieved within 5 minutes of rest or sublingual nitroglycerin.
     ```
   * **Vitals & Physical Findings**:
     ```text
     BP: 148/92 mmHg, HR: 86 bpm regular, SpO2: 98% room air. Mild diaphoresis, S4 gallop audible at apex.
     ```
   * **Lab & Diagnostic Findings**:
     ```text
     Resting 12-lead ECG demonstrates 1.5mm horizontal ST depression in leads V4-V6. Initial high-sensitivity Troponin-I is normal at 0.02 ng/mL.
     ```
3. Click **"Run Analysis"** (or **"Submit"**).
4. Observe the processing state (loading indicator active while background polling runs).
5. **Verify AI-Generated Differential Report**:
   * **Status**: `awaiting_review`
   * **Differential Diagnoses**:
     - *Stable Angina Pectoris* (High probability)
     - *Acute Coronary Syndrome* (needs review / cannot be ruled out despite normal troponin)
   * **Retrieved RAG Evidence**: Cites patient medical history items and timeline records.
   * **Guideline-Directed Recommendations**: Step 1: Complete serial high-sensitivity Troponin testing; Step 2: Echocardiogram; Step 3: Optimize anti-anginal therapy.
   * **Drug Interaction Screening**: Flags interactions with current medications (Amlodipine/Aspirin).

---

### Test Scenario 4: Physician Sign-Off & Attestation
1. In the awaiting review report, review the differential diagnoses and recommendations.
2. Check the doctor attestation checkbox (*"I have independently evaluated the AI recommendations..."*).
3. Optionally add a clinical note: *"Approved following initial ECG and normal troponin review; proceeding with serial biomarkers."*
4. Click **"Approve Report"**.
   * **Expected**:
     - Status updates immediately to `approved`.
     - Decision is persisted with timestamp and reviewer ID.
     - Action buttons are locked (cannot be re-approved).
5. Refresh the browser page (`F5`).
   * **Expected**: Status remains `approved`. Persistence in Supabase is preserved.

---

### Test Scenario 5: AWS S3 Encrypted Document Management
1. In patient `CLQ-10482`, navigate to the **Documents** tab.
2. Click **Upload Document**.
3. Choose category `Lab Report` and attach a sample PDF or image file (e.g. `cardiac_panel.pdf`).
4. Click **Upload**.
   * **Expected**: File is streamed to AWS S3 bucket (`cliniq-app-storage-2026-unique`) with `AES256` server-side encryption. Document appears in the list.
5. Click on the uploaded document name.
   * **Expected**: An AWS S3 **presigned URL** is generated with temporary validity. Document opens in a new tab securely.

---

### Test Scenario 6: Role-Based Authorization Enforcement (Assistant Role)
1. Log out from the Doctor account.
2. Log in as Assistant (`jamie.rivera@northlake.org` / password from `demo_credentials.local.json`).
3. Verify assistant navigation:
   * Assistant can view patient profiles, book appointments, and upload documents.
4. Attempt to run a CDS clinical analysis or approve a report.
   * **Expected**: Doctor-only analysis options are hidden or return `403 Forbidden` if submitted directly.

---

## 5. Account Regeneration & Cleanup

### Creating New Demo Accounts Anytime
```powershell
.\backend\venv\Scripts\python.exe backend\create_user.py --email "dr.new@cliniq.org" --name "Dr. Test Doctor" --role "doctor" --department "Neurology" --password "hospital123"
```

### Revoking Demo Accounts
To deactivate a temporary account, run from PowerShell:
```powershell
.\backend\venv\Scripts\python.exe -c "from core.database import get_db; db = get_db(); db.table('users').update({'status': 'deactivated'}).eq('email', 'dr.new@cliniq.org').execute(); print('Account deactivated.')"
```
