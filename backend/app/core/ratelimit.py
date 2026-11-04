"""Per-user rate limits (code-owned, no model). Sliding window in memory.

Limits are per process: fine for one server. Behind several instances use a shared store (e.g. Redis) instead.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

# action -> list of (max requests, window seconds); every window must allow the request
LIMITS = {
    "post": [(5, 600), (30, 86400)],       # reports: 5 per 10 minutes, 30 per day
    "media": [(10, 600)],
    "comment": [(20, 600)],
    "like": [(60, 60)],
}

_hits: dict[tuple[str, str], deque] = defaultdict(deque)
_lock = threading.Lock()


def check(uid: str, action: str) -> None:
    """Raises 429 (with Retry-After) if `uid` exceeded any window for `action`; otherwise records the hit."""
    rules = LIMITS.get(action)
    if not rules:
        return
    now = time.monotonic()
    longest = max(w for _, w in rules)
    with _lock:
        q = _hits[(uid, action)]
        while q and now - q[0] > longest:
            q.popleft()
        for limit, window in rules:
            recent = [t for t in q if now - t <= window]
            if len(recent) >= limit:
                retry = int(window - (now - recent[0])) + 1
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                    "You are doing that too often. Please wait a little and try again.",
                                    headers={"Retry-After": str(retry)})
        q.append(now)


def reset() -> None:
    """Tests only."""
    with _lock:
        _hits.clear()
