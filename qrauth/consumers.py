"""WebSocket channel that pushes QR status changes to the initiating browser."""
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import services


class QRStatusConsumer(AsyncJsonWebsocketConsumer):
    group_name: str | None = None

    async def connect(self):
        sid = self.scope["url_route"]["kwargs"]["sid"]
        try:
            self.sid = str(uuid.UUID(sid))
        except ValueError:
            await self.close(code=4400)
            return
        if not await self._is_bound():
            await self.close(code=4403)
            return
        self.group_name = f"qr_{uuid.UUID(self.sid).hex}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(await self._payload())

    async def disconnect(self, code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json(await self._payload())

    async def qr_status(self, event):
        await self.send_json(await self._payload())

    @database_sync_to_async
    def _is_bound(self) -> bool:
        session = self.scope.get("session")
        return session is not None and session.get("qr_sid") == self.sid

    @database_sync_to_async
    def _payload(self) -> dict:
        return {"type": "status", **services.payload_for(self.sid)}
