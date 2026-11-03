from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import Principal, current_account, current_principal, get_service
from app.repositories.accounts import AccountExists
from app.schemas.auth import AccountOut, CitizenRegistration, OrganizationRegistration, OrgMemberRegistration
from app.services.account_service import AccountService, InviteInvalid

router = APIRouter(prefix="/api/auth", tags=["auth"])
_EXISTS = HTTPException(status.HTTP_409_CONFLICT, "An account already exists for this login.")


@router.post("/register/citizen", status_code=status.HTTP_201_CREATED)
def register_citizen(body: CitizenRegistration, p: Principal = Depends(current_principal), svc: AccountService = Depends(get_service)):
    try:
        svc.register_citizen(p.uid, p.email, body)
    except AccountExists:
        raise _EXISTS
    return {"ok": True}


@router.post("/register/organization", status_code=status.HTTP_201_CREATED)
def register_organization(body: OrganizationRegistration, p: Principal = Depends(current_principal), svc: AccountService = Depends(get_service)):
    try:
        svc.register_organization(p.uid, p.email, body)
    except AccountExists:
        raise _EXISTS
    return {"ok": True, "verificationStatus": "pending"}


@router.post("/register/organization-member", status_code=status.HTTP_201_CREATED)
def register_org_member(body: OrgMemberRegistration, p: Principal = Depends(current_principal), svc: AccountService = Depends(get_service)):
    try:
        svc.register_org_member(p.uid, p.email, body)
    except AccountExists:
        raise _EXISTS
    except InviteInvalid as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return {"ok": True}


@router.get("/me", response_model=AccountOut)
def me(account: dict = Depends(current_account)):
    return account
