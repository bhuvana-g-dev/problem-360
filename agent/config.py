"""Agent thresholds and settings. Defaults are UNCALIBRATED starting points: tune them on signed cases
(`python -m agent.evals.run_eval`) before trusting them, as the workshop kit's method requires."""
import os


def _f(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


URGENT_THRESHOLD = _f("P360_URGENT_THRESHOLD", 0.80)      # Decider yes-probability that marks a report urgent
DUPLICATE_THRESHOLD = _f("P360_DUPLICATE_THRESHOLD", 0.50)  # similarity score that triggers CHECK_DUPLICATE
DEPARTMENT_MIN_CONFIDENCE = _f("P360_DEPARTMENT_MIN_CONF", 0.50)
COMMUNITY_THRESHOLD = _f("P360_COMMUNITY_THRESHOLD", 0.60)
VAGUE_THRESHOLD = _f("P360_VAGUE_THRESHOLD", 0.70)
MIN_DESCRIPTION_CHARS = 15
DUPLICATE_WINDOW_DAYS = int(os.environ.get("P360_DUPLICATE_DAYS", 30))

MODEL_ID = os.environ.get("SHIP_MODEL", "us.amazon.nova-2-lite-v1:0")  # same default as the workshop kit
REGION = os.environ.get("AWS_REGION", "us-east-1")
# Model provider switch (agent/models.py): bedrock (default) | ollama | litellm
MODEL_PROVIDER = os.environ.get("P360_MODEL_PROVIDER", "bedrock").lower()
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "")
DECIDER_URL = os.environ.get("DECIDER_URL", "https://da25tnxy06gjk.cloudfront.net")  # hosted by AWS UG Madurai (from b09_decider.py)


def decider_key() -> str | None:
    return os.environ.get("DECIDER_API_KEY")
