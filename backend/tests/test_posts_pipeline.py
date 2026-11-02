"""End-to-end through the HTTP API: register -> upload media -> report -> real Strands agent loop -> decision stored -> UI reads it.
Test doubles (see tests/fakes.py): in-memory stores instead of Firestore/Storage, a scripted LLM and a fake Decider endpoint.
NOT covered here: live Firestore, live Firebase Storage, Amazon Bedrock, the hosted Decider."""
import pytest
from fastapi.testclient import TestClient

from agent.decider_client import DeciderClient
from agent.engine import StrandsDeciderEngine
from app.core import deps, security
from app.main import app
from app.services.media_service import MediaService
from tests.fakes import FakeDecider, InMemoryDecisionRepo, InMemoryPostRepo, InMemoryStorage, ScriptedModel
from tests.test_accounts import FakeRepo
from app.services.account_service import AccountService

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 200
H = lambda uid: {"Authorization": f"Bearer {uid}"}
ORG = {"contactName": "Asha", "orgName": "Madurai Green Trust", "category": "NGO / Non-profit",
       "description": "We organize weekly clean-up drives across the city.", "locality": "Anna Nagar"}


def make_env(monkeypatch, engine):
    posts, decisions, storage, accounts = InMemoryPostRepo(), InMemoryDecisionRepo(), InMemoryStorage(), FakeRepo()
    svc = AccountService(accounts, lambda uid, c: None)
    app.dependency_overrides.update({
        security.get_service: lambda: svc, deps.get_post_repo: lambda: posts, deps.get_decision_repo: lambda: decisions,
        deps.get_storage: lambda: storage, deps.get_engine: lambda: engine, deps.get_media_service: lambda: MediaService(storage, 1)})
    monkeypatch.setattr(security, "verify_token", lambda t: security.Principal(uid=t, email=f"{t}@x.in"))
    c = TestClient(app)
    for uid, name in (("cit1", "Ravi Kumar"), ("cit2", "Meena S")):
        assert c.post("/api/auth/register/citizen", json={"displayName": name, "locality": "Anna Nagar"}, headers=H(uid)).status_code == 201
    assert c.post("/api/auth/register/organization", json=ORG, headers=H("org1")).status_code == 201
    return c, posts, decisions, storage


@pytest.fixture
def env(monkeypatch):
    engine = StrandsDeciderEngine(decider=FakeDecider(), model_factory=lambda: ScriptedModel())
    yield make_env(monkeypatch, engine)
    app.dependency_overrides.clear()


def report(c, uid, text, category="Roads & potholes", **kw):
    r = c.post("/api/posts", json={"description": text, "category": category, "locality": "Anna Nagar", **kw}, headers=H(uid))
    assert r.status_code == 201, r.text
    return r.json()


def test_urgent_report_full_workflow(env):
    c, posts, decisions, storage = env
    up = c.post("/api/media", files={"file": ("p.png", PNG, "image/png")}, headers=H("cit1"))
    assert up.status_code == 201 and up.json()["mediaPath"].startswith("posts/cit1/")
    created = report(c, "cit1", "Live wire hanging from the pole near the bus stop, sparking when it rains.", "Electricity", mediaPath=up.json()["mediaPath"])
    assert created["decisionState"] == "pending"                       # returned before the agent finished
    got = c.get(f"/api/posts/{created['id']}", headers=H("cit1")).json()  # the agent ran as a background task
    assert got["decisionState"] == "completed" and got["decision"]["action"] == "FLAG_URGENT"
    assert got["decision"]["externalContact"] is False and got["mediaUrl"].startswith("https://signed.test/posts/cit1/")
    trace = c.get(f"/api/posts/{created['id']}/decision", headers=H("cit1")).json()
    assert {r["tool"] for r in trace["toolRuns"]} >= {"assess_urgency", "detect_duplicates", "strands_decider_call"}
    assert [a["type"] for a in trace["audit"]][0] == "decision_started" and "incident_created" in [a["type"] for a in trace["audit"]]
    inc = decisions.get_incident(got["referenceId"])
    assert inc["urgent"] is True and inc["departmentContacted"] is False and inc["humanApprovalRequired"] is True
    note = c.get("/api/notifications", headers=H("cit1")).json()[0]["text"]
    assert "urgent" in note and "112" in note and "contacted" not in note.replace("no department has been contacted", "")


def test_duplicate_is_detected_against_the_previous_report(env):
    c, *_ = env
    first = report(c, "cit1", "Street light not working near the temple on 5th street", "Street lighting")
    second = report(c, "cit2", "Street light not working near the temple on 5th street", "Street lighting")
    d = c.get(f"/api/posts/{second['id']}", headers=H("cit2")).json()["decision"]
    assert d["action"] == "CHECK_DUPLICATE" and d["duplicate"]["referenceId"] == c.get(f"/api/posts/{first['id']}", headers=H("cit1")).json()["referenceId"]


def test_routing_is_a_recommendation_only(env):
    c, *_ = env
    p = report(c, "cit1", "Big pothole near the signal, bikes slipping badly every day.")
    d = c.get(f"/api/posts/{p['id']}", headers=H("cit1")).json()["decision"]
    assert d["action"] == "ROUTE_TO_DEPARTMENT" and d["department"]["id"] == "roads"
    assert "no department has been contacted" in c.get("/api/notifications", headers=H("cit1")).json()[0]["text"]
    assert c.post(f"/api/posts/{p['id']}/decision/retry", headers=H("cit1")).status_code == 409   # only failed reviews can be retried


def test_permissions_citizen_vs_organization(env):
    c, *_ = env
    body = {"description": "Big pothole near the signal, bikes slipping.", "category": "Roads & potholes", "locality": "Anna Nagar"}
    assert c.post("/api/posts", json=body, headers=H("org1")).status_code == 403          # orgs cannot post as citizens
    p = report(c, "cit1", body["description"])
    assert c.post(f"/api/posts/{p['id']}/like", headers=H("org1")).status_code == 403
    assert c.post(f"/api/posts/{p['id']}/comments", json={"text": "hi"}, headers=H("org1")).status_code == 403
    assert c.post("/api/media", files={"file": ("p.png", PNG, "image/png")}, headers=H("org1")).status_code == 403
    assert c.get("/api/posts", headers=H("org1")).status_code == 200                       # orgs can read the public feed
    assert c.get("/api/posts").status_code == 401
    assert c.get(f"/api/posts/{p['id']}/decision", headers=H("cit2")).status_code == 403   # trace is author/admin only


def test_likes_comments_search_filters(env):
    c, *_ = env
    a = report(c, "cit1", "Big pothole near the signal, bikes slipping badly.")
    report(c, "cit1", "Garbage not collected for three days in our lane.", "Waste & sanitation")
    assert c.post(f"/api/posts/{a['id']}/like", headers=H("cit2")).json() == {"likedByMe": True, "likeCount": 1}
    assert c.post(f"/api/posts/{a['id']}/like", headers=H("cit2")).json() == {"likedByMe": False, "likeCount": 0}
    c.post(f"/api/posts/{a['id']}/like", headers=H("cit2"))
    assert c.post(f"/api/posts/{a['id']}/comments", json={"text": "  same here  "}, headers=H("cit2")).json()["text"] == "same here"
    assert c.get(f"/api/posts/{a['id']}/comments", headers=H("cit1")).json()[0]["author"]["name"] == "Meena S"
    feed = {p["id"]: p for p in c.get("/api/posts", headers=H("cit2")).json()}
    assert feed[a["id"]]["likedByMe"] and feed[a["id"]]["commentCount"] == 1
    assert len(c.get("/api/posts?category=Waste%20%26%20sanitation", headers=H("cit1")).json()) == 1
    assert len(c.get("/api/posts?q=pothole", headers=H("cit1")).json()) == 1
    assert len(c.get("/api/posts?mine=1", headers=H("cit2")).json()) == 0
    assert c.post("/api/posts", json={"description": "x" * 20, "category": "Nonsense", "locality": "Anna Nagar"}, headers=H("cit1")).status_code == 422


def test_media_validation(env):
    c, *_ = env
    assert c.post("/api/media", files={"file": ("x.png", b"MZ not an image at all", "image/png")}, headers=H("cit1")).status_code == 415
    assert c.post("/api/media", files={"file": ("x.pdf", b"%PDF", "application/pdf")}, headers=H("cit1")).status_code == 415
    assert c.post("/api/media", files={"file": ("big.png", PNG + b"0" * 2_000_000, "image/png")}, headers=H("cit1")).status_code == 413
    stolen = c.post("/api/media", files={"file": ("p.png", PNG, "image/png")}, headers=H("cit2")).json()["mediaPath"]
    r = c.post("/api/posts", json={"description": "Big pothole near the signal.", "category": "Roads & potholes", "locality": "Anna Nagar", "mediaPath": stolen}, headers=H("cit1"))
    assert r.status_code == 400                                                              # cannot attach another user's file


def test_agent_unavailable_fails_closed_and_is_not_faked(monkeypatch):
    engine = StrandsDeciderEngine(decider=DeciderClient(url="http://127.0.0.1:9", key=None), model_factory=lambda: ScriptedModel())
    monkeypatch.delenv("DECIDER_API_KEY", raising=False)
    c, posts, decisions, _ = make_env(monkeypatch, engine)
    try:
        p = report(c, "cit1", "Live wire hanging near the school, sparking.", "Electricity")
        got = c.get(f"/api/posts/{p['id']}", headers=H("cit1")).json()
        assert got["decisionState"] == "failed" and got["decision"]["source"] == "fail_closed"
        assert got["decision"]["action"] == "ESCALATE_FOR_HUMAN_REVIEW" and "112" in got["decision"]["summary"]
        trace = c.get(f"/api/posts/{p['id']}/decision", headers=H("cit1")).json()
        assert "DECIDER_API_KEY" in trace["error"] and trace["toolRuns"] == [] and trace["deciderUsed"] is False
        assert decisions.get_incident(got["referenceId"]) is None                          # no incident is created from a failed run
        assert c.post(f"/api/posts/{p['id']}/decision/retry", headers=H("cit2")).status_code == 403
        assert c.post(f"/api/posts/{p['id']}/decision/retry", headers=H("cit1")).status_code == 202
        assert c.get(f"/api/posts/{p['id']}", headers=H("cit1")).json()["decisionState"] == "failed"   # still fails: key still missing
    finally:
        app.dependency_overrides.clear()
