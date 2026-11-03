"""Phase 5 through the HTTP API with in-memory test doubles (see tests/fakes.py): org workspace, volunteer groups, events,
registrations, updates, members/invites, admin verification, and the report -> community-action -> event link."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from agent.engine import StrandsDeciderEngine
from app.core import deps, security
from app.main import app
from app.services.account_service import AccountService
from tests.fakes import (FakeDecider, InMemoryDecisionRepo, InMemoryPostRepo, InMemoryStorage, MemAccounts, MemCommunity, ScriptedModel)

H = lambda uid: {"Authorization": f"Bearer {uid}"}
ORG = {"contactName": "Asha", "orgName": "Madurai Green Trust", "category": "NGO / Non-profit",
       "description": "We organize weekly clean-up drives across the city.", "locality": "Anna Nagar"}
when = lambda days=3, hours=0: (datetime.now(timezone.utc) + timedelta(days=days, hours=hours)).isoformat()
EVENT = {"title": "Saturday park clean-up", "description": "Bring gloves; we provide bags and water.", "locality": "Anna Nagar",
         "startsAt": None, "capacity": 2, "safetyNotes": "Wear gloves and closed shoes. Do not touch sharp or medical waste."}


@pytest.fixture
def env(monkeypatch):
    accounts, community, posts = MemAccounts(), MemCommunity(), InMemoryPostRepo()
    decisions, storage = InMemoryDecisionRepo(), InMemoryStorage()
    engine = StrandsDeciderEngine(decider=FakeDecider(), model_factory=lambda: ScriptedModel())
    svc = AccountService(accounts, lambda uid, c: None)
    app.dependency_overrides.update({security.get_service: lambda: svc, deps.get_account_repo: lambda: accounts, deps.get_community_repo: lambda: community,
        deps.get_post_repo: lambda: posts, deps.get_decision_repo: lambda: decisions, deps.get_storage: lambda: storage, deps.get_engine: lambda: engine})
    monkeypatch.setattr(security, "verify_token", lambda t: security.Principal(uid=t, email=f"{t}@x.in"))
    c = TestClient(app)
    for uid in ("cit1", "cit2", "cit3"):
        assert c.post("/api/auth/register/citizen", json={"displayName": f"Citizen {uid}", "locality": "Anna Nagar"}, headers=H(uid)).status_code == 201
    assert c.post("/api/auth/register/organization", json=ORG, headers=H("owner1")).status_code == 201
    assert c.post("/api/auth/register/organization", json={**ORG, "orgName": "Other Trust"}, headers=H("owner2")).status_code == 201
    # an admin exists only because someone promoted an existing account (scripts/make_admin.py)
    c.post("/api/auth/register/citizen", json={"displayName": "Admin", "locality": "Anna Nagar"}, headers=H("admin1"))
    accounts.users["admin1"]["accountType"] = "admin"
    yield c, accounts, community, posts
    app.dependency_overrides.clear()


def verify(c, org_id, uid="admin1"):
    return c.patch(f"/api/admin/organizations/{org_id}/verification", json={"status": "verified", "note": "documents checked"}, headers=H(uid))


def test_unverified_org_is_blocked_until_an_admin_verifies(env):
    c, accounts, *_ = env
    assert c.get("/api/org/overview", headers=H("owner1")).status_code == 403
    assert c.post("/api/org/groups", json={"name": "Clean Anna Nagar", "description": "Weekly clean-up volunteers", "locality": "Anna Nagar"}, headers=H("owner1")).status_code == 403
    assert verify(c, "org1", "cit1").status_code == 403                          # citizen cannot verify
    assert verify(c, "org1", "owner1").status_code == 403                        # org cannot verify itself
    assert verify(c, "org1").status_code == 200
    assert c.get("/api/org/overview", headers=H("owner1")).status_code == 200
    assert accounts.audit[0]["by"] == "admin1" and accounts.audit[0]["status"] == "verified"
    assert c.patch("/api/admin/organizations/org1/verification", json={"status": "rejected"}, headers=H("admin1")).status_code == 200
    assert c.get("/api/org/overview", headers=H("owner1")).status_code == 403   # rejection removes access immediately
    assert c.get("/api/admin/organizations?status=pending", headers=H("admin1")).json()[0]["name"] == "Other Trust"


def test_groups_events_registrations_and_capacity(env):
    c, *_ = env
    verify(c, "org1")
    g = c.post("/api/org/groups", json={"name": "Clean Anna Nagar", "description": "Weekly clean-up volunteers", "locality": "Anna Nagar", "focus": "Waste & sanitation"}, headers=H("owner1"))
    assert g.status_code == 201 and g.json()["orgName"] == "Madurai Green Trust"
    gid = g.json()["id"]
    assert c.post(f"/api/groups/{gid}/join", headers=H("cit1")).json() == {"joinedByMe": True}
    assert c.post(f"/api/groups/{gid}/join", headers=H("owner1")).status_code == 403   # orgs can't join as citizens
    listed = c.get("/api/groups?locality=Anna%20Nagar", headers=H("cit1")).json()
    assert listed[0]["memberCount"] == 1 and listed[0]["joinedByMe"] is True
    assert c.post("/api/groups/" + gid + "/leave", headers=H("cit1")).json() == {"joinedByMe": False}

    ev = c.post("/api/org/events", json={**EVENT, "startsAt": when(), "groupId": gid}, headers=H("owner1"))
    assert ev.status_code == 201 and ev.json()["spotsLeft"] == 2
    eid = ev.json()["id"]
    assert c.post(f"/api/events/{eid}/register", headers=H("cit1")).status_code == 200
    assert c.post(f"/api/events/{eid}/register", headers=H("cit1")).status_code == 200          # idempotent
    assert c.post(f"/api/events/{eid}/register", headers=H("cit2")).status_code == 200
    full = c.post(f"/api/events/{eid}/register", headers=H("cit3"))
    assert full.status_code == 409 and "full" in full.json()["detail"]                          # capacity enforced
    mine = {e["id"]: e for e in c.get("/api/events", headers=H("cit1")).json()}
    assert mine[eid]["registeredByMe"] and mine[eid]["spotsLeft"] == 0
    regs = c.get(f"/api/org/events/{eid}/registrations", headers=H("owner1")).json()
    assert {r["name"] for r in regs} == {"Citizen cit1", "Citizen cit2"}
    c.post(f"/api/events/{eid}/unregister", headers=H("cit1"))
    assert c.post(f"/api/events/{eid}/register", headers=H("cit3")).status_code == 200          # freed seat
    assert "safety notes" in c.get("/api/notifications", headers=H("cit3")).json()[0]["text"].lower()


def test_org_isolation_cancellation_and_validation(env):
    c, *_ = env
    verify(c, "org1"); verify(c, "org2")
    eid = c.post("/api/org/events", json={**EVENT, "startsAt": when()}, headers=H("owner1")).json()["id"]
    c.post(f"/api/events/{eid}/register", headers=H("cit1"))
    assert c.get(f"/api/org/events/{eid}/registrations", headers=H("owner2")).status_code == 404   # other org can't see it
    assert c.post(f"/api/org/events/{eid}/cancel", headers=H("owner2")).status_code == 404
    assert c.post(f"/api/org/events/{eid}/cancel", headers=H("owner1")).json()["status"] == "cancelled"
    assert "cancelled" in c.get("/api/notifications", headers=H("cit1")).json()[0]["text"]
    assert c.post(f"/api/events/{eid}/register", headers=H("cit2")).status_code == 409
    assert c.post("/api/org/events", json={**EVENT, "startsAt": when(-1)}, headers=H("owner1")).status_code == 422          # past
    assert c.post("/api/org/events", json={**EVENT, "startsAt": when(), "endsAt": when(2)}, headers=H("owner1")).status_code == 422
    assert c.post("/api/org/events", json={**EVENT, "startsAt": when(), "safetyNotes": "x"}, headers=H("owner1")).status_code == 422  # safety notes required
    assert c.post("/api/org/events", json={**EVENT, "startsAt": "2030-01-01T10:00:00"}, headers=H("owner1")).status_code == 422       # no timezone
    other_group = c.post("/api/org/groups", json={"name": "Other group", "description": "Another org's group", "locality": "Anna Nagar"}, headers=H("owner2")).json()["id"]
    assert c.post("/api/org/events", json={**EVENT, "startsAt": when(), "groupId": other_group}, headers=H("owner1")).status_code == 400


def test_member_invites_and_role_matrix(env):
    c, accounts, *_ = env
    verify(c, "org1")
    inv = c.post("/api/org/invites", json={"email": "Volunteer@x.in", "role": "member"}, headers=H("owner1")).json()
    code = inv["code"]
    assert c.post("/api/auth/register/organization-member", json={"contactName": "Vimal", "inviteCode": code}, headers=H("someone-else")).status_code == 400  # wrong email
    assert c.post("/api/auth/register/organization-member", json={"contactName": "Vimal", "inviteCode": "nope-nope-nope"}, headers=H("volunteer")).status_code == 400
    # the invited email is "volunteer@x.in": the test token maps uid -> uid@x.in, so uid "volunteer" matches case-insensitively
    assert c.post("/api/auth/register/organization-member", json={"contactName": "Vimal", "inviteCode": code}, headers=H("volunteer")).status_code == 201
    assert c.post("/api/auth/register/organization-member", json={"contactName": "Vimal", "inviteCode": code}, headers=H("volunteer")).status_code in (400, 409)   # single use
    me = c.get("/api/auth/me", headers=H("volunteer")).json()
    assert me["organization"]["id"] == "org1" and me["organization"]["memberRole"] == "member"   # joined, did NOT create an org
    assert c.get("/api/org/overview", headers=H("volunteer")).status_code == 200                 # members can view
    assert c.post("/api/org/updates", json={"title": "Hello", "body": "A members cannot publish."}, headers=H("volunteer")).status_code == 403
    assert c.post("/api/org/invites", json={"email": "z@x.in", "role": "member"}, headers=H("volunteer")).status_code == 403
    assert c.patch("/api/org/members/volunteer", json={"role": "admin"}, headers=H("volunteer")).status_code == 403
    assert c.patch("/api/org/members/volunteer", json={"role": "admin"}, headers=H("owner1")).status_code == 200
    assert c.post("/api/org/updates", json={"title": "Weekend drive", "body": "Join us this Saturday at the park."}, headers=H("volunteer")).status_code == 201   # now admin
    assert c.patch("/api/org/members/owner1", json={"role": "member"}, headers=H("volunteer")).status_code == 403      # admin can't change roles; owner is protected
    assert c.delete("/api/org/members/owner1", headers=H("owner1")).status_code == 403
    assert {m["role"] for m in c.get("/api/org/members", headers=H("owner1")).json()} == {"owner", "admin"}
    assert c.delete("/api/org/members/volunteer", headers=H("owner1")).status_code == 200
    assert c.get("/api/auth/me", headers=H("volunteer")).json()["organization"] is None
    assert c.get("/api/org/overview", headers=H("volunteer")).status_code == 403                 # removed members lose access at once
    assert c.get("/api/updates", headers=H("cit1")).json()[0]["title"] == "Weekend drive"       # citizens see published updates


def test_report_to_community_action_to_event_workflow(env):
    c, accounts, community, posts = env
    verify(c, "org1")
    # the org organises a verified-safe event first, so the agent can attach it to the suggestion
    eid = c.post("/api/org/events", json={**EVENT, "startsAt": when(), "title": "Vacant plot clean-up"}, headers=H("owner1")).json()["id"]
    r = c.post("/api/posts", headers=H("cit1"), json={"description": "Litter and dry leaves piled at the vacant plot at our street corner.", "category": "Waste & sanitation", "locality": "Anna Nagar"})
    post = c.get(f"/api/posts/{r.json()['id']}", headers=H("cit1")).json()
    assert post["decision"]["action"] == "SUGGEST_COMMUNITY_ACTION"                              # real agent loop, test doubles for LLM/Decider
    assert post["decision"]["communityAction"]["matches"][0]["title"] == "Vacant plot clean-up"  # found by code from real events
    opp = c.get("/api/org/opportunities", headers=H("owner1")).json()
    assert opp[0]["postId"] == post["id"] and opp[0]["suggestion"]
    linked = c.post("/api/org/events", json={**EVENT, "startsAt": when(4), "title": "Plot drive", "relatedPostId": post["id"]}, headers=H("owner1"))
    assert linked.status_code == 201 and linked.json()["relatedPostId"] == post["id"]
    assert c.get("/api/org/overview", headers=H("owner1")).json()["coordinatedActivities"] == 1
    # an urgent / non-community report can NOT be turned into a volunteer event
    urgent = c.post("/api/posts", headers=H("cit2"), json={"description": "Live wire hanging near the school gate, sparking.", "category": "Electricity", "locality": "Anna Nagar"}).json()
    bad = c.post("/api/org/events", json={**EVENT, "startsAt": when(5), "relatedPostId": urgent["id"]}, headers=H("owner1"))
    assert bad.status_code == 400
    assert c.get("/api/org/opportunities", headers=H("owner1")).json()[0]["postId"] == post["id"]


def test_trending_uses_real_reports(env):
    c, *_ = env
    for t in ("Big pothole near the signal, bikes slipping.", "Another pothole outside the school gate here."):
        c.post("/api/posts", headers=H("cit1"), json={"description": t, "category": "Roads & potholes", "locality": "Anna Nagar"})
    c.post("/api/posts", headers=H("cit2"), json={"description": "Garbage not collected for three days.", "category": "Waste & sanitation", "locality": "Anna Nagar"})
    t = c.get("/api/trending?locality=Anna%20Nagar", headers=H("cit1")).json()
    assert t[0] == {"category": "Roads & potholes", "reports": 2, "likes": 0}
