"""Live-HTTP end-to-end run: a real uvicorn server, real multipart upload, polling exactly like the frontend does.
    python -m tests.e2e_http
Uses the same TEST DOUBLES as the pytest suite for Firestore/Storage/LLM/Decider (see tests/fakes.py), so it proves the
HTTP stack and the report -> agent -> decision -> result workflow, not live Firebase or Bedrock."""
import threading
import time
from datetime import datetime, timedelta, timezone

import httpx
import uvicorn

from agent.engine import StrandsDeciderEngine
from app.core import deps, security
from app.main import app
from app.services.account_service import AccountService
from app.services.media_service import MediaService
from tests.fakes import FakeDecider, InMemoryDecisionRepo, InMemoryPostRepo, InMemoryStorage, MemAccounts, MemCommunity, ScriptedModel

PORT = 8765
posts, decisions, storage = InMemoryPostRepo(), InMemoryDecisionRepo(), InMemoryStorage()
accounts, community = MemAccounts(), MemCommunity()
svc = AccountService(accounts, lambda uid, c: None)
engine = StrandsDeciderEngine(decider=FakeDecider(), model_factory=lambda: ScriptedModel())
app.dependency_overrides.update({security.get_service: lambda: svc, deps.get_post_repo: lambda: posts, deps.get_decision_repo: lambda: decisions,
                                 deps.get_storage: lambda: storage, deps.get_community_repo: lambda: community, deps.get_account_repo: lambda: accounts, deps.get_engine: lambda: engine, deps.get_media_service: lambda: MediaService(storage, 5)})
security.verify_token = lambda t: security.Principal(uid=t, email=f"{t}@example.test")


def step(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        raise SystemExit(1)


def main():
    server = uvicorn.Server(uvicorn.Config(app, port=PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    base = f"http://127.0.0.1:{PORT}"
    for _ in range(50):
        try:
            if httpx.get(base + "/api/health").status_code == 200: break
        except httpx.HTTPError: time.sleep(0.1)
    c, H = httpx.Client(base_url=base, timeout=30), {"Authorization": "Bearer citizen-1"}
    step(c.post("/api/auth/register/citizen", json={"displayName": "Ravi Kumar", "locality": "Anna Nagar"}, headers=H).status_code == 201, "citizen registers")
    up = c.post("/api/media", files={"file": ("pole.png", b"\x89PNG\r\n\x1a\n" + b"1" * 500, "image/png")}, headers=H)
    step(up.status_code == 201, f"media uploaded to storage: {up.json().get('mediaPath')}")
    r = c.post("/api/posts", headers=H, json={"description": "Live wire hanging from the pole near the school gate, sparking.", "category": "Electricity",
                                              "locality": "Anna Nagar", "locationText": "School gate", "mediaPath": up.json()["mediaPath"]})
    step(r.status_code == 201 and r.json()["decisionState"] in ("pending", "completed"), f"report created, reference {r.json()['referenceId']}")
    pid = r.json()["id"]
    for _ in range(30):
        post = c.get(f"/api/posts/{pid}", headers=H).json()
        if post["decisionState"] != "pending": break
        time.sleep(0.2)
    step(post["decisionState"] == "completed" and post["decision"]["action"] == "FLAG_URGENT", f"Strands agent decided {post['decision']['action']} (source {post['decision']['source']})")
    trace = c.get(f"/api/posts/{pid}/decision", headers=H).json()
    step({"assess_urgency", "detect_duplicates"} <= {t["tool"] for t in trace["toolRuns"]}, f"tool runs saved: {[t['tool'] for t in trace['toolRuns']]}")
    step(decisions.get_incident(post["referenceId"])["departmentContacted"] is False, "incident created, department NOT contacted")
    step("112" in c.get("/api/notifications", headers=H).json()[0]["text"], "citizen notified with emergency guidance")
    feed = c.get("/api/posts?locality=Anna%20Nagar&q=wire", headers=H).json()
    step(len(feed) == 1 and feed[0]["mediaUrl"], "feed search finds the report with a signed media URL")
    # ---------- Phase 5: organization workflow ----------
    O, A, C2 = {"Authorization": "Bearer org-1"}, {"Authorization": "Bearer admin-1"}, {"Authorization": "Bearer citizen-2"}
    org = {"contactName": "Asha", "orgName": "Madurai Green Trust", "category": "NGO / Non-profit", "description": "We organize weekly clean-up drives across the city.", "locality": "Anna Nagar"}
    step(c.post("/api/auth/register/organization", json=org, headers=O).status_code == 201, "organization registers (starts Pending)")
    step(c.get("/api/org/overview", headers=O).status_code == 403, "pending organization is blocked by the backend")
    c.post("/api/auth/register/citizen", json={"displayName": "Admin", "locality": "Anna Nagar"}, headers=A); accounts.users["admin-1"]["accountType"] = "admin"
    step(c.patch("/api/admin/organizations/org1/verification", json={"status": "verified", "note": "docs checked"}, headers=A).status_code == 200, "admin verifies the organization")
    soon = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    ev = c.post("/api/org/events", headers=O, json={"title": "Plot clean-up", "description": "Bring gloves, bags provided.", "locality": "Anna Nagar", "startsAt": soon, "capacity": 1,
                                                   "safetyNotes": "Gloves and closed shoes. Do not touch sharp waste."})
    step(ev.status_code == 201, "verified organization creates a volunteer event")
    c.post("/api/auth/register/citizen", json={"displayName": "Meena S", "locality": "Anna Nagar"}, headers=C2)
    step(c.post(f"/api/events/{ev.json()['id']}/register", headers=H).status_code == 200, "citizen registers for the event")
    step(c.post(f"/api/events/{ev.json()['id']}/register", headers=C2).status_code == 409, "second citizen is refused: event is full")
    step([r["name"] for r in c.get(f"/api/org/events/{ev.json()['id']}/registrations", headers=O).json()] == ["Ravi Kumar"], "organization sees its registration list")
    r2 = c.post("/api/posts", headers=C2, json={"description": "Litter and dry leaves piled at the vacant plot at our street corner.", "category": "Waste & sanitation", "locality": "Anna Nagar"})
    for _ in range(30):
        p2 = c.get(f"/api/posts/{r2.json()['id']}", headers=C2).json()
        if p2["decisionState"] != "pending": break
        time.sleep(0.2)
    step(p2["decision"]["action"] == "SUGGEST_COMMUNITY_ACTION" and p2["decision"]["communityAction"]["matches"], "community-action report is matched to the real upcoming event")
    step(c.get("/api/org/opportunities", headers=O).json()[0]["postId"] == p2["id"], "organization sees the report under Civic activity")
    server.should_exit = True
    print("E2E OK")


if __name__ == "__main__":
    main()
