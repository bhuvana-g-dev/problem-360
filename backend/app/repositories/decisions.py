"""Firestore access for Strands decisions, the audit trail and structured civic incidents."""
from datetime import datetime, timezone

from app.core.constants import DECISIONS, INCIDENTS

now = lambda: datetime.now(timezone.utc)


class DecisionRepository:
    def __init__(self, db):
        self.db = db

    def save(self, post_id: str, doc: dict) -> None:
        self.db.collection(DECISIONS).document(post_id).set(doc)

    def get(self, post_id: str) -> dict | None:
        s = self.db.collection(DECISIONS).document(post_id).get()
        return s.to_dict() if s.exists else None

    def audit(self, post_id: str, event_type: str, detail: dict | None = None) -> None:
        self.db.collection(DECISIONS).document(post_id).collection("audit").document().create(
            {"type": event_type, "detail": detail or {}, "at": now()})

    def list_audit(self, post_id: str) -> list[dict]:
        rows = [s.to_dict() for s in self.db.collection(DECISIONS).document(post_id).collection("audit").stream()]
        return sorted(rows, key=lambda r: r["at"])

    def create_incident(self, reference_id: str, doc: dict) -> None:
        self.db.collection(INCIDENTS).document(reference_id).set({**doc, "createdAt": now()})

    def get_incident(self, reference_id: str) -> dict | None:
        s = self.db.collection(INCIDENTS).document(reference_id).get()
        return s.to_dict() if s.exists else None
