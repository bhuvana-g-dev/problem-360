from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Locality = Field(min_length=2, max_length=60)


class CitizenRegistration(BaseModel):
    displayName: str = Field(min_length=2, max_length=80)
    locality: str = Locality

    @field_validator("displayName", "locality")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class OrganizationRegistration(BaseModel):
    contactName: str = Field(min_length=2, max_length=80)
    orgName: str = Field(min_length=3, max_length=120)
    category: str = Field(min_length=2, max_length=60)
    description: str = Field(min_length=20, max_length=1000)
    locality: str = Locality
    website: HttpUrl | None = None

    @field_validator("contactName", "orgName", "category", "description", "locality")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class OrganizationSummary(BaseModel):
    id: str
    name: str
    category: str
    locality: str
    verificationStatus: Literal["pending", "verified", "rejected"]
    memberRole: Literal["owner", "admin", "member"]


class AccountOut(BaseModel):
    uid: str
    email: str | None
    displayName: str
    accountType: Literal["citizen", "organization", "admin"]
    locality: str | None = None
    organization: OrganizationSummary | None = None


class OrgMemberRegistration(BaseModel):
    contactName: str = Field(min_length=2, max_length=80)
    inviteCode: str = Field(min_length=10, max_length=80)

    @field_validator("contactName", "inviteCode")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()
