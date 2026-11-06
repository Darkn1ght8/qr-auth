import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _isolate(settings, tmp_path):
    cache.clear()  # rate-limit counters live in the cache
    settings.PUBLIC_URL_FILE = tmp_path / "no-tunnel"
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    yield
    cache.clear()
