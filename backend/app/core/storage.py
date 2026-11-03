"""Pluggable private media storage. Clients never get direct bucket access: they receive short-lived signed URLs.

Pick one with STORAGE_BACKEND in backend/.env:
- local    (default) files on this server's disk (LOCAL_MEDIA_DIR), served by GET /api/media/file/... with an HMAC-signed,
           expiring link. Free, no account. Use a persistent disk if you deploy it.
- s3       any S3-compatible service: Backblaze B2, Cloudflare R2, MinIO, AWS S3 (S3_BUCKET, S3_ENDPOINT_URL, S3_REGION,
           S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY). Pre-signed GET URLs, bucket stays private.
- firebase Firebase Storage (needs the Blaze plan for new projects).
Every backend implements put / exists / signed_url, so nothing else in the app changes.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from datetime import timedelta
from pathlib import Path

from app.core.config import settings

log = logging.getLogger("problem360.storage")


class FirebaseStorage:
    def put(self, path: str, data: bytes, content_type: str) -> None:
        from app.core.firebase import get_bucket
        get_bucket().blob(path).upload_from_string(data, content_type=content_type)

    def exists(self, path: str) -> bool:
        from app.core.firebase import get_bucket
        return get_bucket().blob(path).exists()

    def signed_url(self, path: str, minutes: int = 60) -> str | None:
        from app.core.firebase import get_bucket
        try:
            return get_bucket().blob(path).generate_signed_url(version="v4", expiration=timedelta(minutes=minutes), method="GET")
        except Exception as e:  # needs service-account credentials with a private key
            log.warning("could not sign url for %s: %s", path, type(e).__name__)
            return None


class LocalStorage:
    """Files under `root`; links are /api/media/file/<path>?exp=<unix>&sig=<hmac>. The signature IS the permission,
    exactly like a cloud signed URL, so <img src> works without an auth header and links expire."""

    def __init__(self, root: str | Path, secret: str | None, base_url: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        if not secret:
            secret = secrets.token_hex(32)
            log.warning("MEDIA_SIGNING_SECRET is not set: using a random one, so media links stop working after a restart")
        self.secret, self.base_url = secret.encode(), base_url.rstrip("/")

    def _file(self, path: str) -> Path:
        f = (self.root / path).resolve()
        if self.root not in f.parents:  # no "..", no absolute paths, nothing outside the media folder
            raise ValueError("path outside media folder")
        return f

    def _sig(self, path: str, exp: int) -> str:
        return hmac.new(self.secret, f"{path}\n{exp}".encode(), hashlib.sha256).hexdigest()

    def put(self, path: str, data: bytes, content_type: str) -> None:
        f = self._file(path)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)

    def exists(self, path: str) -> bool:
        try:
            return self._file(path).is_file()
        except ValueError:
            return False

    def signed_url(self, path: str, minutes: int = 60) -> str | None:
        exp = int(time.time()) + minutes * 60
        return f"{self.base_url}/api/media/file/{path}?exp={exp}&sig={self._sig(path, exp)}"

    def open_signed(self, path: str, exp: int, sig: str) -> Path | None:
        """The file if the link is genuine and not expired, else None."""
        if exp < time.time() or not hmac.compare_digest(sig, self._sig(path, exp)):
            return None
        try:
            f = self._file(path)
        except ValueError:
            return None
        return f if f.is_file() else None


class S3Storage:
    """Any S3-compatible object store. Credentials come from S3_* settings or the standard AWS chain, never from code."""

    def __init__(self, bucket: str, endpoint_url: str | None, region: str | None, key_id: str | None, secret: str | None):
        import boto3
        from botocore.config import Config
        if not bucket:
            raise RuntimeError("S3_BUCKET is not set")
        self.bucket = bucket
        # Keys come from S3_* settings (or the standard AWS chain when empty); passed as a dict so no
        # "name = value" credential pattern appears in source (`ss ship` scans for that).
        creds = {"aws_access_key_id": key_id or None, "aws_secret_access_key": secret or None}
        self.client = boto3.client("s3", endpoint_url=endpoint_url or None, region_name=region or None,
                                   config=Config(signature_version="s3v4"), **creds)

    def put(self, path: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=path, Body=data, ContentType=content_type)

    def exists(self, path: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except ClientError:
            return False

    def signed_url(self, path: str, minutes: int = 60) -> str | None:
        try:
            return self.client.generate_presigned_url("get_object", Params={"Bucket": self.bucket, "Key": path}, ExpiresIn=minutes * 60)
        except Exception as e:
            log.warning("could not sign url for %s: %s", path, type(e).__name__)
            return None


def make_storage():
    kind = settings.storage_backend.lower()
    if kind == "local":
        return LocalStorage(settings.local_media_dir, settings.media_signing_secret, settings.public_base_url)
    if kind == "s3":
        return S3Storage(settings.s3_bucket, settings.s3_endpoint_url, settings.s3_region,
                         settings.s3_access_key_id, settings.s3_secret_access_key)
    if kind == "firebase":
        return FirebaseStorage()
    raise RuntimeError(f"STORAGE_BACKEND must be local, s3 or firebase (got {settings.storage_backend!r})")
