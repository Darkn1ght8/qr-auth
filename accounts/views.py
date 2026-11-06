from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.netutils import get_client_ip
from core.ratelimit import RateLimited, hit

from .audit import audit
from .forms import LoginForm, RegisterForm
from .models import AuditEvent, LoginMethod, UserSession
from .realtime import session_revoked


def _safe_next(request, fallback: str = "accounts:cabinet") -> str:
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return fallback


@require_http_methods(["GET", "POST"])
def register(request):
    # A logged-in visitor still sees the form (with a notice) so the button does what it says.
    form = RegisterForm(request.POST or None)
    if request.method == "POST":
        try:
            hit("register", get_client_ip(request) or "unknown")
        except RateLimited as exc:
            audit(request, AuditEvent.RATE_LIMITED, scope="register")
            messages.error(request, f"Тым көп әрекет. {exc.retry_after} секундтан кейін қайталаңыз.")
            return render(request, "accounts/register.html", {"form": form, "next": _safe_next(request, "")}, status=429)
        if form.is_valid():
            user = form.save()
            audit(request, AuditEvent.REGISTERED, user=user, success=True)
            request._login_method = LoginMethod.PASSWORD
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, "Аккаунт жасалды. Енді телефонда осы аккаунтпен QR сканерлей аласыз.")
            return redirect(_safe_next(request))
    return render(request, "accounts/register.html", {"form": form, "next": _safe_next(request, "")})


@require_http_methods(["GET", "POST"])
def password_login(request):
    next_url = _safe_next(request, "")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST":
        try:
            hit("password_login", get_client_ip(request) or "unknown")
        except RateLimited as exc:
            audit(request, AuditEvent.RATE_LIMITED, scope="password_login")
            messages.error(request, f"Тым көп әрекет. {exc.retry_after} секундтан кейін қайталаңыз.")
            return render(request, "accounts/login.html", {"form": form, "next": next_url, "qr_pending": next_url.startswith("/qr/scan/")}, status=429)
        if form.is_valid():
            request._login_method = LoginMethod.PASSWORD
            login(request, form.get_user())  # login() rotates the session key (anti session fixation)
            return redirect(next_url or "accounts:cabinet")
    return render(request, "accounts/login.html", {"form": form, "next": next_url, "qr_pending": next_url.startswith("/qr/scan/")})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Сіз жүйеден шықтыңыз.")
    return redirect("core:home")


@never_cache
@require_GET
def session_status(request):
    """Polling fallback for the live-session socket: 401 once this session was ended."""
    if not request.user.is_authenticated:
        return JsonResponse({"active": False}, status=401)
    return JsonResponse({"active": True, "user": request.user.username})


@login_required
def cabinet(request):
    sessions = UserSession.objects.filter(user=request.user, ended_at__isnull=True)
    # Drop records whose Django session already expired.
    live_keys = set(
        Session.objects.filter(
            session_key__in=[s.session_key for s in sessions], expire_date__gt=timezone.now()
        ).values_list("session_key", flat=True)
    )
    stale = [s.pk for s in sessions if s.session_key not in live_keys]
    if stale:
        UserSession.objects.filter(pk__in=stale).update(ended_at=timezone.now())
        sessions = sessions.exclude(pk__in=stale)
    audit_entries = request.user.audit_entries.all()[:30]
    qr_logins = request.user.audit_entries.filter(event=AuditEvent.LOGIN_SUCCESS, method=LoginMethod.QR).count()
    return render(
        request,
        "accounts/cabinet.html",
        {
            "sessions": sessions,
            "current_key": request.session.session_key,
            "audit_entries": audit_entries,
            "qr_logins": qr_logins,
            "total_logins": request.user.audit_entries.filter(event=AuditEvent.LOGIN_SUCCESS).count(),
        },
    )


def _end_session(tracked: UserSession) -> None:
    Session.objects.filter(session_key=tracked.session_key).delete()
    tracked.ended_at = timezone.now()
    tracked.save(update_fields=["ended_at"])
    session_revoked(tracked.session_key)  # the other device logs out right now


@login_required
@require_POST
def revoke_session(request, pk: int):
    tracked = get_object_or_404(UserSession, pk=pk, user=request.user, ended_at__isnull=True)
    is_current = tracked.session_key == request.session.session_key
    audit(request, AuditEvent.SESSION_REVOKED, success=True, session=pk, current=is_current)
    if is_current:
        logout(request)
        messages.info(request, "Ағымдағы сессия аяқталды.")
        return redirect("core:home")
    _end_session(tracked)
    messages.success(request, f"Сессия аяқталды: {tracked.browser}, {tracked.os}.")
    return redirect("accounts:cabinet")


@login_required
@require_POST
def revoke_others(request):
    others = UserSession.objects.filter(user=request.user, ended_at__isnull=True).exclude(
        session_key=request.session.session_key
    )
    count = 0
    for tracked in others:
        _end_session(tracked)
        count += 1
    audit(request, AuditEvent.SESSION_REVOKED, success=True, scope="others", count=count)
    messages.success(request, f"Басқа {count} сессия аяқталды.")
    return redirect("accounts:cabinet")
