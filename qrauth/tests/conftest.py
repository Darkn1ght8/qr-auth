import json

import pytest
from django.core.cache import cache

UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
UA_PHONE = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Mobile Safari/537.36"
FP = "device-123|kk-KZ|Asia/Almaty|1920x1080x24"


@pytest.fixture(autouse=True)
def _isolate(settings, tmp_path):
    cache.clear()
    settings.PUBLIC_URL_FILE = tmp_path / "no-tunnel"  # ignore a tunnel started by runpublic
    settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    settings.QR_HMAC_KEY = "test-hmac-key"
    yield
    cache.clear()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(username="aruzhan", password="Str0ng-pass!")


@pytest.fixture
def other_user(django_user_model):
    return django_user_model.objects.create_user(username="attacker", password="Str0ng-pass!")


@pytest.fixture
def desktop(client):
    client.defaults["HTTP_USER_AGENT"] = UA_DESKTOP
    return client


@pytest.fixture
def phone(user):
    from django.test import Client

    c = Client(HTTP_USER_AGENT=UA_PHONE)
    c.force_login(user)
    return c


def post_json(client, url, data):
    return client.post(url, data=json.dumps(data), content_type="application/json")
