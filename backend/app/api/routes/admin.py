from typing import Literal

from fastapi import APIRouter, Depends

from app.core.constants import AccountType
from app.core.deps import get_admin_service, get_review_service
from app.core.security import require_account
from app.schemas.community import VerificationChange
from app.schemas.review import ReviewDecision, StatusChange

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin = require_account(AccountType.ADMIN)


@router.get("/organizations")
def organizations(status: str | None = None, a: dict = Depends(admin), svc=Depends(get_admin_service)): return svc.organizations(status)

@router.patch("/organizations/{org_id}/verification")
def verify(org_id: str, body: VerificationChange, a: dict = Depends(admin), svc=Depends(get_admin_service)): return svc.set_verification(a, org_id, body.status, body.note)


# ---- human review queue ----
@router.get("/reviews")
def reviews(state: Literal["pending", "done"] = "pending", a: dict = Depends(admin), svc=Depends(get_review_service)): return svc.queue(state)

@router.get("/reviews/stats")
def review_stats(a: dict = Depends(admin), svc=Depends(get_review_service)): return svc.stats()

@router.post("/reviews/{post_id}")
def review(post_id: str, body: ReviewDecision, a: dict = Depends(admin), svc=Depends(get_review_service)): return svc.decide(a, post_id, body.decision, body.note)

@router.patch("/reports/{post_id}/status")
def report_status(post_id: str, body: StatusChange, a: dict = Depends(admin), svc=Depends(get_review_service)): return svc.set_status(a, post_id, body.status, body.note)
