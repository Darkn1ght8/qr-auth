"""Real-time session events: ending a session on the laptop logs the phone out instantly."""
import pytest
from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.test import Client
from django.urls import reverse

from accounts.models import UserSession
from config.asgi import application

pytestmark = pytest.mark.django_db(transaction=True)


def login(username="aruzhan", password="Str0ng-pass!", ua="Mozilla/5.0 (Linux; Android 14) Chrome/131.0 Mobile"):
    client = Client(HTTP_USER_AGENT=ua)
    response = client.post(reverse("accounts:login"), {"username": username, "password": password})
    assert response.status_code == 302
    return client


def socket_for(client) -> WebsocketCommunicator:
    cookie = f"{settings.SESSION_COOKIE_NAME}={client.cookies[settings.SESSION_COOKIE_NAME].value}"
    return WebsocketCommunicator(
        application, "/ws/session/", headers=[(b"cookie", cookie.encode()), (b"origin", b"http://testserver")]
    )


def test_ending_session_on_laptop_logs_phone_out_live(user):
    phone = login()
    laptop = login(ua="Mozilla/5.0 (Windows NT 10.0) Chrome/131.0")
    tracked_pk = UserSession.objects.get(session_key=phone.session.session_key).pk

    async def scenario():
        ws = socket_for(phone)
        connected, _ = await ws.connect()
        assert connected
        assert (await ws.receive_json_from(timeout=3))["type"] == "hello"
        # the laptop ends the phone's session (a normal HTTP POST, run in a worker thread)
        status = await sync_to_async(lambda: laptop.post(reverse("accounts:revoke", args=[tracked_pk])).status_code)()
        assert status == 302
        # the phone may first get "changed" (journal entry), then must get "revoked"
        for _ in range(5):
            message = await ws.receive_json_from(timeout=3)
            if message["type"] == "revoked":
                break
        await ws.disconnect()
        return message

    assert async_to_sync(scenario)()["type"] == "revoked"
    # and the phone's next request is anonymous
    assert phone.get(reverse("accounts:session_status")).status_code == 401
    assert phone.get(reverse("accounts:cabinet")).status_code == 302


def test_new_login_notifies_open_cabinet(user):
    laptop = login(ua="Mozilla/5.0 (Windows NT 10.0) Chrome/131.0")

    async def scenario():
        ws = socket_for(laptop)
        await ws.connect()
        assert (await ws.receive_json_from(timeout=3))["type"] == "hello"
        await sync_to_async(login)()  # the phone signs in -> the laptop's cabinet must refresh
        message = await ws.receive_json_from(timeout=3)
        await ws.disconnect()
        return message

    assert async_to_sync(scenario)()["type"] == "changed"


def test_anonymous_socket_is_refused():
    async def scenario():
        ws = WebsocketCommunicator(application, "/ws/session/", headers=[(b"origin", b"http://testserver")])
        connected, code = await ws.connect()
        return connected, code

    connected, code = async_to_sync(scenario)()
    assert not connected and code == 4401


def test_session_status_endpoint(user):
    phone = login()
    assert phone.get(reverse("accounts:session_status")).json()["active"] is True
    assert Client().get(reverse("accounts:session_status")).status_code == 401


def test_healthz():
    assert Client().get("/healthz/").content == b"ok"
