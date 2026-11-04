"""Live setup check. Run on YOUR machine with DECIDER_API_KEY and AWS credentials set (project root):

    python -m agent.check

Step 1 calls the hosted Strands Decider (same request as kit/blocks/b09_decider.py).
Step 2 runs the full agent (planner -> critic graph on Amazon Bedrock) on an ordinary report.
Step 3 runs a danger report: the red-flag hook must cancel the agents and ship the fixed 112 text.
It exits non-zero on any failure and never substitutes a made-up answer."""
import sys
import traceback

from . import config
from .app import run
from .decider_client import DeciderClient
from .models import model_label
from .tools import _questions

ROUTINE = {"id": "check-1", "text": "The street lights in our lane have not worked for a week and it is very dark at night.",
           "category": "Street lighting", "locality": "KK Nagar"}
DANGER = {"id": "check-2", "text": "Live wire hanging from the electric pole near the bus stop, sparking when it rains.",
          "category": "Electricity", "locality": "Anna Nagar"}


def main() -> int:
    print(f"Decider URL: {config.DECIDER_URL}\nModel: {model_label()}" + (f" ({config.REGION})" if config.MODEL_PROVIDER == "bedrock" else ""))
    try:
        a = DeciderClient().decide(f"Category: {DANGER['category']}. Report: {DANGER['text']}", _questions())
        print("[1/3] Decider OK:", a)
    except Exception as e:
        print(f"[1/3] Decider FAILED: {type(e).__name__}: {e}")
        return 1
    for step, case, want in (("2/3", ROUTINE, "agent"), ("3/3", DANGER, "emergency")):
        try:
            out = run(case)
        except Exception:
            print(f"[{step}] FAILED:")
            traceback.print_exc(limit=3)
            return 1
        ok = out["meta"]["path"] == want
        print(f"[{step}] {'OK' if ok else 'UNEXPECTED'}: path={out['meta']['path']} action={out['plan']['action']} "
              f"critic_ok={out['meta']['critic_ok']} fixed={out['meta']['fixed']}")
        if not ok:
            return 1
    print("All good.")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
