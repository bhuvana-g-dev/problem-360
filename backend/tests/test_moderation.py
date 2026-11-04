"""Rate limits and comment moderation (deterministic, code-owned)."""
import pytest
from fastapi import HTTPException

from app.core import ratelimit
from app.services import moderation
from tests.test_posts_pipeline import H, env, report  # noqa: F401  (env is a pytest fixture)


def test_comment_rules_block_links_personal_data_spam_and_shouting():
    assert moderation.problems("Same problem on our street since Monday.") == []
    assert moderation.problems("எங்கள் தெருவிலும் இதே பிரச்சனை") == []
    assert "links" in moderation.problems("see www.example.com for details")[0]
    assert "phone numbers" in moderation.problems("call me on 98765 43210")[0]
    assert "email addresses" in " ".join(moderation.problems("mail me at someone@example.com"))
    assert "spam" in moderation.problems("fix this!!!!!!!!!!")[0]
    assert "capitals" in moderation.problems("THIS IS A TERRIBLE ROAD FIX IT NOW")[0]


def test_blocklist_comes_from_the_moderators_file(tmp_path, monkeypatch):
    f = tmp_path / "blocked.txt"
    f.write_text("# one term per line\nbadword\nகெட்டசொல்\n", encoding="utf-8")
    monkeypatch.setenv("MODERATION_BLOCKLIST", str(f))
    moderation.blocked_terms.cache_clear()
    try:
        assert moderation.problems("you badword")
        assert not moderation.problems("badwordish is not the word")          # whole words only for Latin script
        assert moderation.problems("இது கெட்டசொல் தான்")                      # substring for Tamil
    finally:
        moderation.blocked_terms.cache_clear()


def test_rate_limit_returns_429_with_retry_after():
    for _ in range(5):
        ratelimit.check("u1", "post")
    with pytest.raises(HTTPException) as e:
        ratelimit.check("u1", "post")
    assert e.value.status_code == 429 and int(e.value.headers["Retry-After"]) > 0
    ratelimit.check("u2", "post")                     # other users are not affected


def test_api_rejects_bad_comments_and_floods(env):
    c, *_ = env
    p = report(c, "cit1", "Big pothole near the signal, bikes slipping badly.")
    r = c.post(f"/api/posts/{p['id']}/comments", json={"text": "call 9876543210"}, headers=H("cit2"))
    assert r.status_code == 422 and "phone numbers" in r.json()["detail"]
    assert c.get(f"/api/posts/{p['id']}/comments", headers=H("cit2")).json() == []          # never stored
    for i in range(4):
        report(c, "cit1", f"Another pothole near the signal, number {'abcd'[i]} in the row.")
    flood = c.post("/api/posts", json={"description": "One more pothole report today.", "category": "Roads & potholes", "locality": "Anna Nagar"}, headers=H("cit1"))
    assert flood.status_code == 429 and "Retry-After" in flood.headers
