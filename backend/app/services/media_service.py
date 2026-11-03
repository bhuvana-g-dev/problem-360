"""Validated media upload to private Firebase Storage. Type is decided by file CONTENT (magic bytes), not the
client's claimed content-type or filename, and size is capped while reading."""
import logging
import uuid

from fastapi import HTTPException, status

log = logging.getLogger("problem360.media")

_SIGNATURES = {
    "image/jpeg": ("jpg", "image", lambda b: b[:3] == b"\xff\xd8\xff"),
    "image/png": ("png", "image", lambda b: b[:8] == b"\x89PNG\r\n\x1a\n"),
    "image/webp": ("webp", "image", lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP"),
    "video/mp4": ("mp4", "video", lambda b: b[4:8] == b"ftyp"),
    "video/webm": ("webm", "video", lambda b: b[:4] == b"\x1a\x45\xdf\xa3"),
}


class MediaService:
    def __init__(self, storage, max_mb: int):
        self.storage, self.max_bytes = storage, max_mb * 1024 * 1024

    async def upload(self, uid: str, file) -> dict:
        ctype = (file.content_type or "").lower()
        if ctype not in _SIGNATURES:
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a JPEG, PNG, WebP, MP4 or WebM file.")
        data = bytearray()
        while chunk := await file.read(1024 * 1024):
            data += chunk
            if len(data) > self.max_bytes:
                raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"File is larger than {self.max_bytes // 1048576} MB.")
        ext, kind, matches = _SIGNATURES[ctype]
        if not data or not matches(bytes(data[:16])):
            raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "The file content does not match its type.")
        path = f"posts/{uid}/{uuid.uuid4().hex}.{ext}"   # server-chosen name: no client-controlled path
        try:
            self.storage.put(path, bytes(data), ctype)
        except Exception as e:  # bucket missing, wrong name or no permission: say so instead of a bare 500
            log.exception("media upload failed for %s", uid)
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                                "Photo storage is not available right now. You can still submit the report without a photo.") from e
        return {"mediaPath": path, "mediaType": kind}
