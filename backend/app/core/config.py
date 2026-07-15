from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AP Invoice & Contract Exception Agent"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    secret_key: str = Field(min_length=32)
    api_v1_prefix: str = "/api/v1"

    database_url: str
    database_sync_url: str = ""

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    microsoft_oauth_client_id: str = ""
    microsoft_oauth_client_secret: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    azure_document_intelligence_endpoint: str = ""
    azure_document_intelligence_key: str = ""

    google_document_ai_project_id: str = ""
    google_document_ai_location: str = "us"
    google_document_ai_processor_id: str = ""
    google_application_credentials: str = ""

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "ap_minio_admin"
    minio_secret_key: str = "ap_minio_secure_password"
    minio_bucket: str = "ap-documents"
    minio_secure: bool = False

    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "ap_knowledge_base"

    rate_limit_per_minute: int = 100

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def sync_database_url(self) -> str:
        if self.database_sync_url:
            return self.database_sync_url
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()
