from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    firebase_project_id: str | None = None
    firebase_storage_bucket: str | None = None   # e.g. my-project.firebasestorage.app
    max_upload_mb: int = 25
    cors_origins: str = "http://localhost:5173"

    # Media storage (see app/core/storage.py): local | s3 | firebase
    storage_backend: str = "local"
    local_media_dir: str = str(_BACKEND / "uploads")
    media_signing_secret: str | None = None       # any long random string; keeps local media links valid across restarts
    public_base_url: str = "http://localhost:8000"  # how browsers reach this API (used in local media links)
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None            # e.g. https://s3.us-west-004.backblazeb2.com ; empty for AWS S3
    s3_region: str | None = None
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
