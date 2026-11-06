"""QR login state machine.

pending -> scanned -> confirmed | rejected | expired
A confirmed session yields a one-time exchange code that the initiating
browser trades for a Django session exactly once.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from core.i18n import N_, t
from core.netutils import parse_user_agent

from .models import QRSession, QRStatus

logger = logging.getLogger("qrauth")

ACTIVE_STATES = (QRStatus.PENDING, QRStatus.SCANNED)


class QRError(Exception):
    """Domain error with a machine-readable code and a Kazakh user message."""

    MESSAGES = {
        "invalid": N_("QR-код недействителен или уже использован."),
        "signature": N_("Неверная подпись QR-кода."),
        "expired": N_("Срок QR-кода истёк. Откройте новый на компьютере."),
        "state": N_("Этот запрос больше не активен."),
        "forbidden": N_("Этот запрос отсканировал другой пользователь."),
        "replay": N_("Этот код уже использован. Повторный вход невозможен."),
        "fingerprint": N_("Запрос пришёл из другого браузера. Вход заблокирован."),
        "code": N_("Неверный код обмена."),
    }

    def __init__(self, code: str):
        self.code = code
        self.message = t(self.MESSAGES.get(code, code))
        super().__init__(self.message)


@dataclass(frozen=True)
class IssuedQR:
    session: QRSession
    token: str
    signature: str


# --- primitives -----------------------------------------------------------------

def hash_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sign_token(token: str, nonce: str) -> str:
    key = settings.QR_HMAC_KEY.encode("utf-8")
    return hmac.new(key, f"{token}.{nonce}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def verify_signature(token: str, nonce: str, signature: str) -> bool:
    return hmac.compare_digest(sign_token(token, nonce), signature or "")


def compute_fingerprint(client_fp: str, user_agent: str) -> str:
    return hash_secret(f"{(client_fp or '')[:512]}|{(user_agent or '')[:512]}")


def code_cache_key(session_id) -> str:
    return f"qr:code:{uuid.UUID(str(session_id)).hex}"


# --- notifications ------------------------------------------------------------

def notify(session: QRSession) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(session.group_name, {"type": "qr.status", "sid": str(session.pk)})
    except Exception:  # never let a broken channel layer break the HTTP flow
        logger.exception("channel layer notify failed")


# --- lifecycle -----------------------------------------------------------------

def _invalidate(session: QRSession) -> None:
    session.status = QRStatus.EXPIRED
    session.token_hash = None
    session.exchange_code_hash = None
    session.save(update_fields=["status", "token_hash", "exchange_code_hash"])
    cache.delete(code_cache_key(session.pk))
    notify(session)


def create_qr_session(*, client_fp: str, ip: str | None, user_agent: str, previous_id: str | None = None) -> IssuedQR:
    """Issue a fresh QR token; the previous token of this browser is annulled."""
    if previous_id:
        try:
            previous = QRSession.objects.filter(pk=previous_id, status=QRStatus.PENDING).first()
        except Exception:  # malformed UUID stored in session
            previous = None
        if previous is not None:
            _invalidate(previous)

    token = secrets.token_urlsafe(32)
    nonce = secrets.token_hex(16)
    browser, system = parse_user_agent(user_agent)
    now = timezone.now()
    session = QRSession.objects.create(
        token_hash=hash_secret(token),
        nonce=nonce,
        fingerprint_hash=compute_fingerprint(client_fp, user_agent),
        initiator_ip=ip,
        initiator_user_agent=(user_agent or "")[:512],
        initiator_browser=browser,
        initiator_os=system,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.QR_TTL_SECONDS),
    )
    return IssuedQR(session=session, token=token, signature=sign_token(token, nonce))


def expire_if_needed(session: QRSession) -> bool:
    """Lazily move an outdated session to `expired`. Returns True if it changed."""
    now = timezone.now()
    if session.status in ACTIVE_STATES and now >= session.expires_at:
        _invalidate(session)
        return True
    if (
        session.status == QRStatus.CONFIRMED
        and session.consumed_at is None
        and session.exchange_expires_at is not None
        and now >= session.exchange_expires_at
    ):
        _invalidate(session)
        return True
    return False


def resolve_token(token: str, signature: str) -> QRSession:
    """Find the session for a scanned token and validate signature + TTL."""
    if not token or len(token) > 128:
        raise QRError("invalid")
    session = QRSession.objects.filter(token_hash=hash_secret(token)).first()
    if session is None:
        raise QRError("invalid")
    if not verify_signature(token, session.nonce, signature):
        raise QRError("signature")
    if expire_if_needed(session):
        raise QRError("expired")
    return session


def mark_opened(session: QRSession) -> QRSession:
    """A phone opened the QR link but must log in first.

    The desktop stops rotating this QR and the request gets a one-time grace period,
    so signing in on the phone does not invalidate the token being confirmed.
    """
    if session.status != QRStatus.PENDING or session.opened_at is not None:
        return session
    now = timezone.now()
    new_expiry = max(session.expires_at, now + timedelta(seconds=settings.QR_LOGIN_GRACE_SECONDS))
    QRSession.objects.filter(pk=session.pk, status=QRStatus.PENDING, opened_at__isnull=True).update(
        opened_at=now, expires_at=new_expiry
    )
    session.refresh_from_db()
    notify(session)
    return session


def mark_scanned(session: QRSession, user, ip: str | None) -> QRSession:
    if session.status == QRStatus.SCANNED and session.scanned_by_id == user.pk:
        return session  # page reload on the phone
    if session.status != QRStatus.PENDING:
        raise QRError("forbidden" if session.status == QRStatus.SCANNED else "state")
    now = timezone.now()
    updated = QRSession.objects.filter(pk=session.pk, status=QRStatus.PENDING).update(
        status=QRStatus.SCANNED, scanned_by=user, scanned_at=now, scanner_ip=ip
    )
    if updated != 1:  # another phone won the race
        raise QRError("forbidden")
    session.refresh_from_db()
    notify(session)
    return session


def confirm(session: QRSession, user) -> str:
    """Approve the login; returns the raw one-time exchange code."""
    if expire_if_needed(session):
        raise QRError("expired")
    if session.status != QRStatus.SCANNED:
        raise QRError("state")
    if session.scanned_by_id != user.pk:
        raise QRError("forbidden")
    code = secrets.token_urlsafe(32)
    now = timezone.now()
    updated = QRSession.objects.filter(pk=session.pk, status=QRStatus.SCANNED, scanned_by=user).update(
        status=QRStatus.CONFIRMED,
        decided_at=now,
        exchange_code_hash=hash_secret(code),
        exchange_expires_at=now + timedelta(seconds=settings.QR_EXCHANGE_TTL_SECONDS),
        token_hash=None,  # the QR token can never be scanned again
    )
    if updated != 1:
        raise QRError("state")
    # The raw code lives only in the cache, only for the exchange window,
    # and is delivered exclusively to the initiator-bound channel.
    cache.set(code_cache_key(session.pk), code, timeout=settings.QR_EXCHANGE_TTL_SECONDS)
    session.refresh_from_db()
    notify(session)
    return code


def reject(session: QRSession, user) -> QRSession:
    if session.status != QRStatus.SCANNED:
        raise QRError("state")
    if session.scanned_by_id != user.pk:
        raise QRError("forbidden")
    QRSession.objects.filter(pk=session.pk, status=QRStatus.SCANNED).update(
        status=QRStatus.REJECTED, decided_at=timezone.now(), token_hash=None
    )
    session.refresh_from_db()
    notify(session)
    return session


def exchange(*, session_id: str, code: str, client_fp: str, user_agent: str):
    """Trade the one-time code for the approving user. Exactly-once semantics."""
    try:
        session = QRSession.objects.select_related("scanned_by").get(pk=session_id)
    except (QRSession.DoesNotExist, ValueError, Exception):
        raise QRError("invalid")
    if session.consumed_at is not None:
        raise QRError("replay")
    if expire_if_needed(session):
        raise QRError("expired")
    if session.status != QRStatus.CONFIRMED or not session.exchange_code_hash:
        raise QRError("state")
    if not hmac.compare_digest(session.exchange_code_hash, hash_secret(code or "")):
        raise QRError("code")
    if not hmac.compare_digest(session.fingerprint_hash, compute_fingerprint(client_fp, user_agent)):
        raise QRError("fingerprint")
    with transaction.atomic():
        won = QRSession.objects.filter(
            pk=session.pk, status=QRStatus.CONFIRMED, consumed_at__isnull=True
        ).update(consumed_at=timezone.now(), exchange_code_hash=None, token_hash=None)
    if won != 1:
        raise QRError("replay")
    cache.delete(code_cache_key(session.pk))
    return session.scanned_by


# --- payloads for WebSocket / long-poll ---------------------------------------

def mask_username(username: str) -> str:
    if len(username) <= 2:
        return username[0] + "*"
    return username[0] + "•" * (len(username) - 2) + username[-1]


def status_payload(session: QRSession) -> dict:
    expire_if_needed(session)
    payload = {
        "sid": str(session.pk),
        "status": session.status,
        "seconds_left": session.seconds_left(),
        "consumed": session.consumed_at is not None,
        "opened": session.opened_at is not None,
    }
    if session.scanned_by_id and session.status in (QRStatus.SCANNED, QRStatus.CONFIRMED):
        payload["user"] = mask_username(session.scanned_by.username)
    if session.status == QRStatus.CONFIRMED and session.consumed_at is None:
        code = cache.get(code_cache_key(session.pk))
        if code:
            payload["code"] = code
    return payload


def payload_for(session_id: str) -> dict:
    session = QRSession.objects.select_related("scanned_by").filter(pk=session_id).first()
    if session is None:
        return {"sid": session_id, "status": QRStatus.EXPIRED, "seconds_left": 0, "consumed": False}
    return status_payload(session)
