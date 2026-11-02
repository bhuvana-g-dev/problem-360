"""The real Strands graph (planner -> critic), real hook, real tools and real enforcement.
Test doubles: ScriptedModel (LLM for both agents) and FakeDecider (hosted endpoint)."""
import pytest

from agent.app import review
from agent.decider_client import DeciderClient, DeciderError
from agent.engine import StrandsDeciderEngine
from agent.score import score
from tests.fakes import FakeDecider, ScriptedModel

NO_NEARBY = lambda loc, days, ex: []


def engine(force=None, decider=None, critic_ok=True):
    return StrandsDeciderEngine(decider=decider or FakeDecider(), model_factory=lambda: ScriptedModel(force, critic_ok))


def report(text, category="Roads & potholes", **kw):
    return {"id": "r1", "description": text, "category": category, "locality": "Anna Nagar", "locationText": "", "coordinates": None, **kw}


def test_tools_run_through_the_real_strands_graph():
    d = engine().decide(report("Big pothole near the signal, bikes are slipping badly."), NO_NEARBY)
    agent_tools = {r["tool"] for r in d["toolRuns"] if r["invokedBy"] == "agent"}
    assert agent_tools == {"search_nearby_reports", "detect_duplicates", "assess_urgency", "recommend_department", "recommend_community_action"}
    assert all(r["invokedBy"] != "enforcer" for r in d["toolRuns"])
    assert d["action"] == "ROUTE_TO_DEPARTMENT" and d["department"]["id"] == "roads" and d["overrides"] == []
    assert d["critic"]["ok"] is True and d["externalContact"] is False and d["source"] == "strands_agent"
    assert "G-DEPT-roads" in d["citations"] and "No department has been contacted." in d["summary"]


def test_red_flag_hook_cancels_the_agents_and_ships_fixed_text():
    before = ScriptedModel.planner_runs
    d = engine(force="CREATE_REPORT").decide(report("Live wire hanging near the bus stop and sparking", "Electricity"), NO_NEARBY)
    assert ScriptedModel.planner_runs == before                      # no model ran: the hook stopped the graph first
    assert d["action"] == "FLAG_URGENT" and d["source"] == "red_flag_hook" and d["humanReviewRequired"] is True
    assert "112" in d["summary"] and not any(r["invokedBy"] == "agent" for r in d["toolRuns"])


def test_decider_alone_trips_the_hook_without_keywords():
    class DangerDecider(FakeDecider):  # no danger keyword in the text; only the Decider's probability is above threshold
        def decide(self, state, questions):
            a = super().decide(state, questions)
            a["urgent"]["noul"] = 0.97
            return a
    d = engine(decider=DangerDecider()).decide(report("A man is lying on the road and not moving, people walk past him.", "Public safety"), NO_NEARBY)
    assert d["action"] == "FLAG_URGENT" and d["urgency"]["keywordHits"] == [] and d["source"] == "red_flag_hook"


def test_tamil_report_gets_tamil_fixed_emergency_text():
    d = engine().decide(report("தெருவில் மின்கம்பி அறுந்து கிடக்கிறது, குழந்தைகள் அருகில் விளையாடுகிறார்கள்", "Electricity"), NO_NEARBY)
    assert d["action"] == "FLAG_URGENT" and d["language"] == "ta" and "112" in d["summary"] and "அவசரம்" in d["summary"]


def test_critic_never_passing_fails_closed_to_fixed_text():
    d = engine(critic_ok=False).decide(report("Big pothole near the signal, bikes are slipping badly."), NO_NEARBY)
    assert d["critic"]["ok"] is False and d["critic"]["passes"] == 2
    assert d["action"] == "ROUTE_TO_DEPARTMENT" and d["summary"].startswith("Recommended department:") and "Scripted" not in d["summary"]


def test_vague_report_forced_to_request_more_information():
    d = engine().decide(report("bad", "Other"), NO_NEARBY)
    assert d["action"] == "REQUEST_MORE_INFORMATION" and d["questions"]


def test_duplicate_detected_from_nearby_reports():
    near = [{"id": "old", "referenceId": "P360-OLD", "category": "Street lighting", "locality": "Anna Nagar", "status": "Submitted", "coordinates": None,
             "description": "Street light not working near the temple on 5th street", "locationText": ""}]
    d = engine().decide(report("Street light not working near the temple on 5th street", "Street lighting"), lambda *a: near)
    assert d["action"] == "CHECK_DUPLICATE" and d["duplicate"]["referenceId"] == "P360-OLD"


def test_community_action_only_for_safe_categories():
    d = engine(force="SUGGEST_COMMUNITY_ACTION").decide(report("Litter and dry leaves piled at the vacant plot", "Waste & sanitation"), NO_NEARBY)
    assert d["action"] == "SUGGEST_COMMUNITY_ACTION" and d["communityAction"]["suggestion"]
    d2 = engine(force="SUGGEST_COMMUNITY_ACTION").decide(report("Big pothole near the signal, bikes are slipping badly."), NO_NEARBY)
    assert d2["action"] == "ROUTE_TO_DEPARTMENT" and d2["overrides"] and "Scripted" not in d2["summary"]


def test_missing_decider_key_fails_instead_of_faking(monkeypatch):
    """Code computes every fact before any agent runs; without a key that raises, so the caller fails closed. Nothing is fabricated."""
    monkeypatch.delenv("DECIDER_API_KEY", raising=False)
    with pytest.raises(DeciderError, match="DECIDER_API_KEY"):
        engine(decider=DeciderClient(url="http://127.0.0.1:9", key=None)).decide(report("Big pothole near the signal, bikes slipping."), NO_NEARBY)


def test_score_flags_contact_claims_and_invented_numbers():
    case = {"id": "x", "text": "Big pothole near the signal", "job": "routing", "nearby": [],
            "expected": {"action": "ROUTE_TO_DEPARTMENT", "escalation": "none", "community_suitable": False}}
    out = review({**report(case["text"]), "id": "x"}, NO_NEARBY, decider=FakeDecider(), model_factory=lambda: ScriptedModel())
    good = score(case, out)
    assert good["unsafe"] == [] and good["risk_correct"] and good["citations"] == good["citations_valid"] > 0
    bad = {**out, "plan": {**out["plan"], "summary": "We have informed the roads department, call 98765 43210."}}
    assert len(score(case, bad)["unsafe"]) == 2
    ok = {**out, "plan": {**out["plan"], "summary": "No department has been contacted. Call 112 if anyone is hurt."}}
    assert score(case, ok)["unsafe"] == []
