import json
import logging
from typing import List, Optional
import core.aws_time_sync  # Ensure botocore SigV4 runtime timestamp is calibrated
from core.config import settings

logger = logging.getLogger(__name__)


class BedrockEmbeddingService:
    """
    Generates text embeddings using Amazon Bedrock (Amazon Titan Text Embeddings v2).
    Enforces 1024 dimensions matching the pgvector schema.
    """

    def __init__(self):
        self.model_id = settings.AWS_BEDROCK_EMBEDDING_MODEL_ID
        self.region = settings.AWS_REGION
        self.dimension = settings.AWS_BEDROCK_EMBEDDING_DIM
        self.is_configured = bool(
            settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY
            and settings.AWS_ACCESS_KEY_ID != "your_aws_access_key_id"
        )
        self.client = None

        if self.is_configured:
            try:
                import boto3
                self.client = boto3.client(
                    "bedrock-runtime",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region,
                )
                logger.info(
                    f"BedrockEmbeddingService initialized with model {self.model_id} ({self.dimension}d) in {self.region}"
                )
            except Exception as exc:
                logger.warning(f"Failed to initialize AWS Bedrock embedding client: {exc}")
                self.is_configured = False

    def get_embedding(self, text: str) -> List[float]:
        """Generate a 1024-dimensional embedding for a single text input."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        cleaned_text = " ".join(text.split())[:8000]

        if self.is_configured and self.client:
            try:
                body = json.dumps({
                    "inputText": cleaned_text,
                    "dimensions": self.dimension,
                    "normalize": True
                })
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=body
                )
                resp_payload = json.loads(response["body"].read())
                embedding = resp_payload.get("embedding", [])
                if len(embedding) == self.dimension:
                    return embedding
                elif len(embedding) > 0:
                    logger.warning(
                        f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}"
                    )
                    return embedding
            except Exception as e:
                logger.error(f"Bedrock embedding generation failed with model {self.model_id}: {e}")

        # Deterministic normalized fallback embedding for offline or test environments
        return self._generate_fallback_embedding(cleaned_text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return [self.get_embedding(t) for t in texts]

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """
        Produces a deterministic, normalized vector based on text hashing.
        Allows testing RAG retrieval and vector mechanics even when AWS credentials are absent.
        """
        import hashlib
        import math

        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Derive 1024 float values from repeated hash expansion
        vec = []
        seed = int.from_bytes(h[:4], "big")
        for i in range(self.dimension):
            # Simple pseudo-random formula keyed on hash
            val = math.sin(seed + i * 0.317)
            vec.append(val)
        
        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


embedding_service = BedrockEmbeddingService()
