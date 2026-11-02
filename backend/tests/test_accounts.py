"""Verifies the permission rules without Firebase: fakes stand in for the repository and token check."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core import security
from app.core.constants import Verification
from app.main import app
from app.repositories.accounts import AccountExists
from app.schemas.auth import OrganizationRegistration
from app.services.account_service import AccountService


class FakeRepo:
    def __init__(self):
        self.users, self.orgs, self.members = {}, {}, {}

    def get_user(self, uid): return self.users.get(uid)
    def get_organization(self, oid): return self.orgs.get(oid)
    def get_membership(self, oid, uid): return self.members.get(f"{oid}_{uid}")

    def create_citizen(self, uid, email, name, loc):
        if uid in self.users: raise AccountExists()
        self.users[uid] = {"displayName": name, "accountType": "citizen", "locality": loc}

    def create_organization_with_owner(self, uid, email, contact, org):
        if uid in self.users: raise AccountExists()
        oid = f"org{len(self.orgs) + 1}"
        self.users[uid] = {"displayName": contact, "accountType": "organization", "locality": org["locality"], "organizationId": oid}
        self.orgs[oid] = {**org, "verificationStatus": Verification.PENDING}
        self.members[f"{oid}_{uid}"] = {"role": "owner"}
        return self.users[uid], oid


@pytest.fixture
def env(monkeypatch):
    repo, claims = FakeRepo(), {}
    svc = AccountService(repo, lambda uid, c: claims.update({uid: c}))
    app.dependency_overrides[security.get_service] = lambda: svc
    monkeypatch.setattr(security, "verify_token", lambda t: security.Principal(uid=t, email=f"{t}@x.in"))
    yield TestClient(app), repo, claims
    app.dependency_overrides.clear()


H = lambda uid: {"Authorization": f"Bearer {uid}"}
ORG = {"contactName": "Asha", "orgName": "Madurai Green Trust", "category": "NGO / Non-profit",
       "description": "We organize weekly clean-up drives across the city.", "locality": "Anna Nagar"}


def test_org_registration_is_pending_and_gets_no_verified_privileges(env):
    c, repo, _ = env
    assert c.post("/api/auth/register/organization", json=ORG, headers=H("u1")).status_code == 201
    me = c.get("/api/auth/me", headers=H("u1")).json()
    assert me["accountType"] == "organization" and me["organization"]["verificationStatus"] == "pending"
    assert me["organization"]["memberRole"] == "owner"


def test_unverified_org_blocked_from_management(env):
    c, _, _ = env
    c.post("/api/auth/register/organization", json=ORG, headers=H("u1"))
    account = c.get("/api/auth/me", headers=H("u1")).json()
    with pytest.raises(HTTPException) as e:
        security.require_verified_org_member()(account)
    assert e.value.status_code == 403


def test_verified_org_member_allowed(env):
    c, repo, _ = env
    c.post("/api/auth/register/organization", json=ORG, headers=H("u1"))
    repo.orgs["org1"]["verificationStatus"] = Verification.VERIFIED  # admin action, out of band
    account = c.get("/api/auth/me", headers=H("u1")).json()
    assert security.require_verified_org_member()(account) is account


def test_citizen_cannot_pass_org_guard(env):
    c, _, _ = env
    c.post("/api/auth/register/citizen", json={"displayName": "Ravi", "locality": "KK Nagar"}, headers=H("u2"))
    account = c.get("/api/auth/me", headers=H("u2")).json()
    with pytest.raises(HTTPException) as e:
        security.require_account("organization")(account)
    assert e.value.status_code == 403


def test_cannot_register_twice_or_switch_type(env):
    c, _, _ = env
    assert c.post("/api/auth/register/citizen", json={"displayName": "Ravi", "locality": "KK Nagar"}, headers=H("u2")).status_code == 201
    assert c.post("/api/auth/register/organization", json=ORG, headers=H("u2")).status_code == 409


def test_requires_token_and_validates_input(env):
    c, _, _ = env
    assert c.get("/api/auth/me").status_code == 401
    assert c.post("/api/auth/register/citizen", json={"displayName": "R", "locality": ""}, headers=H("u3")).status_code == 422
    assert c.get("/api/auth/me", headers=H("nobody")).status_code == 404
