"""Organization workspace use-cases. Every method receives the verified-member `account` produced by
require_verified_org_member(); it scopes ALL reads/writes to account["organization"]["id"]."""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.core.constants import MemberRole
from app.services.community_service import event_out, group_out, iso, update_out

INVITE_DAYS = 7


class OrgService:
    def __init__(self, accounts, community, posts):
        self.a, self.c, self.posts = accounts, community, posts

    @staticmethod
    def _org(account):
        return account["organization"]

    # ---- overview ----
    def overview(self, account) -> dict:
        o = self._org(account)["id"]
        now = datetime.now(timezone.utc)
        groups, events = self.c.list_groups(org_id=o), self.c.list_events(org_id=o)
        upcoming = [e for e in events if e["status"] == "scheduled" and e["startsAt"] >= now]
        return {"members": len(self.a.list_members(o)), "groups": len(groups), "groupMembers": sum(g.get("memberCount", 0) for g in groups),
                "upcomingEvents": len(upcoming), "registrations": sum(e.get("registrationCount", 0) for e in events if e["status"] == "scheduled"),
                "updates": len(self.c.list_updates(org_id=o)), "coordinatedActivities": sum(1 for e in events if e.get("relatedPostId")),
                "openOpportunities": len(self.opportunities(account))}

    # ---- groups ----
    def create_group(self, account, body) -> dict:
        o = self._org(account)
        gid = uuid.uuid4().hex
        self.c.create_group(gid, {"orgId": o["id"], "orgName": o["name"], "createdBy": account["uid"], **body.model_dump()})
        return group_out(self.c.get_group(gid), set())

    def groups(self, account) -> list[dict]:
        return [group_out(g, set()) for g in self.c.list_groups(org_id=self._org(account)["id"])]

    # ---- events ----
    def create_event(self, account, body) -> dict:
        o = self._org(account)
        if body.startsAt <= datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Start time must be in the future.")
        if body.groupId:
            g = self.c.get_group(body.groupId)
            if not g or g["orgId"] != o["id"]:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "That group doesn't belong to your organization.")
        if body.relatedPostId:   # only reports the Strands Decider judged safe for community action can be coordinated
            p = self.posts.get(body.relatedPostId)
            if not p or (p.get("decision") or {}).get("action") != "SUGGEST_COMMUNITY_ACTION":
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Events can only be linked to reports marked safe for community action.")
        eid = uuid.uuid4().hex
        self.c.create_event(eid, {"orgId": o["id"], "orgName": o["name"], "createdBy": account["uid"], **body.model_dump()})
        return event_out(self.c.get_event(eid), set())

    def events(self, account) -> list[dict]:
        return [event_out(e, set()) for e in self.c.list_events(org_id=self._org(account)["id"])]

    def _own_event(self, account, eid: str) -> dict:
        e = self.c.get_event(eid)
        if not e or e["orgId"] != self._org(account)["id"]:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found.")   # 404, not 403: don't reveal other orgs' events
        return e

    def cancel_event(self, account, eid: str) -> dict:
        e = self._own_event(account, eid)
        if e["status"] != "scheduled":
            raise HTTPException(status.HTTP_409_CONFLICT, "Event is already cancelled.")
        self.c.cancel_event(eid)
        for r in self.c.list_registrations(eid):
            self.posts.add_notification(r["uid"], f"The event “{e['title']}” by {e['orgName']} was cancelled.", None)
        return event_out(self.c.get_event(eid), set())

    def registrations(self, account, eid: str) -> list[dict]:
        self._own_event(account, eid)
        return [{"uid": r["uid"], "name": r["name"], "registeredAt": iso(r["registeredAt"])} for r in self.c.list_registrations(eid)]

    # ---- updates ----
    def publish_update(self, account, body) -> dict:
        o = self._org(account)
        uid = uuid.uuid4().hex
        self.c.create_update(uid, {"orgId": o["id"], "orgName": o["name"], "authorUid": account["uid"], **body.model_dump()})
        return update_out({**self.c.list_updates(org_id=o["id"])[0]})

    def updates(self, account) -> list[dict]:
        return [update_out(u) for u in self.c.list_updates(org_id=self._org(account)["id"])]

    # ---- civic activity: reports the Decider marked safe for community action ----
    def opportunities(self, account) -> list[dict]:
        rows = self.posts.list_community_opportunities()
        return [{"postId": p["id"], "referenceId": p["referenceId"], "category": p["category"], "locality": p["locality"], "locationText": p.get("locationText", ""),
                 "description": p["description"], "suggestion": ((p.get("decision") or {}).get("communityAction") or {}).get("suggestion"), "createdAt": iso(p["createdAt"])}
                for p in rows]

    # ---- members ----
    def members(self, account) -> list[dict]:
        return [{"uid": m["uid"], "name": m.get("displayName", ""), "email": m.get("email"), "role": m["role"], "joinedAt": iso(m["createdAt"])}
                for m in self.a.list_members(self._org(account)["id"])]

    def invite(self, account, body) -> dict:
        o = self._org(account)
        code = secrets.token_urlsafe(16)
        self.a.create_invite(code, {"organizationId": o["id"], "organizationName": o["name"], "email": body.email.lower(), "role": body.role,
                                    "invitedBy": account["uid"], "expiresAt": datetime.now(timezone.utc) + timedelta(days=INVITE_DAYS)})
        return {"code": code, "email": body.email.lower(), "role": body.role, "expiresInDays": INVITE_DAYS}

    def invites(self, account) -> list[dict]:
        now = datetime.now(timezone.utc)
        return [{"code": i["code"], "email": i["email"], "role": i["role"], "expiresAt": iso(i["expiresAt"])}
                for i in self.a.list_invites(self._org(account)["id"]) if i["expiresAt"] > now]

    def revoke_invite(self, account, code: str) -> dict:
        inv = self.a.get_invite(code)
        if not inv or inv["organizationId"] != self._org(account)["id"]:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Invite not found.")
        self.a.revoke_invite(code)
        return {"ok": True}

    def _target(self, account, uid: str) -> dict:
        m = self.a.get_membership(self._org(account)["id"], uid)
        if not m:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found.")
        if m["role"] == MemberRole.OWNER:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "The organization owner can't be changed or removed.")
        return m

    def set_role(self, account, uid: str, role: str) -> dict:
        self._target(account, uid)
        self.a.set_member_role(self._org(account)["id"], uid, role)
        return {"ok": True}

    def remove_member(self, account, uid: str) -> dict:
        self._target(account, uid)
        self.a.remove_member(self._org(account)["id"], uid)
        return {"ok": True}
