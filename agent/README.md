# agent/

The Strands agent `ss measure` scores and the FastAPI backend calls (`engine.StrandsDeciderEngine` → `app.review`).
See `../DESIGN.md` for the graph, the hook and what code owns.

| File | Role |
|---|---|
| `app.py` | planner → critic Strands graph, red-flag hook, `run(case)` for `ss measure`, CLI |
| `safety.py` | `RedFlagGate` hook and all fixed citizen-facing text (EN + TA) |
| `enforce.py` | code-owned overrides, citations, fail-closed text, `ReviewPlan` builder |
| `tools.py` | five bound `@tool`s, one cached Decider call, guidance + language + Amazon Translate helpers |
| `knowledge.py`, `config.py`, `similarity.py` | facts and thresholds the model cannot change |
| `baseline.py` | one-prompt baseline (same model, same guidance) |
| `score.py` | deterministic scoring + Strands Evals rubric |
| `data/guidance.json` | the only ids the agent may cite |
| `check.py` | live check: Decider, an ordinary report, a danger report |
