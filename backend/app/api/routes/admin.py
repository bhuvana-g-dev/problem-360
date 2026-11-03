from fastapi import APIRouter, Depends

from app.core.constants import AccountType
from app.core.deps import get_admin_service
from app.core.security import require_account
from app.schemas.community import VerificationChange

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin = require_account(AccountType.ADMIN)


@router.get("/organizations")
def organizations(status: str | None = None, a: dict = Depends(admin), svc=Depends(get_admin_service)): return svc.organizations(status)

@router.patch("/organizations/{org_id}/verification")
def verify(org_id: str, body: VerificationChange, a: dict = Depends(admin), svc=Depends(get_admin_service)): return svc.set_verification(a, org_id, body.status, body.note)
