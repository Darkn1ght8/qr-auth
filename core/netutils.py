"""Request helpers: client IP and a lightweight User-Agent parser."""
from __future__ import annotations

import ipaddress
import re
import socket
import time
from functools import lru_cache

from django.conf import settings

TUNNEL_STALE_SECONDS = 60
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "[::1]", "::1", "0.0.0.0"}


@lru_cache(maxsize=1)
def lan_ip() -> str | None:
    """IP of this machine in the local network (the interface of the default route)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # UDP connect sends no packets
            ip = s.getsockname()[0]
        return None if ipaddress.ip_address(ip).is_loopback else ip
    except OSError:
        return None


def tunnel_url() -> str | None:
    """Public https URL of the tunnel started by `manage.py runpublic`, if it is running."""
    path = getattr(settings, "PUBLIC_URL_FILE", None)
    if not path:
        return None
    try:
        # The launcher touches the file every few seconds; an old file means the tunnel is gone.
        if time.time() - path.stat().st_mtime > TUNNEL_STALE_SECONDS:
            return None
        url = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return url.rstrip("/") if url.startswith("https://") else None


def public_base_url(request) -> str:
    """Base URL that a *phone* can open.

    Order: QR_PUBLIC_BASE_URL setting > running public tunnel (`manage.py runpublic`) >
    the request host, with `localhost` replaced by the LAN IP (on a phone, localhost
    would point to the phone itself).
    """
    configured = getattr(settings, "QR_PUBLIC_BASE_URL", "")
    if configured:
        return configured.rstrip("/")
    host = request.get_host()
    # A running public tunnel wins: its link opens from any network (mobile data, other Wi-Fi).
    tunnel = tunnel_url()
    if tunnel:
        return tunnel
    if host.startswith("["):  # IPv6 literal, e.g. [::1]:8000
        hostname, _, rest = host.partition("]")
        hostname += "]"
        port = rest.lstrip(":")
    else:
        hostname, _, port = host.partition(":")
    if hostname in LOOPBACK_HOSTS:
        ip = lan_ip()
        if ip:
            return f"{request.scheme}://{ip}{':' + port if port else ''}"
    return f"{request.scheme}://{host}"


def absolute_public_url(request, path: str) -> str:
    return public_base_url(request) + path

_BROWSERS = [
    ("Edge", r"Edg(?:e|A|iOS)?/([\d.]+)"),
    ("Opera", r"OPR/([\d.]+)"),
    ("Yandex", r"YaBrowser/([\d.]+)"),
    ("Samsung Internet", r"SamsungBrowser/([\d.]+)"),
    ("Firefox", r"(?:Firefox|FxiOS)/([\d.]+)"),
    ("Chrome", r"(?:Chrome|CriOS)/([\d.]+)"),
    ("Safari", r"Version/([\d.]+).*Safari"),
]

_SYSTEMS = [
    ("iOS", r"(?:iPhone|iPad|iPod).*OS ([\d_]+)"),
    ("Android", r"Android ([\d.]+)"),
    ("Windows", r"Windows NT ([\d.]+)"),
    ("macOS", r"Mac OS X ([\d_]+)"),
    ("ChromeOS", r"CrOS"),
    ("Linux", r"Linux"),
]

_WINDOWS_VERSIONS = {"10.0": "10/11", "6.3": "8.1", "6.2": "8", "6.1": "7"}


# Headers set by the edge proxy itself (Render sits behind Cloudflare). Cloudflare overwrites
# them on every request, so unlike X-Forwarded-For a visitor cannot fake them.
_EDGE_IP_HEADERS = ("HTTP_CF_CONNECTING_IP", "HTTP_TRUE_CLIENT_IP")


def _valid_ip(value: str | None) -> str | None:
    value = (value or "").strip()
    try:
        return str(ipaddress.ip_address(value)) if value else None
    except ValueError:
        return None


def get_client_ip(request) -> str | None:
    """The visitor's real public IP address.

    Behind a trusted proxy: the edge headers first, then the first valid address in
    X-Forwarded-For (the one the proxy saw connecting). Without a proxy: REMOTE_ADDR.
    """
    if getattr(settings, "TRUST_PROXY", False):
        for header in _EDGE_IP_HEADERS:
            ip = _valid_ip(request.META.get(header))
            if ip:
                return ip
        for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(","):
            ip = _valid_ip(part)
            if ip:
                return ip
    return _valid_ip(request.META.get("REMOTE_ADDR"))


def parse_user_agent(ua: str) -> tuple[str, str]:
    """Return (browser, os) human-readable labels."""
    ua = ua or ""
    browser = "Неизвестный браузер"
    for name, pattern in _BROWSERS:
        match = re.search(pattern, ua)
        if match:
            version = match.group(1).split(".")[0] if match.groups() else ""
            browser = f"{name} {version}".strip()
            break
    system = "Неизвестная ОС"
    for name, pattern in _SYSTEMS:
        match = re.search(pattern, ua)
        if match:
            version = match.group(1) if match.groups() else ""
            if name == "Windows":
                version = _WINDOWS_VERSIONS.get(version, version)
            system = f"{name} {version.replace('_', '.')}".strip()
            break
    return browser, system


def device_kind(ua: str) -> str:
    return "mobile" if re.search(r"Mobi|Android|iPhone|iPad", ua or "") else "desktop"
