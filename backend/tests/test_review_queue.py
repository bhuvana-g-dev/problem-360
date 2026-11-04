"""Human review queue through the HTTP API: the agent flags a report, an admin reviews it, the citizen is told.
Test doubles: in-memory stores, scripted LLM, fake Decider (tests/fakes.py)."""
import pytest
from fastapi.testclient import TestClient

from agent.engine import StrandsDeciderEngine
from app.core import deps, security
from app.main import app
from app.services.account_service import AccountService
from app.services.media_service import MediaService
from tests.fakes import FakeDecider, InMemoryDecisionRepo, InMemoryPostRepo, InMemoryStorage, ScriptedModel
from tests.test_accounts import FakeRepo

H = lambda uid: {"Authorization": f"Bearer {uid}"}


@pytest.fixture
def env(monkeypatch):
    posts, decisions, storage, accounts = InMemoryPostRepo(), InMemoryDecisionRepo(), InMemoryStorage(), FakeRepo()
    engine = StrandsDeciderEngine(decider=FakeDecider(), model_factory=lambda: ScriptedModel())
    app.dependency_overrides.update({
        security.get_service: lambda: AccountService(accounts, lambda uid, c: None), deps.get_post_repo: lambda: posts,
        deps.get_decision_repo: lambda: decisions, deps.get_storage: lambda: storage, deps.get_engine: lambda: engine,
        deps.get_media_service: lambda: MediaService(storage, 1)})
    monkeypatch.setattr(security, "verify_token", lambda t: security.Principal(uid=t, email=f"{t}@x.in"))
    c = TestClient(app)
    for uid, name in (("cit1", "Ravi Kumar"), ("cit2", "Meena S"), ("admin1", "Reviewer")):
        assert c.post("/api/auth/register/citizen", json={"displayName": name, "locality": "Anna Nagar"}, headers=H(uid)).status_code == 201
    accounts.users["admin1"]["accountType"] = "admin"     # promoted out of band (scripts/make_admin.py)
    yield c, posts, decisions
    app.dependency_overrides.clear()


def report(c, uid, text, category):
    r = c.post("/api/posts", json={"description": text, "category": category, "locality": "Anna Nagar"}, headers=H(uid))
    assert r.status_code == 201, r.text
    return r.json()


def notes(c, uid):
    return [n["text"] for n in c.get("/api/notifications", headers=H(uid)).json()]


def test_urgent_report_is_queued_first_approved_resolved_and_citizen_is_told(env):
    c, posts, decisions = env
    routine = report(c, "cit1", "Big pothole near the signal, bikes slipping badly every day.", "Roads & potholes")
    urgent = report(c, "cit1", "Live wire hanging from the pole near the bus stop, sparking when it rains.", "Electricity")
    assert c.get("/api/admin/reviews", headers=H("cit1")).status_code == 403                 # citizens cannot see the queue
    q = c.get("/api/admin/reviews", headers=H("admin1")).json()
    assert [r["id"] for r in q] == [urgent["id"]] and q[0]["urgent"] and q[0]["action"] == "FLAG_URGENT"   # routed report is not queued
    assert c.post(f"/api/admin/reviews/{routine['id']}", json={"decision": "approve"}, headers=H("admin1")).status_code == 409

    r = c.post(f"/api/admin/reviews/{urgent['id']}", json={"decision": "approve", "note": "Called the line crew"}, headers=H("admin1"))
    assert r.status_code == 200 and r.json()["status"] == "Acknowledged" and r.json()["review"]["minutesToReview"] >= 0
    assert c.post(f"/api/admin/reviews/{urgent['id']}", json={"decision": "reject", "note": "dup"}, headers=H("admin1")).status_code == 409
    got = c.get(f"/api/posts/{urgent['id']}", headers=H("cit1")).json()
    assert got["status"] == "Acknowledged" and got["review"]["state"] == "approved" and "by" not in got["review"]
    ack = [n for n in notes(c, "cit1") if "acknowledged it" in n]
    assert len(ack) == 1 and "112" in ack[0] and "has not contacted any department" in ack[0] and "Called the line crew" in ack[0]
    assert decisions.get_incident(got["referenceId"])["humanApproved"] is True
    assert "human_review" in [a["type"] for a in decisions.list_audit(urgent["id"])]

    assert c.patch(f"/api/admin/reports/{urgent['id']}/status", json={"status": "Resolved", "note": "Line repaired"}, headers=H("admin1")).json()["status"] == "Resolved"
    assert any("marked resolved" in n and "Line repaired" in n for n in notes(c, "cit1"))
    assert c.get("/api/admin/reviews", headers=H("admin1")).json() == []
    done = c.get("/api/admin/reviews?state=done", headers=H("admin1")).json()
    assert done[0]["review"]["state"] == "approved" and done[0]["status"] == "Resolved"
    s = c.get("/api/admin/reviews/stats", headers=H("admin1")).json()
    assert s["pending"] == 0 and s["reviewed"] == 1 and s["resolved"] == 1 and s["medianMinutesToReviewUrgent"] is not None


def test_reject_needs_a_reason_and_blocks_status_changes(env):
    c, *_ = env
    report(c, "cit1", "Street light not working near the temple on 5th street", "Street lighting")
    dup = report(c, "cit2", "Street light not working near the temple on 5th street", "Street lighting")
    q = c.get("/api/admin/reviews", headers=H("admin1")).json()
    assert [r["id"] for r in q] == [dup["id"]] and q[0]["action"] == "CHECK_DUPLICATE" and q[0]["duplicateOf"]
    assert c.post(f"/api/admin/reviews/{dup['id']}", json={"decision": "reject"}, headers=H("admin1")).status_code == 422
    assert c.post(f"/api/admin/reviews/{dup['id']}", json={"decision": "reject", "note": "Same as the earlier report"}, headers=H("admin1")).json()["status"] == "Rejected"
    assert any("closed it. Reason: Same as the earlier report" in n for n in notes(c, "cit2"))
    assert c.patch(f"/api/admin/reports/{dup['id']}/status", json={"status": "Resolved"}, headers=H("admin1")).status_code == 409
    assert c.patch(f"/api/admin/reports/{dup['id']}/status", json={"status": "Deleted"}, headers=H("admin1")).status_code == 422


def test_reviewers_get_the_report_location(env):
    c, *_ = env
    spot = {"lat": 9.92518, "lng": 78.11987}
    body = {"description": "Live wire hanging from the pole near the bus stop, sparking when it rains.", "category": "Electricity",
            "locality": "Anna Nagar", "coordinates": spot}
    assert c.post("/api/posts", json=body, headers=H("cit1")).status_code == 201
    row = c.get("/api/admin/reviews", headers=H("admin1")).json()[0]
    assert row["coordinates"] == spot
