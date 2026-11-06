"""Single entrypoint for writing audit records."""
from __future__ import annotations

import logging

from core.netutils import get_client_ip

from .models import AuditEvent, LoginAudit

logger = logging.getLogger("qrauth")


def audit(request, event: str, *, user=None, method: str = "", success: bool = False, **details) -> LoginAudit:
    if user is None and request is not None and getattr(request, "user", None) is not None:
        if request.user.is_authenticated:
            user = request.user
    entry = LoginAudit.objects.create(
        user=user,
        event=event,
        method=method,
        success=success,
        ip_address=get_client_ip(request) if request is not None else None,
        user_agent=(request.META.get("HTTP_USER_AGENT", "")[:512] if request is not None else ""),
        details=details,
    )
    logger.info("audit event=%s user=%s success=%s details=%s", event, getattr(user, "pk", None), success, details)
    from .realtime import admins_changed, sessions_changed

    if user is not None:
        sessions_changed(user.pk)
    if event != AuditEvent.QR_CREATED:  # every open QR page makes one each 30 s: too noisy for admins
        admins_changed()
    return entry
