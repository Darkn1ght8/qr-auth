"""Push session events to connected browsers over the Channels layer."""
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger("qrauth")


def user_group(user_id) -> str:
    return f"user_{user_id}"


def session_group(session_key: str) -> str:
    return f"sess_{session_key}"


def _send(group: str, message: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(group, message)
    except Exception:  # a broken channel layer must never break the HTTP request
        logger.exception("realtime send failed group=%s", group)


def sessions_changed(user_id) -> None:
    """Something changed in the user's sessions/journal: open cabinets refresh themselves."""
    _send(user_group(user_id), {"type": "sessions.changed"})


def session_revoked(session_key: str) -> None:
    """A session was ended elsewhere: the device using it logs out immediately."""
    _send(session_group(session_key), {"type": "session.revoked"})
