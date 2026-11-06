"""Measure the full QR login flow through the service layer and store results.

Usage: python manage.py benchmark_qr [--sizes 10 50 100 250 500]
"""
import statistics
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Metric
from qrauth import services
from qrauth.models import QRSession

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"


def run_flow(user) -> tuple[float, str]:
    start = time.perf_counter()
    issued = services.create_qr_session(client_fp="bench-fp", ip="127.0.0.1", user_agent=UA)
    session = services.resolve_token(issued.token, issued.signature)
    session = services.mark_scanned(session, user, "127.0.0.2")
    code = services.confirm(session, user)
    services.exchange(session_id=str(session.pk), code=code, client_fp="bench-fp", user_agent=UA)
    return (time.perf_counter() - start) * 1000, str(session.pk)


class Command(BaseCommand):
    help = "Benchmark the QR flow (create → scan → confirm → exchange) and save results for the testing page."

    def add_arguments(self, parser):
        parser.add_argument("--sizes", nargs="+", type=int, default=[10, 50, 100, 250, 500])

    def handle(self, *args, sizes, **options):
        User = get_user_model()
        user, _ = User.objects.get_or_create(username="bench_user")
        all_samples: list[float] = []
        created: list[str] = []
        for order, size in enumerate(sizes):
            samples = []
            for _ in range(size):
                ms, sid = run_flow(user)
                samples.append(ms)
                created.append(sid)
            samples.sort()
            p95 = samples[max(0, int(len(samples) * 0.95) - 1)]
            all_samples.extend(samples)
            Metric.objects.update_or_create(
                group="load",
                key=f"n{size}",
                defaults={"label": f"{size} сессия", "value": round(p95, 2), "unit": "мс", "order": order, "source": "benchmark"},
            )
            self.stdout.write(f"{size:>5} flows: median {statistics.median(samples):.2f} ms, p95 {p95:.2f} ms")

        throughput = 1000 / statistics.mean(all_samples)
        Metric.objects.update_or_create(
            group="kpi", key="throughput",
            defaults={"label": "Өткізу қабілеті", "value": round(throughput, 1), "unit": "кіру/с", "order": 3, "source": "benchmark"},
        )
        Metric.objects.update_or_create(
            group="kpi", key="p95",
            defaults={"label": "Сервер p95", "value": round(sorted(all_samples)[int(len(all_samples) * 0.95) - 1], 1),
                      "unit": "мс", "order": 4, "source": "benchmark"},
        )
        QRSession.objects.filter(pk__in=created).delete()
        user.delete()
        self.stdout.write(self.style.SUCCESS(f"Done: {len(all_samples)} flows, {throughput:.1f} logins/s"))
