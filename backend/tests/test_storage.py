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


# ---- Cloudinary: real SDK URL signing (offline); the network upload/lookup is replaced ----
def test_cloudinary_needs_all_three_settings():
    from app.core.storage import CloudinaryStorage
    for args in (("", "k", "s"), ("c", "", "s"), ("c", "k", None)):
        try:
            CloudinaryStorage(*args)
            assert False, "expected an error"
        except RuntimeError as e:
            assert "CLOUDINARY_CLOUD_NAME" in str(e)


def test_cloudinary_uploads_private_and_hands_out_signed_urls(monkeypatch):
    import cloudinary.api
    import cloudinary.uploader
    from cloudinary.exceptions import NotFound

    from app.core.storage import CloudinaryStorage
    calls = []
    monkeypatch.setattr(cloudinary.uploader, "upload", lambda f, **kw: calls.append((f.read(), kw)) or {"public_id": kw["public_id"]})
    store = CloudinaryStorage("democloud", "123456", "not-a-real-secret")

    store.put("posts/u1/abc123.jpg", PNG, "image/jpeg")
    store.put("posts/u1/def456.mp4", b"\x00\x00\x00\x18ftypmp42", "video/mp4")
    (data, img), (_, vid) = calls
    assert data == PNG and img["public_id"] == "posts/u1/abc123" and img["resource_type"] == "image" and img["type"] == "authenticated"
    assert vid["public_id"] == "posts/u1/def456" and vid["resource_type"] == "video" and vid["type"] == "authenticated"
    assert img["overwrite"] is False

    url = store.signed_url("posts/u1/abc123.jpg")
    assert url.startswith("https://res.cloudinary.com/democloud/image/authenticated/s--") and url.endswith("/posts/u1/abc123.jpg")
    assert "/video/authenticated/s--" in store.signed_url("posts/u1/def456.mp4")
    assert store.signed_url("posts/u1/abc123.jpg") == url and store.signed_url("posts/u2/abc123.jpg") != url   # signature is per file

    monkeypatch.setattr(cloudinary.api, "resource", lambda pid, **kw: {"public_id": pid})
    assert store.exists("posts/u1/abc123.jpg")

    def missing(pid, **kw):
        raise NotFound("Resource not found")
    monkeypatch.setattr(cloudinary.api, "resource", missing)
    assert not store.exists("posts/u1/nope.jpg")
