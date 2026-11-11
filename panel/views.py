"""Administrator panel: users (with e-mails), logins, sessions, audit log, QR attempts.

Access: staff users only. Every action is a POST (CSRF-protected) and is written
to the audit log as `admin_action`.
"""
import csv
from datetime import timedelta
from functools import wraps
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Count, F, Max, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.audit import audit
from accounts.models import AuditEvent, LoginAudit, LoginMethod, UserSession
from accounts.tracking import close_stale_sessions
from accounts.emails import email_enabled, reset_link, send_reset_email
from accounts.forms import NewPasswordForm
from accounts.views import _end_session
from core.i18n import t
from core.netutils import parse_user_agent
from qrauth.models import QRSession, QRStatus

User = get_user_model()

SECURITY_EVENTS = [
    AuditEvent.LOGIN_FAILED,
    AuditEvent.REPLAY_BLOCKED,
    AuditEvent.FINGERPRINT_MISMATCH,
    AuditEvent.RATE_LIMITED,
    AuditEvent.QR_INVALID,
]
ONLINE_WINDOW = timedelta(minutes=5)


# --- access control -----------------------------------------------------------

def staff_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?{urlencode({'next': request.get_full_path()})}")
        if not (request.user.is_active and request.user.is_staff):
            return render(request, "panel/forbidden.html", status=403)
        # Devices that expired or went idle must not be listed as active sessions.
        close_stale_sessions()
        return view(request, *args, **kwargs)

    return wrapper


def _active_sessions():
    return UserSession.objects.filter(ended_at__isnull=True)


def _admin_audit(request, action: str, target=None, **details):
    audit(
        request,
        AuditEvent.ADMIN_ACTION,
        user=request.user,
        success=True,
        action=action,
        target=getattr(target, "username", None),
        target_id=getattr(target, "pk", None),
        **details,
    )


def _last_ip():
    """The user's most recent IP: from their latest login session, else from the audit log."""
    from_session = UserSession.objects.filter(user=OuterRef("pk"), ip_address__isnull=False).order_by("-last_seen")
    from_audit = LoginAudit.objects.filter(user=OuterRef("pk"), ip_address__isnull=False).order_by("-created_at")
    return Coalesce(Subquery(from_session.values("ip_address")[:1]), Subquery(from_audit.values("ip_address")[:1]))


def _with_users():
    """Users annotated with login statistics (distinct counts avoid join multiplication)."""
    return User.objects.annotate(
        last_ip=_last_ip(),
        login_count=Count("audit_entries", filter=Q(audit_entries__event=AuditEvent.LOGIN_SUCCESS), distinct=True),
        qr_login_count=Count(
            "audit_entries",
            filter=Q(audit_entries__event=AuditEvent.LOGIN_SUCCESS, audit_entries__method=LoginMethod.QR),
            distinct=True,
        ),
        active_sessions=Count("tracked_sessions", filter=Q(tracked_sessions__ended_at__isnull=True), distinct=True),
        last_seen=Max("tracked_sessions__last_seen"),
    )


# --- dashboard ----------------------------------------------------------------

@staff_required
@require_GET
def dashboard(request):
    now = timezone.now()
    today = timezone.localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    logins_24h = LoginAudit.objects.filter(event=AuditEvent.LOGIN_SUCCESS, created_at__gte=day_ago)
    qr_scanned = QRSession.objects.filter(scanned_at__isnull=False).count()
    qr_consumed = QRSession.objects.filter(consumed_at__isnull=False).count()
    stats = {
        "users": User.objects.count(),
        "users_today": User.objects.filter(date_joined__gte=today).count(),
        "users_week": User.objects.filter(date_joined__gte=week_ago).count(),
        "online": _active_sessions().filter(last_seen__gte=now - ONLINE_WINDOW).values("user").distinct().count(),
        "sessions": _active_sessions().count(),
        "logins_24h": logins_24h.count(),
        "qr_logins_24h": logins_24h.filter(method=LoginMethod.QR).count(),
        "failed_24h": LoginAudit.objects.filter(event=AuditEvent.LOGIN_FAILED, created_at__gte=day_ago).count(),
        "security_24h": LoginAudit.objects.filter(event__in=SECURITY_EVENTS, created_at__gte=day_ago).count(),
        "qr_success": round(100 * qr_consumed / qr_scanned) if qr_scanned else None,
        "blocked": User.objects.filter(is_active=False).count(),
    }

    # 14-day activity chart: registrations and successful logins per day.
    start = (today - timedelta(days=13))
    regs = dict(
        User.objects.filter(date_joined__gte=start).annotate(d=TruncDate("date_joined")).values("d")
        .annotate(n=Count("id")).values_list("d", "n")
    )
    logins = dict(
        LoginAudit.objects.filter(event=AuditEvent.LOGIN_SUCCESS, created_at__gte=start)
        .annotate(d=TruncDate("created_at")).values("d").annotate(n=Count("id")).values_list("d", "n")
    )
    days = [(start + timedelta(days=i)).date() for i in range(14)]
    peak = max([regs.get(d, 0) for d in days] + [logins.get(d, 0) for d in days] + [1])
    chart = [
        {
            "label": d.strftime("%d.%m"),
            "regs": regs.get(d, 0),
            "logins": logins.get(d, 0),
            "regs_h": round(100 * regs.get(d, 0) / peak),
            "logins_h": round(100 * logins.get(d, 0) / peak),
        }
        for d in days
    ]

    recent_logins = []
    for e in LoginAudit.objects.filter(event=AuditEvent.LOGIN_SUCCESS).select_related("user")[:10]:
        browser, system = parse_user_agent(e.user_agent)
        recent_logins.append({"entry": e, "device": f"{browser} · {system}"})

    return render(request, "panel/dashboard.html", {
        "stats": stats,
        "chart": chart,
        "recent_users": User.objects.order_by("-date_joined")[:8],
        "recent_logins": recent_logins,
        "security": LoginAudit.objects.filter(event__in=SECURITY_EVENTS).select_related("user")[:8],
        "section": "dashboard",
    })


# --- users --------------------------------------------------------------------

USER_ORDERS = {
    "new": "-date_joined",
    "old": "date_joined",
    "login": F("last_login").desc(nulls_last=True),
    "active": F("last_seen").desc(nulls_last=True),
    "name": "username",
}


def _filtered_users(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all")
    order = request.GET.get("order", "new")
    users = _with_users()
    if q:
        users = users.filter(
            Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q)
            | Q(last_name__icontains=q) | Q(last_ip__icontains=q)
        )
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "blocked":
        users = users.filter(is_active=False)
    elif status == "admins":
        users = users.filter(is_staff=True)
    elif status == "online":
        users = users.filter(
            tracked_sessions__ended_at__isnull=True,
            tracked_sessions__last_seen__gte=timezone.now() - ONLINE_WINDOW,
        ).distinct()
    users = users.order_by(USER_ORDERS.get(order, "-date_joined"), "-pk")
    return users, q, status, order


@staff_required
@require_GET
def users(request):
    queryset, q, status, order = _filtered_users(request)
    page = Paginator(queryset, 25).get_page(request.GET.get("page"))
    params = {k: v for k, v in {"q": q, "status": status, "order": order}.items() if v}
    return render(request, "panel/users.html", {
        "page": page,
        "q": q,
        "status": status,
        "order": order,
        "total": queryset.count(),
        "query": urlencode(params),
        "online_since": timezone.now() - ONLINE_WINDOW,
        "section": "users",
    })


@staff_required
@require_GET
def users_export(request):
    queryset, *_ = _filtered_users(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="qr-auth-users-{timezone.localdate():%Y%m%d}.csv"'
    response.write("﻿")  # BOM so Excel opens Kazakh text correctly
    writer = csv.writer(response)
    writer.writerow(["ID", t("Логин"), t("Имя"), t("Почта"), t("Зарегистрирован"), t("Последний вход"), t("Входов"),
                     t("Входов по QR"), t("Активные сессии"), "IP", t("Статус"), t("Администратор")])
    for u in queryset:
        writer.writerow([
            u.pk, u.username, u.get_full_name(), u.email,
            timezone.localtime(u.date_joined).strftime("%Y-%m-%d %H:%M"),
            timezone.localtime(u.last_login).strftime("%Y-%m-%d %H:%M") if u.last_login else "",
            u.login_count, u.qr_login_count, u.active_sessions, u.last_ip or "",
            t("активен") if u.is_active else t("заблокирован"), t("да") if u.is_staff else "",
        ])
    _admin_audit(request, "export_users", rows=queryset.count())
    return response


@staff_required
@require_GET
def user_detail(request, pk: int):
    target = get_object_or_404(_with_users(), pk=pk)
    sessions = UserSession.objects.filter(user=target).order_by(F("ended_at").desc(nulls_first=True), "-last_seen")[:30]
    entries = LoginAudit.objects.filter(user=target)[:50]
    qr = QRSession.objects.filter(scanned_by=target)[:15]
    flash = request.session.pop("panel_reset_link", None)
    return render(request, "panel/user_detail.html", {
        "password_form": NewPasswordForm(target),
        "email_enabled": email_enabled(),
        "reset_link": flash["url"] if flash and flash.get("user") == target.pk else None,
        "target": target,
        "sessions": sessions,
        "ended_sessions": UserSession.objects.filter(user=target, ended_at__isnull=False).count(),
        "entries": entries,
        "qr_sessions": qr,
        "security_events": SECURITY_EVENTS,
        "online_since": timezone.now() - ONLINE_WINDOW,
        "section": "users",
    })


@staff_required
@require_POST
def user_action(request, pk: int):
    target = get_object_or_404(User, pk=pk)
    action = request.POST.get("action", "")
    is_self = target.pk == request.user.pk
    back = redirect("panel:user", pk=target.pk)

    if is_self and action in {"block", "remove_admin", "delete", "end_sessions", "set_password", "reset_link", "send_reset"}:
        messages.error(request, t("Это действие нельзя применить к своему аккаунту."))
        return back
    if target.is_superuser and not request.user.is_superuser and action in {
        "block", "remove_admin", "delete", "set_password", "reset_link", "send_reset",
    }:
        messages.error(request, t("Главного администратора может менять только главный администратор."))
        return back

    ended = 0
    if action in {"block", "end_sessions", "delete"}:
        for tracked in UserSession.objects.filter(user=target, ended_at__isnull=True):
            _end_session(tracked)  # pushes an instant logout to that device
            ended += 1

    if action == "block":
        target.is_active = False
        target.save(update_fields=["is_active"])
        messages.success(request, t("{username} заблокирован, завершено сессий: {count}.", username=target.username, count=ended))
    elif action == "unblock":
        target.is_active = True
        target.save(update_fields=["is_active"])
        messages.success(request, t("{username} разблокирован.", username=target.username))
    elif action == "end_sessions":
        messages.success(request, t("{username}: завершено сессий: {count}.", username=target.username, count=ended))
    elif action == "make_admin":
        target.is_staff = True
        target.save(update_fields=["is_staff"])
        messages.success(request, t("{username} теперь администратор.", username=target.username))
    elif action == "remove_admin":
        target.is_staff = False
        target.is_superuser = False
        target.save(update_fields=["is_staff", "is_superuser"])
        messages.success(request, t("{username} лишён прав администратора.", username=target.username))
    elif action == "delete":
        if request.POST.get("confirm_username", "").strip() != target.username:
            messages.error(request, t("Для удаления точно введите логин пользователя."))
            return back
        _admin_audit(request, "delete", target, email=target.email)
        username = target.username
        target.delete()
        messages.success(request, t("Аккаунт {username} удалён.", username=username))
        return redirect("panel:users")
    elif action == "set_password":
        form = NewPasswordForm(target, request.POST)
        if not form.is_valid():
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
            return back
        form.save()
        for tracked in UserSession.objects.filter(user=target, ended_at__isnull=True):
            _end_session(tracked)  # the old password's sessions end everywhere
            ended += 1
        messages.success(request, t("Новый пароль для {username} установлен, завершено сессий: {count}.", username=target.username, count=ended))
    elif action == "reset_link":
        # Shown once on the user page, for handing over when e-mail is not configured.
        request.session["panel_reset_link"] = {"user": target.pk, "url": reset_link(request, target)}
        messages.success(request, t("Одноразовая ссылка для сброса создана."))
    elif action == "send_reset":
        if send_reset_email(request, target):
            messages.success(request, t("Письмо со ссылкой отправлено на {email}.", email=target.email))
        else:
            messages.error(request, t("Не удалось отправить письмо: почта не настроена или у пользователя нет адреса."))
            return back
    else:
        messages.error(request, t("Неизвестное действие."))
        return back

    _admin_audit(request, action, target, sessions_ended=ended)
    return back


# --- sessions -----------------------------------------------------------------

@staff_required
@require_GET
def sessions(request):
    rows = _active_sessions().select_related("user").order_by("-last_seen")
    return render(request, "panel/sessions.html", {
        "rows": rows,
        "online_since": timezone.now() - ONLINE_WINDOW,
        "current_key": request.session.session_key,
        "section": "sessions",
    })


@staff_required
@require_POST
def session_end(request, pk: int):
    tracked = get_object_or_404(UserSession, pk=pk, ended_at__isnull=True)
    if tracked.session_key == request.session.session_key:
        messages.error(request, t("Текущую сессию завершите кнопкой «Выйти»."))
        return redirect("panel:sessions")
    _end_session(tracked)
    _admin_audit(request, "end_session", tracked.user, session=tracked.pk)
    messages.success(request, t("Сессия завершена: {device}.", device=f"{tracked.user.username}, {tracked.browser} · {tracked.os}"))
    back = request.POST.get("next", "")
    return redirect(back if back.startswith("/panel/") and "//" not in back else "panel:sessions")


# --- audit log ----------------------------------------------------------------

@staff_required
@require_GET
def audit_log(request):
    entries = LoginAudit.objects.select_related("user")
    event = request.GET.get("event", "")
    method = request.GET.get("method", "")
    result = request.GET.get("result", "")
    q = request.GET.get("q", "").strip()
    if event == "security":
        entries = entries.filter(event__in=SECURITY_EVENTS)
    elif event:
        entries = entries.filter(event=event)
    if method:
        entries = entries.filter(method=method)
    if result == "ok":
        entries = entries.filter(success=True)
    elif result == "fail":
        entries = entries.filter(success=False)
    if q:
        entries = entries.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q) | Q(ip_address__icontains=q))
    page = Paginator(entries, 50).get_page(request.GET.get("page"))
    params = {k: v for k, v in {"event": event, "method": method, "result": result, "q": q}.items() if v}
    return render(request, "panel/audit.html", {
        "page": page,
        "events": AuditEvent.choices,
        "methods": LoginMethod.choices,
        "event": event,
        "method": method,
        "result": result,
        "q": q,
        "query": urlencode(params),
        "security_events": SECURITY_EVENTS,
        "section": "audit",
    })


# --- QR attempts --------------------------------------------------------------

@staff_required
@require_GET
def qr_sessions(request):
    rows = QRSession.objects.select_related("scanned_by")[:100]
    counts = dict(QRSession.objects.values("status").annotate(n=Count("id")).values_list("status", "n"))
    return render(request, "panel/qr.html", {
        "rows": rows,
        "counts": [(value, label, counts.get(value, 0)) for value, label in QRStatus.choices],
        "consumed": QRSession.objects.filter(consumed_at__isnull=False).count(),
        "section": "qr",
    })


# --- clearing (main administrator only) -------------------------------------------

def _superuser_only(request) -> bool:
    if request.user.is_superuser:
        return True
    messages.error(request, t("Очищать данные может только главный администратор."))
    return False


@staff_required
@require_POST
def audit_clear(request):
    """Delete the whole audit log; one entry recording the clearing is kept."""
    if not _superuser_only(request):
        return redirect("panel:audit")
    _, per_model = LoginAudit.objects.all().delete()
    deleted = per_model.get(LoginAudit._meta.label, 0)
    _admin_audit(request, "clear_audit", deleted=deleted)
    messages.success(request, t("Журнал аудита очищен. Удалено записей: {n}.", n=deleted))
    return redirect("panel:audit")


@staff_required
@require_POST
def qr_clear(request):
    """Delete finished QR sessions; codes that are still open on someone's screen stay."""
    if not _superuser_only(request):
        return redirect("panel:qr")
    now = timezone.now()
    still_open = Q(status__in=[QRStatus.PENDING, QRStatus.SCANNED], expires_at__gt=now) | Q(
        status=QRStatus.CONFIRMED, consumed_at__isnull=True, exchange_expires_at__gt=now
    )
    finished = QRSession.objects.exclude(still_open)
    deleted = finished.count()
    finished.delete()
    _admin_audit(request, "clear_qr_sessions", deleted=deleted)
    messages.success(request, t("QR-сессии очищены. Удалено: {n}.", n=deleted))
    return redirect("panel:qr")


@staff_required
@require_POST
def user_sessions_clear(request, pk: int):
    """Delete a user's ended sessions (history); sessions still signed in are kept."""
    target = get_object_or_404(User, pk=pk)
    if not _superuser_only(request):
        return redirect("panel:user", pk=target.pk)
    deleted, _ = UserSession.objects.filter(user=target, ended_at__isnull=False).delete()
    _admin_audit(request, "clear_session_history", target, deleted=deleted)
    messages.success(request, t("История сессий {username} очищена. Удалено: {n}.", username=target.username, n=deleted))
    return redirect("panel:user", pk=target.pk)
