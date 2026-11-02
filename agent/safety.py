"""Hard stop (method part 2) and every piece of citizen-facing text that code owns.

`RedFlagGate` is a Strands hook on the graph. Before ANY agent node runs it checks the report with code:
fixed danger keywords (English + Tamil, agent/knowledge.py) OR the Strands Decider's urgency probability at or
above URGENT_THRESHOLD (agent/config.py; calibrate it on signed cases). If either fires it cancels the node,
so no model writes the answer; app.py ships TEXT["emergency"] instead.

The keyword list misses wording it has never seen. Every miss `ss measure` finds goes into FAILURES.md and
into URGENT_EN / URGENT_TA. Tamil strings below need a fluent reader's check before real use.
"""
from __future__ import annotations

from strands.hooks import BeforeNodeCallEvent, HookProvider, HookRegistry

from .tools import RunContext, do_assess_urgency

NO_CONTACT = {"en": "No department has been contacted.", "ta": "எந்தத் துறையும் தொடர்பு கொள்ளப்படவில்லை."}
TEXT = {
    "emergency": {
        "en": "URGENT: this may be a danger to life. If anyone is at risk, call 112 now (police, fire, ambulance) or 108 for an "
              "ambulance, and keep people away from the spot. Your report is flagged urgent for a person to review. "
              "This app has not contacted any department.",
        "ta": "அவசரம்: இது உயிருக்கு ஆபத்தாக இருக்கலாம். யாருக்காவது ஆபத்து இருந்தால் இப்போதே 112 அழையுங்கள் (காவல், தீயணைப்பு, "
              "ஆம்புலன்ஸ்) அல்லது ஆம்புலன்ஸுக்கு 108 அழையுங்கள்; அந்த இடத்திலிருந்து மக்களை விலக்கி வையுங்கள். உங்கள் புகார் "
              "அவசரமாகக் குறிக்கப்பட்டு ஒருவர் பார்வையிடுவார். இந்தச் செயலி எந்தத் துறையையும் தொடர்பு கொள்ளவில்லை.",
    },
    "escalation": {
        "en": "If anyone is in immediate danger, call 112 now (police, fire, ambulance) or 108 for an ambulance.",
        "ta": "யாராவது உடனடி ஆபத்தில் இருந்தால் இப்போதே 112 அழையுங்கள் (காவல், தீயணைப்பு, ஆம்புலன்ஸ்) அல்லது ஆம்புலன்ஸுக்கு 108 அழையுங்கள்.",
    },
    # Fixed summaries: shipped when the critic never passes (fail closed) and used by the backend fallback.
    "summary": {
        "CHECK_DUPLICATE": {"en": "This looks like an existing report ({ref}). A person will check whether they are the same. " + NO_CONTACT["en"],
                            "ta": "இது ஏற்கனவே உள்ள புகார் ({ref}) போலத் தெரிகிறது. இவை ஒன்றா என்பதை ஒருவர் சரிபார்ப்பார். " + NO_CONTACT["ta"]},
        "REQUEST_MORE_INFORMATION": {"en": "We need a few more details before this report can be acted on.",
                                     "ta": "இந்தப் புகாரின் மேல் நடவடிக்கை எடுக்க இன்னும் சில விவரங்கள் தேவை."},
        "ROUTE_TO_DEPARTMENT": {"en": "Recommended department: {dept}. This is a recommendation only. " + NO_CONTACT["en"],
                                "ta": "பரிந்துரைக்கப்பட்ட துறை: {dept}. இது பரிந்துரை மட்டுமே. " + NO_CONTACT["ta"]},
        "SUGGEST_COMMUNITY_ACTION": {"en": "{idea} " + NO_CONTACT["en"], "ta": "{idea} " + NO_CONTACT["ta"]},
        "ESCALATE_FOR_HUMAN_REVIEW": {"en": "Your report is saved and a person will review it. " + NO_CONTACT["en"],
                                      "ta": "உங்கள் புகார் சேமிக்கப்பட்டது; ஒருவர் இதைப் பார்வையிடுவார். " + NO_CONTACT["ta"]},
        "CREATE_REPORT": {"en": "Your report is recorded. " + NO_CONTACT["en"], "ta": "உங்கள் புகார் பதிவு செய்யப்பட்டது. " + NO_CONTACT["ta"]},
    },
    "questions": {
        "en": ["What exactly is wrong?", "Where is it (street or landmark)?", "Since when?"],
        "ta": ["சரியாக என்ன பிரச்சனை?", "எந்த இடத்தில் (தெரு அல்லது அடையாளம்)?", "எப்போதிலிருந்து?"],
    },
}


def check(ctx: RunContext) -> tuple[str | None, list[str]]:
    """("emergency", reasons) when code or the Decider (above threshold) says immediate danger, else (None, [])."""
    u = ctx.cache.get("urgency") or do_assess_urgency(ctx)
    if not u["urgent"]:
        return None, []
    return "emergency", (u["keywordHits"] or [f"Strands Decider p(urgent)={u['pUrgent']:.2f} >= {u['threshold']}"])


class RedFlagGate(HookProvider):
    """Cancels every agent node in the graph when the report shows immediate danger.

    The graph raises when its node is cancelled; app.py catches that, reads `tripped` and answers with
    TEXT["emergency"]. No model output can replace it."""

    def __init__(self, ctx: RunContext) -> None:
        self.ctx = ctx
        self.tripped: list[str] = []

    def register_hooks(self, registry: HookRegistry, **_: object) -> None:
        registry.add_callback(BeforeNodeCallEvent, self._before_node)

    def _before_node(self, event: BeforeNodeCallEvent) -> None:
        tier, reasons = check(self.ctx)
        if tier == "emergency":
            self.tripped = reasons
            event.cancel_node = "red flag: " + ", ".join(reasons)
