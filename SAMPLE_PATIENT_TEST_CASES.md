# ClinIQ — Verified Sample Patient Test Cases (Dataset-Grounded)

This document contains **5 ready-to-use, verified clinical test scenarios** matching records actively indexed in ClinIQ's Supabase database and vector store. 

Using these test cases guarantees:
1. **High-Confidence RAG Grounding**: The AI will retrieve and explicitly cite real patient historical chunks (e.g. `[EVIDENCE ITEM #1]`).
2. **Realistic Differential Diagnoses**: Produced by **AWS Bedrock Meta Llama 3 70B** with guideline-directed rationale.
3. **Active Drug Interaction Checks**: Accurate screening against the patient's existing medication list.

---

## 📌 Test Case 1: Exertional Angina in Established CAD
* **Patient Name:** **Sunita Jadhav**
* **Patient ID:** `CLQ-10482` (MRN: `MRN-883104`)
* **Demographics:** 59-year-old Female
* **Known Chart History:** Hypertension; stable coronary artery disease; hyperlipidemia; prior cardiac rehab (Aug 2024).
* **Documented Allergies:** `Penicillin — severe urticaria`
* **Active Medications:** `Amlodipine 5 mg, Atorvastatin 40 mg, Aspirin 81 mg`

### Form Input Data (Copy & Paste):

#### 1. Symptoms & Observations
* **New symptoms**:
  ```text
  Substernal chest tightness radiating to the left arm and jaw, occurring with mild exertion (walking uphill), lasting 5-10 minutes, accompanied by exertional dyspnea. Relieved with rest.
  ```
* **Current observations**:
  ```text
  BP: 148/92 mmHg, HR: 86 bpm regular, SpO2: 98% room air, RR: 18/min. Mild diaphoresis, S4 gallop audible at cardiac apex. No peripheral edema or JVD.
  ```

#### 2. Clinical Findings
* **Current diagnosis or impression**:
  ```text
  Suspected Stable Angina Pectoris vs. Acute Coronary Syndrome (ACS); Rule out unstable angina in high-risk cardiovascular profile.
  ```
* **New test results**:
  ```text
  12-Lead ECG: 1.5 mm horizontal ST-segment depression in leads V4–V6. High-sensitivity Troponin-I: 0.02 ng/mL (normal). Lipid Panel: Total Cholesterol 210 mg/dL, LDL 132 mg/dL.
  ```
* **New allergies**:
  ```text
  None reported
  ```
* **Tests to perform**:
  ```text
  Serial high-sensitivity Troponin-I at 3h and 6h, Transthoracic Echocardiogram (TTE), outpatient Coronary CT Angiography / stress test.
  ```

#### 3. Visit Notes
* **Additional clinical notes**:
  ```text
  Current medications: Amlodipine 5 mg; Atorvastatin 40 mg; Aspirin 81 mg
  Past treatments: Cardiac rehabilitation, completed Aug 2024
  Known allergies: Penicillin — severe urticaria

  Clinical Context: 59-year-old female presenting with 2-week progression of exertional angina. Compliant with statin and antihypertensive therapy. Evaluate anti-anginal escalation and urgent risk stratification.
  ```

### Expected AI & RAG Outcomes:
* **Rank 1 Differential**: *Stable Angina Pectoris* (High Confidence: 80%–85%).
* **Rank 2 Differential**: *Acute Coronary Syndrome (ACS)* (Needs Review: 40%–50% due to horizontal ST depressions).
* **RAG Evidence Citing**: Cites patient profile chunk `chunk_CLQ-10482_profile_0`, previous clinic visits, and baseline ejection fraction ($52\%$).
* **Drug Interaction Check**: Evaluates Aspirin/Amlodipine synergy; flags CYP3A4 inhibitors with Atorvastatin.
* **Guideline Steps**: Serial high-sensitivity troponins per AHA/ACC protocol; cardiology referral.

---

## 📌 Test Case 2: Post-Infarction Diabetic with Dyspnea & Contrast Safety
* **Patient Name:** **Ramesh Bhosale**
* **Patient ID:** `CLQ-10479` (MRN: `MRN-928410`)
* **Demographics:** 68-year-old Male
* **Known Chart History:** Type 2 Diabetes Mellitus; previous Myocardial Infarction (MI).
* **Documented Allergies:** `No known drug allergies`
* **Active Medications:** `Metformin 500 mg BID, Lisinopril 10 mg daily`

### Form Input Data (Copy & Paste):

#### 1. Symptoms & Observations
* **New symptoms**:
  ```text
  Gradual onset of exertional shortness of breath when climbing 1 flight of stairs, 2-pillow orthopnea over the past 4 days, mild dry cough when recumbent. Denies acute squeezing chest pain.
  ```
* **Current observations**:
  ```text
  BP: 136/82 mmHg, HR: 74 bpm, SpO2: 96% room air. Bilateral trace pretibial pitting edema (1+). Bibasilar fine inspiratory crackles on auscultation.
  ```

#### 2. Clinical Findings
* **Current diagnosis or impression**:
  ```text
  Early Heart Failure with preserved/reduced Ejection Fraction (HFpEF/HFrEF) secondary to ischemic cardiomyopathy; rule out silent ischemia.
  ```
* **New test results**:
  ```text
  Serum Creatinine: 1.4 mg/dL (eGFR 52 mL/min/1.73m²). HbA1c: 7.8%. Point-of-care capillary glucose: 154 mg/dL. Resting ECG: Old Q-waves in inferior leads (II, III, aVF) consistent with prior MI.
  ```
* **New allergies**:
  ```text
  None reported
  ```
* **Tests to perform**:
  ```text
  Serum NT-proBNP level, 2-view Chest Radiograph (CXR), Comprehensive Echocardiogram with Doppler, spot urine albumin-to-creatinine ratio.
  ```

#### 3. Visit Notes
* **Additional clinical notes**:
  ```text
  Current medications: Metformin 500 mg; Lisinopril 10 mg
  Known allergies: None reported

  Clinical Context: Patient with prior MI and type 2 diabetes presenting with insidious volume overload and functional decline. Note that if contrast cardiac CT/angiography is ordered, Metformin must be safely held.
  ```

### Expected AI & RAG Outcomes:
* **Rank 1 Differential**: *Heart Failure Exacerbation / Ischemic Cardiomyopathy* (High Confidence: 75%–82%).
* **Rank 2 Differential**: *Silent Myocardial Ischemia / Diabetic Angina Equivalent* (Needs Review: 45%–55%).
* **RAG Evidence Citing**: Cites previous MI encounter chunk and diabetic baseline.
* **Critical Drug Safety Warning**: Flags **Metformin hold requirement** before any iodinated radiocontrast procedures to prevent contrast-induced nephropathy and lactic acidosis.
* **Guideline Steps**: NT-proBNP confirmation, loop diuretic titration, guideline-directed medical therapy (GDMT) optimization.

---

## 📌 Test Case 3: Inpatient Angioplasty Recurrent Exertional Symptoms
* **Patient Name:** **Demo Patient #1** (Kaggle Dataset Record #1)
* **Patient ID:** `CLQ-HOSP-0001` (MRN: `MRN-HOSP-0001`)
* **Demographics:** 45-year-old Female
* **Known Chart History:** Diagnosed with Heart Disease; underwent Inpatient Angioplasty with 5-day hospital admission ($15,000 care cost, outcome: Recovered, 30-day readmission: No).
* **Documented Allergies:** `No known allergies documented`
* **Active Medications:** `None documented in demo baseline`

### Form Input Data (Copy & Paste):

#### 1. Symptoms & Observations
* **New symptoms**:
  ```text
  Recurrent episodes of mid-sternal chest tightness when jogging or carrying groceries, resolving completely within 4 minutes of rest. Similar to symptoms prior to angioplasty.
  ```
* **Current observations**:
  ```text
  BP: 132/84 mmHg, HR: 76 bpm regular, SpO2: 99% room air. Cardiac auscultation demonstrates normal S1/S2, soft S4 gallop audible. Lungs clear to auscultation bilaterally.
  ```

#### 2. Clinical Findings
* **Current diagnosis or impression**:
  ```text
  Post-percutaneous coronary intervention (PCI) exertional angina; Evaluate for in-stent restenosis vs. progressive de novo coronary disease.
  ```
* **New test results**:
  ```text
  Resting 12-lead ECG demonstrates non-specific T-wave flattening in lateral leads without acute ST elevation. Initial troponin is non-elevated.
  ```
* **New allergies**:
  ```text
  None reported
  ```
* **Tests to perform**:
  ```text
  Exercise Stress Echocardiogram or Nuclear Myocardial Perfusion Imaging (MPI), Fasting Lipid Panel, Repeat high-sensitivity Troponin in 3 hours.
  ```

#### 3. Visit Notes
* **Additional clinical notes**:
  ```text
  Patient underwent inpatient angioplasty for heart disease during prior hospital stay. Seeking AI clinical decision support on post-revascularization ischemia risk and antiplatelet verification.
  ```

### Expected AI & RAG Outcomes:
* **Rank 1 Differential**: *Stable Angina Pectoris / Coronary Artery Disease* (High Confidence: 80%–85%).
* **Rank 2 Differential**: *In-Stent Restenosis (ISR)* (Needs Review: 50%–60%).
* **RAG Evidence Citing**: Explicitly cites `chunk_CLQ-HOSP-0001_profile_0` and hospital encounter `chunk_CLQ-HOSP-0001_visit_5_0` referencing the **Angioplasty inpatient procedure**.
* **Recommendations**: Non-invasive functional ischemic testing, dual antiplatelet therapy (DAPT) compliance audit, high-intensity statin initiation.

---

## 📌 Test Case 4: High-Risk Recurrent Stroke & TIA Warning
* **Patient Name:** **Demo Patient #4** (Kaggle Dataset Record #4)
* **Patient ID:** `CLQ-HOSP-0004` (MRN: `MRN-HOSP-0004`)
* **Demographics:** 75-year-old Male (DOB: `1951-01-01`)
* **Known Chart History:** Previous hospital admission for Stroke with Inpatient CT Scan and Medication (7-day hospital stay, $10,000 care cost, **30-Day Readmission: YES**).
* **Documented Allergies:** `No known allergies documented`
* **Active Medications:** `None documented in demo baseline`

### Form Input Data (Copy & Paste):

#### 1. Symptoms & Observations
* **New symptoms**:
  ```text
  Sudden-onset transient weakness in the right hand and mild slurring of speech lasting approximately 25 minutes, followed by complete spontaneous resolution. No loss of consciousness or seizures.
  ```
* **Current observations**:
  ```text
  BP: 164/98 mmHg, HR: 88 bpm irregular (suggesting atrial fibrillation), SpO2: 97% room air. Current NIHSS score: 0 (symptoms resolved). Mild right facial asymmetry on maximum smile.
  ```

#### 2. Clinical Findings
* **Current diagnosis or impression**:
  ```text
  Transient Ischemic Attack (TIA) in high-risk patient with prior stroke and 30-day readmission history; Rule out secondary recurrent cerebral infarction.
  ```
* **New test results**:
  ```text
  Urgent Non-Contrast Head CT: No acute intracranial hemorrhage or large-vessel territory demarcation. Chronic lacunar infarcts identified. 12-lead ECG demonstrates Atrial Fibrillation with rapid ventricular response.
  ```
* **New allergies**:
  ```text
  None reported
  ```
* **Tests to perform**:
  ```text
  Brain MRI with Diffusion-Weighted Imaging (DWI), Carotid Duplex Ultrasound, Transthoracic Echocardiogram (TTE) with bubble study, Coagulation Panel (PT/INR, PTT).
  ```

#### 3. Visit Notes
* **Additional clinical notes**:
  ```text
  Patient has documented prior inpatient stroke admission with readmission flag in hospital record. High ABCD2 risk score. Needs urgent evaluation for secondary stroke prevention and oral anticoagulation.
  ```

### Expected AI & RAG Outcomes:
* **Rank 1 Differential**: *Transient Ischemic Attack (TIA) / Acute Ischemic Stroke* (High Confidence: 82%–88%).
* **Rank 2 Differential**: *Cardioembolic Cerebrovascular Event secondary to Atrial Fibrillation* (High Confidence: 75%–80%).
* **RAG Evidence Citing**: Cites `chunk_CLQ-HOSP-0004_visit_4_0` detailing previous stroke hospital admission and **30-day readmission status**.
* **Safety & Recommendations**: Emergency inpatient admission/observation, urgent MRI DWI, calculate CHA2DS2-VASc score, initiate anticoagulation (DOAC) once hemorrhage ruled out.

---

## 📌 Test Case 5: NSAID Nephrotoxicity & Sulfa Allergy Alert
* **Patient Name:** **Manjusha Pawar**
* **Patient ID:** `CLQ-10491` (MRN: `MRN-783214`)
* **Demographics:** 55-year-old Female
* **Known Chart History:** Hypothyroidism; severe Osteoarthritis of bilateral knees.
* **Documented Allergies:** `Sulfa drugs` (documented cutaneous rash & angioedema)
* **Active Medications:** `Levothyroxine 75 mcg daily, Ibuprofen 600 mg TID PRN`

### Form Input Data (Copy & Paste):

#### 1. Symptoms & Observations
* **New symptoms**:
  ```text
  Epigastric burning discomfort exacerbated after meals and increased NSAID usage over the past 3 weeks for knee pain flare, accompanied by dark tarry stools (melena) for 2 days. Mild fatigue and lightheadedness on standing.
  ```
* **Current observations**:
  ```text
  BP: 108/68 mmHg supine, 94/60 mmHg standing (orthostatic drop), HR: 98 bpm regular. Conjunctival pallor noted. Epigastric tenderness on deep palpation without rebound or guarding.
  ```

#### 2. Clinical Findings
* **Current diagnosis or impression**:
  ```text
  Upper Gastrointestinal Bleeding secondary to NSAID-induced peptic ulcer disease; Symptomatic acute blood-loss anemia.
  ```
* **New test results**:
  ```text
  Hemoglobin: 8.9 g/dL (baseline 12.8 g/dL). Fecal Occult Blood Test (FOBT): Positive. BUN: 34 mg/dL, Serum Creatinine: 1.3 mg/dL (BUN:Cr ratio > 20:1, consistent with upper GI bleed).
  ```
* **New allergies**:
  ```text
  None reported
  ```
* **Tests to perform**:
  ```text
  Urgent Esophagogastroduodenoscopy (EGD), Type and Screen with cross-match for 2 units packed RBCs, Serial Complete Blood Count (CBC) every 6 hours.
  ```

#### 3. Visit Notes
* **Additional clinical notes**:
  ```text
  Current medications: Levothyroxine 75 mcg; Ibuprofen 600 mg TID PRN
  Known allergies: Sulfa drugs (severe rash)

  Clinical Context: Patient taking chronic high-dose Ibuprofen for osteoarthritis presenting with acute GI bleeding and orthostasis. Verify that any antimicrobial, diuretic, or analgesic therapies avoid Sulfa compounds.
  ```

### Expected AI & RAG Outcomes:
* **Rank 1 Differential**: *NSAID-Induced Peptic Ulcer Disease with Upper GI Hemorrhage* (High Confidence: 85%–90%).
* **Rank 2 Differential**: *Acute Normocytic Blood-Loss Anemia* (High Confidence: 80%–84%).
* **RAG Evidence Citing**: Cites patient medical history (`Osteoarthritis`) and chronic NSAID usage.
* **Critical Drug Safety Warning**:
  - Immediately **discontinue Ibuprofen (NSAID)**.
  - **Sulfa Allergy Warning**: Flags and blocks cross-reactive drugs (e.g., Celecoxib contains a sulfonamide moiety; loops/thiazides with sulfa cross-reactivity).
* **Guideline Steps**: Intravenous Proton Pump Inhibitor (Pantoprazole infusion), emergent endoscopy within 24 hours, volume resuscitation.

---

## 🧭 Quick Summary of Test Cases & Purpose

| Test Case | Patient ID | Clinical Domain | Key Feature Tested |
| :--- | :--- | :--- | :--- |
| **Case 1: Sunita Jadhav** | `CLQ-10482` | Cardiology | Baseline ECG comparison, CAD history RAG chunk retrieval, Penicillin allergy safety. |
| **Case 2: Ramesh Bhosale** | `CLQ-10479` | Cardio-Metabolic | Prior MI evidence retrieval, CHF differential, **Metformin contrast warning**. |
| **Case 3: Demo Patient #1** | `CLQ-HOSP-0001` | Post-Revascularization | Cites Kaggle hospital dataset #1 **Angioplasty inpatient record**, in-stent restenosis check. |
| **Case 4: Demo Patient #4** | `CLQ-HOSP-0004` | Neurology / Cerebrovascular | Cites Kaggle hospital dataset #4 **Stroke 30-day readmission**, Atrial Fibrillation cardioembolic risk. |
| **Case 5: Manjusha Pawar** | `CLQ-10491` | Gastroenterology / Safety | NSAID peptic ulceration, acute blood loss, **Sulfa drug allergy screening (Celecoxib block)**. |
