"""Keep UserSession and the audit log in sync with Django's auth signals."""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.utils import timezone

from core.netutils import get_client_ip, parse_user_agent

from .audit import audit
from .models import AuditEvent, LoginMethod, UserSession


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    if request is None:
        return
    if not request.session.session_key:
        request.session.save()
    method = getattr(request, "_login_method", LoginMethod.PASSWORD)
    ua = request.META.get("HTTP_USER_AGENT", "")[:512]
    browser, system = parse_user_agent(ua)
    UserSession.objects.update_or_create(
        session_key=request.session.session_key,
        defaults={
            "user": user,
            "method": method,
            "ip_address": get_client_ip(request),
            "user_agent": ua,
            "browser": browser,
            "os": system,
            "created_at": timezone.now(),
            "last_seen": timezone.now(),
            "ended_at": None,
        },
    )
    audit(request, AuditEvent.LOGIN_SUCCESS, user=user, method=method, success=True)


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    if request is None:
        return
    key = request.session.session_key
    if key:
        UserSession.objects.filter(session_key=key, ended_at__isnull=True).update(ended_at=timezone.now())
    if user is not None:
        audit(request, AuditEvent.LOGOUT, user=user, success=True)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    if request is None:
        return
    audit(
        request,
        AuditEvent.LOGIN_FAILED,
        method=LoginMethod.PASSWORD,
        username=str(credentials.get("username", ""))[:150],
    )
