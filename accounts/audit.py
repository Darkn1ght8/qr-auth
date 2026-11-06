"""Single entrypoint for writing audit records."""
from __future__ import annotations

import logging

from core.netutils import get_client_ip

from .models import LoginAudit

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
    if user is not None:
        from .realtime import sessions_changed

        sessions_changed(user.pk)
    return entry
