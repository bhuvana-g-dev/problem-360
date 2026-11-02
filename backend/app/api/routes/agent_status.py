import os

from fastapi import APIRouter, Depends

from app.core.security import current_account

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/status")
def status(account: dict = Depends(current_account)):
    """Configuration presence only (never secret values), so setup problems are visible without reading logs."""
    import agent.config as c  # noqa: PLC0415 (repo root is on sys.path via core.deps)
    return {"deciderKeyConfigured": bool(c.decider_key()), "deciderUrl": c.DECIDER_URL, "model": c.MODEL_ID, "region": c.REGION,
            "awsCredentialsHint": bool(os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE") or os.environ.get("AWS_BEARER_TOKEN_BEDROCK")),
            "thresholds": {"urgent": c.URGENT_THRESHOLD, "duplicate": c.DUPLICATE_THRESHOLD, "department": c.DEPARTMENT_MIN_CONFIDENCE, "community": c.COMMUNITY_THRESHOLD}}
