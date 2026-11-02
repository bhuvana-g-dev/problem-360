from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status

from app.core.constants import AccountType
from app.core.deps import get_decision_service, get_media_service, get_post_service
from app.core.security import require_account
from app.schemas.posts import CommentCreate, PostCreate, PostOut

router = APIRouter(prefix="/api", tags=["posts"])
citizen = require_account(AccountType.CITIZEN)
anyone = require_account(AccountType.CITIZEN, AccountType.ORGANIZATION, AccountType.ADMIN)


@router.post("/media", status_code=status.HTTP_201_CREATED)
async def upload_media(file: UploadFile = File(...), account: dict = Depends(citizen), media=Depends(get_media_service)):
    return await media.upload(account["uid"], file)


@router.get("/posts", response_model=list[PostOut])
def list_posts(locality: str | None = None, category: str | None = None, q: str | None = None, mine: str | None = None,
               account: dict = Depends(anyone), svc=Depends(get_post_service)):
    return svc.list(account, locality, category, q, bool(mine))


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(body: PostCreate, bg: BackgroundTasks, account: dict = Depends(citizen), svc=Depends(get_post_service), decide=Depends(get_decision_service)):
    post_id = svc.create(account, body)
    bg.add_task(decide.run, post_id)  # the Strands agent runs after the response; the UI polls decisionState
    return svc.get_out(account, post_id)


@router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: str, account: dict = Depends(anyone), svc=Depends(get_post_service)):
    return svc.get_out(account, post_id)


@router.post("/posts/{post_id}/like")
def like(post_id: str, account: dict = Depends(citizen), svc=Depends(get_post_service)):
    return svc.like(account, post_id)


@router.get("/posts/{post_id}/comments")
def comments(post_id: str, account: dict = Depends(anyone), svc=Depends(get_post_service)):
    return svc.comments(post_id)


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(post_id: str, body: CommentCreate, account: dict = Depends(citizen), svc=Depends(get_post_service)):
    return svc.add_comment(account, post_id, body.text)


@router.get("/posts/{post_id}/decision")
def decision_trace(post_id: str, account: dict = Depends(anyone), decide=Depends(get_decision_service)):
    return decide.trace(account, post_id)


@router.post("/posts/{post_id}/decision/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_decision(post_id: str, bg: BackgroundTasks, account: dict = Depends(anyone), decide=Depends(get_decision_service)):
    decide.retry(account, post_id)
    bg.add_task(decide.run, post_id)
    return {"ok": True}


@router.get("/notifications")
def notifications(account: dict = Depends(anyone), svc=Depends(get_post_service)):
    return svc.notifications(account)
