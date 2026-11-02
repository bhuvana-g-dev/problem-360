"""Strands @tool functions for civic reports, plus the plain helpers app.py, safety.py and score.py use.

`build_tools(ctx)` returns tools bound to ONE report: the model cannot pass a different report, so it cannot
tamper with what is analysed. Every call is recorded (name, output, time) so the backend can store it.
All Decider questions are asked in a single call and cached (hosted quota: 2,000 decisions/month).
Each result carries `cite`: the only guidance ids that fact may be cited with."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable

from strands import tool

from . import config
from .knowledge import (CATEGORY_TO_DEPARTMENT, COMMUNITY_CITE, COMMUNITY_IDEAS, COMMUNITY_IDEAS_TA, DEPARTMENTS,
                        urgent_keyword_hits)
from .similarity import distance_m, score_pair

DATA = Path(__file__).parent / "data"
TAMIL = re.compile(r"[\u0B80-\u0BFF]")


# ---- guidance and language helpers (no model) ----
@lru_cache(maxsize=1)
def guidance() -> dict:
    return json.loads((DATA / "guidance.json").read_text(encoding="utf-8"))


def guidance_ids() -> set[str]:
    return {g["id"] for g in guidance()["items"]}


def language_of(text: str) -> str:
    """Reply language: Tamil script -> "ta"; English and Tanglish (Tamil in Latin script) -> "en"."""
    return "ta" if TAMIL.search(text or "") else "en"


def has_tamil(text: str) -> bool:
    return bool(TAMIL.search(text or ""))


def translate_to_tamil(texts: list[str]) -> list[str]:
    """Amazon Translate fallback when the model answered a Tamil speaker in English."""
    import boto3
    c = boto3.client("translate", region_name=config.REGION)
    return [c.translate_text(Text=t, SourceLanguageCode="en", TargetLanguageCode="ta")["TranslatedText"] if t and not has_tamil(t) else t
            for t in texts]


# ---- per-report context ----
@dataclass
class RunContext:
    report: dict                       # id, description, category, locality, locationText, coordinates
    nearby_provider: Callable[[str, int, str], list[dict]]   # (locality, days, exclude_id) -> recent reports
    decider: object                    # DeciderClient (or any object with .decide(state, questions))
    runs: list = field(default_factory=list)
    cache: dict = field(default_factory=dict)

    def record(self, name: str, output: dict, ms: int, invoked_by: str = "agent") -> dict:
        self.runs.append({"tool": name, "output": output, "ms": ms, "invokedBy": invoked_by})
        return output

    def state_text(self) -> str:
        r = self.report
        return f"Category: {r['category']}. Locality: {r['locality']}. Report: {r['description']}"


def _questions() -> dict:
    return {
        "urgent": {"type": "noul", "instructions": "Does this civic report describe an immediate danger to life or safety "
                   "(for example exposed live wires, a gas leak, fire, an open manhole on a road, a collapsing structure, someone trapped or injured)?"},
        "department": {"type": "choice", "instructions": "Which municipal department should handle this report?",
                       "criteria": {k: v["hint"] for k, v in DEPARTMENTS.items()}},
        "community": {"type": "noul", "instructions": "Could ordinary neighbours safely help fix or reduce this problem themselves "
                      "(for example a clean-up) without special equipment, permits or exposure to danger?"},
        "vague": {"type": "noul", "instructions": "Is this report too vague to act on because it does not say what is wrong?"},
    }


def decider_answers(ctx: RunContext) -> dict:
    """One cached Decider call covering every question. Raises DeciderError on failure (the run then fails closed)."""
    if "decider" not in ctx.cache:
        t = time.time()
        a = ctx.decider.decide(ctx.state_text(), _questions())
        ctx.cache["decider"] = {
            "pUrgent": float(a["urgent"]["noul"]), "pCommunity": float(a["community"]["noul"]), "pVague": float(a["vague"]["noul"]),
            "department": a["department"]["choice"], "departmentConfidence": float(a["department"].get("confidence") or 0.0)}
        ctx.record("strands_decider_call", ctx.cache["decider"], int((time.time() - t) * 1000), "tool")
    return ctx.cache["decider"]


# ---- plain functions (used by tools, the safety gate AND the enforcer, so results are identical) ----
def do_search_nearby(ctx: RunContext, days: int = config.DUPLICATE_WINDOW_DAYS) -> dict:
    r = ctx.report
    if "nearby" not in ctx.cache:
        ctx.cache["nearby"] = ctx.nearby_provider(r["locality"], days, r["id"])
    found = ctx.cache["nearby"]
    return {"count": len(found), "reports": [
        {"id": x["id"], "referenceId": x.get("referenceId"), "category": x["category"], "status": x.get("status"),
         "snippet": x["description"][:120], "distanceM": (None if distance_m(r.get("coordinates"), x.get("coordinates")) is None
                                                          else round(distance_m(r.get("coordinates"), x.get("coordinates"))))} for x in found[:10]]}


def do_detect_duplicates(ctx: RunContext) -> dict:
    do_search_nearby(ctx)
    scored = []
    for x in ctx.cache["nearby"]:
        s = score_pair(ctx.report, x)
        if s["sameCategory"]:
            scored.append({"id": x["id"], "referenceId": x.get("referenceId"), **s})
    scored.sort(key=lambda s: -s["score"])
    best = scored[0] if scored else None
    dup = bool(best and best["score"] >= config.DUPLICATE_THRESHOLD)
    out = {"best": best, "isLikelyDuplicate": dup, "threshold": config.DUPLICATE_THRESHOLD, "compared": len(scored),
           "cite": ["G-POLICY-DUPLICATE", "G-POLICY-HUMAN-REVIEW"] if dup else []}
    ctx.cache["duplicates"] = out
    return out


def do_assess_urgency(ctx: RunContext) -> dict:
    a = decider_answers(ctx)
    hits = urgent_keyword_hits(ctx.report["description"])
    urgent = bool(hits) or a["pUrgent"] >= config.URGENT_THRESHOLD
    out = {"pUrgent": a["pUrgent"], "keywordHits": hits, "threshold": config.URGENT_THRESHOLD, "urgent": urgent,
           "cite": ["G-EMERGENCY-112", "G-AMBULANCE-108", "G-POLICY-HUMAN-REVIEW"] if urgent else []}
    ctx.cache["urgency"] = out
    return out


def do_recommend_department(ctx: RunContext) -> dict:
    a = decider_answers(ctx)
    dept = a["department"] if a["department"] in DEPARTMENTS else "unclear"
    prior = CATEGORY_TO_DEPARTMENT.get(ctx.report["category"], "unclear")
    out = {"id": dept, "name": DEPARTMENTS[dept]["name"], "confidence": a["departmentConfidence"],
           "categoryDefault": prior, "agreesWithCategory": dept == prior,
           "confident": a["departmentConfidence"] >= config.DEPARTMENT_MIN_CONFIDENCE and dept != "unclear",
           "note": "A recommendation only. No department has been contacted.",
           "cite": ([f"G-DEPT-{dept}"] if dept != "unclear" else ["G-POLICY-HUMAN-REVIEW"]) + ["G-POLICY-NO-CONTACT"]}
    ctx.cache["department"] = out
    return out


def do_recommend_community_action(ctx: RunContext) -> dict:
    a = decider_answers(ctx)
    urgent = ctx.cache.get("urgency") or do_assess_urgency(ctx)
    cat = ctx.report["category"]
    idea = COMMUNITY_IDEAS.get(cat)
    suitable = bool(idea) and not urgent["urgent"] and a["pCommunity"] >= config.COMMUNITY_THRESHOLD
    out = {"suitable": suitable, "pCommunity": a["pCommunity"], "suggestion": idea if suitable else None,
           "suggestion_ta": COMMUNITY_IDEAS_TA.get(cat) if suitable else None,
           "reason": None if suitable else ("urgent report" if urgent["urgent"] else "category not safe for volunteers" if not idea else "low confidence"),
           "cite": [COMMUNITY_CITE[cat], "G-POLICY-NO-CONTACT"] if suitable else []}
    ctx.cache["community"] = out
    return out


def compute_facts(ctx: RunContext) -> dict:
    """Every fact the decision depends on, computed by code before any agent runs. Raises if the Decider is unavailable."""
    return {"urgency": do_assess_urgency(ctx), "duplicates": do_detect_duplicates(ctx),
            "department": do_recommend_department(ctx), "community": do_recommend_community_action(ctx),
            "pVague": ctx.cache["decider"]["pVague"]}


def build_tools(ctx: RunContext) -> list:
    def wrap(name, fn):
        t = time.time()
        out = fn(ctx)
        return ctx.record(name, out, int((time.time() - t) * 1000))

    @tool
    def search_nearby_reports() -> dict:
        """List recent open civic reports in the same locality (last 30 days) so duplicates can be checked.
        Takes no arguments: it always searches around the report being reviewed."""
        return wrap("search_nearby_reports", do_search_nearby)

    @tool
    def detect_duplicates() -> dict:
        """Score how likely this report duplicates an existing nearby report (text overlap plus GPS closeness).
        Returns the best match and whether it passes the duplicate threshold."""
        return wrap("detect_duplicates", do_detect_duplicates)

    @tool
    def assess_urgency() -> dict:
        """Assess whether the report describes immediate danger. Uses the Strands Decider probability plus fixed
        danger keywords. `urgent` is true if either fires. Never override this result."""
        return wrap("assess_urgency", do_assess_urgency)

    @tool
    def recommend_department() -> dict:
        """Recommend which municipal department should handle this report, with Decider confidence.
        This is a recommendation only; nobody is contacted."""
        return wrap("recommend_department", do_recommend_department)

    @tool
    def recommend_community_action() -> dict:
        """Say whether neighbours can safely help (only low-risk categories) and give the fixed safety-checked suggestion."""
        return wrap("recommend_community_action", do_recommend_community_action)

    return [search_nearby_reports, detect_duplicates, assess_urgency, recommend_department, recommend_community_action]
