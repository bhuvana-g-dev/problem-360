"""What one review returns to the citizen (`ss measure` scores this) and the critic's verdict."""
from typing import Literal

from pydantic import BaseModel, Field

from .schemas import Action


class ReviewPlan(BaseModel):
    language: Literal["en", "ta"]
    action: Action
    summary: str = Field(description="What happens next, for the citizen, in their language")
    questions: list[str] = Field(default_factory=list, description="Only for REQUEST_MORE_INFORMATION")
    urgent: bool = False
    department_id: str | None = Field(default=None, description="Recommended department id (a recommendation only)")
    department_name: str | None = None
    duplicate_of: str | None = Field(default=None, description="id of the existing report this may duplicate")
    community_suggestion: str | None = None
    escalation: str = Field(description="When and whom to call if anyone is in danger")
    citations: list[str] = Field(description="Guidance ids from agent/data/guidance.json")
    human_review_required: bool = False


class Critique(BaseModel):
    ok: bool
    problems: list[str] = Field(default_factory=list)
