import logging
from typing import Optional
from pathlib import Path
import core.aws_time_sync  # Ensure botocore SigV4 runtime timestamp is calibrated
from core.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.bucket = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_REGION
        self.is_configured = bool(
            settings.AWS_ACCESS_KEY_ID
            and settings.AWS_SECRET_ACCESS_KEY
            and settings.AWS_ACCESS_KEY_ID != "your_aws_access_key_id"
        )
        self.s3_client = None

        if self.is_configured:
            try:
                import boto3
                from botocore.client import Config
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=self.region,
                    endpoint_url=f"https://s3.{self.region}.amazonaws.com",
                    config=Config(signature_version="s3v4")
                )
                logger.info(f"S3Service initialized successfully for bucket: {self.bucket} in {self.region}")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS S3 client ({e}). Will use fallback storage.")
                self.is_configured = False

    def upload_file(self, file_bytes: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """
        Uploads file to AWS S3 with AES256 server-side encryption.
        Falls back to local mock URL if AWS credentials are not configured.
        """
        if self.is_configured and self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=file_bytes,
                    ContentType=content_type,
                    ServerSideEncryption="AES256"
                )
                return s3_key
            except Exception as e:
                logger.error(f"S3 upload failed for {s3_key}: {e}. Falling back.")

        return f"local/{s3_key}"

    def get_document_url(self, s3_key: str, expires_in: int = 900) -> str:
        """
        Generates a secure, temporary pre-signed URL (default 15 mins) for viewing/downloading.
        """
        if self.is_configured and self.s3_client and not s3_key.startswith("local/"):
            try:
                return self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket, "Key": s3_key},
                    ExpiresIn=expires_in
                )
            except Exception as e:
                logger.error(f"Failed to generate pre-signed URL for {s3_key}: {e}")

        return f"/uploads/patient-documents/{s3_key}"

    def delete_file(self, s3_key: str) -> bool:
        """Deletes file from S3."""
        if self.is_configured and self.s3_client and not s3_key.startswith("local/"):
            try:
                self.s3_client.delete_object(Bucket=self.bucket, Key=s3_key)
                return True
            except Exception as e:
                logger.error(f"Failed to delete S3 object {s3_key}: {e}")
                return False
        return True

    def download_file(self, s3_key: str) -> bytes:
        """Download an uploaded document for server-side clinical processing."""
        if not self.is_configured or not self.s3_client or s3_key.startswith("local/"):
            raise RuntimeError("Uploaded document is not available in AWS S3")

        response = self.s3_client.get_object(Bucket=self.bucket, Key=s3_key)
        return response["Body"].read()

s3_service = S3Service()
