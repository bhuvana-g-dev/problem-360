from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import ISSUE_CATEGORIES


class Coordinates(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class PostCreate(BaseModel):
    description: str = Field(min_length=3, max_length=1000)
    category: str
    locality: str = Field(min_length=2, max_length=60)
    locationText: str = Field(default="", max_length=120)
    coordinates: Coordinates | None = None
    mediaPath: str | None = Field(default=None, max_length=200)

    @field_validator("description", "locality", "locationText")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("category")
    @classmethod
    def known_category(cls, v: str) -> str:
        if v not in ISSUE_CATEGORIES:
            raise ValueError("Unknown category")
        return v


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=500)

    @field_validator("text")
    @classmethod
    def strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Comment is empty")
        return v


class Author(BaseModel):
    uid: str
    name: str
    locality: str | None = None


class PostOut(BaseModel):
    id: str
    author: Author
    description: str
    category: str
    locality: str
    locationText: str = ""
    coordinates: Coordinates | None = None
    createdAt: str
    mediaUrl: str | None = None
    mediaType: Literal["image", "video"] | None = None
    status: str
    referenceId: str
    likeCount: int
    commentCount: int
    likedByMe: bool
    decisionState: Literal["pending", "completed", "failed"]
    decision: dict | None = None
    review: dict | None = None   # human review: {state, at, note}; never the reviewer's id
