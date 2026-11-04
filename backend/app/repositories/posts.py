from __future__ import annotations

"""All Firestore access for posts, likes, comments and notifications."""
from datetime import datetime, timezone

from google.cloud import firestore

from app.core.constants import NOTIFICATIONS, POSTS

now = lambda: datetime.now(timezone.utc)


class PostRepository:
    def __init__(self, db):
        self.db = db

    def _posts(self):
        return self.db.collection(POSTS)

    def create(self, post_id: str, data: dict) -> None:
        self._posts().document(post_id).create({**data, "createdAt": now(), "updatedAt": now()})

    def get(self, post_id: str) -> dict | None:
        s = self._posts().document(post_id).get()
        return {**s.to_dict(), "id": s.id} if s.exists else None

    def list(self, locality=None, category=None, author_uid=None, limit=200) -> list[dict]:
        q = self._posts()
        for field, val in (("locality", locality), ("category", category), ("authorUid", author_uid)):
            if val:
                q = q.where(field, "==", val)
        if not (locality or category or author_uid):
            q = q.order_by("createdAt", direction=firestore.Query.DESCENDING)
        out = [{**s.to_dict(), "id": s.id} for s in q.limit(limit).stream()]
        return sorted(out, key=lambda p: p["createdAt"], reverse=True)

    def recent_for_duplicates(self, locality: str, since: datetime, exclude_id: str) -> list[dict]:
        """Equality filter only (no composite index needed); the date window is applied here."""
        rows = [{**s.to_dict(), "id": s.id} for s in self._posts().where("locality", "==", locality).limit(300).stream()]
        return [p for p in rows if p["id"] != exclude_id and p["createdAt"] >= since and p.get("status") not in ("Resolved", "Verified")]

    def list_community_opportunities(self, limit: int = 100) -> list[dict]:
        q = self._posts().where("decision.action", "==", "SUGGEST_COMMUNITY_ACTION").limit(limit)
        return sorted(({**s.to_dict(), "id": s.id} for s in q.stream()), key=lambda p: p["createdAt"], reverse=True)

    def set_decision(self, post_id: str, state: str, summary: dict | None) -> None:
        self._posts().document(post_id).update({"decisionState": state, "decision": summary, "updatedAt": now()})

    # ---- human review queue ----
    def list_review_queue(self, limit: int = 500) -> list[dict]:
        """Every report the agent (or the fail-closed fallback) marked for a person. Equality filter only: no composite index."""
        q = self._posts().where("decision.humanReviewRequired", "==", True).limit(limit)
        return [{**s.to_dict(), "id": s.id} for s in q.stream()]

    def update_review(self, post_id: str, fields: dict) -> None:
        self._posts().document(post_id).update({**fields, "updatedAt": now()})

    # ---- likes ----
    def toggle_like(self, post_id: str, uid: str) -> dict | None:
        post_ref = self._posts().document(post_id)
        like_ref = post_ref.collection("likes").document(uid)

        @firestore.transactional
        def tx(t):
            liked = like_ref.get(transaction=t).exists
            snap = post_ref.get(transaction=t)
            if not snap.exists:
                return None
            count = snap.get("likeCount") or 0
            if liked:
                t.delete(like_ref); count = max(0, count - 1)
            else:
                t.set(like_ref, {"createdAt": now()}); count += 1
            t.update(post_ref, {"likeCount": count})
            return {"likedByMe": not liked, "likeCount": count}

        return tx(self.db.transaction())

    def liked_ids(self, post_ids: list[str], uid: str) -> set[str]:
        refs = [self._posts().document(i).collection("likes").document(uid) for i in post_ids]
        return {r.reference.parent.parent.id for r in self.db.get_all(refs) if r.exists} if refs else set()

    # ---- comments ----
    def list_comments(self, post_id: str, limit=200) -> list[dict]:
        q = self._posts().document(post_id).collection("comments").order_by("createdAt").limit(limit)
        return [{**s.to_dict(), "id": s.id} for s in q.stream()]

    def add_comment(self, post_id: str, comment_id: str, data: dict) -> None:
        post_ref = self._posts().document(post_id)
        batch = self.db.batch()
        batch.create(post_ref.collection("comments").document(comment_id), {**data, "createdAt": now()})
        batch.update(post_ref, {"commentCount": firestore.Increment(1)})
        batch.commit()

    # ---- notifications ----
    def add_notification(self, uid: str, text: str, post_id: str | None) -> None:
        self.db.collection(NOTIFICATIONS).document().create({"uid": uid, "text": text, "postId": post_id, "createdAt": now(), "read": False})

    def list_notifications(self, uid: str, limit=50) -> list[dict]:
        rows = [{**s.to_dict(), "id": s.id} for s in self.db.collection(NOTIFICATIONS).where("uid", "==", uid).limit(200).stream()]
        return sorted(rows, key=lambda n: n["createdAt"], reverse=True)[:limit]
