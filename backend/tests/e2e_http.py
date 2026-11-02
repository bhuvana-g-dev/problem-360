"""Live-HTTP end-to-end run: a real uvicorn server, real multipart upload, polling exactly like the frontend does.
    python -m tests.e2e_http
Uses the same TEST DOUBLES as the pytest suite for Firestore/Storage/LLM/Decider (see tests/fakes.py), so it proves the
HTTP stack and the report -> agent -> decision -> result workflow, not live Firebase or Bedrock."""
import threading
import time

import httpx
import uvicorn

from agent.engine import StrandsDeciderEngine
from app.core import deps, security
from app.main import app
from app.services.account_service import AccountService
from app.services.media_service import MediaService
from tests.fakes import FakeDecider, InMemoryDecisionRepo, InMemoryPostRepo, InMemoryStorage, ScriptedModel
from tests.test_accounts import FakeRepo

PORT = 8765
posts, decisions, storage = InMemoryPostRepo(), InMemoryDecisionRepo(), InMemoryStorage()
svc = AccountService(FakeRepo(), lambda uid, c: None)
engine = StrandsDeciderEngine(decider=FakeDecider(), model_factory=lambda: ScriptedModel())
app.dependency_overrides.update({security.get_service: lambda: svc, deps.get_post_repo: lambda: posts, deps.get_decision_repo: lambda: decisions,
                                 deps.get_storage: lambda: storage, deps.get_engine: lambda: engine, deps.get_media_service: lambda: MediaService(storage, 5)})
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
    step(c.post("/api/posts", headers={"Authorization": "Bearer org-1"}, json={"description": "abc def ghi", "category": "Other", "locality": "Anna Nagar"}).status_code == 404,
         "unregistered login cannot post (404, no account)")
    server.should_exit = True
    print("E2E OK")


if __name__ == "__main__":
    main()
