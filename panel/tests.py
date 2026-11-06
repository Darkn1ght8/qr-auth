"""Admin panel: access control, user data (e-mails), actions, export, live updates."""
import pytest
from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from accounts.models import AuditEvent, LoginAudit, UserSession

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_user():
    return User.objects.create_user("boss", "boss@example.kz", "Adm1n-pass!", is_staff=True)


@pytest.fixture
def member():
    return User.objects.create_user("aigerim", "aigerim@example.kz", "Str0ng-pass!")


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    assert c.post(reverse("accounts:login"), {"username": "boss", "password": "Adm1n-pass!"}).status_code == 302
    return c


def login(username, password):
    c = Client(HTTP_USER_AGENT="Mozilla/5.0 (Linux; Android 14) Chrome/131.0 Mobile")
    assert c.post(reverse("accounts:login"), {"username": username, "password": password}).status_code == 302
    return c


PAGES = ["panel:dashboard", "panel:users", "panel:sessions", "panel:audit", "panel:qr"]


def test_anonymous_is_sent_to_login():
    response = Client().get(reverse("panel:dashboard"))
    assert response.status_code == 302 and reverse("accounts:login") in response["Location"]


def test_regular_user_gets_403(member):
    c = login("aigerim", "Str0ng-pass!")
    for name in PAGES:
        assert c.get(reverse(name)).status_code == 403
    assert c.get(reverse("panel:users_export")).status_code == 403


def test_admin_sees_all_pages(admin_client, member):
    for name in PAGES:
        assert admin_client.get(reverse(name)).status_code == 200, name
    assert admin_client.get(reverse("panel:user", args=[member.pk])).status_code == 200


def test_users_list_shows_emails_and_logins(admin_client, member):
    login("aigerim", "Str0ng-pass!")
    page = admin_client.get(reverse("panel:users")).content.decode()
    assert "aigerim@example.kz" in page and "boss@example.kz" in page
    dashboard = admin_client.get(reverse("panel:dashboard")).content.decode()
    assert "aigerim" in dashboard  # recent logins / registrations


def test_user_search_by_email(admin_client, member):
    page = admin_client.get(reverse("panel:users"), {"q": "aigerim@"}).content.decode()
    assert "aigerim@example.kz" in page and "boss@example.kz" not in page


def test_csv_export_contains_emails(admin_client, member):
    response = admin_client.get(reverse("panel:users_export"))
    body = response.content.decode("utf-8-sig")
    assert response["Content-Type"].startswith("text/csv")
    assert "aigerim@example.kz" in body and "Пошта" in body
    assert LoginAudit.objects.filter(event=AuditEvent.ADMIN_ACTION, details__action="export_users").exists()


def test_block_ends_sessions_and_prevents_login(admin_client, member):
    phone = login("aigerim", "Str0ng-pass!")
    response = admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "block"})
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.is_active is False
    assert not UserSession.objects.filter(user=member, ended_at__isnull=True).exists()
    assert phone.get(reverse("accounts:session_status")).status_code == 401
    assert Client().post(reverse("accounts:login"), {"username": "aigerim", "password": "Str0ng-pass!"}).status_code == 200
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "unblock"})
    member.refresh_from_db()
    assert member.is_active is True


def test_admin_cannot_block_or_delete_self(admin_client, admin_user):
    for action in ("block", "delete", "remove_admin"):
        admin_client.post(reverse("panel:user_action", args=[admin_user.pk]), {"action": action, "confirm_username": "boss"})
    admin_user.refresh_from_db()
    assert admin_user.is_active and admin_user.is_staff


def test_delete_requires_typed_username(admin_client, member):
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "delete", "confirm_username": "wrong"})
    assert User.objects.filter(pk=member.pk).exists()
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "delete", "confirm_username": "aigerim"})
    assert not User.objects.filter(pk=member.pk).exists()


def test_grant_and_revoke_admin(admin_client, member):
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "make_admin"})
    member.refresh_from_db()
    assert member.is_staff
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "remove_admin"})
    member.refresh_from_db()
    assert not member.is_staff


def test_end_single_session_from_panel(admin_client, member):
    phone = login("aigerim", "Str0ng-pass!")
    tracked = UserSession.objects.get(user=member, ended_at__isnull=True)
    admin_client.post(reverse("panel:session_end", args=[tracked.pk]), {"next": "https://evil.example/"})
    tracked.refresh_from_db()
    assert tracked.ended_at is not None
    assert phone.get(reverse("accounts:session_status")).status_code == 401


def test_actions_require_post(admin_client, member):
    assert admin_client.get(reverse("panel:user_action", args=[member.pk])).status_code == 405


def test_register_requires_unique_email_and_blocks_reserved_names(member):
    c = Client()
    base = {"password1": "Very-strong-pass-1", "password2": "Very-strong-pass-1", "first_name": ""}
    r = c.post(reverse("accounts:register"), {**base, "username": "newbie", "email": ""})
    assert r.status_code == 200 and not User.objects.filter(username="newbie").exists()
    r = c.post(reverse("accounts:register"), {**base, "username": "newbie", "email": "AIGERIM@example.kz"})
    assert not User.objects.filter(username="newbie").exists()
    r = c.post(reverse("accounts:register"), {**base, "username": "admin", "email": "x@example.kz"})
    assert not User.objects.filter(username="admin").exists()
    r = c.post(reverse("accounts:register"), {**base, "username": "newbie", "email": "newbie@example.kz"})
    assert r.status_code == 302 and User.objects.get(username="newbie").email == "newbie@example.kz"


def test_ensure_admin_command(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "chief")
    monkeypatch.setenv("ADMIN_PASSWORD", "Env-secret-123")
    call_command("ensure_admin")
    chief = User.objects.get(username="chief")
    assert chief.is_staff and chief.is_superuser and chief.check_password("Env-secret-123")


@pytest.mark.django_db(transaction=True)
def test_admin_panel_gets_live_event_on_new_registration(admin_user):
    admin = Client()
    admin.post(reverse("accounts:login"), {"username": "boss", "password": "Adm1n-pass!"})
    cookie = f"{settings.SESSION_COOKIE_NAME}={admin.cookies[settings.SESSION_COOKIE_NAME].value}"

    def register():
        Client().post(reverse("accounts:register"), {
            "username": "fresh", "email": "fresh@example.kz", "first_name": "",
            "password1": "Very-strong-pass-1", "password2": "Very-strong-pass-1",
        })

    async def scenario():
        ws = WebsocketCommunicator(
            __import__("config.asgi", fromlist=["application"]).application, "/ws/session/",
            headers=[(b"cookie", cookie.encode()), (b"origin", b"http://testserver")],
        )
        assert (await ws.connect())[0]
        assert (await ws.receive_json_from(timeout=3))["type"] == "hello"
        await sync_to_async(register)()
        message = await ws.receive_json_from(timeout=3)
        await ws.disconnect()
        return message

    assert async_to_sync(scenario)()["type"] == "changed"
