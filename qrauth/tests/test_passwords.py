"""Password change, forgotten-password reset by e-mail, admin password tools."""
import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from accounts.models import AuditEvent, LoginAudit, UserSession

User = get_user_model()
pytestmark = pytest.mark.django_db
PHONE = "Mozilla/5.0 (Linux; Android 14) Chrome/131.0 Mobile"


@pytest.fixture
def member():
    return User.objects.create_user("aigerim", "aigerim@example.kz", "Old-pass-123!")


def login(username="aigerim", password="Old-pass-123!", ua=PHONE):
    c = Client(HTTP_USER_AGENT=ua)
    assert c.post(reverse("accounts:login"), {"username": username, "password": password}).status_code == 302
    return c


def reset_url_from_mail() -> str:
    assert mail.outbox, "no e-mail sent"
    return re.search(r"https?://\S+/password/reset/\S+/\S+/", mail.outbox[-1].body).group(0)


# --- change password ---------------------------------------------------------------

def test_change_password_keeps_this_session_and_ends_others(member):
    laptop = login(ua="Mozilla/5.0 (Windows NT 10.0) Chrome/131.0")
    phone = login()
    response = phone.post(reverse("accounts:password_change"), {
        "old_password": "Old-pass-123!", "new_password1": "New-pass-456!", "new_password2": "New-pass-456!",
        "logout_others": "on",
    })
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.check_password("New-pass-456!")
    assert phone.get(reverse("accounts:cabinet")).status_code == 200          # still signed in here
    assert laptop.get(reverse("accounts:session_status")).status_code == 401  # logged out there
    assert LoginAudit.objects.filter(user=member, event=AuditEvent.PASSWORD_CHANGED, success=True).exists()
    assert mail.outbox and "aigerim@example.kz" in mail.outbox[-1].to         # "password changed" notice


def test_change_password_rejects_wrong_current_password(member):
    phone = login()
    response = phone.post(reverse("accounts:password_change"), {
        "old_password": "wrong", "new_password1": "New-pass-456!", "new_password2": "New-pass-456!",
    })
    assert response.status_code == 200
    member.refresh_from_db()
    assert member.check_password("Old-pass-123!")


def test_change_password_requires_login():
    response = Client().get(reverse("accounts:password_change"))
    assert response.status_code == 302 and reverse("accounts:login") in response["Location"]


# --- forgotten password -----------------------------------------------------------

def test_reset_sends_one_time_link_and_ends_all_sessions(member):
    phone = login()
    response = Client().post(reverse("accounts:password_reset"), {"email": "AIGERIM@example.kz"})
    assert response.status_code == 302 and response["Location"] == reverse("accounts:password_reset_sent")
    url = reset_url_from_mail()
    path = url.split("://", 1)[1].split("/", 1)[1]
    c = Client()
    assert c.get("/" + path).status_code == 200
    response = c.post("/" + path, {"new_password1": "Reset-pass-789!", "new_password2": "Reset-pass-789!"})
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.check_password("Reset-pass-789!")
    assert phone.get(reverse("accounts:session_status")).status_code == 401   # old sessions are gone
    assert not UserSession.objects.filter(user=member, ended_at__isnull=True).exists()
    # the link works only once
    assert Client().get("/" + path).status_code == 400


def test_reset_does_not_reveal_unknown_emails(member):
    known = Client().post(reverse("accounts:password_reset"), {"email": "aigerim@example.kz"})
    unknown = Client().post(reverse("accounts:password_reset"), {"email": "nobody@example.kz"})
    assert known.status_code == unknown.status_code == 302
    assert known["Location"] == unknown["Location"]
    assert len(mail.outbox) == 1


def test_reset_link_with_bad_token_is_rejected(member):
    assert Client().get("/password/reset/Mg/bad-token/").status_code == 400


def test_reset_is_rate_limited_per_address(member, settings):
    settings.RATE_LIMITS = {**settings.RATE_LIMITS, "password_reset_email": (2, 3600)}
    for _ in range(4):
        Client().post(reverse("accounts:password_reset"), {"email": "aigerim@example.kz"})
    assert len(mail.outbox) == 2


# --- admin tools -----------------------------------------------------------------------

@pytest.fixture
def admin_client():
    User.objects.create_user("boss", "boss@example.kz", "Adm1n-pass!", is_staff=True)
    return login("boss", "Adm1n-pass!")


def test_admin_sets_new_password_and_user_is_logged_out(admin_client, member):
    phone = login()
    response = admin_client.post(reverse("panel:user_action", args=[member.pk]), {
        "action": "set_password", "new_password1": "Admin-set-321!", "new_password2": "Admin-set-321!",
    })
    assert response.status_code == 302
    member.refresh_from_db()
    assert member.check_password("Admin-set-321!")
    assert phone.get(reverse("accounts:session_status")).status_code == 401


def test_admin_reset_link_is_shown_once_and_works(admin_client, member):
    admin_client.post(reverse("panel:user_action", args=[member.pk]), {"action": "reset_link"})
    page = admin_client.get(reverse("panel:user", args=[member.pk])).content.decode()
    link = re.search(r'value="(https?://[^"]+/password/reset/[^"]+/)"', page).group(1)
    assert "/password/reset/" in link
    again = admin_client.get(reverse("panel:user", args=[member.pk])).content.decode()
    assert link not in again  # shown only once
    path = "/" + link.split("://", 1)[1].split("/", 1)[1]
    assert Client().get(path).status_code == 200


def test_admin_cannot_reset_own_password_from_panel(admin_client):
    boss = User.objects.get(username="boss")
    admin_client.post(reverse("panel:user_action", args=[boss.pk]), {
        "action": "set_password", "new_password1": "Other-pass-999!", "new_password2": "Other-pass-999!",
    })
    boss.refresh_from_db()
    assert boss.check_password("Adm1n-pass!")


def test_ensure_admin_does_not_overwrite_a_changed_password(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "chief")
    monkeypatch.setenv("ADMIN_PASSWORD", "Env-secret-123")
    call_command("ensure_admin")
    chief = User.objects.get(username="chief")
    chief.set_password("Changed-on-site-1!")
    chief.save()
    call_command("ensure_admin")  # next restart
    chief.refresh_from_db()
    assert chief.check_password("Changed-on-site-1!")


# --- languages on real pages ----------------------------------------------------------

@pytest.mark.parametrize("lang,phrase", [
    ("ru", "Забыли пароль?"), ("kk", "Құпиясөзді ұмыттыңыз ба?"), ("en", "Forgot your password?"),
])
def test_login_page_in_three_languages(lang, phrase):
    c = Client()
    c.get(f"/login/password/?lang={lang}")
    assert phrase in c.get(reverse("accounts:login")).content.decode()


def test_form_errors_follow_the_language(member):
    c = Client()
    c.get("/?lang=en")
    page = c.post(reverse("accounts:login"), {"username": "aigerim", "password": "nope"}).content.decode()
    assert "Wrong username or password" in page
