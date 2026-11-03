from typing import Literal

from pydantic import AwareDatetime, BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.constants import ISSUE_CATEGORIES


class _Stripped(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


class GroupCreate(_Stripped):
    name: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=10, max_length=500)
    locality: str = Field(min_length=2, max_length=60)
    focus: str | None = None

    @field_validator("focus")
    @classmethod
    def known_focus(cls, v):
        if v and v not in ISSUE_CATEGORIES:
            raise ValueError("Unknown focus category")
        return v or None


class EventCreate(_Stripped):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=10, max_length=1000)
    locality: str = Field(min_length=2, max_length=60)
    locationText: str = Field(default="", max_length=120)
    startsAt: AwareDatetime
    endsAt: AwareDatetime | None = None
    capacity: int | None = Field(default=None, ge=1, le=5000)
    groupId: str | None = None
    relatedPostId: str | None = None
    safetyNotes: str = Field(min_length=10, max_length=500, description="Required: how participants stay safe")

    @model_validator(mode="after")
    def order(self):
        if self.endsAt and self.endsAt <= self.startsAt:
            raise ValueError("End time must be after the start time")
        return self


class UpdateCreate(_Stripped):
    title: str = Field(min_length=3, max_length=100)
    body: str = Field(min_length=10, max_length=2000)


class InviteCreate(_Stripped):
    email: EmailStr
    role: Literal["admin", "member"]


class RoleChange(BaseModel):
    role: Literal["admin", "member"]


class VerificationChange(_Stripped):
    status: Literal["verified", "rejected", "pending"]
    note: str = Field(default="", max_length=300)
