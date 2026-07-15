import io
import os
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ObjectStorageService:
    """Enterprise-grade object storage service for documents using MinIO/S3 or local fallback."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "ap_minio_admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "ap_minio_secure_password")
        self.bucket = os.getenv("MINIO_BUCKET", "ap-documents")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Try to connect to MinIO, fall back to local storage if unavailable
        self._storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
        try:
            from minio import Minio
            self.client = Minio(
                endpoint=self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
            self._ensure_bucket()
            self._use_minio = True
        except Exception as e:
            logger.warning("minio_unavailable", error=str(e), fallback="local_storage")
            self.client = None
            self._use_minio = False
            # Create local storage directory
            os.makedirs(self._storage_path, exist_ok=True)

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        if self.client and not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info("bucket_created", bucket=self.bucket)

    def upload_file(
        self,
        content: bytes,
        filename: str,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload document to object storage. Returns storage path."""
        object_name = f"{filename}"
        
        if self._use_minio and self.client:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=io.BytesIO(content),
                length=len(content),
                content_type=content_type,
            )
            logger.info("file_uploaded_to_minio", path=object_name, size=len(content))
        else:
            # Local fallback storage
            local_path = os.path.join(self._storage_path, object_name)
            with open(local_path, "wb") as f:
                f.write(content)
            logger.info("file_uploaded_locally", path=local_path, size=len(content))
        
        return object_name

    def download_file(self, path: str) -> bytes:
        """Download file content from storage."""
        if self._use_minio and self.client:
            try:
                response = self.client.get_object(self.bucket, path)
                return response.read()
            except Exception as exc:
                logger.error("download_failed", path=path, error=str(exc))
                raise
        else:
            local_path = os.path.join(self._storage_path, path)
            try:
                with open(local_path, "rb") as f:
                    return f.read()
            except Exception as exc:
                logger.error("local_download_failed", path=path, error=str(exc))
                raise

    def get_presigned_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Generate a presigned URL for secure file access."""
        if self._use_minio and self.client:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=path,
                expires=expires_seconds,
            )
        else:
            # Return a placeholder for local storage
            return f"/api/v1/documents/download/{path}"

    def delete_file(self, path: str) -> None:
        """Delete file from storage."""
        if self._use_minio and self.client:
            self.client.remove_object(self.bucket, path)
            logger.info("file_deleted_from_minio", path=path)
        else:
            local_path = os.path.join(self._storage_path, path)
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info("file_deleted_locally", path=local_path)

    def file_exists(self, path: str) -> bool:
        """Check if file exists in storage."""
        if self._use_minio and self.client:
            try:
                self.client.stat_object(self.bucket, path)
                return True
            except Exception:
                return False
        else:
            local_path = os.path.join(self._storage_path, path)
            return os.path.exists(local_path)