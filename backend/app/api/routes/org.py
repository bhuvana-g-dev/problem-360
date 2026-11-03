from fastapi import APIRouter, Depends, status

from app.core.constants import MemberRole
from app.core.deps import get_org_service
from app.core.security import require_verified_org_member
from app.schemas.community import EventCreate, GroupCreate, InviteCreate, RoleChange, UpdateCreate

router = APIRouter(prefix="/api/org", tags=["organization"])
# Role matrix (enforced here, in the backend): any verified member can view; owner/admin manage; owner alone changes roles/removes members.
view = require_verified_org_member()
manage = require_verified_org_member(MemberRole.OWNER, MemberRole.ADMIN)
owner = require_verified_org_member(MemberRole.OWNER)


@router.get("/overview")
def overview(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.overview(a)

@router.get("/groups")
def groups(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.groups(a)

@router.post("/groups", status_code=status.HTTP_201_CREATED)
def create_group(body: GroupCreate, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.create_group(a, body)

@router.get("/events")
def events(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.events(a)

@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_event(body: EventCreate, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.create_event(a, body)

@router.post("/events/{event_id}/cancel")
def cancel_event(event_id: str, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.cancel_event(a, event_id)

@router.get("/events/{event_id}/registrations")
def registrations(event_id: str, a: dict = Depends(view), svc=Depends(get_org_service)): return svc.registrations(a, event_id)

@router.get("/updates")
def updates(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.updates(a)

@router.post("/updates", status_code=status.HTTP_201_CREATED)
def publish(body: UpdateCreate, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.publish_update(a, body)

@router.get("/opportunities")
def opportunities(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.opportunities(a)

@router.get("/members")
def members(a: dict = Depends(view), svc=Depends(get_org_service)): return svc.members(a)

@router.get("/invites")
def invites(a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.invites(a)

@router.post("/invites", status_code=status.HTTP_201_CREATED)
def invite(body: InviteCreate, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.invite(a, body)

@router.delete("/invites/{code}")
def revoke(code: str, a: dict = Depends(manage), svc=Depends(get_org_service)): return svc.revoke_invite(a, code)

@router.patch("/members/{uid}")
def set_role(uid: str, body: RoleChange, a: dict = Depends(owner), svc=Depends(get_org_service)): return svc.set_role(a, uid, body.role)

@router.delete("/members/{uid}")
def remove(uid: str, a: dict = Depends(owner), svc=Depends(get_org_service)): return svc.remove_member(a, uid)
