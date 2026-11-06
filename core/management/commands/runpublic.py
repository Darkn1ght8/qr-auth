"""Run the site with a public https address that opens from any device.

Usage: python manage.py runpublic [--port 8000]

Starts the dev server (unless one already listens on the port) and a free
Cloudflare quick tunnel (https://<random>.trycloudflare.com, no account needed).
The public address is written to `.public_url`, so every QR code on the site
points to it. The address changes on every start; stop with Ctrl+C.
"""
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import qrcode
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
TOUCH_EVERY = 15  # seconds; core.netutils treats the file as stale after 60 s


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_cloudflared() -> str:
    bundled = Path(settings.BASE_DIR) / "tools" / "cloudflared" / ("cloudflared.exe" if sys.platform == "win32" else "cloudflared")
    if bundled.exists():
        return str(bundled)
    found = shutil.which("cloudflared")
    if found:
        return found
    raise CommandError(
        "cloudflared не найден. Скачайте: https://github.com/cloudflare/cloudflared/releases "
        "и положите в папку tools/cloudflared/ (см. README)."
    )


class Command(BaseCommand):
    help = "Start the site with a public https link (Cloudflare quick tunnel) that works from any device."

    def add_arguments(self, parser):
        parser.add_argument("--port", type=int, default=8000)

    def handle(self, *args, port, **options):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        url_file: Path = settings.PUBLIC_URL_FILE
        url_file.unlink(missing_ok=True)
        procs: list[subprocess.Popen] = []

        if port_in_use(port):
            self.stdout.write(f"Сервер уже работает на порту {port} — использую его.")
        else:
            self.stdout.write(f"Запуск сервера: 0.0.0.0:{port} …")
            procs.append(subprocess.Popen(
                [sys.executable, str(Path(settings.BASE_DIR) / "manage.py"), "runserver", f"0.0.0.0:{port}", "--noreload"],
                cwd=settings.BASE_DIR,
            ))
            for _ in range(60):
                if port_in_use(port):
                    break
                time.sleep(0.5)
            else:
                self._stop(procs, url_file)
                raise CommandError("Сервер не запустился.")

        self.stdout.write("Открываю туннель Cloudflare …")
        tunnel = subprocess.Popen(
            [find_cloudflared(), "tunnel", "--no-autoupdate", "--url", f"http://localhost:{port}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
        )
        procs.append(tunnel)
        found: dict[str, str] = {}
        ready = threading.Event()

        def read_logs():
            for line in tunnel.stderr:
                match = URL_RE.search(line)
                if match and "url" not in found:
                    found["url"] = match.group(0)
                    ready.set()

        threading.Thread(target=read_logs, daemon=True).start()
        if not ready.wait(60):
            self._stop(procs, url_file)
            raise CommandError("Туннель не открылся. Проверьте интернет и запустите снова.")

        url = found["url"]
        url_file.write_text(url, encoding="utf-8")
        self._banner(url)
        try:
            while tunnel.poll() is None:
                time.sleep(TOUCH_EVERY)
                url_file.touch()
            self.stderr.write("Туннель остановлен.")
        except KeyboardInterrupt:
            self.stdout.write("\nОстанавливаю …")
        finally:
            self._stop(procs, url_file)

    def _banner(self, url: str) -> None:
        line = "=" * 64
        self.stdout.write(self.style.SUCCESS(f"\n{line}\n  Сайт открыт в интернете — любой телефон, ноутбук, компьютер:\n\n    {url}\n"))
        self.stdout.write(f"  Вход с компьютера (QR): {url}/login/")
        self.stdout.write(f"  Сканер для телефона:    {url}/qr/scanner/")
        self.stdout.write(self.style.SUCCESS(f"{line}\n  Друг может открыть сайт, отсканировав этот код:\n"))
        qr = qrcode.QRCode(border=2)
        qr.add_data(url)
        qr.print_ascii(out=sys.stdout, invert=True)
        self.stdout.write(f"\n  Ссылка меняется при каждом запуске. Остановить: Ctrl+C\n{line}")

    @staticmethod
    def _stop(procs, url_file: Path) -> None:
        url_file.unlink(missing_ok=True)
        for proc in reversed(procs):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
