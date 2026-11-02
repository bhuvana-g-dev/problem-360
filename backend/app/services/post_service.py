from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.constants import AccountType


def iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def reference_id() -> str:
    return f"P360-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3).upper()}"


class PostService:
    def __init__(self, posts, storage):
        self.posts, self.storage = posts, storage

    def to_out(self, p: dict, liked: set[str]) -> dict:
        url = self.storage.signed_url(p["mediaPath"]) if p.get("mediaPath") else None
        return {"id": p["id"], "author": {"uid": p["authorUid"], "name": p["authorName"], "locality": p.get("authorLocality")},
                "description": p["description"], "category": p["category"], "locality": p["locality"], "locationText": p.get("locationText", ""),
                "coordinates": p.get("coordinates"), "createdAt": iso(p["createdAt"]), "mediaUrl": url, "mediaType": p.get("mediaType") if url else None,
                "status": p["status"], "referenceId": p["referenceId"], "likeCount": p.get("likeCount", 0), "commentCount": p.get("commentCount", 0),
                "likedByMe": p["id"] in liked, "decisionState": p.get("decisionState", "pending"), "decision": p.get("decision")}

    def _out_many(self, rows, account):
        liked = self.posts.liked_ids([r["id"] for r in rows], account["uid"]) if rows else set()
        return [self.to_out(r, liked) for r in rows]

    def create(self, account: dict, body) -> dict:
        if body.mediaPath:
            if not body.mediaPath.startswith(f"posts/{account['uid']}/") or ".." in body.mediaPath or not self.storage.exists(body.mediaPath):
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid media reference. Upload the file again.")
        media_type = None
        if body.mediaPath:
            media_type = "video" if body.mediaPath.endswith((".mp4", ".webm")) else "image"
        post_id = uuid.uuid4().hex
        self.posts.create(post_id, {
            "authorUid": account["uid"], "authorName": account["displayName"], "authorLocality": account.get("locality"),
            "description": body.description, "category": body.category, "locality": body.locality, "locationText": body.locationText,
            "coordinates": body.coordinates.model_dump() if body.coordinates else None, "mediaPath": body.mediaPath, "mediaType": media_type,
            "status": "Submitted", "referenceId": reference_id(), "likeCount": 0, "commentCount": 0, "decisionState": "pending", "decision": None})
        return post_id

    def get_out(self, account, post_id: str) -> dict:
        p = self.posts.get(post_id)
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        return self._out_many([p], account)[0]

    def list(self, account, locality=None, category=None, q=None, mine=False) -> list[dict]:
        rows = self.posts.list(locality=locality, category=category, author_uid=account["uid"] if mine else None)
        if q:
            s = q.lower().strip()
            rows = [r for r in rows if s in r["description"].lower() or s in r.get("locationText", "").lower() or s in r["referenceId"].lower()]
        return self._out_many(rows, account)

    def like(self, account, post_id: str) -> dict:
        r = self.posts.toggle_like(post_id, account["uid"])
        if r is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        return r

    def comments(self, post_id: str) -> list[dict]:
        if not self.posts.get(post_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        return [{"id": c["id"], "author": {"uid": c["authorUid"], "name": c["authorName"]}, "text": c["text"], "createdAt": iso(c["createdAt"])}
                for c in self.posts.list_comments(post_id)]

    def add_comment(self, account, post_id: str, text: str) -> dict:
        if not self.posts.get(post_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found.")
        cid = uuid.uuid4().hex
        self.posts.add_comment(post_id, cid, {"authorUid": account["uid"], "authorName": account["displayName"], "text": text})
        return {"id": cid, "author": {"uid": account["uid"], "name": account["displayName"]}, "text": text, "createdAt": datetime.now(timezone.utc).isoformat()}

    def notifications(self, account) -> list[dict]:
        return [{"id": n["id"], "text": n["text"], "postId": n.get("postId"), "createdAt": iso(n["createdAt"])} for n in self.posts.list_notifications(account["uid"])]
