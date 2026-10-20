# ClinIQ — Users, Credentials & Testing Workflow Guide

This guide contains all login credentials, roles, and step-by-step instructions for testing **AWS Bedrock (Llama 3 70B)**, **AWS S3 Document Storage**, and the clinical workflows in ClinIQ.

---

## 🔐 1. User Directory & Credentials

All seeded accounts are active. Every account uses the standard clinical testing password:

> **Default Password for all accounts:** `clinical-access`

### Available Accounts by Role

| Role | Name | Email (Username) | Password | Permissions & Features |
| :--- | :--- | :--- | :--- | :--- |
| **Doctor** *(Recommended)* | **Dr. Parth Chavan** | `parth.chavan@cliniq.org` | `clinical-access` | **Full Clinical Access**: Run AWS Bedrock CDS analyses, review differential diagnoses, approve/modify clinical decisions, view/upload patient records. |
| **Doctor** | Dr. Priya Deshmukh | `maya.patel@northlake.org` | `clinical-access` | Run Bedrock analyses, review cardiology patients, manage diagnoses. |
| **Doctor** | Dr. Rajesh Joshi | `jon.bell@northlake.org` | `clinical-access` | Internal Medicine consultations, review timelines, patient management. |
| **Doctor** *(Newly added)* | Dr. Arjun Mehta | `test.doctor@cliniq.org` | `doctor123` | Fresh doctor test account in Cardiology. |
| **Assistant** | **Aditya Kulkarni** | `jamie.rivera@northlake.org` | `clinical-access` | **Clinical Desk**: Register new patients, upload lab reports/imaging to **AWS S3**, book and reschedule appointments. |
| **Admin** | **Sneha Patil** | `admin@northlake.org` | `clinical-access` | **System Admin**: Create & manage staff accounts, monitor CDS usage metrics, view audit logs. |

---

## 🛠️ 2. How to Create Custom Users Anytime

You can create brand new users at any time using either the command line or the Admin interface:

### Method A: One-line Terminal Command (Fastest)
From the project root or `backend/` directory:
```powershell
.\backend\venv\Scripts\python.exe backend\create_user.py --email "dr.smith@cliniq.org" --name "Dr. Jane Smith" --role "doctor" --department "Neurology" --password "hospital123"
```
*(Supported roles: `doctor`, `assistant`, `admin`)*

### Method B: Interactive Prompt
```powershell
.\backend\venv\Scripts\python.exe backend\create_user.py
```
It will guide you to enter the email, full name, role, department, and password.

### Method C: Through the Admin UI
1. Log in as `admin@northlake.org` with password `clinical-access`.
2. Go to the **Admin Dashboard** &rarr; **User Management**.
3. Click **Add User**, enter the details, and submit.

---

## 🚀 3. Step-by-Step Testing Workflows

### How to Start the App

You can launch both frontend and backend with a single click or command:

```powershell
# From the project root:
.\start-all.bat
```
* **Frontend UI**: [http://localhost:5173](http://localhost:5173) or [http://localhost:8443](http://localhost:8443)
* **Backend API**: [http://localhost:8000](http://localhost:8000)
* **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **AWS Status Check**: [http://localhost:8000/aws/status](http://localhost:8000/aws/status)

---

### Workflow 1: Testing AWS Bedrock (Meta Llama 3 70B Instruct)

1. Open your browser at [http://localhost:5173](http://localhost:5173).
2. Log in with:
   * **Email**: `parth.chavan@cliniq.org`
   * **Password**: `clinical-access`
3. Click on patient **Sunita Jadhav** (`CLQ-10482`) or search for any patient.
4. Click **"Request Analysis"** or **"New Clinical Analysis"**.
5. Input the following realistic clinical presentation:
   * **New Symptoms / Chief Complaint**:
     ```text
     Substernal chest tightness radiating to the left arm and jaw, occurring with mild exertion, relieved within 5 minutes of rest or sublingual nitroglycerin.
     ```
   * **Physical Observations & Vitals**:
     ```text
     BP: 148/92 mmHg, Heart Rate: 86 bpm regular, SpO2: 98% room air. Mild diaphoresis, S4 gallop audible at apex. No peripheral edema.
     ```
   * **Lab / Diagnostic Findings**:
     ```text
     Resting 12-lead ECG demonstrates 1.5mm horizontal ST depression in leads V4-V6. Initial high-sensitivity Troponin-I is normal at 0.02 ng/mL.
     ```
   * **Clinical Notes**:
     ```text
     Patient with known hypertension and hyperlipidemia presenting for urgent cardiovascular risk stratification.
     ```
6. Click **"Run Analysis"** (or **"Submit"**).
7. **What AWS Bedrock Does:**
   * ClinIQ automatically packages the patient's medical history, current medications, existing S3 medical documents, and entered vitals into a structured clinical prompt.
   * Dispatches the call to **AWS Bedrock Converse API** (`meta.llama3-70b-instruct-v1:0` in `ap-south-1`).
   * Generates:
     - **Ranked Differential Diagnoses** (e.g. *Stable Angina Pectoris*, *Acute Coronary Syndrome*) with confidence percentages and pathophysiological summaries.
     - **Guideline-Directed Recommendations** (e.g. serial high-sensitivity Troponin testing, beta-blocker optimization, stress testing).
     - **Drug Interaction Screening** against patient's current medications (e.g. Aspirin, Amlodipine, Atorvastatin).
     - **Patient-Specific Risk Factors**.
8. **Physician Sign-Off**:
   * Review the generated CDS report.
   * Click **"Approve"** (or **"Modify"**) to record your signed decision and update the patient's record.

---

### Workflow 2: Testing AWS S3 (AES256 Encrypted Document Storage)

1. Log in as Doctor (`parth.chavan@cliniq.org`) or Assistant (`jamie.rivera@northlake.org`).
2. Open a patient record (e.g. **Sunita Jadhav** `CLQ-10482` or **Ramesh Bhosale** `CLQ-10479`).
3. Click the **"Documents"** or **"Upload Document"** tab.
4. Select a category:
   * `Lab Report`
   * `Imaging` (X-ray, MRI, Echo)
   * `Clinical Note`
   * `Prescription`
5. Choose any test PDF, PNG, or JPEG file from your computer and click **Upload**.
6. **What AWS S3 Does:**
   * Streams the binary payload to AWS S3 bucket `cliniq-app-storage-2026-unique` in `ap-south-1`.
   * Enforces server-side encryption with **`AES256`**.
   * Associates the uploaded file key with the patient's profile in the database.
7. **Verify Secure Retrieval:**
   * In the documents list, click on the uploaded document.
   * Notice that the URL is a dynamic, temporary **AWS S3 Presigned URL** generated with an **AWS4-HMAC-SHA256 signature** that safely expires without exposing raw storage keys.
8. **Verify Bedrock Integration:**
   * Any newly uploaded document is automatically detected by the Bedrock analysis engine and factored into subsequent CDS differential reports.

---

### Workflow 3: Testing Patient Registration & Appointments (Assistant Role)

1. Log in as Clinical Assistant:
   * **Email**: `jamie.rivera@northlake.org`
   * **Password**: `clinical-access`
2. **Register a New Patient**:
   * Click **"New Patient"** / **"Register"**.
   * Enter Patient Name (e.g. *Ananya Deshmukh*), Date of Birth, Gender, Contact Number, and assigned doctor.
   * Click **Register** &rarr; ClinIQ automatically generates a patient ID (e.g. `CLQ-54321`) and calculates age.
3. **Book an Appointment**:
   * Navigate to **Appointments**.
   * Select a patient and doctor, choose date/time, and select appointment type (Consultation, Follow-up, Routine Checkup).
   * Confirm the appointment.

---

### Workflow 4: Testing the Admin Dashboard

1. Log in as Admin:
   * **Email**: `admin@northlake.org`
   * **Password**: `clinical-access`
2. Review real-time system metrics:
   * Active users count
   * Total registered patients
   * Total CDS analyses generated today
   * Knowledge sources status
3. View the system audit log capturing user logins, document uploads, and clinical decisions.

---

## 🧪 4. Automated Verification Scripts

You have two ready-to-run diagnostic scripts in `backend/`:

### 1. Full 8-Step API & AWS Test Suite
Tests authentication, S3 upload, S3 presigned URL, Bedrock Llama 3 70B inference, CDS decision recording, and S3 cleanup:
```powershell
.\backend\venv\Scripts\python.exe backend\test_api_aws.py
```

### 2. Direct AWS S3 & Bedrock Probe Test
Directly tests AWS connectivity, bucket read/write, and live inference:
```powershell
.\backend\venv\Scripts\python.exe backend\test_aws.py
```
