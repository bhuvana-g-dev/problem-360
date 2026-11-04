"""Human review queue: closes the loop on every report the agent (or the fail-closed fallback) marked humanReviewRequired.

Rules (code-owned, not the model's):
- Only an admin reviews. A report is reviewed once: approve -> status "Acknowledged", reject -> "Rejected" (reason required).
- After approval an admin may move it between "Acknowledged" and "Resolved".
- Every change is written to the decision's audit trail, mirrored on the incident, and the citizen is notified.
- The app still never claims a department was contacted: no integration exists, so no notification says so.
- `minutesToReview` (report created -> first human decision) is stored, so the queue can report real time-to-human numbers.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.services.decision_service import EMERGENCY_NOTE

NO_CONTACT = "This app has not contacted any department."
PENDING, APPROVED, REJECTED = "pending", "approved", "rejected"
LIFECYCLE = {"Acknowledged", "Resolved"}


def _now():
    return datetime.now(timezone.utc)


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _state(p: dict) -> str:
    return (p.get("review") or {}).get("state", PENDING)


class ReviewService:
    def __init__(self, posts, decisions):
        self.posts, self.decisions = posts, decisions

    # ---------- reading ----------
    def _row(self, p: dict, now: datetime) -> dict:
        d = p.get("decision") or {}
        urg = d.get("urgency") or {}
        r = p.get("review") or {}
        return {
            "id": p["id"], "referenceId": p["referenceId"], "description": p["description"], "category": p["category"],
            "locality": p["locality"], "locationText": p.get("locationText", ""), "coordinates": p.get("coordinates"), "createdAt": _iso(p["createdAt"]),
            "ageMinutes": int((now - p["createdAt"]).total_seconds() // 60), "status": p["status"],
            "action": d.get("action"), "source": d.get("source"), "summary": d.get("summary"),
            "urgent": bool(urg.get("urgent")) or d.get("action") == "FLAG_URGENT", "keywordHits": urg.get("keywordHits") or [],
            "duplicateOf": (d.get("duplicate") or {}).get("referenceId"), "failedClosed": d.get("source") == "fail_closed",
            "review": {"state": r.get("state", PENDING), "byName": r.get("byName"), "at": _iso(r.get("at")), "note": r.get("note"),
                       "minutesToReview": r.get("minutesToReview")},
        }

    def queue(self, state: str = PENDING) -> list[dict]:
        now = _now()
        rows = [p for p in self.posts.list_review_queue() if (_state(p) == PENDING) == (state == PENDING)]
        if state == PENDING:   # danger first, then reports the agent could not review, then oldest first
            rows.sort(key=lambda p: (not self._row(p, now)["urgent"], (p.get("decision") or {}).get("source") != "fail_closed", p["createdAt"]))
        else:
            rows.sort(key=lambda p: (p.get("review") or {}).get("at") or p["createdAt"], reverse=True)
        return [self._row(p, now) for p in rows]

    def stats(self) -> dict:
        now = _now()
        rows = [self._row(p, now) for p in self.posts.list_review_queue()]
        pending = [r for r in rows if r["review"]["state"] == PENDING]
        done = [r for r in rows if r["review"]["minutesToReview"] is not None]
        med = lambda xs: round(statistics.median(xs), 1) if xs else None
        return {"pending": len(pending), "urgentPending": sum(r["urgent"] for r in pending),
                "oldestPendingMinutes": max((r["ageMinutes"] for r in pending), default=None),
                "reviewed": len(done), "medianMinutesToReview": med([r["review"]["minutesToReview"] for r in done]),
                "medianMinutesToReviewUrgent": med([r["review"]["minutesToReview"] for r in done if r["urgent"]]),
                "resolved": sum(r["status"] == "Resolved" for r in rows)}

    # ---------- acting ----------
    def _post(self, post_id: str) -> dict:
        p = self.posts.get(post_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found.")
        if not (p.get("decision") or {}).get("humanReviewRequired"):
            raise HTTPException(status.HTTP_409_CONFLICT, "This report is not waiting for human review.")
        return p

    def _mirror(self, p: dict, fields: dict) -> None:
        if (p.get("decision") or {}).get("incident") or self.decisions.get_incident(p["referenceId"]):
            self.decisions.update_incident(p["referenceId"], fields)

    def decide(self, admin: dict, post_id: str, decision: str, note: str) -> dict:
        p = self._post(post_id)
        if _state(p) != PENDING:
            raise HTTPException(status.HTTP_409_CONFLICT, "This report has already been reviewed.")
        note = (note or "").strip()
        if decision == "reject" and len(note) < 3:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Give the citizen a short reason for closing the report.")
        now = _now()
        minutes = round((now - p["createdAt"]).total_seconds() / 60, 1)
        state, new_status = (APPROVED, "Acknowledged") if decision == "approve" else (REJECTED, "Rejected")
        review = {"state": state, "by": admin["uid"], "byName": admin.get("displayName"), "at": now, "note": note, "minutesToReview": minutes}
        self.posts.update_review(post_id, {"review": review, "status": new_status})
        self.decisions.audit(post_id, "human_review", {"state": state, "by": admin["uid"], "note": note, "minutesToReview": minutes})
        self._mirror(p, {"humanApproved": state == APPROVED, "reviewedBy": admin["uid"], "reviewedAt": now, "status": new_status})
        ref, urgent = p["referenceId"], (p.get("decision") or {}).get("action") == "FLAG_URGENT"
        if state == APPROVED:
            text = f"A Problem 360 reviewer has checked report {ref} and acknowledged it." + (f" {EMERGENCY_NOTE}" if urgent else "")
        else:
            text = f"A Problem 360 reviewer has checked report {ref} and closed it. Reason: {note}"
        self.posts.add_notification(p["authorUid"], f"{text}{' Note: ' + note if note and state == APPROVED else ''} {NO_CONTACT}", post_id)
        return {"id": post_id, "status": new_status, "review": {"state": state, "minutesToReview": minutes}}

    def set_status(self, admin: dict, post_id: str, new_status: str, note: str) -> dict:
        p = self._post(post_id)
        if _state(p) != APPROVED:
            raise HTTPException(status.HTTP_409_CONFLICT, "Approve the report before changing its status.")
        if new_status not in LIFECYCLE:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Status must be Acknowledged or Resolved.")
        if p["status"] == new_status:
            return {"id": post_id, "status": new_status}
        now, note = _now(), (note or "").strip()
        self.posts.update_review(post_id, {"status": new_status, **({"resolvedAt": now} if new_status == "Resolved" else {"resolvedAt": None})})
        self.decisions.audit(post_id, "status_changed", {"from": p["status"], "to": new_status, "by": admin["uid"], "note": note})
        self._mirror(p, {"status": new_status, **({"resolvedAt": now} if new_status == "Resolved" else {})})
        verb = "marked resolved" if new_status == "Resolved" else "reopened and is acknowledged again"
        self.posts.add_notification(p["authorUid"], f"Report {p['referenceId']} was {verb} by a Problem 360 reviewer."
                                    + (f" Note: {note}" if note else ""), post_id)
        return {"id": post_id, "status": new_status}
