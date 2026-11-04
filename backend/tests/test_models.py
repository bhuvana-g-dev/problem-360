"""Model-provider switch (agent/models.py). No network calls: only which Strands model class gets built."""
import pytest
from strands.models import BedrockModel

from agent import config, models


def test_default_is_bedrock(monkeypatch):
    monkeypatch.setattr(config, "MODEL_PROVIDER", "bedrock")
    assert isinstance(models.make_model(), BedrockModel) and models.model_label().startswith("bedrock:")


def test_ollama_builds_a_local_model_or_says_what_to_install(monkeypatch):
    monkeypatch.setattr(config, "MODEL_PROVIDER", "ollama")
    try:
        m = models.make_model()
    except RuntimeError as e:
        assert "pip install ollama" in str(e)
    else:
        assert type(m).__name__ == "OllamaModel" and m.config["model_id"] == config.OLLAMA_MODEL
    assert models.model_label() == f"ollama:{config.OLLAMA_MODEL}"


def test_litellm_needs_a_model_name(monkeypatch):
    monkeypatch.setattr(config, "MODEL_PROVIDER", "litellm")
    monkeypatch.setattr(config, "LITELLM_MODEL", "")
    with pytest.raises(RuntimeError, match="LITELLM_MODEL"):
        models.make_model()


def test_unknown_provider_is_refused(monkeypatch):
    monkeypatch.setattr(config, "MODEL_PROVIDER", "mystery")
    with pytest.raises(RuntimeError, match="bedrock, ollama or litellm"):
        models.make_model()
