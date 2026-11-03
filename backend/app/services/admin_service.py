from fastapi import HTTPException, status


class AdminService:
    def __init__(self, accounts, posts):
        self.a, self.posts = accounts, posts

    def organizations(self, st: str | None) -> list[dict]:
        return [{"id": o["id"], "name": o["name"], "category": o["category"], "locality": o["locality"], "description": o["description"],
                 "website": o.get("website"), "verificationStatus": o["verificationStatus"], "createdAt": o["createdAt"].isoformat()}
                for o in self.a.list_organizations(st)]

    def set_verification(self, admin: dict, org_id: str, st: str, note: str) -> dict:
        org = self.a.get_organization(org_id)
        if not org:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization not found.")
        self.a.set_verification(org_id, st, admin["uid"], note)
        if org.get("createdBy"):
            self.posts.add_notification(org["createdBy"], f"Your organization “{org['name']}” is now {st}." + (f" Note: {note}" if note else ""), None)
        return {"id": org_id, "verificationStatus": st}
