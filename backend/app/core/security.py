"""Authentication + authorization dependencies.

Firebase verifies *who* the caller is. Firestore (not the token's claims) decides *what* they are,
so revoking or changing a role takes effect immediately. Every protected route must use one of these."""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth as fb_auth

from app.core.constants import AccountType, MemberRole, Verification
from app.core.firebase import get_app, get_db
from app.repositories.accounts import AccountRepository
from app.services.account_service import AccountService

bearer = HTTPBearer(auto_error=False)


@dataclass
class Principal:
    uid: str
    email: str | None


def verify_token(token: str) -> Principal:
    decoded = fb_auth.verify_id_token(token, app=get_app())
    return Principal(uid=decoded["uid"], email=decoded.get("email"))


def current_principal(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required.")
    try:
        return verify_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session is invalid or expired. Please sign in again.")


def get_service() -> AccountService:
    return AccountService(AccountRepository(get_db()), lambda uid, c: fb_auth.set_custom_user_claims(uid, c, app=get_app()))


def current_account(p: Principal = Depends(current_principal), svc: AccountService = Depends(get_service)) -> dict:
    account = svc.describe(p.uid, p.email)
    if account is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No Problem 360 account for this login.")
    return account


def require_account(*types: str):
    def dep(account: dict = Depends(current_account)) -> dict:
        if account["accountType"] not in types:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This action isn't available for your account type.")
        return account
    return dep


def require_verified_org_member(*roles: str):
    """For organization management endpoints (Phase 5): org account + Verified org + membership role."""
    allowed = roles or (MemberRole.OWNER, MemberRole.ADMIN, MemberRole.MEMBER)

    def dep(account: dict = Depends(require_account(AccountType.ORGANIZATION))) -> dict:
        org = account.get("organization")
        if not org or org["verificationStatus"] != Verification.VERIFIED:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your organization must be verified first.")
        if org["memberRole"] not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your organization role can't do this.")
        return account
    return dep
