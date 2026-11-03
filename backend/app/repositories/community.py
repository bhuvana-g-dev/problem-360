"""Firestore access for volunteer groups, events (with registrations) and organization updates."""
from __future__ import annotations

from datetime import datetime, timezone

from google.cloud import firestore

from app.core.constants import EVENTS, GROUPS, UPDATES

now = lambda: datetime.now(timezone.utc)


class CommunityRepository:
    def __init__(self, db):
        self.db = db

    # ---------------- groups ----------------
    def create_group(self, gid: str, data: dict) -> None:
        self.db.collection(GROUPS).document(gid).create({**data, "memberCount": 0, "createdAt": now()})

    def get_group(self, gid: str) -> dict | None:
        s = self.db.collection(GROUPS).document(gid).get()
        return {**s.to_dict(), "id": s.id} if s.exists else None

    def list_groups(self, org_id: str | None = None, locality: str | None = None, limit: int = 200) -> list[dict]:
        q = self.db.collection(GROUPS)
        for f, v in (("orgId", org_id), ("locality", locality)):
            if v:
                q = q.where(f, "==", v)
        return sorted(({**s.to_dict(), "id": s.id} for s in q.limit(limit).stream()), key=lambda g: g["createdAt"], reverse=True)

    def join_group(self, gid: str, uid: str, name: str) -> str:
        gref = self.db.collection(GROUPS).document(gid)
        mref = gref.collection("members").document(uid)

        @firestore.transactional
        def tx(t):
            g = gref.get(transaction=t)
            if not g.exists:
                return "missing"
            if mref.get(transaction=t).exists:
                return "already"
            t.set(mref, {"name": name, "joinedAt": now()})
            t.update(gref, {"memberCount": (g.get("memberCount") or 0) + 1})
            return "ok"

        return tx(self.db.transaction())

    def leave_group(self, gid: str, uid: str) -> bool:
        gref = self.db.collection(GROUPS).document(gid)
        mref = gref.collection("members").document(uid)

        @firestore.transactional
        def tx(t):
            g = gref.get(transaction=t)
            if not g.exists or not mref.get(transaction=t).exists:
                return False
            t.delete(mref)
            t.update(gref, {"memberCount": max(0, (g.get("memberCount") or 0) - 1)})
            return True

        return tx(self.db.transaction())

    def joined_group_ids(self, gids: list[str], uid: str) -> set[str]:
        refs = [self.db.collection(GROUPS).document(g).collection("members").document(uid) for g in gids]
        return {r.reference.parent.parent.id for r in self.db.get_all(refs) if r.exists} if refs else set()

    def list_group_members(self, gid: str) -> list[dict]:
        return [{**s.to_dict(), "uid": s.id} for s in self.db.collection(GROUPS).document(gid).collection("members").stream()]

    # ---------------- events ----------------
    def create_event(self, eid: str, data: dict) -> None:
        self.db.collection(EVENTS).document(eid).create({**data, "registrationCount": 0, "status": "scheduled", "createdAt": now()})

    def get_event(self, eid: str) -> dict | None:
        s = self.db.collection(EVENTS).document(eid).get()
        return {**s.to_dict(), "id": s.id} if s.exists else None

    def list_events(self, org_id: str | None = None, locality: str | None = None, limit: int = 200) -> list[dict]:
        q = self.db.collection(EVENTS)
        for f, v in (("orgId", org_id), ("locality", locality)):
            if v:
                q = q.where(f, "==", v)
        return sorted(({**s.to_dict(), "id": s.id} for s in q.limit(limit).stream()), key=lambda e: e["startsAt"])

    def cancel_event(self, eid: str) -> None:
        self.db.collection(EVENTS).document(eid).update({"status": "cancelled", "cancelledAt": now()})

    def register(self, eid: str, uid: str, name: str) -> str:
        """Capacity-safe registration in one transaction. Returns ok | already | full | cancelled | past | missing."""
        eref = self.db.collection(EVENTS).document(eid)
        rref = eref.collection("registrations").document(uid)

        @firestore.transactional
        def tx(t):
            e = eref.get(transaction=t)
            if not e.exists:
                return "missing"
            d = e.to_dict()
            if d["status"] != "scheduled":
                return "cancelled"
            if d["startsAt"] < now():
                return "past"
            if rref.get(transaction=t).exists:
                return "already"
            if d.get("capacity") is not None and d["registrationCount"] >= d["capacity"]:
                return "full"
            t.set(rref, {"name": name, "registeredAt": now()})
            t.update(eref, {"registrationCount": d["registrationCount"] + 1})
            return "ok"

        return tx(self.db.transaction())

    def unregister(self, eid: str, uid: str) -> bool:
        eref = self.db.collection(EVENTS).document(eid)
        rref = eref.collection("registrations").document(uid)

        @firestore.transactional
        def tx(t):
            e = eref.get(transaction=t)
            if not e.exists or not rref.get(transaction=t).exists:
                return False
            t.delete(rref)
            t.update(eref, {"registrationCount": max(0, e.get("registrationCount") - 1)})
            return True

        return tx(self.db.transaction())

    def registered_event_ids(self, eids: list[str], uid: str) -> set[str]:
        refs = [self.db.collection(EVENTS).document(e).collection("registrations").document(uid) for e in eids]
        return {r.reference.parent.parent.id for r in self.db.get_all(refs) if r.exists} if refs else set()

    def list_registrations(self, eid: str) -> list[dict]:
        rows = [{**s.to_dict(), "uid": s.id} for s in self.db.collection(EVENTS).document(eid).collection("registrations").stream()]
        return sorted(rows, key=lambda r: r["registeredAt"])

    # ---------------- updates ----------------
    def create_update(self, uid: str, data: dict) -> None:
        self.db.collection(UPDATES).document(uid).create({**data, "createdAt": now()})

    def list_updates(self, org_id: str | None = None, limit: int = 50) -> list[dict]:
        q = self.db.collection(UPDATES)
        if org_id:
            q = q.where("orgId", "==", org_id)
        return sorted(({**s.to_dict(), "id": s.id} for s in q.limit(200).stream()), key=lambda u: u["createdAt"], reverse=True)[:limit]
