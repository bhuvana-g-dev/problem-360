"""Citizen-facing groups, events and org updates, plus the shared output shapers."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status

iso = lambda v: v.isoformat() if hasattr(v, "isoformat") else v


def group_out(g: dict, joined: set[str]) -> dict:
    return {"id": g["id"], "orgId": g["orgId"], "orgName": g["orgName"], "name": g["name"], "description": g["description"], "locality": g["locality"],
            "focus": g.get("focus"), "memberCount": g.get("memberCount", 0), "joinedByMe": g["id"] in joined, "createdAt": iso(g["createdAt"])}


def event_out(e: dict, registered: set[str]) -> dict:
    cap = e.get("capacity")
    return {"id": e["id"], "orgId": e["orgId"], "orgName": e["orgName"], "groupId": e.get("groupId"), "title": e["title"], "description": e["description"],
            "locality": e["locality"], "locationText": e.get("locationText", ""), "startsAt": iso(e["startsAt"]), "endsAt": iso(e.get("endsAt")),
            "capacity": cap, "registrationCount": e.get("registrationCount", 0), "spotsLeft": None if cap is None else max(0, cap - e.get("registrationCount", 0)),
            "status": e["status"], "relatedPostId": e.get("relatedPostId"), "safetyNotes": e.get("safetyNotes", ""), "registeredByMe": e["id"] in registered}


def update_out(u: dict) -> dict:
    return {"id": u["id"], "orgId": u["orgId"], "orgName": u["orgName"], "title": u["title"], "body": u["body"], "createdAt": iso(u["createdAt"])}


class CommunityService:
    def __init__(self, community, posts):
        self.c, self.posts = community, posts   # posts repo is used only for notifications

    def groups(self, account, locality=None) -> list[dict]:
        rows = self.c.list_groups(locality=locality)
        joined = self.c.joined_group_ids([g["id"] for g in rows], account["uid"])
        return [group_out(g, joined) for g in rows]

    def join(self, account, gid: str) -> dict:
        r = self.c.join_group(gid, account["uid"], account["displayName"])
        if r == "missing":
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Group not found.")
        return {"joinedByMe": True}

    def leave(self, account, gid: str) -> dict:
        self.c.leave_group(gid, account["uid"])
        return {"joinedByMe": False}

    def events(self, account, locality=None, upcoming=True) -> list[dict]:
        rows = self.c.list_events(locality=locality)
        if upcoming:
            now = datetime.now(timezone.utc)
            rows = [e for e in rows if e["status"] == "scheduled" and e["startsAt"] >= now]
        reg = self.c.registered_event_ids([e["id"] for e in rows], account["uid"])
        return [event_out(e, reg) for e in rows]

    def register(self, account, eid: str) -> dict:
        r = self.c.register(eid, account["uid"], account["displayName"])
        msg = {"missing": (404, "Event not found."), "cancelled": (409, "This event was cancelled."), "past": (409, "This event has already started."),
               "full": (409, "This event is full.")}.get(r)
        if msg:
            raise HTTPException(*msg)
        if r == "ok":
            e = self.c.get_event(eid)
            self.posts.add_notification(account["uid"], f"You're registered for “{e['title']}” by {e['orgName']} on {e['startsAt']:%d %b %Y, %I:%M %p} UTC. Follow the safety notes: {e['safetyNotes']}", None)
        return {"registeredByMe": True}

    def unregister(self, account, eid: str) -> dict:
        self.c.unregister(eid, account["uid"])
        return {"registeredByMe": False}

    def updates(self) -> list[dict]:
        return [update_out(u) for u in self.c.list_updates()]
