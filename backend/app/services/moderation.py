"""Comment moderation: deterministic rules, no model. A rejected comment is never stored; the citizen sees why.

Built-in rules protect people and the feed: no links, no phone numbers or email addresses (personal data), no spam-like
repetition or shouting. Extra blocked terms are configured by your moderators, not hard-coded: put one term per line in
the file named by MODERATION_BLOCKLIST (backend/.env). Matching is case-insensitive and whole-word for Latin script,
substring for Tamil script.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, status

LINK = re.compile(r"https?://|www\.|\b[\w-]+\.(?:com|in|net|org|xyz|info|ly|io)\b", re.I)
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
PHONE = re.compile(r"(?:\+?91[\s-]?)?\b\d(?:[\s-]?\d){9}\b")          # 10-digit Indian mobile numbers, with or without +91
REPEAT = re.compile(r"(.)\1{7,}")                                       # "!!!!!!!!" or "aaaaaaaa"
TAMIL = re.compile(r"[\u0B80-\u0BFF]")


@lru_cache(maxsize=1)
def blocked_terms() -> tuple[str, ...]:
    path = os.environ.get("MODERATION_BLOCKLIST")
    if not path or not Path(path).is_file():
        return ()
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return tuple(t.strip().lower() for t in lines if t.strip() and not t.startswith("#"))


def problems(text: str) -> list[str]:
    out = []
    if LINK.search(text):
        out.append("links are not allowed in comments")
    if EMAIL.search(text) or PHONE.search(text):
        out.append("please don't share phone numbers or email addresses in public comments")
    if REPEAT.search(text):
        out.append("the comment looks like spam")
    letters = [c for c in text if c.isalpha() and c.isascii()]
    if len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) > 0.8:
        out.append("please don't write in all capitals")
    low = text.lower()
    for term in blocked_terms():
        hit = term in low if TAMIL.search(term) else re.search(rf"(?<!\w){re.escape(term)}(?!\w)", low)
        if hit:
            out.append("the comment contains language that isn't allowed here")
            break
    return out


def check_comment(text: str) -> None:
    p = problems(text)
    if p:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Comment not posted: " + "; ".join(p) + ".")
