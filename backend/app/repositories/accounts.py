"""Firestore access for accounts. All reads/writes of users, organizations and memberships live here."""
from datetime import datetime, timezone

from google.api_core.exceptions import AlreadyExists

from app.core.constants import ADMIN_AUDIT, INVITES, ORG_MEMBERS, ORGANIZATIONS, USERS, MemberRole, Verification, AccountType


class AccountExists(Exception):
    pass


def _now():
    return datetime.now(timezone.utc)


class AccountRepository:
    def __init__(self, db):
        self.db = db

    def get_user(self, uid: str) -> dict | None:
        snap = self.db.collection(USERS).document(uid).get()
        return snap.to_dict() if snap.exists else None

    def get_organization(self, org_id: str) -> dict | None:
        snap = self.db.collection(ORGANIZATIONS).document(org_id).get()
        return {**snap.to_dict(), "id": snap.id} if snap.exists else None

    def get_membership(self, org_id: str, uid: str) -> dict | None:
        snap = self.db.collection(ORG_MEMBERS).document(f"{org_id}_{uid}").get()
        return snap.to_dict() if snap.exists else None

    def create_citizen(self, uid: str, email: str | None, display_name: str, locality: str) -> dict:
        data = {"uid": uid, "email": email, "displayName": display_name, "accountType": AccountType.CITIZEN,
                "locality": locality, "status": "active", "createdAt": _now()}
        try:
            self.db.collection(USERS).document(uid).create(data)  # create() fails if it already exists
        except AlreadyExists as e:
            raise AccountExists() from e
        return data

    def create_organization_with_owner(self, uid: str, email: str | None, contact_name: str, org: dict) -> tuple[dict, str]:
        """Atomically creates user + organization (always Pending) + owner membership."""
        org_ref = self.db.collection(ORGANIZATIONS).document()
        user = {"uid": uid, "email": email, "displayName": contact_name, "accountType": AccountType.ORGANIZATION,
                "locality": org["locality"], "organizationId": org_ref.id, "status": "active", "createdAt": _now()}
        org_doc = {**org, "verificationStatus": Verification.PENDING, "createdBy": uid, "createdAt": _now()}
        member = {"organizationId": org_ref.id, "uid": uid, "role": MemberRole.OWNER, "displayName": contact_name, "email": email, "createdAt": _now()}
        batch = self.db.batch()
        batch.create(self.db.collection(USERS).document(uid), user)
        batch.set(org_ref, org_doc)
        batch.set(self.db.collection(ORG_MEMBERS).document(f"{org_ref.id}_{uid}"), member)
        try:
            batch.commit()
        except AlreadyExists as e:
            raise AccountExists() from e
        return user, org_ref.id

    # ---- members, invites, verification (Phase 5) ----
    def list_members(self, org_id: str) -> list[dict]:
        rows = [s.to_dict() for s in self.db.collection(ORG_MEMBERS).where("organizationId", "==", org_id).stream()]
        return sorted(rows, key=lambda m: m["createdAt"])

    def set_member_role(self, org_id: str, uid: str, role: str) -> None:
        self.db.collection(ORG_MEMBERS).document(f"{org_id}_{uid}").update({"role": role})

    def remove_member(self, org_id: str, uid: str) -> None:
        batch = self.db.batch()
        batch.delete(self.db.collection(ORG_MEMBERS).document(f"{org_id}_{uid}"))
        batch.update(self.db.collection(USERS).document(uid), {"organizationId": None, "status": "removed"})
        batch.commit()

    def create_invite(self, code: str, data: dict) -> None:
        self.db.collection(INVITES).document(code).create({**data, "status": "pending", "createdAt": _now()})

    def get_invite(self, code: str) -> dict | None:
        snap = self.db.collection(INVITES).document(code).get()
        return {**snap.to_dict(), "code": snap.id} if snap.exists else None

    def list_invites(self, org_id: str) -> list[dict]:
        rows = [{**s.to_dict(), "code": s.id} for s in self.db.collection(INVITES).where("organizationId", "==", org_id).stream()]
        return sorted([r for r in rows if r["status"] == "pending"], key=lambda r: r["createdAt"], reverse=True)

    def revoke_invite(self, code: str) -> None:
        self.db.collection(INVITES).document(code).update({"status": "revoked"})

    def accept_invite(self, uid: str, email: str | None, contact_name: str, invite: dict, locality: str) -> None:
        """Atomically creates the member's account + membership and marks the invite used."""
        org_id = invite["organizationId"]
        user = {"uid": uid, "email": email, "displayName": contact_name, "accountType": AccountType.ORGANIZATION, "locality": locality,
                "organizationId": org_id, "status": "active", "createdAt": _now()}
        member = {"organizationId": org_id, "uid": uid, "role": invite["role"], "displayName": contact_name, "email": email, "createdAt": _now()}
        batch = self.db.batch()
        batch.create(self.db.collection(USERS).document(uid), user)
        batch.set(self.db.collection(ORG_MEMBERS).document(f"{org_id}_{uid}"), member)
        batch.update(self.db.collection(INVITES).document(invite["code"]), {"status": "accepted", "acceptedBy": uid})
        try:
            batch.commit()
        except AlreadyExists as e:
            raise AccountExists() from e

    def list_organizations(self, status: str | None = None) -> list[dict]:
        q = self.db.collection(ORGANIZATIONS)
        if status:
            q = q.where("verificationStatus", "==", status)
        rows = [{**s.to_dict(), "id": s.id} for s in q.limit(300).stream()]
        return sorted(rows, key=lambda o: o["createdAt"], reverse=True)

    def set_verification(self, org_id: str, status: str, by_uid: str, note: str) -> None:
        batch = self.db.batch()
        batch.update(self.db.collection(ORGANIZATIONS).document(org_id), {"verificationStatus": status, "verifiedBy": by_uid, "verificationNote": note, "verificationUpdatedAt": _now()})
        batch.create(self.db.collection(ADMIN_AUDIT).document(), {"type": "organization_verification", "organizationId": org_id, "status": status, "by": by_uid, "note": note, "at": _now()})
        batch.commit()
