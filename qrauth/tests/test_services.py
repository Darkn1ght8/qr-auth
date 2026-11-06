"""Unit tests for the QR state machine (service layer)."""
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from qrauth import services
from qrauth.models import QRSession, QRStatus

from .conftest import FP, UA_DESKTOP

pytestmark = pytest.mark.django_db


def issue():
    return services.create_qr_session(client_fp=FP, ip="10.0.0.5", user_agent=UA_DESKTOP)


# --- token generation -------------------------------------------------------

def test_token_is_random_urlsafe_and_long():
    a, b = issue(), issue()
    assert a.token != b.token
    assert len(a.token) >= 43  # 32 bytes base64url
    assert all(c.isalnum() or c in "-_" for c in a.token)


def test_only_hash_of_token_is_stored():
    issued = issue()
    session = QRSession.objects.get(pk=issued.session.pk)
    assert session.token_hash == services.hash_secret(issued.token)
    assert issued.token not in session.token_hash
    assert session.status == QRStatus.PENDING
    assert (session.expires_at - session.created_at).total_seconds() == pytest.approx(60, abs=1)


def test_signature_is_verified():
    issued = issue()
    assert services.verify_signature(issued.token, issued.session.nonce, issued.signature)
    assert not services.verify_signature(issued.token, issued.session.nonce, "0" * 32)
    with pytest.raises(services.QRError) as exc:
        services.resolve_token(issued.token, "deadbeef" * 4)
    assert exc.value.code == "signature"


def test_unknown_token_is_rejected():
    with pytest.raises(services.QRError) as exc:
        services.resolve_token("not-a-real-token", "x")
    assert exc.value.code == "invalid"


def test_refresh_annuls_previous_token():
    first = issue()
    second = services.create_qr_session(
        client_fp=FP, ip="10.0.0.5", user_agent=UA_DESKTOP, previous_id=str(first.session.pk)
    )
    first.session.refresh_from_db()
    assert first.session.status == QRStatus.EXPIRED
    assert first.session.token_hash is None
    with pytest.raises(services.QRError):
        services.resolve_token(first.token, first.signature)
    assert services.resolve_token(second.token, second.signature).pk == second.session.pk


# --- TTL -----------------------------------------------------------------------

def test_expired_token_cannot_be_scanned(user):
    issued = issue()
    QRSession.objects.filter(pk=issued.session.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(services.QRError) as exc:
        services.resolve_token(issued.token, issued.signature)
    assert exc.value.code == "expired"
    session = QRSession.objects.get(pk=issued.session.pk)
    assert session.status == QRStatus.EXPIRED
    assert session.token_hash is None


def test_scanned_session_expires_before_confirmation(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, "10.0.0.9")
    QRSession.objects.filter(pk=session.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    session.refresh_from_db()
    with pytest.raises(services.QRError) as exc:
        services.confirm(session, user)
    assert exc.value.code == "expired"


def test_exchange_window_expires(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    code = services.confirm(session, user)
    QRSession.objects.filter(pk=session.pk).update(exchange_expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(services.QRError) as exc:
        services.exchange(session_id=str(session.pk), code=code, client_fp=FP, user_agent=UA_DESKTOP)
    assert exc.value.code == "expired"


# --- full flow & reuse ------------------------------------------------------------

def test_full_flow_returns_user_and_wipes_secrets(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    code = services.confirm(session, user)
    result = services.exchange(session_id=str(session.pk), code=code, client_fp=FP, user_agent=UA_DESKTOP)
    assert result == user
    session.refresh_from_db()
    assert session.consumed_at is not None
    assert session.token_hash is None and session.exchange_code_hash is None
    assert cache.get(services.code_cache_key(session.pk)) is None


def test_exchange_code_cannot_be_reused(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    code = services.confirm(session, user)
    services.exchange(session_id=str(session.pk), code=code, client_fp=FP, user_agent=UA_DESKTOP)
    with pytest.raises(services.QRError) as exc:
        services.exchange(session_id=str(session.pk), code=code, client_fp=FP, user_agent=UA_DESKTOP)
    assert exc.value.code == "replay"


def test_qr_token_cannot_be_scanned_after_confirmation(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    services.confirm(session, user)
    with pytest.raises(services.QRError) as exc:
        services.resolve_token(issued.token, issued.signature)
    assert exc.value.code == "invalid"


def test_fingerprint_mismatch_blocks_exchange(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    code = services.confirm(session, user)
    with pytest.raises(services.QRError) as exc:
        services.exchange(session_id=str(session.pk), code=code, client_fp="attacker-browser", user_agent=UA_DESKTOP)
    assert exc.value.code == "fingerprint"


def test_wrong_exchange_code(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    services.confirm(session, user)
    with pytest.raises(services.QRError) as exc:
        services.exchange(session_id=str(session.pk), code="guess", client_fp=FP, user_agent=UA_DESKTOP)
    assert exc.value.code == "code"


# --- rejection & ownership ----------------------------------------------------------

def test_reject_closes_session(user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    services.reject(session, user)
    session.refresh_from_db()
    assert session.status == QRStatus.REJECTED
    assert session.token_hash is None
    with pytest.raises(services.QRError):
        services.confirm(session, user)


def test_second_phone_cannot_hijack_scanned_session(user, other_user):
    issued = issue()
    session = services.mark_scanned(services.resolve_token(issued.token, issued.signature), user, None)
    with pytest.raises(services.QRError) as exc:
        services.mark_scanned(session, other_user, None)
    assert exc.value.code == "forbidden"
    with pytest.raises(services.QRError):
        services.confirm(session, other_user)
