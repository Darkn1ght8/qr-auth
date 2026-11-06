"""WebSocket channel for a logged-in browser: instant logout and live cabinet updates."""
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import UserSession
from .realtime import ADMINS_GROUP, session_group, user_group


class SessionConsumer(AsyncJsonWebsocketConsumer):
    groups_joined: list[str] = []

    async def connect(self):
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=4401)
            return
        key = await self._session_key()
        if not key or not await self._is_active(key):
            # Session was ended between page load and socket connect.
            await self.accept()
            await self.send_json({"type": "revoked"})
            await self.close(code=4401)
            return
        self.groups_joined = [user_group(user.pk), session_group(key)]
        if user.is_staff:
            self.groups_joined.append(ADMINS_GROUP)
        for group in self.groups_joined:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()
        await self.send_json({"type": "hello"})

    async def disconnect(self, code):
        for group in self.groups_joined:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            key = await self._session_key()
            if key and await self._is_active(key):
                await self.send_json({"type": "pong"})
            else:
                await self.send_json({"type": "revoked"})

    async def session_revoked(self, event):
        await self.send_json({"type": "revoked"})
        await self.close(code=4401)

    async def sessions_changed(self, event):
        await self.send_json({"type": "changed"})

    @database_sync_to_async
    def _session_key(self):
        session = self.scope.get("session")
        return session.session_key if session is not None else None

    @database_sync_to_async
    def _is_active(self, key: str) -> bool:
        from django.contrib.sessions.models import Session
        from django.utils import timezone

        if not Session.objects.filter(session_key=key, expire_date__gt=timezone.now()).exists():
            return False
        tracked = UserSession.objects.filter(session_key=key).only("ended_at").first()
        return tracked is None or tracked.ended_at is None
