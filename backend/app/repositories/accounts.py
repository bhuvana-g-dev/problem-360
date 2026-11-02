"""Firestore access for accounts. All reads/writes of users, organizations and memberships live here."""
from datetime import datetime, timezone

from google.api_core.exceptions import AlreadyExists

from app.core.constants import ORG_MEMBERS, ORGANIZATIONS, USERS, MemberRole, Verification, AccountType


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
        member = {"organizationId": org_ref.id, "uid": uid, "role": MemberRole.OWNER, "createdAt": _now()}
        batch = self.db.batch()
        batch.create(self.db.collection(USERS).document(uid), user)
        batch.set(org_ref, org_doc)
        batch.set(self.db.collection(ORG_MEMBERS).document(f"{org_ref.id}_{uid}"), member)
        try:
            batch.commit()
        except AlreadyExists as e:
            raise AccountExists() from e
        return user, org_ref.id
