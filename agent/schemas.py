from enum import Enum

from pydantic import BaseModel, Field


class Action(str, Enum):
    CREATE_REPORT = "CREATE_REPORT"
    CHECK_DUPLICATE = "CHECK_DUPLICATE"
    FLAG_URGENT = "FLAG_URGENT"
    REQUEST_MORE_INFORMATION = "REQUEST_MORE_INFORMATION"
    ROUTE_TO_DEPARTMENT = "ROUTE_TO_DEPARTMENT"
    SUGGEST_COMMUNITY_ACTION = "SUGGEST_COMMUNITY_ACTION"
    ESCALATE_FOR_HUMAN_REVIEW = "ESCALATE_FOR_HUMAN_REVIEW"


class AgentChoice(BaseModel):
    """Structured output of the planner agent. Facts (urgency, department, duplicate) are NOT here:
    code copies them from tool results so the model cannot invent them."""
    action: Action = Field(description="the single next action for this report")
    summary: str = Field(max_length=400, description="one or two plain sentences for the citizen, in their language; never claim anyone was contacted")
    reasoning: str = Field(max_length=500, description="why, citing the tool results you used")
    questions: list[str] = Field(default_factory=list, description="only for REQUEST_MORE_INFORMATION: up to 3 short questions, in the citizen's language")
    citations: list[str] = Field(default_factory=list, description="guidance ids from the tools' `cite` fields")
