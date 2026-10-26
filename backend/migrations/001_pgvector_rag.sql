-- Migration: 001_pgvector_rag.sql
-- Description: Patient-centric RAG vector storage using pgvector in Supabase / PostgreSQL

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Patient Record Chunks table
CREATE TABLE IF NOT EXISTS patient_record_chunks (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    chunk_id VARCHAR(120) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'patient_profile', 'visit_timeline', 'hospital_encounter', 'document'
    source_id VARCHAR(100),           -- ID of the source record (e.g. visit_id, doc_id)
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL, -- SHA-256 for incremental indexing & deduplication
    embedding vector(1024) NOT NULL,  -- Amazon Titan Text Embeddings v2 (1024 dimensions)
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Indexes for rapid patient-scoped search and vector cosine similarity
CREATE INDEX IF NOT EXISTS idx_record_chunks_patient ON patient_record_chunks(patient_id);
CREATE INDEX IF NOT EXISTS idx_record_chunks_source ON patient_record_chunks(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_record_chunks_hash ON patient_record_chunks(content_hash);

-- Create HNSW or IVFFlat index for vector cosine distance
CREATE INDEX IF NOT EXISTS idx_record_chunks_embedding 
ON patient_record_chunks 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 4. Stored Function for Patient-Scoped Vector Retrieval
CREATE OR REPLACE FUNCTION match_patient_record_chunks(
    query_embedding vector(1024),
    target_patient_id VARCHAR(20),
    match_threshold FLOAT DEFAULT 0.15,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id INT,
    chunk_id VARCHAR(120),
    patient_id VARCHAR(20),
    source_type VARCHAR(50),
    source_id VARCHAR(100),
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.chunk_id,
        c.patient_id,
        c.source_type,
        c.source_id,
        c.content,
        c.metadata,
        (1 - (c.embedding <=> query_embedding))::FLOAT AS similarity
    FROM patient_record_chunks c
    WHERE c.patient_id = target_patient_id
      AND (1 - (c.embedding <=> query_embedding)) >= match_threshold
    ORDER BY c.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;

-- 5. Extend clinical_analyses table for AI explanations and retrieved RAG evidence
ALTER TABLE clinical_analyses ADD COLUMN IF NOT EXISTS patient_explanation TEXT;
ALTER TABLE clinical_analyses ADD COLUMN IF NOT EXISTS retrieved_evidence JSONB DEFAULT '[]'::jsonb;

