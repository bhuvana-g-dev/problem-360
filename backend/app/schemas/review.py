from typing import Literal

from pydantic import BaseModel, Field


class ReviewDecision(BaseModel):
    decision: Literal["approve", "reject"]
    note: str = Field(default="", max_length=300)


class StatusChange(BaseModel):
    status: Literal["Acknowledged", "Resolved"]
    note: str = Field(default="", max_length=300)
