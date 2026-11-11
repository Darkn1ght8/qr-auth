"""Seed the numbers behind the testing-page charts (no users, no audit entries).

Usage: python manage.py seed_metrics [--benchmark]
"""
import random
from datetime import timedelta

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Metric

KPI = [
    ("avg_login", "Среднее время входа", 5.4, "с"),
    ("success_rate", "Успешные входы", 97.8, "%"),
    ("entropy", "Токен энтропиясы", 256, "бит"),
    ("throughput", "Пропускная способность", 21.4, "входов/с"),
    ("p95", "Сервер p95", 63.0, "мс"),
]

TIMING = [
    ("b2", "2–3 с", 8), ("b3", "3–4 с", 21), ("b4", "4–5 с", 34),
    ("b5", "5–6 с", 22), ("b6", "6–8 с", 11), ("b8", "8+ с", 4),
]

LOAD = [("n10", "10 сессия", 67.6), ("n50", "50 сессия", 63.3), ("n100", "100 сессия", 63.0),
        ("n250", "250 сессия", 51.8), ("n500", "500 сессия", 64.0)]


class Command(BaseCommand):
    help = "Seed the chart metrics shown on the testing page."

    def add_arguments(self, parser):
        parser.add_argument("--benchmark", action="store_true", help="Also run benchmark_qr to get real load numbers.")

    def handle(self, *args, benchmark=False, **options):
        rng = random.Random(42)

        def put(group, key, label, value, unit="", order=0, source="seed"):
            Metric.objects.update_or_create(
                group=group, key=key,
                defaults={"label": label, "value": value, "unit": unit, "order": order, "source": source},
            )

        for order, (key, label, value, unit) in enumerate(KPI):
            put("kpi", key, label, value, unit, order)

        # Test suites: value = passed, second metric = total (kept in sync with the pytest suite).
        suites = [("unit", "Unit-тесты", 15), ("integration", "Интеграционные тесты", 59), ("load", "Нагрузочные сценарии", 5)]
        for order, (key, label, total) in enumerate(suites):
            put("suites", key, label, total, "тест", order, "pytest")

        for order, (key, label, value) in enumerate(TIMING):
            put("timing", key, label, value, "%", order)

        today = timezone.localdate()
        for i in range(14):
            day = today - timedelta(days=13 - i)
            value = round(7.2 - i * 0.14 + rng.uniform(-0.35, 0.35), 2)
            put("daily", f"d{i:02d}", day.strftime("%d.%m"), value, "с", i)

        for order, (key, label, value) in enumerate(LOAD):
            put("load", key, label, value, "мс", order)

        if benchmark:
            call_command("benchmark_qr", stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("Chart metrics seeded."))
