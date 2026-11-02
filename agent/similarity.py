"""Duplicate detection: text overlap plus optional GPS proximity. No embeddings, no model: fully explainable."""
import math
import re

_STOP = {"the", "a", "an", "is", "are", "in", "on", "at", "of", "to", "and", "for", "near", "from", "with", "it", "this",
         "that", "has", "have", "been", "was", "since", "there", "my", "our", "we", "very", "please", "no", "not"}


def tokens(text: str) -> set[str]:
    parts = re.split(r"[\s,.;:!?()\"'/\\\-–—]+", text.lower())
    return {p for p in parts if len(p) > 1 and p not in _STOP}


def distance_m(a: dict | None, b: dict | None) -> float | None:
    if not a or not b:
        return None
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def score_pair(new: dict, old: dict) -> dict:
    """Score 0-1. Text Jaccard, +0.25 when GPS points are within 150 m, +0.1 for the same landmark text."""
    a, b = tokens(new["description"]), tokens(old["description"])
    jac = len(a & b) / len(a | b) if a and b else 0.0
    d = distance_m(new.get("coordinates"), old.get("coordinates"))
    near = d is not None and d <= 150
    same_spot = bool(new.get("locationText") and old.get("locationText")
                     and new["locationText"].strip().lower() == old["locationText"].strip().lower())
    score = min(1.0, jac + (0.25 if near else 0) + (0.1 if same_spot else 0))
    return {"score": round(score, 3), "textOverlap": round(jac, 3), "distanceM": None if d is None else round(d),
            "sameCategory": new["category"] == old.get("category")}
