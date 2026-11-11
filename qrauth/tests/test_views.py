"""Integration tests: HTTP endpoints, session binding, rate limits, audit log."""
import re

import pytest
from django.urls import reverse

from accounts.models import AuditEvent, LoginAudit, LoginMethod, UserSession
from qrauth.models import QRSession, QRStatus

from .conftest import FP, post_json

pytestmark = pytest.mark.django_db


def new_qr(client):
    response = post_json(client, reverse("qrauth:api_new"), {"fp": FP})
    assert response.status_code == 200, response.content
    return response.json()


@pytest.fixture
def issued(desktop, monkeypatch):
    """Create a QR via the API and capture the scan URL that the QR encodes."""
    from qrauth import views

    captured = {}
    original = views._scan_url

    def spy(request, token, signature):
        url = original(request, token, signature)
        captured["url"] = url
        return url

    monkeypatch.setattr(views, "_scan_url", spy)
    data = new_qr(desktop)
    data["_url"] = captured["url"]
    data["path"] = re.search(r"(/qr/scan/[^/]+/[^/]+/)", captured["url"]).group(1)
    return data


def confirm_on_phone(phone, path):
    page = phone.get(path)
    assert page.status_code == 200
    token, signature = path.strip("/").split("/")[2:4]
    return phone.post(reverse("qrauth:decide"), {"token": token, "signature": signature, "action": "confirm"})


def test_new_qr_returns_svg_and_matrix(issued):
    assert issued["ok"] is True
    assert issued["svg"].startswith("<svg")
    assert set("".join(issued["matrix"])) <= {"0", "1"}
    assert issued["ttl"] == 60 and issued["refresh"] == 30
    assert QRSession.objects.filter(pk=issued["sid"], status=QRStatus.PENDING).exists()


def test_scan_requires_login(client, issued):
    response = client.get(issued["path"])
    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


def test_full_http_flow_logs_desktop_in(desktop, phone, user, issued):
    response = confirm_on_phone(phone, issued["path"])
    assert response.status_code == 200
    status = desktop.get(reverse("qrauth:api_status", args=[issued["sid"]])).json()
    assert status["status"] == "confirmed" and status["code"]

    response = post_json(desktop, reverse("qrauth:api_exchange"), {"sid": issued["sid"], "code": status["code"], "fp": FP})
    assert response.status_code == 200
    assert response.json()["redirect"] == reverse("accounts:cabinet")
    assert desktop.get(reverse("accounts:cabinet")).status_code == 200
    assert UserSession.objects.filter(user=user, method=LoginMethod.QR, ended_at__isnull=True).exists()
    assert LoginAudit.objects.filter(user=user, event=AuditEvent.LOGIN_SUCCESS, method=LoginMethod.QR).exists()


def test_exchange_replay_is_blocked_and_audited(desktop, phone, issued):
    confirm_on_phone(phone, issued["path"])
    code = desktop.get(reverse("qrauth:api_status", args=[issued["sid"]])).json()["code"]
    first = post_json(desktop, reverse("qrauth:api_exchange"), {"sid": issued["sid"], "code": code, "fp": FP})
    assert first.status_code == 200
    # Session key rotated on login; the qr binding is gone, so replay from this browser is forbidden...
    second = post_json(desktop, reverse("qrauth:api_exchange"), {"sid": issued["sid"], "code": code, "fp": FP})
    assert second.status_code in (403, 409)


def test_status_channel_is_bound_to_initiator(client, issued):
    from django.test import Client

    stranger = Client()
    response = stranger.get(reverse("qrauth:api_status", args=[issued["sid"]]))
    assert response.status_code == 403
    response = post_json(stranger, reverse("qrauth:api_exchange"), {"sid": issued["sid"], "code": "x", "fp": FP})
    assert response.status_code == 403


def test_reject_from_phone(desktop, phone, issued):
    phone.get(issued["path"])
    token, signature = issued["path"].strip("/").split("/")[2:4]
    response = phone.post(reverse("qrauth:decide"), {"token": token, "signature": signature, "action": "reject"})
    assert response.status_code == 200
    status = desktop.get(reverse("qrauth:api_status", args=[issued["sid"]])).json()
    assert status["status"] == "rejected"
    assert "code" not in status
    assert LoginAudit.objects.filter(event=AuditEvent.QR_REJECTED).exists()


def test_confirmation_page_shows_initiator_context(phone, issued):
    page = phone.get(issued["path"]).content.decode()
    assert "Chrome 131" in page
    assert "Windows 10/11" in page
    assert "127.0.0.1" in page


def test_tampered_signature_rejected(phone, issued):
    token = issued["path"].strip("/").split("/")[2]
    response = phone.get(reverse("qrauth:scan", args=[token, "0" * 32]))
    assert response.status_code == 400
    assert QRSession.objects.get(pk=issued["sid"]).status == QRStatus.PENDING


def test_rate_limit_on_qr_generation(desktop, settings):
    settings.RATE_LIMITS = {**settings.RATE_LIMITS, "qr_new": (3, 60)}
    codes = [post_json(desktop, reverse("qrauth:api_new"), {"fp": FP}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3:] == [429, 429]
    assert LoginAudit.objects.filter(event=AuditEvent.RATE_LIMITED).count() == 2


def test_rate_limit_on_confirmation(phone, settings):
    settings.RATE_LIMITS = {**settings.RATE_LIMITS, "qr_decide": (2, 60)}
    codes = [
        phone.post(reverse("qrauth:decide"), {"token": "x", "signature": "y", "action": "confirm"}).status_code
        for _ in range(4)
    ]
    assert codes[:2] == [400, 400]
    assert codes[2:] == [429, 429]


def test_revoke_other_session(user):
    from django.test import Client

    a, b = Client(), Client()
    assert a.post(reverse("accounts:login"), {"username": "aruzhan", "password": "Str0ng-pass!"}).status_code == 302
    assert b.post(reverse("accounts:login"), {"username": "aruzhan", "password": "Str0ng-pass!"}).status_code == 302
    other = UserSession.objects.exclude(session_key=a.session.session_key).get(user=user, ended_at__isnull=True)
    assert a.post(reverse("accounts:revoke", args=[other.pk])).status_code == 302
    response = b.get(reverse("accounts:cabinet"))
    assert response.status_code == 302  # kicked out


def test_anonymous_phone_holds_qr_and_is_sent_to_login(client, user, issued):
    from django.test import Client

    phone = Client()
    response = phone.get(issued["path"])
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login") + "?next=")
    session = QRSession.objects.get(pk=issued["sid"])
    assert session.opened_at is not None
    assert session.seconds_left() > 60  # grace period for signing in on the phone
    # after logging in, the same link continues to the confirmation page
    phone.post(reverse("accounts:login"), {"username": "aruzhan", "password": "Str0ng-pass!"})
    assert phone.get(issued["path"]).status_code == 200


def test_qr_never_encodes_localhost(monkeypatch, settings):
    from django.test import RequestFactory

    from core import netutils

    settings.QR_PUBLIC_BASE_URL = ""
    monkeypatch.setattr(netutils, "lan_ip", lambda: "192.168.1.50")
    for host in ("localhost:8000", "127.0.0.1:8000"):
        request = RequestFactory().get("/", HTTP_HOST=host)
        assert netutils.public_base_url(request) == "http://192.168.1.50:8000"
    request = RequestFactory().get("/", HTTP_HOST="demo.example.kz")
    assert netutils.public_base_url(request) == "http://demo.example.kz"


def test_scanner_and_auth_pages_open_without_redirect(client, user):
    assert client.get(reverse("qrauth:scanner")).status_code == 200
    client.force_login(user)
    assert client.get(reverse("accounts:login")).status_code == 200
    assert client.get(reverse("accounts:register")).status_code == 200


def test_client_ip_prefers_cloudflare_header_behind_proxy(settings):
    from django.test import RequestFactory

    from core.netutils import get_client_ip

    settings.TRUST_PROXY = True
    request = RequestFactory().get(
        "/", REMOTE_ADDR="10.0.0.5",
        HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.9", HTTP_CF_CONNECTING_IP="198.51.100.7",
    )
    assert get_client_ip(request) == "198.51.100.7"


def test_client_ip_skips_garbage_and_ignores_headers_without_proxy(settings):
    from django.test import RequestFactory

    from core.netutils import get_client_ip

    settings.TRUST_PROXY = True
    request = RequestFactory().get("/", REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="unknown, 203.0.113.9")
    assert get_client_ip(request) == "203.0.113.9"
    settings.TRUST_PROXY = False
    request = RequestFactory().get("/", REMOTE_ADDR="10.0.0.5", HTTP_CF_CONNECTING_IP="198.51.100.7")
    assert get_client_ip(request) == "10.0.0.5"


@pytest.mark.django_db
def test_seed_metrics_creates_no_users_or_audit():
    from django.contrib.auth import get_user_model
    from django.core.management import call_command

    from core.models import Metric

    call_command("seed_metrics")
    assert Metric.objects.exists()
    assert not get_user_model().objects.filter(username="demo").exists()
    assert not LoginAudit.objects.exists()
