import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.config import settings
from core.database import get_db, local_db
from services.embedding_service import embedding_service
from services.s3_service import s3_service

logger = logging.getLogger(__name__)


def resolve_chunk_db(db):
    """Checks if patient_record_chunks is available in remote db; if not migrated, falls back to local_db."""
    try:
        db.table("patient_record_chunks").select("id").limit(1).execute()
        return db
    except Exception as e:
        if "PGRST205" in str(e) or "schema cache" in str(e).lower():
            logger.info("Supabase patient_record_chunks table not yet migrated; using local_db.")
            return local_db
        return db


def compute_sha256(text: str) -> str:
    """Compute deterministic SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Splits text into chunks by sentences/words respecting chunk_size and chunk_overlap.
    Defaults to settings.RAG_CHUNK_SIZE (500 chars) and settings.RAG_CHUNK_OVERLAP (50 chars).
    """
    if not text or not text.strip():
        return []

    size = chunk_size or settings.RAG_CHUNK_SIZE
    overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

    cleaned = " ".join(text.split())
    if len(cleaned) <= size:
        return [cleaned]

    chunks = []
    start = 0
    while start < len(cleaned):
        end = start + size
        if end >= len(cleaned):
            chunk = cleaned[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Attempt to split cleanly on punctuation or space
        split_pos = -1
        for sep in [". ", "? ", "! ", "; ", ", ", " "]:
            p = cleaned.rfind(sep, start, end)
            if p > start:
                split_pos = p + len(sep)
                break

        if split_pos == -1 or split_pos <= start:
            split_pos = end

        chunk = cleaned[start:split_pos].strip()
        if chunk:
            chunks.append(chunk)

        start = split_pos - overlap
        if start < 0 or start >= len(cleaned):
            break

    return chunks


class RagIngestionService:
    """
    Manages indexing of patient clinical records, longitudinal visits,
    and attached medical documents into the vector store.
    """

    def __init__(self):
        self.chunk_size = settings.RAG_CHUNK_SIZE
        self.chunk_overlap = settings.RAG_CHUNK_OVERLAP

    def index_patient(self, patient_id: str, force_reindex: bool = False, db=None) -> Dict[str, Any]:
        """
        Indexes all eligible knowledge sources for a single patient into patient_record_chunks.
        Idempotent: uses SHA-256 content hashes to avoid redundant embedding calls.
        """
        db = db or get_db()
        logger.info(f"Starting RAG indexing for patient {patient_id}")

        # 1. Fetch Patient Record
        p_res = db.table("patients").select("*").eq("id", patient_id).execute()
        if not p_res.data:
            return {
                "patient_id": patient_id,
                "status": "not_found",
                "chunks_created": 0,
                "chunks_updated": 0,
                "chunks_unchanged": 0,
                "chunks_deleted": 0,
                "total_chunks": 0,
                "error": "Patient does not exist"
            }

        patient = p_res.data[0]
        chunks_to_upsert = []
        active_chunk_ids = set()

        created_count = 0
        updated_count = 0
        unchanged_count = 0

        # Query existing chunks for this patient using resolved chunk database
        chunk_db = resolve_chunk_db(db)
        existing_res = chunk_db.table("patient_record_chunks").select("chunk_id, content_hash").eq("patient_id", patient_id).execute()
        existing_chunks = {r["chunk_id"]: r["content_hash"] for r in (existing_res.data or [])}

        # -------------------------------------------------------------
        # SOURCE 1: Patient Chart Profile
        # -------------------------------------------------------------
        profile_parts = [
            f"Patient ID: {patient.get('id')} (MRN: {patient.get('mrn', 'Unknown')})",
            f"Demographics: Gender {patient.get('gender')}, Date of Birth {patient.get('date_of_birth')}",
            f"Reason for Visit: {patient.get('reason_for_visit') or 'Not reported'}",
            f"Known Medical History: {patient.get('medical_history') or 'None reported'}",
            f"Allergies: {patient.get('allergies') or 'No known drug allergies'}",
            f"Current Medications: {patient.get('current_medications') or 'None reported'}",
            f"Past Treatments / Surgeries: {patient.get('past_treatments') or 'None reported'}",
        ]
        profile_text = " | ".join(profile_parts)
        profile_chunks = chunk_text(profile_text, self.chunk_size, self.chunk_overlap)

        for idx, text in enumerate(profile_chunks):
            chunk_id = f"chunk_{patient_id}_profile_{idx}"
            active_chunk_ids.add(chunk_id)
            c_hash = compute_sha256(text)

            if not force_reindex and existing_chunks.get(chunk_id) == c_hash:
                unchanged_count += 1
                continue

            emb = embedding_service.get_embedding(text)
            chunks_to_upsert.append({
                "patient_id": patient_id,
                "chunk_id": chunk_id,
                "source_type": "patient_profile",
                "source_id": patient_id,
                "content": text,
                "content_hash": c_hash,
                "embedding": emb,
                "metadata": {
                    "source_title": "Patient Demographics & Clinical Profile",
                    "category": "chart_summary",
                    "patient_id": patient_id,
                }
            })
            if chunk_id in existing_chunks:
                updated_count += 1
            else:
                created_count += 1

        # -------------------------------------------------------------
        # SOURCE 2: Patient Visits & Hospital Encounters
        # -------------------------------------------------------------
        v_res = db.table("visits").select("*").eq("patient_id", patient_id).execute()
        visits = v_res.data or []

        for v in visits:
            v_id = str(v.get("id"))
            v_type = v.get("type", "clinical_note")
            v_title = v.get("title", "Clinical Encounter")
            v_date = v.get("visit_date", "")
            v_body = v.get("body", "")

            combined_v_text = f"Encounter Date: {v_date} | Type: {v_type} | Title: {v_title}\nClinical Details: {v_body}"
            v_chunks = chunk_text(combined_v_text, self.chunk_size, self.chunk_overlap)

            for idx, text in enumerate(v_chunks):
                chunk_id = f"chunk_{patient_id}_visit_{v_id}_{idx}"
                active_chunk_ids.add(chunk_id)
                c_hash = compute_sha256(text)

                if not force_reindex and existing_chunks.get(chunk_id) == c_hash:
                    unchanged_count += 1
                    continue

                emb = embedding_service.get_embedding(text)
                chunks_to_upsert.append({
                    "patient_id": patient_id,
                    "chunk_id": chunk_id,
                    "source_type": "visit_timeline" if "Hospital Inpatient" not in v_body else "hospital_encounter",
                    "source_id": v_id,
                    "content": text,
                    "content_hash": c_hash,
                    "embedding": emb,
                    "metadata": {
                        "source_title": v_title,
                        "encounter_type": v_type,
                        "visit_date": v_date,
                        "patient_id": patient_id
                    }
                })
                if chunk_id in existing_chunks:
                    updated_count += 1
                else:
                    created_count += 1

        # -------------------------------------------------------------
        # SOURCE 3: Uploaded Medical Documents (S3 / PDF Text)
        # -------------------------------------------------------------
        d_res = db.table("documents").select("*").eq("patient_id", patient_id).execute()
        documents = d_res.data or []

        for doc in documents:
            doc_id = str(doc.get("id"))
            filename = doc.get("filename", "medical_document")
            category = doc.get("category", "lab")
            file_url = doc.get("file_url", "")

            doc_text = self._extract_document_text(doc)
            if not doc_text:
                continue

            doc_content = f"Medical Document: {filename} (Category: {category})\nContent: {doc_text}"
            d_chunks = chunk_text(doc_content, self.chunk_size, self.chunk_overlap)

            for idx, text in enumerate(d_chunks):
                chunk_id = f"chunk_{patient_id}_doc_{doc_id}_{idx}"
                active_chunk_ids.add(chunk_id)
                c_hash = compute_sha256(text)

                if not force_reindex and existing_chunks.get(chunk_id) == c_hash:
                    unchanged_count += 1
                    continue

                emb = embedding_service.get_embedding(text)
                chunks_to_upsert.append({
                    "patient_id": patient_id,
                    "chunk_id": chunk_id,
                    "source_type": "document",
                    "source_id": doc_id,
                    "content": text,
                    "content_hash": c_hash,
                    "embedding": emb,
                    "metadata": {
                        "filename": filename,
                        "category": category,
                        "patient_id": patient_id
                    }
                })
                if chunk_id in existing_chunks:
                    updated_count += 1
                else:
                    created_count += 1

        # -------------------------------------------------------------
        # Persist Upserts
        # -------------------------------------------------------------
        if chunks_to_upsert:
            try:
                # Use upsert with chunk_id as conflict target
                chunk_db.table("patient_record_chunks").upsert(chunks_to_upsert, on_conflict="chunk_id").execute()
                logger.info(f"Upserted {len(chunks_to_upsert)} chunks for patient {patient_id}")
            except Exception as e:
                logger.error(f"Failed to upsert chunks for patient {patient_id}: {e}")
                # Fallback to individual inserts if batch upsert fails
                for c in chunks_to_upsert:
                    try:
                        chunk_db.table("patient_record_chunks").upsert(c, on_conflict="chunk_id").execute()
                    except Exception as ie:
                        logger.warning(f"Single chunk upsert failed ({c['chunk_id']}): {ie}")

        # -------------------------------------------------------------
        # Obsolete Chunks Cleanup
        # -------------------------------------------------------------
        deleted_count = 0
        obsolete_ids = [cid for cid in existing_chunks.keys() if cid not in active_chunk_ids]
        for obsolete_id in obsolete_ids:
            try:
                chunk_db.table("patient_record_chunks").delete().eq("chunk_id", obsolete_id).execute()
                deleted_count += 1
            except Exception as de:
                logger.warning(f"Failed to delete obsolete chunk {obsolete_id}: {de}")

        total_chunks = len(active_chunk_ids)
        return {
            "patient_id": patient_id,
            "status": "success",
            "chunks_created": created_count,
            "chunks_updated": updated_count,
            "chunks_unchanged": unchanged_count,
            "chunks_deleted": deleted_count,
            "total_chunks": total_chunks
        }

    def index_all_patients(self, limit: int = None, force_reindex: bool = False, db=None) -> Dict[str, Any]:
        """Indexes all registered patients in the database."""
        db = db or get_db()
        query = db.table("patients").select("id").order("created_at", desc=False)
        if limit:
            query = query.limit(limit)

        patients = query.execute().data or []
        details = []
        total_chunks = 0

        for p in patients:
            pid = p["id"]
            res = self.index_patient(pid, force_reindex=force_reindex, db=db)
            details.append(res)
            total_chunks += res.get("total_chunks", 0)

        return {
            "success": True,
            "indexed_patients": len(details),
            "total_chunks_indexed": total_chunks,
            "details": details
        }

    def _extract_document_text(self, document: dict) -> str:
        """Download from S3 and extract readable text from PDF / text documents."""
        file_url = document.get("file_url", "")
        filename = document.get("filename", "")
        if "patients/" not in file_url:
            return ""

        s3_key = "patients/" + file_url.split("patients/", 1)[1].split("?", 1)[0]
        try:
            content = s3_service.download_file(s3_key)
            ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
            if ext == "pdf":
                from pypdf import PdfReader
                import io
                reader = PdfReader(io.BytesIO(content))
                pages = [p.extract_text() or "" for p in reader.pages]
                return " ".join(" ".join(pages).split())
            elif ext in {"txt", "csv", "json"}:
                return content.decode("utf-8", errors="replace").strip()
            else:
                return ""
        except Exception as e:
            logger.warning(f"Could not extract text from document {filename} ({s3_key}): {e}")
            return ""


rag_ingestion_service = RagIngestionService()
