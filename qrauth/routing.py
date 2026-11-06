from django.urls import re_path

from .consumers import QRStatusConsumer

websocket_urlpatterns = [
    re_path(r"^ws/qr/(?P<sid>[0-9a-f-]{32,36})/$", QRStatusConsumer.as_asgi()),
]
