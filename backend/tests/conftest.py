import pytest

from app.core import ratelimit


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Rate limits are process-wide; each test starts with clean counters."""
    ratelimit.reset()
    yield
    ratelimit.reset()
