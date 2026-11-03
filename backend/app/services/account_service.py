"""Account use-cases. Key rule: registering as an organization grants NO organization privileges —
the organization starts Pending and only an admin can set it to Verified."""
from datetime import datetime, timezone

from app.core.constants import AccountType
from app.repositories.accounts import AccountExists, AccountRepository


class InviteInvalid(Exception):
    pass


class AccountService:
    def __init__(self, repo: AccountRepository, set_claims):
        self.repo = repo
        self.set_claims = set_claims  # callable(uid, dict) — Firebase custom claims

    def register_citizen(self, uid, email, body) -> None:
        self.repo.create_citizen(uid, email, body.displayName, body.locality)
        self.set_claims(uid, {"accountType": AccountType.CITIZEN})

    def register_organization(self, uid, email, body) -> None:
        org = {"name": body.orgName, "category": body.category, "description": body.description,
               "locality": body.locality, "website": str(body.website) if body.website else None}
        self.repo.create_organization_with_owner(uid, email, body.contactName, org)
        self.set_claims(uid, {"accountType": AccountType.ORGANIZATION})

    def register_org_member(self, uid, email, body) -> None:
        """Join an EXISTING organization through a single-use invite sent to this exact email. Never creates an organization."""
        inv = self.repo.get_invite(body.inviteCode)
        org = self.repo.get_organization(inv["organizationId"]) if inv else None
        if not inv or not org or inv["status"] != "pending" or inv["expiresAt"] < datetime.now(timezone.utc):
            raise InviteInvalid("This invite is invalid, expired or already used.")
        if (email or "").strip().lower() != inv["email"].strip().lower():
            raise InviteInvalid("This invite was sent to a different email address.")
        self.repo.accept_invite(uid, email, body.contactName, inv, org["locality"])
        self.set_claims(uid, {"accountType": AccountType.ORGANIZATION})

    def describe(self, uid, email) -> dict | None:
        user = self.repo.get_user(uid)
        if not user:
            return None
        out = {"uid": uid, "email": email or user.get("email"), "displayName": user["displayName"],
               "accountType": user["accountType"], "locality": user.get("locality"), "organization": None}
        org_id = user.get("organizationId")
        if org_id:
            org, member = self.repo.get_organization(org_id), self.repo.get_membership(org_id, uid)
            if org and member:  # no membership record => no organization access
                out["organization"] = {"id": org_id, "name": org["name"], "category": org["category"], "locality": org["locality"],
                                       "verificationStatus": org["verificationStatus"], "memberRole": member["role"]}
        return out
