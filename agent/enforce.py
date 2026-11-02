"""Code-owned rules applied AFTER the agents answer (method parts 1 and 3: model proposes, code disposes).

- decide_final: danger -> FLAG_URGENT, duplicate -> CHECK_DUPLICATE, vague -> REQUEST_MORE_INFORMATION, unsafe community
  idea or unconfident routing -> ROUTE / ESCALATE. Every change is returned as an override and stored.
- finalize: puts back every field code owns (escalation text, department, duplicate, community suggestion, citations) and
  ships fixed text when the critic never passed or the action was overridden (fail closed).
"""
from __future__ import annotations

import time

from . import config
from .knowledge import COMMUNITY_IDEAS, COMMUNITY_IDEAS_TA
from .safety import NO_CONTACT, TEXT
from .schemas import Action
from .tools import (RunContext, do_assess_urgency, do_detect_duplicates, do_recommend_community_action,
                    do_recommend_department, guidance_ids)

_CODE_OK = {Action.ROUTE_TO_DEPARTMENT, Action.CREATE_REPORT, Action.SUGGEST_COMMUNITY_ACTION, Action.ESCALATE_FOR_HUMAN_REVIEW}
_NEEDS_NO_CONTACT = {Action.ROUTE_TO_DEPARTMENT, Action.SUGGEST_COMMUNITY_ACTION, Action.CREATE_REPORT, Action.ESCALATE_FOR_HUMAN_REVIEW}


def ensure_facts(ctx: RunContext) -> None:
    """If a fact is missing (it never should be: app.py computes them first), compute it now, recorded as the enforcer."""
    for key, fn in (("duplicates", do_detect_duplicates), ("urgency", do_assess_urgency),
                    ("department", do_recommend_department), ("community", do_recommend_community_action)):
        if key not in ctx.cache:
            t = time.time()
            out = fn(ctx)
            ctx.record(fn.__name__.replace("do_", ""), out, int((time.time() - t) * 1000), "enforcer")


def is_vague(ctx: RunContext) -> bool:
    return (ctx.cache["decider"]["pVague"] >= config.VAGUE_THRESHOLD
            or len(ctx.report["description"].strip()) < config.MIN_DESCRIPTION_CHARS)


def decide_final(choice_action: Action, ctx: RunContext) -> tuple[Action, list[dict]]:
    ensure_facts(ctx)
    urg, dup, dept, com = ctx.cache["urgency"], ctx.cache["duplicates"], ctx.cache["department"], ctx.cache["community"]
    forced, why = None, ""
    if urg["urgent"]:
        forced, why = Action.FLAG_URGENT, "urgency tool reported immediate danger"
    elif dup["isLikelyDuplicate"]:
        forced, why = Action.CHECK_DUPLICATE, f"duplicate score {dup['best']['score']} >= {dup['threshold']}"
    elif is_vague(ctx):
        forced, why = Action.REQUEST_MORE_INFORMATION, "report too vague to act on"
    elif choice_action not in _CODE_OK:
        forced, why = (Action.ROUTE_TO_DEPARTMENT if dept["confident"] else Action.ESCALATE_FOR_HUMAN_REVIEW), \
            f"{choice_action.value} is not allowed here (no danger, duplicate or vagueness found)"
    elif choice_action == Action.SUGGEST_COMMUNITY_ACTION and not com["suitable"]:
        forced, why = (Action.ROUTE_TO_DEPARTMENT if dept["confident"] else Action.ESCALATE_FOR_HUMAN_REVIEW), "community action is not safe/suitable"
    elif choice_action == Action.ROUTE_TO_DEPARTMENT and not dept["confident"]:
        forced, why = Action.ESCALATE_FOR_HUMAN_REVIEW, "department recommendation below confidence threshold"
    if forced and forced != choice_action:
        return forced, [{"from": choice_action.value, "to": forced.value, "reason": why}]
    return choice_action, []


def human_review_required(action: Action) -> bool:
    return action in (Action.FLAG_URGENT, Action.ESCALATE_FOR_HUMAN_REVIEW, Action.CHECK_DUPLICATE)


def required_citations(action: Action, ctx: RunContext) -> list[str]:
    c = ctx.cache
    need = {Action.FLAG_URGENT: c["urgency"]["cite"] or ["G-EMERGENCY-112", "G-AMBULANCE-108", "G-POLICY-HUMAN-REVIEW"],
            Action.CHECK_DUPLICATE: c["duplicates"]["cite"] or ["G-POLICY-DUPLICATE"],
            Action.REQUEST_MORE_INFORMATION: ["G-POLICY-VAGUE"],
            Action.ROUTE_TO_DEPARTMENT: c["department"]["cite"],
            Action.SUGGEST_COMMUNITY_ACTION: c["community"]["cite"] or ["G-POLICY-NO-CONTACT"],
            Action.ESCALATE_FOR_HUMAN_REVIEW: ["G-POLICY-HUMAN-REVIEW", "G-POLICY-NO-CONTACT"],
            Action.CREATE_REPORT: ["G-POLICY-NO-CONTACT"]}[action]
    return need + ["G-EMERGENCY-112", "G-AMBULANCE-108"]  # the escalation line on every plan names 112 and 108


def fixed_summary(action: Action, ctx: RunContext, lang: str) -> str:
    if action == Action.FLAG_URGENT:
        return TEXT["emergency"][lang]
    c = ctx.cache
    best = (c["duplicates"]["best"] or {})
    idea = (COMMUNITY_IDEAS_TA if lang == "ta" else COMMUNITY_IDEAS).get(ctx.report["category"], "")
    return TEXT["summary"][action.value][lang].format(ref=best.get("referenceId") or best.get("id") or "",
                                                      dept=c["department"]["name"], idea=idea)


def finalize(action: Action, summary: str, reasoning: str, questions: list[str], overrides: list[dict], proposed_cites: list[str],
             ctx: RunContext, lang: str, model: str | None, source: str) -> tuple[dict, list[str]]:
    """Build the stored decision. Returns (decision, list of fields code had to correct)."""
    c, fixed = ctx.cache, []
    if action == Action.FLAG_URGENT and summary != TEXT["emergency"][lang]:
        summary = TEXT["emergency"][lang]
        fixed.append("summary: fixed emergency text")
    if action == Action.REQUEST_MORE_INFORMATION:
        if not questions:
            questions = TEXT["questions"][lang]
            fixed.append("questions: fixed questions used")
        questions = questions[:3]
    else:
        questions = []
    if action in _NEEDS_NO_CONTACT and NO_CONTACT[lang].lower() not in summary.lower():
        summary = summary.rstrip() + " " + NO_CONTACT[lang]
    known = guidance_ids()
    dropped = [x for x in proposed_cites if x not in known]
    if dropped:
        fixed.append("dropped unknown citations " + ", ".join(dropped))
    cites = list(dict.fromkeys([x for x in proposed_cites if x in known] + required_citations(action, ctx)))
    dup = c["duplicates"]["best"] if c["duplicates"]["isLikelyDuplicate"] else None
    com = c["community"] if action == Action.SUGGEST_COMMUNITY_ACTION else None
    decision = {
        "action": action.value, "summary": summary, "reasoning": reasoning, "questions": questions,
        "urgency": c["urgency"], "department": c["department"], "duplicate": dup, "communityAction": com,
        "humanReviewRequired": human_review_required(action), "overrides": overrides, "source": source, "model": model,
        "deciderUsed": "decider" in c, "externalContact": False,
        "language": lang, "escalation": TEXT["escalation"][lang], "citations": cites,
    }
    return decision, fixed


def to_plan(d: dict) -> dict:
    """The citizen-facing plan `ss measure` scores (agent/plan.py ReviewPlan)."""
    from .plan import ReviewPlan
    lang = d["language"]
    com = d.get("communityAction") or {}
    dept = d.get("department") or {}
    show_dept = d["action"] in (Action.ROUTE_TO_DEPARTMENT.value, Action.SUGGEST_COMMUNITY_ACTION.value)
    return ReviewPlan(language=lang, action=d["action"], summary=d["summary"], questions=d["questions"],
                      urgent=bool((d.get("urgency") or {}).get("urgent")),
                      department_id=dept.get("id") if show_dept else None, department_name=dept.get("name") if show_dept else None,
                      duplicate_of=(d.get("duplicate") or {}).get("id"),
                      community_suggestion=(com.get("suggestion_ta") if lang == "ta" else com.get("suggestion")) or None,
                      escalation=d["escalation"], citations=d["citations"],
                      human_review_required=d["humanReviewRequired"]).model_dump(mode="json")
