from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.models import Session
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.i18n import t
from core.netutils import get_client_ip
from core.ratelimit import RateLimited, hit

from .audit import audit
from .emails import email_enabled, send_password_changed_notice, send_reset_email
from .forms import ChangePasswordForm, LoginForm, NewPasswordForm, RegisterForm, ResetRequestForm
from .models import AuditEvent, LoginMethod, UserSession
from .realtime import session_revoked

User = get_user_model()


def _safe_next(request, fallback: str = "accounts:cabinet") -> str:
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return fallback


def _too_many(request, exc: RateLimited) -> None:
    audit(request, AuditEvent.RATE_LIMITED, scope=exc.scope)
    messages.error(request, t("Слишком много попыток. Повторите через {seconds} с.", seconds=exc.retry_after))


@require_http_methods(["GET", "POST"])
def register(request):
    # A logged-in visitor still sees the form (with a notice) so the button does what it says.
    form = RegisterForm(request.POST or None)
    ctx = {"form": form, "next": _safe_next(request, "")}
    if request.method == "POST":
        try:
            hit("register", get_client_ip(request) or "unknown")
        except RateLimited as exc:
            _too_many(request, exc)
            return render(request, "accounts/register.html", ctx, status=429)
        if form.is_valid():
            user = form.save()
            audit(request, AuditEvent.REGISTERED, user=user, success=True)
            request._login_method = LoginMethod.PASSWORD
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, t("Аккаунт создан. Теперь вы можете сканировать QR этим аккаунтом на телефоне."))
            return redirect(_safe_next(request))
    return render(request, "accounts/register.html", ctx)


@require_http_methods(["GET", "POST"])
def password_login(request):
    next_url = _safe_next(request, "")
    form = LoginForm(request, data=request.POST or None)
    ctx = {"form": form, "next": next_url, "qr_pending": next_url.startswith("/qr/scan/")}
    if request.method == "POST":
        try:
            hit("password_login", get_client_ip(request) or "unknown")
        except RateLimited as exc:
            _too_many(request, exc)
            return render(request, "accounts/login.html", ctx, status=429)
        if form.is_valid():
            request._login_method = LoginMethod.PASSWORD
            login(request, form.get_user())  # login() rotates the session key (anti session fixation)
            return redirect(next_url or "accounts:cabinet")
    return render(request, "accounts/login.html", ctx)


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, t("Вы вышли из системы."))
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


def end_user_sessions(user, keep_key: str | None = None) -> int:
    """End every tracked session of `user` (except `keep_key`); returns how many."""
    ended = 0
    for tracked in UserSession.objects.filter(user=user, ended_at__isnull=True).exclude(session_key=keep_key or ""):
        _end_session(tracked)
        ended += 1
    return ended


@login_required
@require_POST
def revoke_session(request, pk: int):
    tracked = get_object_or_404(UserSession, pk=pk, user=request.user, ended_at__isnull=True)
    is_current = tracked.session_key == request.session.session_key
    audit(request, AuditEvent.SESSION_REVOKED, success=True, session=pk, current=is_current)
    if is_current:
        logout(request)
        messages.info(request, t("Текущая сессия завершена."))
        return redirect("core:home")
    _end_session(tracked)
    messages.success(request, t("Сессия завершена: {device}.", device=f"{tracked.browser}, {tracked.os}"))
    return redirect("accounts:cabinet")


@login_required
@require_POST
def revoke_others(request):
    count = end_user_sessions(request.user, keep_key=request.session.session_key)
    audit(request, AuditEvent.SESSION_REVOKED, success=True, scope="others", count=count)
    messages.success(request, t("Завершено других сессий: {count}.", count=count))
    return redirect("accounts:cabinet")


# --- password change (logged in: users and admins) -----------------------------

@login_required
@require_http_methods(["GET", "POST"])
def password_change(request):
    form = ChangePasswordForm(request.user, request.POST or None)
    if request.method == "POST":
        try:
            hit("password_change", f"u{request.user.pk}")
        except RateLimited as exc:
            _too_many(request, exc)
            return render(request, "accounts/password_change.html", {"form": form}, status=429)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # stay signed in on this device
            ended = 0
            if form.cleaned_data.get("logout_others"):
                ended = end_user_sessions(user, keep_key=request.session.session_key)
            audit(request, AuditEvent.PASSWORD_CHANGED, user=user, success=True, sessions_ended=ended)
            send_password_changed_notice(request, user)
            messages.success(request, t("Пароль изменён. Завершено других сессий: {count}.", count=ended))
            return redirect("accounts:cabinet")
        audit(request, AuditEvent.PASSWORD_CHANGED, user=request.user, success=False, reason="invalid_form")
    return render(request, "accounts/password_change.html", {"form": form})


# --- forgotten password: request a one-time link by e-mail ------------------------

@require_http_methods(["GET", "POST"])
def password_reset_request(request):
    form = ResetRequestForm(request.POST or None)
    ctx = {"form": form, "email_enabled": email_enabled()}
    if request.method == "POST":
        try:
            hit("password_reset", get_client_ip(request) or "unknown")
        except RateLimited as exc:
            _too_many(request, exc)
            return render(request, "accounts/password_reset.html", ctx, status=429)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                hit("password_reset_email", email)
            except RateLimited:
                # Same answer as success: never reveal anything about the address.
                return redirect("accounts:password_reset_sent")
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            if user is not None and user.has_usable_password():
                sent = send_reset_email(request, user)
                audit(request, AuditEvent.PASSWORD_RESET_REQUESTED, user=user, success=sent, delivered=sent)
            else:
                audit(request, AuditEvent.PASSWORD_RESET_REQUESTED, success=False, reason="unknown_email")
            # The same page whether or not the address exists (no user enumeration).
            return redirect("accounts:password_reset_sent")
    return render(request, "accounts/password_reset.html", ctx)


@require_GET
def password_reset_sent(request):
    return render(request, "accounts/password_reset_sent.html", {"timeout_minutes": settings.PASSWORD_RESET_TIMEOUT // 60})


def _user_from_uid(uidb64):
    try:
        return User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)), is_active=True)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        return None


@never_cache
@require_http_methods(["GET", "POST"])
def password_reset_confirm(request, uidb64: str, token: str):
    user = _user_from_uid(uidb64)
    valid = user is not None and default_token_generator.check_token(user, token)
    if not valid:
        audit(request, AuditEvent.PASSWORD_RESET_DONE, user=user, success=False, reason="bad_or_used_link")
        return render(request, "accounts/password_reset_confirm.html", {"valid": False}, status=400)
    form = NewPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()  # changing the password makes this link unusable (token is bound to it)
        ended = end_user_sessions(user)  # everyone who knew the old password is logged out
        audit(request, AuditEvent.PASSWORD_RESET_DONE, user=user, success=True, sessions_ended=ended)
        messages.success(request, t("Пароль обновлён. Войдите с новым паролем."))
        return redirect("accounts:login")
    return render(request, "accounts/password_reset_confirm.html", {"valid": True, "form": form, "reset_user": user})
