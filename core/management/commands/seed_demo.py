"""Create the demo user and the data behind the testing-page charts.

Usage: python manage.py seed_demo [--benchmark]
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import AuditEvent, LoginAudit, LoginMethod
from core.models import Metric

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "Demo12345!"

KPI = [
    ("avg_login", "Орташа кіру уақыты", 5.4, "с"),
    ("success_rate", "Сәтті кірулер", 97.8, "%"),
    ("entropy", "Токен энтропиясы", 256, "бит"),
    ("throughput", "Өткізу қабілеті", 21.4, "кіру/с"),
    ("p95", "Сервер p95", 63.0, "мс"),
]

TIMING = [
    ("b2", "2–3 с", 8), ("b3", "3–4 с", 21), ("b4", "4–5 с", 34),
    ("b5", "5–6 с", 22), ("b6", "6–8 с", 11), ("b8", "8+ с", 4),
]

LOAD = [("n10", "10 сессия", 67.6), ("n50", "50 сессия", 63.3), ("n100", "100 сессия", 63.0),
        ("n250", "250 сессия", 51.8), ("n500", "500 сессия", 64.0)]


class Command(BaseCommand):
    help = "Seed the demo user, audit history and chart metrics."

    def add_arguments(self, parser):
        parser.add_argument("--benchmark", action="store_true", help="Also run benchmark_qr to get real load numbers.")

    def handle(self, *args, benchmark=False, **options):
        rng = random.Random(42)
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME, defaults={"first_name": "Демо", "email": "demo@example.kz"}
        )
        user.set_password(DEMO_PASSWORD)
        user.save()

        def put(group, key, label, value, unit="", order=0, source="seed"):
            Metric.objects.update_or_create(
                group=group, key=key,
                defaults={"label": label, "value": value, "unit": unit, "order": order, "source": source},
            )

        for order, (key, label, value, unit) in enumerate(KPI):
            put("kpi", key, label, value, unit, order)

        # Test suites: value = passed, second metric = total (kept in sync with the pytest suite).
        suites = [("unit", "Unit тесттер", 15), ("integration", "Интеграциялық тесттер", 34), ("load", "Жүктеме сценарийлері", 5)]
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

        if not LoginAudit.objects.filter(user=user).exists():
            now = timezone.now()
            history = [
                (AuditEvent.LOGIN_SUCCESS, LoginMethod.PASSWORD, True, 3 * 24 * 60),
                (AuditEvent.QR_SCANNED, LoginMethod.QR, False, 2 * 24 * 60 + 5),
                (AuditEvent.QR_CONFIRMED, LoginMethod.QR, True, 2 * 24 * 60 + 4),
                (AuditEvent.LOGIN_SUCCESS, LoginMethod.QR, True, 2 * 24 * 60 + 4),
                (AuditEvent.LOGIN_FAILED, LoginMethod.PASSWORD, False, 26 * 60),
                (AuditEvent.QR_REJECTED, LoginMethod.QR, False, 24 * 60),
                (AuditEvent.LOGIN_SUCCESS, LoginMethod.QR, True, 90),
            ]
            for event, method, success, minutes_ago in history:
                LoginAudit.objects.create(
                    user=user, event=event, method=method, success=success,
                    ip_address="192.168.1.%d" % rng.randint(2, 250),
                    user_agent="Mozilla/5.0 (seed)", details={"seed": True},
                    created_at=now - timedelta(minutes=minutes_ago),
                )

        if benchmark:
            call_command("benchmark_qr", stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS(
            f"Demo user '{DEMO_USERNAME}' {'created' if created else 'updated'}; metrics seeded."
        ))
