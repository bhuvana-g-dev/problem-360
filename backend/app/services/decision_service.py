"""Runs the Strands Decider engine on a saved report and applies the result.

HONESTY RULES (enforced here):
- If the engine raises for ANY reason, the run is stored as state="failed", source="fail_closed", action=ESCALATE_FOR_HUMAN_REVIEW.
  Nothing is ever presented as an agent decision when the agent did not complete.
- The structured incident is created by this code AFTER the decision (the model never writes data).
- `departmentContacted` is always False: no department integration exists, so none is ever claimed."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.constants import AccountType

log = logging.getLogger("problem360.decision")
EMERGENCY_NOTE = "If anyone is in immediate danger, call 112 now (police, fire, ambulance) or 108 for an ambulance."  # same as agent/knowledge.py
NO_INCIDENT = {"CHECK_DUPLICATE", "REQUEST_MORE_INFORMATION"}


def _trim(v, n=2000):
    s = str(v)
    return s if len(s) <= n else s[:n] + "…"


def notification_text(d: dict, ref: str) -> str:
    a, dept = d["action"], (d.get("department") or {}).get("name")
    if d["source"] == "fail_closed":
        return f"Report {ref} is saved, but the automatic review could not run, so it is marked for human review. {EMERGENCY_NOTE}"
    if a == "FLAG_URGENT":
        return f"Report {ref} was flagged as urgent and marked for human review. {EMERGENCY_NOTE}"
    if a == "CHECK_DUPLICATE":
        return f"Report {ref} looks similar to an existing report ({d['duplicate']['referenceId']}) and is marked for review."
    if a == "REQUEST_MORE_INFORMATION":
        return f"Report {ref} needs more details: " + " ".join(d.get("questions") or ["Please add what is wrong and where."])
    if a == "ROUTE_TO_DEPARTMENT":
        return f"Report {ref}: recommended department is {dept}. This is a recommendation only; no department has been contacted."
    if a == "SUGGEST_COMMUNITY_ACTION":
        return f"Report {ref}: neighbours may be able to help. {d['communityAction']['suggestion']} No department has been contacted."
    return f"Report {ref} is recorded and marked for human review. No department has been contacted."


class DecisionService:
    def __init__(self, posts, decisions, engine, community=None):
        self.posts, self.decisions, self.engine, self.community = posts, decisions, engine, community

    def _nearby(self, locality: str, days: int, exclude_id: str) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return [{"id": p["id"], "referenceId": p["referenceId"], "category": p["category"], "locality": p["locality"], "description": p["description"],
                 "locationText": p.get("locationText", ""), "coordinates": p.get("coordinates"), "status": p["status"],
                 "createdAt": p["createdAt"].isoformat()} for p in self.posts.recent_for_duplicates(locality, since, exclude_id)]

    def run(self, post_id: str) -> None:
        """Background task. Never raises: every outcome is stored."""
        post = self.posts.get(post_id)
        if not post:
            return
        ref = post["referenceId"]
        self.decisions.audit(post_id, "decision_started", {"referenceId": ref})
        report = {"id": post_id, "description": post["description"], "category": post["category"], "locality": post["locality"],
                  "locationText": post.get("locationText", ""), "coordinates": post.get("coordinates")}
        try:
            d = self.engine.decide(report, self._nearby)
            d["state"], d["error"] = "completed", None
        except Exception as e:  # fail closed, loudly
            log.exception("decision failed for %s", post_id)
            d = {"action": "ESCALATE_FOR_HUMAN_REVIEW", "source": "fail_closed", "state": "failed", "error": _trim(f"{type(e).__name__}: {e}", 300),
                 "summary": "The automatic review could not run, so this report is marked for human review. Nothing has been sent to any department. " + EMERGENCY_NOTE,
                 "reasoning": "Strands agent did not complete.", "questions": [], "urgency": None, "department": None, "duplicate": None,
                 "communityAction": None, "humanReviewRequired": True, "overrides": [], "model": None, "deciderUsed": False, "externalContact": False, "toolRuns": []}
        now = datetime.now(timezone.utc)
        if d["state"] == "completed" and d["action"] == "SUGGEST_COMMUNITY_ACTION" and self.community:   # real upcoming events, found by code
            try:
                soon = [e for e in self.community.list_events(locality=post["locality"]) if e["status"] == "scheduled" and e["startsAt"] >= now][:3]
                d["communityAction"]["matches"] = [{"id": e["id"], "title": e["title"], "orgName": e["orgName"], "startsAt": e["startsAt"].isoformat()} for e in soon]
            except Exception:
                log.exception("could not look up community events")
        for r in d.get("toolRuns", []):
            self.decisions.audit(post_id, "tool_run", {"tool": r["tool"], "invokedBy": r["invokedBy"], "ms": r["ms"], "output": _trim(r["output"])})
        for o in d.get("overrides", []):
            self.decisions.audit(post_id, "override", o)
        incident_ref = None
        try:
            if d["state"] == "completed" and d["action"] not in NO_INCIDENT:
                incident_ref = ref
                self.decisions.create_incident(ref, {
                    "postId": post_id, "category": post["category"], "locality": post["locality"], "status": "Submitted", "action": d["action"],
                    "urgent": bool((d["urgency"] or {}).get("urgent")), "recommendedDepartment": (d.get("department") or {}).get("id"),
                    "humanApprovalRequired": True, "departmentContacted": False, "createdBy": "system:strands-decider"})
                self.decisions.audit(post_id, "incident_created", {"incident": ref, "departmentContacted": False})
            d["incident"] = incident_ref
            d["createdAt"] = d["completedAt"] = now
            self.decisions.save(post_id, d)
            public = {k: v for k, v in d.items() if k not in ("toolRuns", "createdAt", "completedAt", "error")}
            public["state"] = d["state"]
            self.posts.set_decision(post_id, d["state"], public)
            self.posts.add_notification(post["authorUid"], notification_text(d, ref), post_id)
            self.decisions.audit(post_id, "decision_" + d["state"], {"action": d["action"], "source": d["source"]})
        except Exception:
            log.exception("could not store decision for %s", post_id)
            self.posts.set_decision(post_id, "failed", {"action": "ESCALATE_FOR_HUMAN_REVIEW", "source": "fail_closed", "state": "failed",
                                                        "summary": "The review result could not be saved. " + EMERGENCY_NOTE, "humanReviewRequired": True, "externalContact": False})

    def retry(self, account: dict, post_id: str):
        post = self.posts.get(post_id)
        if not post:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        if account["accountType"] != AccountType.ADMIN and post["authorUid"] != account["uid"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can retry the review.")
        if post.get("decisionState") != "failed":
            raise HTTPException(status.HTTP_409_CONFLICT, "Only failed reviews can be retried.")
        self.posts.set_decision(post_id, "pending", None)
        return post_id

    def trace(self, account: dict, post_id: str) -> dict:
        post = self.posts.get(post_id)
        if not post:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        if account["accountType"] != AccountType.ADMIN and post["authorUid"] != account["uid"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the author can see the decision trace.")
        d = self.decisions.get(post_id)
        if not d:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "No decision yet.")
        d = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in d.items()}
        d["audit"] = [{"type": a["type"], "detail": a["detail"], "at": a["at"].isoformat()} for a in self.decisions.list_audit(post_id)]
        return d
