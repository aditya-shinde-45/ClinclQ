-- Seed data with Maharashtra/Marathi names
-- Password for all users: "clinical-access" (hashed with bcrypt)

-- Insert Users
INSERT INTO users (email, password_hash, full_name, role, department, status) VALUES
('maya.patel@northlake.org', '$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm', 'Dr. Priya Deshmukh', 'doctor', 'Cardiology', 'active'),
('jamie.rivera@northlake.org', '$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm', 'Aditya Kulkarni', 'assistant', 'Cardiology', 'active'),
('jon.bell@northlake.org', '$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm', 'Dr. Rajesh Joshi', 'doctor', 'Internal Medicine', 'active'),
('admin@northlake.org', '$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm', 'Sneha Patil', 'admin', NULL, 'active'),
('morgan.scott@northlake.org', '$2b$12$eW1Su2FIRyZEVmggEfHBJebLjUOi8qMrjU5BU13ANXXpxMCDuzpsm', 'Kavita Sharma', 'assistant', 'Radiology', 'deactivated');

-- Insert Patients (age will be calculated by the view)
INSERT INTO patients (id, mrn, full_name, date_of_birth, gender, contact_number, reason_for_visit, medical_history, allergies, current_medications, past_treatments, assigned_doctor_id) VALUES
('CLQ-10482', 'MRN-883104', 'Sunita Jadhav', '1967-09-12', 'Female', '+91-9876543210', 'Dyspnea and chest pressure', 'Hypertension; stable coronary artery disease; hyperlipidemia', 'Penicillin — severe urticaria', 'Amlodipine 5 mg; Atorvastatin 40 mg; Aspirin 81 mg', 'Cardiac rehabilitation, completed Aug 2024', 1),
('CLQ-10479', 'MRN-881092', 'Ramesh Bhosale', '1958-03-22', 'Male', '+91-9876543211', 'Post-operative review', 'Type 2 diabetes; previous MI', 'None known', 'Metformin 500mg; Lisinopril 10mg', 'CABG surgery Nov 2024', 1),
('CLQ-10491', 'MRN-883891', 'Manjusha Pawar', '1971-07-08', 'Female', '+91-9876543212', 'Medication follow-up', 'Hypothyroidism; osteoarthritis', 'Sulfa drugs', 'Levothyroxine 75mcg; Ibuprofen as needed', NULL, 3),
('CLQ-10496', 'MRN-884201', 'Anand Kale', '1965-11-15', 'Male', '+91-9876543213', 'Abnormal lab review', 'Chronic kidney disease stage 3', 'None known', 'Losartan 50mg', NULL, 3);

-- Insert Appointments (for today)
INSERT INTO appointments (patient_id, doctor_id, appointment_time, reason, status) VALUES
('CLQ-10479', 1, CURRENT_DATE + INTERVAL '8 hours 30 minutes', 'Post-operative review', 'checked_in'),
('CLQ-10482', 1, CURRENT_DATE + INTERVAL '9 hours 15 minutes', 'Dyspnea and chest pressure', 'in_progress'),
('CLQ-10491', 1, CURRENT_DATE + INTERVAL '10 hours', 'Medication follow-up', 'scheduled'),
('CLQ-10496', 1, CURRENT_DATE + INTERVAL '11 hours 30 minutes', 'Abnormal lab review', 'scheduled');

-- Insert Timeline/Visits for patient CLQ-10482
INSERT INTO visits (patient_id, title, body, type, visit_date, created_by_id) VALUES
('CLQ-10482', 'Current visit opened', 'Persistent dyspnea on exertion and intermittent chest pressure reported.', 'clinical_note', CURRENT_TIMESTAMP, 1),
('CLQ-10482', 'Cardiology follow-up', 'Ejection fraction stable at 52%. Continue current medications.', 'doctor_note', CURRENT_DATE - INTERVAL '35 days', 1),
('CLQ-10482', 'Complete blood count', 'Hemoglobin 11.2 g/dL, mildly below reference range.', 'lab_result', CURRENT_DATE - INTERVAL '138 days', NULL),
('CLQ-10482', 'Clinical analysis approved', 'Recommendation reviewed and approved by Dr. Priya Deshmukh.', 'ai_analysis', CURRENT_DATE - INTERVAL '212 days', 1);

-- Insert Risk Factors
INSERT INTO risk_factors (name) VALUES
('Known coronary artery disease'),
('Hypertension'),
('Hyperlipidemia'),
('Age over 55'),
('Type 2 diabetes'),
('Previous MI'),
('Chronic kidney disease'),
('Smoking history');

-- Insert Knowledge Sources (Admin)
INSERT INTO knowledge_sources (name, type, version, status, last_synchronized) VALUES
('ACC/AHA Clinical Guidelines', 'guideline_library', '2025.06', 'current', CURRENT_TIMESTAMP),
('Northlake Formulary', 'local_formulary', 'v42.8', 'current', CURRENT_TIMESTAMP - INTERVAL '2 hours'),
('DrugBank Clinical', 'drug_data', '2025-Q2', 'current', CURRENT_TIMESTAMP - INTERVAL '2 days'),
('NICE Guidance', 'guideline_library', '2025.05', 'update_pending', CURRENT_DATE - INTERVAL '17 days');

-- Insert a sample Clinical Analysis with mock data
INSERT INTO clinical_analyses (patient_id, report_id, status, new_symptoms, observations, test_results, clinical_notes, generated_at, reviewed_by_id)
VALUES (
    'CLQ-10482',
    'CDS-2025-0618',
    'awaiting_review',
    'Shortness of breath on exertion for 5 days. Intermittent central chest pressure, resolving with rest.',
    'Patient alert and oriented. No acute distress at rest. Mild bilateral ankle edema.',
    'Troponin I, BNP, chest X-ray, repeat echocardiogram',
    'Working diagnosis: possible stable angina vs heart failure exacerbation',
    CURRENT_TIMESTAMP,
    NULL
);

-- Get the analysis ID for inserting related data
DO $$
DECLARE
    analysis_id_var INTEGER;
BEGIN
    SELECT id INTO analysis_id_var FROM clinical_analyses WHERE report_id = 'CDS-2025-0618';
    
    -- Insert Diagnoses
    INSERT INTO diagnoses (analysis_id, rank, name, confidence_percentage, confidence_label, summary, evidence) VALUES
    (analysis_id_var, 1, 'Stable angina', 78.00, 'high', 'Exertional chest pressure resolving with rest is consistent with chronic coronary syndrome.', 
     '["Known coronary artery disease", "Symptoms are exertional and resolve with rest", "Nonspecific ST changes without acute ischemic pattern"]'::jsonb),
    (analysis_id_var, 2, 'Heart failure exacerbation', 64.00, 'needs_review', 'Dyspnea and peripheral edema may indicate early volume overload; BNP and imaging are pending.',
     '["Dyspnea on exertion", "Mild bilateral ankle edema", "Previous ejection fraction 52%"]'::jsonb),
    (analysis_id_var, 3, 'Symptomatic anemia', 41.00, 'needs_review', 'Prior iron-deficiency anemia could contribute to dyspnea; current blood count is not available.',
     '["History of iron-deficiency anemia", "Hemoglobin 11.2 g/dL in February", "Fatigue reported during exertion"]'::jsonb);
    
    -- Insert Recommendations
    INSERT INTO recommendations (analysis_id, step_number, title, description) VALUES
    (analysis_id_var, 1, 'Complete serial high-sensitivity troponin testing', 'Exclude acute myocardial injury before outpatient management.'),
    (analysis_id_var, 2, 'Obtain BNP and chest radiograph', 'Assess possible volume overload given dyspnea and peripheral edema.'),
    (analysis_id_var, 3, 'Continue current aspirin and statin therapy', 'Review antianginal optimization after acute causes are excluded.');
    
    -- Insert Drug Interaction
    INSERT INTO drug_interactions (analysis_id, severity, title, description) VALUES
    (analysis_id_var, 'critical', 'Avoid adding clarithromycin with current atorvastatin 40 mg', 
     'Concurrent use can substantially increase atorvastatin exposure and risk of myopathy. Choose an alternative antibiotic or temporarily withhold atorvastatin under clinician guidance.');
    
    -- Link Risk Factors
    INSERT INTO analysis_risk_factors (analysis_id, risk_factor_id)
    SELECT analysis_id_var, id FROM risk_factors WHERE name IN ('Known coronary artery disease', 'Hypertension', 'Hyperlipidemia', 'Age over 55');
END $$;

-- Insert some audit log entries
INSERT INTO audit_log (user_id, action_type, resource_type, resource_id, timestamp) VALUES
(1, 'login', NULL, NULL, CURRENT_TIMESTAMP - INTERVAL '3 hours'),
(1, 'view_patient', 'patient', 'CLQ-10482', CURRENT_TIMESTAMP - INTERVAL '2 hours 30 minutes'),
(1, 'request_analysis', 'analysis', 'CDS-2025-0618', CURRENT_TIMESTAMP - INTERVAL '15 minutes'),
(2, 'login', NULL, NULL, CURRENT_TIMESTAMP - INTERVAL '4 hours'),
(2, 'upload_document', 'document', '1', CURRENT_TIMESTAMP - INTERVAL '3 hours 30 minutes');
