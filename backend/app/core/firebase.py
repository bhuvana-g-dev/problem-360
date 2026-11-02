"""Firebase Admin SDK bootstrap. Credentials come from GOOGLE_APPLICATION_CREDENTIALS, never from code."""
import firebase_admin
from firebase_admin import firestore, storage

from app.core.config import settings

_app = None


def get_app():
    global _app
    if _app is None:
        opts = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
        _app = firebase_admin.initialize_app(options=opts)
    return _app


def get_db():
    return firestore.client(get_app())


def get_bucket():
    if not settings.firebase_storage_bucket:
        raise RuntimeError("FIREBASE_STORAGE_BUCKET is not set")
    return storage.bucket(settings.firebase_storage_bucket, app=get_app())
