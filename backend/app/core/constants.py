class AccountType:
    CITIZEN = "citizen"
    ORGANIZATION = "organization"
    ADMIN = "admin"  # never self-registered; granted out-of-band


class Verification:
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class MemberRole:
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# Collection names: one place, used only by repositories.
USERS = "users"
ORGANIZATIONS = "organizations"
ORG_MEMBERS = "organization_members"

POSTS = "posts"
DECISIONS = "decisions"
INCIDENTS = "incidents"
NOTIFICATIONS = "notifications"

ISSUE_CATEGORIES = [
    "Roads & potholes", "Waste & sanitation", "Water supply", "Drainage & flooding", "Street lighting",
    "Electricity", "Public transport", "Parks & public spaces", "Public safety", "Other",
]
