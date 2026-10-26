-- ClinIQ Database Schema for Supabase/PostgreSQL

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('doctor', 'assistant', 'admin')),
    department VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deactivated')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Patients table
CREATE TABLE patients (
    id VARCHAR(20) PRIMARY KEY, -- e.g., CLQ-10482
    mrn VARCHAR(20) UNIQUE NOT NULL, -- e.g., MRN-883104
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(50) NOT NULL,
    contact_number VARCHAR(20),
    reason_for_visit TEXT,
    medical_history TEXT,
    allergies TEXT,
    current_medications TEXT,
    past_treatments TEXT,
    assigned_doctor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create function to calculate age
CREATE OR REPLACE FUNCTION calculate_age(date_of_birth DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(CURRENT_DATE, date_of_birth))::INTEGER;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create view for patients with computed age
CREATE OR REPLACE VIEW patients_with_age AS
SELECT 
    *,
    calculate_age(date_of_birth) AS age
FROM patients;

-- Appointments table
CREATE TABLE appointments (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    reason VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Visits/Timeline entries
CREATE TABLE visits (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(id) ON DELETE CASCADE,
    visit_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('clinical_note', 'doctor_note', 'lab_result', 'ai_analysis', 'procedure')),
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Clinical Analyses (AI Reports)
CREATE TABLE clinical_analyses (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(id) ON DELETE CASCADE,
    visit_id INTEGER REFERENCES visits(id) ON DELETE SET NULL,
    report_id VARCHAR(50) UNIQUE NOT NULL, -- e.g., CDS-2025-0618
    status VARCHAR(30) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'awaiting_review', 'approved', 'modified', 'rejected')),
    new_symptoms TEXT,
    observations TEXT,
    test_results TEXT,
    clinical_notes TEXT,
    patient_explanation TEXT,
    retrieved_evidence JSONB DEFAULT '[]'::jsonb,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Diagnoses (differential diagnoses for each analysis)
CREATE TABLE diagnoses (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES clinical_analyses(id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    confidence_percentage DECIMAL(5,2) NOT NULL CHECK (confidence_percentage >= 0 AND confidence_percentage <= 100),
    confidence_label VARCHAR(20) NOT NULL CHECK (confidence_label IN ('high', 'needs_review', 'low')),
    summary TEXT NOT NULL,
    evidence JSONB NOT NULL, -- Array of evidence strings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations (next steps for each analysis)
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES clinical_analyses(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Risk Factors lookup table
CREATE TABLE risk_factors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL
);

-- Join table for analysis risk factors (many-to-many)
CREATE TABLE analysis_risk_factors (
    analysis_id INTEGER REFERENCES clinical_analyses(id) ON DELETE CASCADE,
    risk_factor_id INTEGER REFERENCES risk_factors(id) ON DELETE CASCADE,
    PRIMARY KEY (analysis_id, risk_factor_id)
);

-- Drug Interactions/Warnings
CREATE TABLE drug_interactions (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES clinical_analyses(id) ON DELETE CASCADE,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'caution', 'info')),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Clinical Decisions
CREATE TABLE clinical_decisions (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER UNIQUE REFERENCES clinical_analyses(id) ON DELETE CASCADE,
    decision_type VARCHAR(20) NOT NULL CHECK (decision_type IN ('approve', 'modify', 'reject')),
    clinician_notes TEXT,
    attestation_confirmed BOOLEAN NOT NULL DEFAULT true,
    decided_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents/Uploads
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('lab', 'imaging', 'clinical_note', 'prescription', 'external')),
    file_url TEXT NOT NULL, -- Supabase Storage URL
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Knowledge Sources (Admin)
CREATE TABLE knowledge_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL CHECK (type IN ('guideline_library', 'drug_data', 'local_formulary')),
    version VARCHAR(50) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'current' CHECK (status IN ('current', 'update_pending', 'deprecated')),
    last_synchronized TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(50),
    ip_address VARCHAR(50),
    metadata JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_patients_mrn ON patients(mrn);
CREATE INDEX idx_patients_doctor ON patients(assigned_doctor_id);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_time ON appointments(appointment_time);
CREATE INDEX idx_visits_patient ON visits(patient_id);
CREATE INDEX idx_visits_date ON visits(visit_date);
CREATE INDEX idx_analyses_patient ON clinical_analyses(patient_id);
CREATE INDEX idx_analyses_status ON clinical_analyses(status);
CREATE INDEX idx_diagnoses_analysis ON diagnoses(analysis_id);
CREATE INDEX idx_documents_patient ON documents(patient_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_sources_updated_at BEFORE UPDATE ON knowledge_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable pgvector extension for RAG vector search
CREATE EXTENSION IF NOT EXISTS vector;

-- Patient Record Chunks table for patient-centric RAG
CREATE TABLE IF NOT EXISTS patient_record_chunks (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    chunk_id VARCHAR(120) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(100),
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    embedding vector(1024) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_record_chunks_patient ON patient_record_chunks(patient_id);
CREATE INDEX IF NOT EXISTS idx_record_chunks_source ON patient_record_chunks(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_record_chunks_hash ON patient_record_chunks(content_hash);
