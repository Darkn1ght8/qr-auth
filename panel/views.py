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
from django.db.models import Count, F, Max, Q
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from accounts.audit import audit
from accounts.models import AuditEvent, LoginAudit, LoginMethod, UserSession
from accounts.views import _end_session
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


def _with_users():
    """Users annotated with login statistics (distinct counts avoid join multiplication)."""
    return User.objects.annotate(
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
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
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
    writer.writerow(["ID", "Логин", "Аты", "Пошта", "Тіркелген", "Соңғы кіру", "Кірулер", "QR кірулер", "Белсенді сессиялар", "Мәртебе", "Әкімші"])
    for u in queryset:
        writer.writerow([
            u.pk, u.username, u.get_full_name(), u.email,
            timezone.localtime(u.date_joined).strftime("%Y-%m-%d %H:%M"),
            timezone.localtime(u.last_login).strftime("%Y-%m-%d %H:%M") if u.last_login else "",
            u.login_count, u.qr_login_count, u.active_sessions,
            "белсенді" if u.is_active else "бұғатталған", "иә" if u.is_staff else "",
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
    return render(request, "panel/user_detail.html", {
        "target": target,
        "sessions": sessions,
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

    if is_self and action in {"block", "remove_admin", "delete", "end_sessions"}:
        messages.error(request, "Бұл әрекетті өз аккаунтыңызға қолдануға болмайды.")
        return back
    if target.is_superuser and not request.user.is_superuser and action in {"block", "remove_admin", "delete"}:
        messages.error(request, "Бас әкімшіні тек бас әкімші өзгерте алады.")
        return back

    ended = 0
    if action in {"block", "end_sessions", "delete"}:
        for tracked in UserSession.objects.filter(user=target, ended_at__isnull=True):
            _end_session(tracked)  # pushes an instant logout to that device
            ended += 1

    if action == "block":
        target.is_active = False
        target.save(update_fields=["is_active"])
        messages.success(request, f"{target.username} бұғатталды, {ended} сессия аяқталды.")
    elif action == "unblock":
        target.is_active = True
        target.save(update_fields=["is_active"])
        messages.success(request, f"{target.username} бұғаттан шығарылды.")
    elif action == "end_sessions":
        messages.success(request, f"{target.username}: {ended} сессия аяқталды.")
    elif action == "make_admin":
        target.is_staff = True
        target.save(update_fields=["is_staff"])
        messages.success(request, f"{target.username} енді әкімші.")
    elif action == "remove_admin":
        target.is_staff = False
        target.is_superuser = False
        target.save(update_fields=["is_staff", "is_superuser"])
        messages.success(request, f"{target.username} әкімші құқығынан айырылды.")
    elif action == "delete":
        if request.POST.get("confirm_username", "").strip() != target.username:
            messages.error(request, "Жою үшін пайдаланушының логинін дәл енгізіңіз.")
            return back
        _admin_audit(request, "delete", target, email=target.email)
        username = target.username
        target.delete()
        messages.success(request, f"{username} аккаунты жойылды.")
        return redirect("panel:users")
    else:
        messages.error(request, "Белгісіз әрекет.")
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
        messages.error(request, "Ағымдағы сессияны «Шығу» батырмасымен аяқтаңыз.")
        return redirect("panel:sessions")
    _end_session(tracked)
    _admin_audit(request, "end_session", tracked.user, session=tracked.pk)
    messages.success(request, f"Сессия аяқталды: {tracked.user.username}, {tracked.browser} · {tracked.os}.")
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
