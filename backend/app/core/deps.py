"""Dependency providers. Tests replace these with in-memory test doubles; production wiring lives only here."""
import sys
from pathlib import Path

from fastapi import Depends

from app.core.config import settings
from app.core.firebase import get_db
from app.core.storage import make_storage
from app.repositories.accounts import AccountRepository
from app.repositories.community import CommunityRepository
from app.repositories.decisions import DecisionRepository
from app.repositories.posts import PostRepository
from app.services.admin_service import AdminService
from app.services.community_service import CommunityService
from app.services.decision_service import DecisionService
from app.services.org_service import OrgService
from app.services.media_service import MediaService
from app.services.post_service import PostService
from app.services.review_service import ReviewService

_ROOT = Path(__file__).resolve().parents[3]  # repo root holds the `agent/` package (kept separate from the API)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_engine = None
_storage = None


def get_post_repo(): return PostRepository(get_db())
def get_decision_repo(): return DecisionRepository(get_db())
def get_account_repo(): return AccountRepository(get_db())


def get_storage():
    global _storage
    if _storage is None:  # one instance per process: the local backend's signing secret must stay the same
        _storage = make_storage()
    return _storage
def get_community_repo(): return CommunityRepository(get_db())


def get_engine():
    global _engine
    if _engine is None:
        from agent.engine import StrandsDeciderEngine  # imported lazily so the API starts even if the agent stack is misconfigured
        _engine = StrandsDeciderEngine()
    return _engine


def get_post_service(posts=Depends(get_post_repo), storage=Depends(get_storage)):
    return PostService(posts, storage)


def get_media_service(storage=Depends(get_storage)):
    return MediaService(storage, settings.max_upload_mb)


def get_decision_service(posts=Depends(get_post_repo), decisions=Depends(get_decision_repo), engine=Depends(get_engine), community=Depends(get_community_repo)):
    return DecisionService(posts, decisions, engine, community)


def get_org_service(accounts=Depends(get_account_repo), community=Depends(get_community_repo), posts=Depends(get_post_repo)):
    return OrgService(accounts, community, posts)


def get_community_service(community=Depends(get_community_repo), posts=Depends(get_post_repo)):
    return CommunityService(community, posts)


def get_admin_service(accounts=Depends(get_account_repo), posts=Depends(get_post_repo)):
    return AdminService(accounts, posts)


def get_review_service(posts=Depends(get_post_repo), decisions=Depends(get_decision_repo)):
    return ReviewService(posts, decisions)
