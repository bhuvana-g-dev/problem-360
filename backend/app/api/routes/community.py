from fastapi import APIRouter, Depends

from app.core.constants import AccountType
from app.core.deps import get_community_service
from app.core.security import require_account

router = APIRouter(prefix="/api", tags=["community"])
citizen = require_account(AccountType.CITIZEN)
anyone = require_account(AccountType.CITIZEN, AccountType.ORGANIZATION, AccountType.ADMIN)


@router.get("/groups")
def groups(locality: str | None = None, a: dict = Depends(anyone), svc=Depends(get_community_service)): return svc.groups(a, locality)

@router.post("/groups/{gid}/join")
def join(gid: str, a: dict = Depends(citizen), svc=Depends(get_community_service)): return svc.join(a, gid)

@router.post("/groups/{gid}/leave")
def leave(gid: str, a: dict = Depends(citizen), svc=Depends(get_community_service)): return svc.leave(a, gid)

@router.get("/events")
def events(locality: str | None = None, upcoming: bool = True, a: dict = Depends(anyone), svc=Depends(get_community_service)): return svc.events(a, locality, upcoming)

@router.post("/events/{eid}/register")
def register(eid: str, a: dict = Depends(citizen), svc=Depends(get_community_service)): return svc.register(a, eid)

@router.post("/events/{eid}/unregister")
def unregister(eid: str, a: dict = Depends(citizen), svc=Depends(get_community_service)): return svc.unregister(a, eid)

@router.get("/updates")
def updates(a: dict = Depends(anyone), svc=Depends(get_community_service)): return svc.updates()
