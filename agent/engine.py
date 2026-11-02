"""Backend entry point. The FastAPI DecisionService calls `StrandsDeciderEngine().decide(report, nearby_provider)`.
It runs exactly the agent `ss measure` scores (agent/app.py review) and returns the stored decision dict."""
from __future__ import annotations

from .app import review


class StrandsDeciderEngine:
    """Raises on any failure (no Decider key, no AWS credentials, Decider down): the caller fails closed."""

    def __init__(self, decider=None, model_factory=None):
        self.decider, self.model_factory = decider, model_factory

    def decide(self, report: dict, nearby_provider) -> dict:
        return review(report, nearby_provider, decider=self.decider, model_factory=self.model_factory)["decision"]
