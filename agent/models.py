"""Which model the agents run on. One setting, same agent code (the provider is the only thing that changes).

    P360_MODEL_PROVIDER=bedrock   (default) Amazon Bedrock, SHIP_MODEL + AWS_REGION. What `ss measure` and the hackathon use.
    P360_MODEL_PROVIDER=ollama    a local model, free: install https://ollama.com, `ollama pull qwen2.5:7b`,
                                  `pip install ollama`; OLLAMA_HOST (default http://localhost:11434), OLLAMA_MODEL.
    P360_MODEL_PROVIDER=litellm   OpenAI, Gemini, Anthropic and others through LiteLLM: `pip install litellm`,
                                  LITELLM_MODEL (e.g. "gemini/gemini-2.0-flash"), the provider's API key in its usual env var.

Pick a model that supports tool calling: the planner calls five tools and returns structured output.
Numbers from one provider say nothing about another: re-run `ss measure` after switching (the kit's judge stays on Bedrock).
"""
from __future__ import annotations

from . import config


def make_model(temperature: float = 0.2):
    p = config.MODEL_PROVIDER
    if p == "bedrock":
        from strands.models import BedrockModel
        return BedrockModel(model_id=config.MODEL_ID, region_name=config.REGION, temperature=temperature)
    if p == "ollama":
        try:
            from strands.models.ollama import OllamaModel
        except ImportError as e:
            raise RuntimeError("P360_MODEL_PROVIDER=ollama needs the ollama package: pip install ollama") from e
        return OllamaModel(config.OLLAMA_HOST, model_id=config.OLLAMA_MODEL, temperature=temperature)
    if p == "litellm":
        if not config.LITELLM_MODEL:
            raise RuntimeError("P360_MODEL_PROVIDER=litellm needs LITELLM_MODEL, e.g. gemini/gemini-2.0-flash")
        try:
            from strands.models.litellm import LiteLLMModel
        except ImportError as e:
            raise RuntimeError("P360_MODEL_PROVIDER=litellm needs the litellm package: pip install litellm") from e
        return LiteLLMModel(model_id=config.LITELLM_MODEL, params={"temperature": temperature})
    raise RuntimeError(f"P360_MODEL_PROVIDER must be bedrock, ollama or litellm (got {p!r})")


def model_label() -> str:
    """What is stored with each decision, so a record always says which model made it."""
    return {"bedrock": f"bedrock:{config.MODEL_ID}", "ollama": f"ollama:{config.OLLAMA_MODEL}",
            "litellm": f"litellm:{config.LITELLM_MODEL}"}.get(config.MODEL_PROVIDER, config.MODEL_PROVIDER)
