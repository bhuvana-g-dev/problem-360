"""Local media storage: signed, expiring, path-safe links served through the real API route."""
import time

from fastapi.testclient import TestClient

from app.core import deps
from app.core.storage import LocalStorage, S3Storage
from app.main import app

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _client(tmp_path):
    store = LocalStorage(tmp_path, "test-secret", "http://testserver")
    app.dependency_overrides[deps.get_storage] = lambda: store
    return store, TestClient(app)


def test_signed_link_serves_the_file(tmp_path):
    store, c = _client(tmp_path)
    try:
        store.put("posts/u1/a.png", PNG, "image/png")
        assert store.exists("posts/u1/a.png")
        r = c.get(store.signed_url("posts/u1/a.png").replace("http://testserver", ""))
        assert r.status_code == 200 and r.content == PNG and r.headers["content-type"] == "image/png"
    finally:
        app.dependency_overrides.clear()


def test_tampered_expired_or_unsigned_links_are_refused(tmp_path):
    store, c = _client(tmp_path)
    try:
        store.put("posts/u1/a.png", PNG, "image/png")
        url = store.signed_url("posts/u1/a.png").replace("http://testserver", "")
        assert c.get(url.replace("a.png", "b.png")).status_code == 404               # signature is for another file
        assert c.get(url[:-4] + "0000").status_code == 404                            # forged signature
        old = int(time.time()) - 10
        assert c.get(f"/api/media/file/posts/u1/a.png?exp={old}&sig={store._sig('posts/u1/a.png', old)}").status_code == 404
        assert c.get("/api/media/file/posts/u1/a.png").status_code == 422             # no signature at all
    finally:
        app.dependency_overrides.clear()


def test_paths_cannot_escape_the_media_folder(tmp_path):
    store = LocalStorage(tmp_path / "media", "s", "http://x")
    assert not store.exists("../secret.txt")
    exp = int(time.time()) + 60
    assert store.open_signed("../secret.txt", exp, store._sig("../secret.txt", exp)) is None


def test_s3_storage_needs_a_bucket():
    try:
        S3Storage("", None, None, None, None)
        assert False, "expected an error"
    except RuntimeError as e:
        assert "S3_BUCKET" in str(e)
