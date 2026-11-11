"""Which tracked sessions still count as "active", and closing the ones that do not.

A login stays valid until the user presses «Выйти», the session cookie expires, or the
device stays idle longer than IDLE_TIMEOUT. Without this cleanup a device that simply
stopped visiting kept showing up as an active session forever.
"""
from datetime import timedelta

from django.contrib.sessions.models import Session
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from .models import UserSession
from .realtime import session_revoked

IDLE_TIMEOUT = timedelta(hours=24)


def close_stale_sessions() -> int:
    """End sessions that expired, were deleted, or were idle too long; returns how many."""
    now = timezone.now()
    live = Session.objects.filter(session_key=OuterRef("session_key"), expire_date__gt=now)
    stale = (
        UserSession.objects.filter(ended_at__isnull=True)
        .annotate(live=Exists(live))
        .filter(Q(live=False) | Q(last_seen__lt=now - IDLE_TIMEOUT))
    )
    keys = list(stale.values_list("session_key", flat=True))
    if not keys:
        return 0
    Session.objects.filter(session_key__in=keys).delete()  # the idle device is signed out too
    UserSession.objects.filter(session_key__in=keys, ended_at__isnull=True).update(ended_at=now)
    for key in keys:
        session_revoked(key)
    return len(keys)
