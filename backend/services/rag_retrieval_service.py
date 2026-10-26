import logging
from typing import List, Dict, Any, Optional
from core.config import settings
from core.database import get_db, local_db
from models.schemas import RetrievedEvidenceItem
from services.embedding_service import embedding_service

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


class RagRetrievalService:
    """
    Patient-Centric RAG Retrieval Service.
    Enforces strict patient-level boundary filtering so that queries
    can ONLY retrieve clinical chunks belonging to the targeted patient.
    """

    def __init__(self):
        self.default_top_k = settings.RAG_TOP_K
        self.min_similarity = settings.RAG_MIN_SIMILARITY

    def retrieve_patient_evidence(
        self,
        patient_id: str,
        query_text: str,
        current_user: Optional[Dict[str, Any]] = None,
        top_k: int = None,
        min_similarity: float = None,
        db=None
    ) -> List[RetrievedEvidenceItem]:
        """
        Executes a patient-scoped vector similarity search.
        Guarantees that results are strictly restricted to the specified patient_id.
        """
        if not patient_id or not query_text or not query_text.strip():
            return []

        # Role-based authorization check
        if current_user:
            role = current_user.get("role")
            if role not in ("doctor", "assistant", "admin"):
                logger.warning(f"Unauthorized RAG retrieval attempt by user {current_user.get('id')} with role {role}")
                return []

        db = db or get_db()
        chunk_db = resolve_chunk_db(db)
        k = top_k or self.default_top_k
        threshold = min_similarity if min_similarity is not None else self.min_similarity

        # 1. Generate Query Vector via Amazon Titan Embeddings v2
        query_vector = embedding_service.get_embedding(query_text)
        if not query_vector:
            logger.warning("Empty query vector generated; returning empty retrieval result.")
            return []

        results = []

        # 2. Vector Search Execution
        # Strategy A: Use match_patient_record_chunks stored function (works in Supabase pgvector & LocalDatabase)
        try:
            rpc_res = chunk_db.rpc(
                "match_patient_record_chunks",
                {
                    "query_embedding": query_vector,
                    "target_patient_id": patient_id,
                    "match_threshold": threshold,
                    "match_count": k
                }
            ).execute()

            if rpc_res.data:
                for row in rpc_res.data:
                    # STRICT SAFETY CHECK: Verify patient_id match
                    if str(row.get("patient_id")) != str(patient_id):
                        logger.error(
                            f"SECURITY ALERT: Chunk {row.get('chunk_id')} for patient {row.get('patient_id')} leaked in query for {patient_id}!"
                        )
                        continue

                    results.append(RetrievedEvidenceItem(
                        chunk_id=str(row["chunk_id"]),
                        source_type=str(row.get("source_type", "record")),
                        source_id=str(row.get("source_id", "")),
                        content=str(row.get("content", "")),
                        similarity=float(row.get("similarity", 0.0)),
                        metadata=row.get("metadata") or {}
                    ))
                logger.info(f"Retrieved {len(results)} chunks for patient {patient_id} via RPC")
                return results

        except Exception as rpc_err:
            logger.info(f"RPC match_patient_record_chunks fallback to direct table query: {rpc_err}")

        # Strategy B: Direct Table Filtering + in-memory cosine similarity
        try:
            chunks_res = chunk_db.table("patient_record_chunks").select("*").eq("patient_id", patient_id).execute()
            rows = chunks_res.data or []
            if not rows:
                return []

            import numpy as np
            q_vec = np.array(query_vector, dtype=np.float32)
            q_norm = float(np.linalg.norm(q_vec))
            if q_norm == 0:
                return []

            scored = []
            for r in rows:
                if str(r.get("patient_id")) != str(patient_id):
                    continue
                emb = r.get("embedding", [])
                if not emb or len(emb) != len(query_vector):
                    continue

                c_vec = np.array(emb, dtype=np.float32)
                c_norm = float(np.linalg.norm(c_vec))
                if c_norm > 0:
                    sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                else:
                    sim = 0.0

                if sim >= threshold:
                    scored.append((sim, r))

            scored.sort(key=lambda x: x[0], reverse=True)
            for sim, r in scored[:k]:
                results.append(RetrievedEvidenceItem(
                    chunk_id=str(r["chunk_id"]),
                    source_type=str(r.get("source_type", "record")),
                    source_id=str(r.get("source_id", "")),
                    content=str(r.get("content", "")),
                    similarity=round(sim, 4),
                    metadata=r.get("metadata") or {}
                ))

            logger.info(f"Retrieved {len(results)} chunks for patient {patient_id} via table scoring")
            return results

        except Exception as table_err:
            logger.error(f"Failed direct retrieval for patient {patient_id}: {table_err}")
            return []

    def format_retrieved_evidence_for_prompt(self, evidence_list: List[RetrievedEvidenceItem]) -> str:
        """
        Formats retrieved patient chunks into a clean, citeable context block
        for the Amazon Bedrock clinical guidelines prompt.
        """
        if not evidence_list:
            return "No historical evidence retrieved from patient records."

        blocks = []
        for i, item in enumerate(evidence_list, 1):
            source_label = item.source_type.replace("_", " ").title()
            source_id = f" (Ref: {item.source_id})" if item.source_id else ""
            sim_pct = int(item.similarity * 100)
            meta_desc = ""
            if item.metadata and item.metadata.get("source_title"):
                meta_desc = f" — {item.metadata['source_title']}"

            blocks.append(
                f"[EVIDENCE ITEM #{i}] [{source_label}{source_id}{meta_desc} | Relevance: {sim_pct}%]\n"
                f"{item.content}"
            )

        return "\n\n".join(blocks)


rag_retrieval_service = RagRetrievalService()
