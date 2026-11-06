import json
import time
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from accounts.audit import audit
from accounts.models import AuditEvent, LoginMethod
from core.i18n import t
from core.netutils import absolute_public_url, get_client_ip, parse_user_agent, public_base_url
from core.ratelimit import RateLimited, hit

from . import services
from .models import QRSession, QRStatus
from .qrrender import render as render_qr

SESSION_KEY = "qr_sid"


def _json_body(request) -> dict:
    try:
        return json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _error(message: str, status: int, code: str = "error", **extra) -> JsonResponse:
    return JsonResponse({"ok": False, "error": code, "message": message, **extra}, status=status)


def _rate_limited(request, exc: RateLimited) -> JsonResponse:
    audit(request, AuditEvent.RATE_LIMITED, scope=exc.scope)
    return _error(
        t("Слишком много запросов. Повторите через {seconds} с.", seconds=exc.retry_after),
        429,
        "rate_limited",
        retry_after=exc.retry_after,
    )


def _scan_url(request, token: str, signature: str) -> str:
    return absolute_public_url(request, reverse("qrauth:scan", args=[token, signature]))


def _bound(request, sid: str) -> bool:
    """The status channel is readable only by the browser that created the QR."""
    return bool(sid) and request.session.get(SESSION_KEY) == str(sid)


# --- desktop -------------------------------------------------------------------

@never_cache
@require_GET
def qr_login(request):
    return render(
        request,
        "qrauth/login.html",
        {
            "ttl": settings.QR_TTL_SECONDS,
            "refresh": settings.QR_REFRESH_SECONDS,
            "scanner_url": absolute_public_url(request, reverse("qrauth:scanner")),
            "public_base": public_base_url(request),
            "is_public": public_base_url(request).startswith("https://"),
        },
    )


@require_POST
def api_new(request):
    try:
        hit("qr_new", get_client_ip(request) or "unknown")
    except RateLimited as exc:
        return _rate_limited(request, exc)
    body = _json_body(request)
    issued = services.create_qr_session(
        client_fp=str(body.get("fp", "")),
        ip=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        previous_id=request.session.get(SESSION_KEY),
    )
    request.session[SESSION_KEY] = str(issued.session.pk)
    url = _scan_url(request, issued.token, issued.signature)
    svg, rows = render_qr(url)
    audit(request, AuditEvent.QR_CREATED, method=LoginMethod.QR, sid=str(issued.session.pk))
    extra = {"url": url} if settings.DEBUG else {}  # same data the QR shows; handy for local testing
    return JsonResponse(
        {
            **extra,
            "ok": True,
            "sid": str(issued.session.pk),
            "svg": svg,
            "matrix": rows,
            "ttl": settings.QR_TTL_SECONDS,
            "refresh": settings.QR_REFRESH_SECONDS,
            "expires_at": issued.session.expires_at.isoformat(),
            "ws": f"/ws/qr/{issued.session.pk}/",
            "poll": reverse("qrauth:api_status", args=[issued.session.pk]),
        }
    )


@never_cache
@require_GET
def api_status(request, sid):
    """Long-polling fallback: waits until the status differs from `since`."""
    sid = str(sid)
    if not _bound(request, sid):
        return _error(t("Нет доступа к этой QR-сессии."), 403, "forbidden")
    since = request.GET.get("since", "")
    deadline = time.monotonic() + settings.QR_LONGPOLL_TIMEOUT
    payload = services.payload_for(sid)
    while payload["status"] == since and "code" not in payload and time.monotonic() < deadline:
        time.sleep(0.6)
        payload = services.payload_for(sid)
    return JsonResponse({"ok": True, **payload})


@require_POST
def api_exchange(request):
    try:
        hit("qr_exchange", get_client_ip(request) or "unknown")
    except RateLimited as exc:
        return _rate_limited(request, exc)
    body = _json_body(request)
    sid = str(body.get("sid", ""))
    if not _bound(request, sid):
        audit(request, AuditEvent.QR_INVALID, method=LoginMethod.QR, reason="unbound", sid=sid)
        return _error(t("Нет доступа к этой QR-сессии."), 403, "forbidden")
    try:
        user = services.exchange(
            session_id=sid,
            code=str(body.get("code", "")),
            client_fp=str(body.get("fp", "")),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    except services.QRError as exc:
        event = {
            "replay": AuditEvent.REPLAY_BLOCKED,
            "fingerprint": AuditEvent.FINGERPRINT_MISMATCH,
            "expired": AuditEvent.QR_EXPIRED,
        }.get(exc.code, AuditEvent.QR_INVALID)
        audit(request, event, method=LoginMethod.QR, sid=sid, reason=exc.code)
        return _error(exc.message, 409 if exc.code == "replay" else 400, exc.code)
    request.session.pop(SESSION_KEY, None)
    request._login_method = LoginMethod.QR
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")  # rotates session key
    duration = QRSession.objects.filter(pk=sid).values_list("created_at", "consumed_at").first()
    seconds = round((duration[1] - duration[0]).total_seconds(), 2) if duration and duration[1] else None
    audit(request, AuditEvent.QR_CONFIRMED, user=user, method=LoginMethod.QR, success=True, sid=sid, seconds=seconds)
    return JsonResponse({"ok": True, "redirect": reverse("accounts:cabinet")})


# --- phone ---------------------------------------------------------------------

@never_cache
def scanner(request):
    return render(request, "qrauth/scanner.html", {"public_base": public_base_url(request)})


def _phone_error(request, message: str, status: int = 400):
    return render(request, "qrauth/error.html", {"message": message}, status=status)


@never_cache
@require_GET
def scan(request, token: str, signature: str):
    if not request.user.is_authenticated:
        return _scan_anonymous(request, token, signature)
    try:
        hit("qr_scan", f"u{request.user.pk}")
    except RateLimited as exc:
        audit(request, AuditEvent.RATE_LIMITED, scope=exc.scope)
        return _phone_error(request, t("Слишком много запросов. Повторите через {seconds} с.", seconds=exc.retry_after), 429)
    try:
        session = services.resolve_token(token, signature)
        session = services.mark_scanned(session, request.user, get_client_ip(request))
    except services.QRError as exc:
        audit(request, AuditEvent.QR_INVALID if exc.code != "expired" else AuditEvent.QR_EXPIRED,
              method=LoginMethod.QR, reason=exc.code)
        return _phone_error(request, exc.message, 410 if exc.code == "expired" else 400)
    audit(request, AuditEvent.QR_SCANNED, method=LoginMethod.QR, sid=str(session.pk))
    phone_browser, phone_os = parse_user_agent(request.META.get("HTTP_USER_AGENT", ""))
    return render(
        request,
        "qrauth/confirm.html",
        {
            "qr": session,
            "token": token,
            "signature": signature,
            "same_ip": session.initiator_ip == get_client_ip(request),
            "phone_device": f"{phone_browser} · {phone_os}",
            "host": request.get_host(),
        },
    )


def _scan_anonymous(request, token: str, signature: str):
    """Phone is not logged in yet: hold the QR request, then send the user to sign in."""
    try:
        hit("qr_scan", get_client_ip(request) or "unknown")
    except RateLimited as exc:
        audit(request, AuditEvent.RATE_LIMITED, scope=exc.scope)
        return _phone_error(request, t("Слишком много запросов. Повторите через {seconds} с.", seconds=exc.retry_after), 429)
    try:
        session = services.resolve_token(token, signature)
        services.mark_opened(session)
    except services.QRError as exc:
        audit(request, AuditEvent.QR_INVALID if exc.code != "expired" else AuditEvent.QR_EXPIRED,
              method=LoginMethod.QR, reason=exc.code, stage="anonymous")
        return _phone_error(request, exc.message, 410 if exc.code == "expired" else 400)
    login_url = reverse("accounts:login")
    return redirect(f"{login_url}?{urlencode({'next': request.get_full_path()})}")


@login_required
@require_POST
def decide(request):
    try:
        hit("qr_decide", f"u{request.user.pk}")
    except RateLimited as exc:
        audit(request, AuditEvent.RATE_LIMITED, scope=exc.scope)
        return _phone_error(request, t("Слишком много запросов. Повторите через {seconds} с.", seconds=exc.retry_after), 429)
    token = request.POST.get("token", "")
    signature = request.POST.get("signature", "")
    action = request.POST.get("action", "")
    session = QRSession.objects.filter(token_hash=services.hash_secret(token)).first() if token else None
    if session is None or not services.verify_signature(token, session.nonce, signature):
        audit(request, AuditEvent.QR_INVALID, method=LoginMethod.QR, reason="decide_lookup")
        return _phone_error(request, services.QRError("invalid").message)
    try:
        if action == "confirm":
            services.confirm(session, request.user)
            audit(request, AuditEvent.QR_CONFIRMED, method=LoginMethod.QR, success=True, sid=str(session.pk), stage="phone")
            outcome = "confirmed"
        elif action == "reject":
            services.reject(session, request.user)
            audit(request, AuditEvent.QR_REJECTED, method=LoginMethod.QR, sid=str(session.pk))
            outcome = "rejected"
        else:
            return _phone_error(request, t("Неизвестное действие."))
    except services.QRError as exc:
        audit(request, AuditEvent.QR_INVALID, method=LoginMethod.QR, reason=exc.code, sid=str(session.pk))
        return _phone_error(request, exc.message, 410 if exc.code == "expired" else 400)
    return render(request, "qrauth/result.html", {"outcome": outcome, "qr": session})


def scan_redirect(request):
    return redirect("qrauth:scanner")
