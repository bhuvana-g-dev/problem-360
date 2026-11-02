"""The baseline to beat: one agent, one prompt, same model, same guidance and the same nearby reports pasted in.
No tools, no Decider, no graph, no critic, no hook, no code-owned facts."""
import json
import time

from strands import Agent

from . import tools
from .app import LANG_NAME, _model
from .knowledge import DEPARTMENTS
from .plan import ReviewPlan


def run(case):
    t0 = time.time()
    lang = tools.language_of(case["text"])
    guidance = "\n".join(f"{g['id']}: {g['text']}" for g in tools.guidance()["items"])
    depts = "\n".join(f"{k}: {v['name']} ({v['hint']})" for k, v in DEPARTMENTS.items())
    nearby = json.dumps([{k: x.get(k) for k in ("id", "referenceId", "category", "description", "locationText")}
                         for x in case.get("nearby") or []], ensure_ascii=False)
    a = Agent(model=_model(), callback_handler=None, structured_output_model=ReviewPlan, system_prompt=(
        "You review one citizen civic report for Problem 360 in Madurai and choose the next action: FLAG_URGENT (immediate danger), "
        "CHECK_DUPLICATE, REQUEST_MORE_INFORMATION, ROUTE_TO_DEPARTMENT, SUGGEST_COMMUNITY_ACTION (only if neighbours can safely help), "
        "ESCALATE_FOR_HUMAN_REVIEW or CREATE_REPORT. Answer helpfully and safely. Never say anyone was contacted.\n"
        f"Departments:\n{depts}\nCite only these guidance ids:\n{guidance}"))
    msg = (f"Answer in {LANG_NAME[lang]}.\nCategory: {case.get('category')}. Locality: {case.get('locality')}. "
           f"Landmark: {case.get('locationText') or 'not given'}.\nRecent nearby reports: {nearby}\nReport: {case['text']}")
    ans = a(msg).structured_output
    if ans is None:
        raise RuntimeError("baseline returned no structured answer")
    return {"plan": ans.model_dump(mode="json"), "meta": {"path": "baseline", "latency_ms": int((time.time() - t0) * 1000)}}
