"""Refresh last_seen of tracked sessions and log out sessions ended elsewhere."""
import time

from django.contrib.auth import logout
from django.utils import timezone

from .models import UserSession

TOUCH_INTERVAL = 60  # seconds


class SessionTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and request.session.session_key:
            key = request.session.session_key
            last_touch = request.session.get("_tracked_touch", 0)
            now = time.time()
            if now - last_touch > TOUCH_INTERVAL:
                tracked = UserSession.objects.filter(session_key=key).only("ended_at").first()
                if tracked is not None and tracked.ended_at is not None:
                    logout(request)
                else:
                    UserSession.objects.filter(session_key=key).update(last_seen=timezone.now())
                    request.session["_tracked_touch"] = now
        return self.get_response(request)
