"""Firebase Storage gateway. Files are private: clients never get bucket access (see storage.rules);
they receive short-lived V4 signed URLs minted by the backend."""
import logging
from datetime import timedelta

from app.core.firebase import get_bucket

log = logging.getLogger("problem360.storage")


class FirebaseStorage:
    def put(self, path: str, data: bytes, content_type: str) -> None:
        get_bucket().blob(path).upload_from_string(data, content_type=content_type)

    def exists(self, path: str) -> bool:
        return get_bucket().blob(path).exists()

    def signed_url(self, path: str, minutes: int = 60) -> str | None:
        try:
            return get_bucket().blob(path).generate_signed_url(version="v4", expiration=timedelta(minutes=minutes), method="GET")
        except Exception as e:  # needs service-account credentials with a private key
            log.warning("could not sign url for %s: %s", path, type(e).__name__)
            return None
