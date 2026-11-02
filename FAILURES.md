# Failures we found and fixed

Judges trust a project that shows what broke. Add one `## ` entry per real failure, newest first.
`ss ship` needs at least one. Keep the numbers from `results/MEASURE.md`, before and after.

<!-- Copy this block for each failure:

## <short name> (<date>)
- What broke: <the case id and what the plan said>
- How we found it: <ss measure / a tester / red-team case>
- What we changed: <file and change>
- After: <the re-measured number>

-->

## "Fire extinguisher" tripped the danger keywords (2026-11-02)
- What broke: case `n01` ("The fire extinguisher box at the community hall is empty and needs to be refilled") matched the
  `fire` danger keyword, so it would be flagged urgent and the red-flag hook would cancel the agents on a routine request.
- How we found it: the original Problem 360 rule-based eval (`agent/evals/run_eval.py --engine baseline`, unsigned draft labels)
  listed `n01: expected ROUTE_TO_DEPARTMENT, got FLAG_URGENT`.
- What we changed: `agent/knowledge.py` URGENT_EN, the `fire` pattern now skips "fire extinguisher / exit / safety" as it already
  skipped "fire station / brigade / engine / department / office".
- After: keyword-only check over all 45 cases in `cases.jsonl` (no model): false alarms 1 -> 0; urgent cases caught by keywords
  9/13 before and after. `ss measure` not yet run (needs AWS + Decider key); re-measure and add the number here.
