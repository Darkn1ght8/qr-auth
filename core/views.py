from django.db.models import Avg, Count, F, Q
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from core.i18n import N_, t, translate
from core.netutils import absolute_public_url
from qrauth.models import QRSession, QRStatus
from qrauth.qrrender import render as render_qr

from .models import Metric

# Russian phrases marked with N_() are translated in templates with |tr.
AUTH_METHODS = [
    # name, security, convenience, phishing resistance, extra device, cost, avg time
    {"name": N_("Пароль"), "security": 2, "ux": 3, "phishing": N_("Нет"), "device": N_("Не нужно"), "cost": N_("Очень низкая"), "time": N_("8–15 с")},
    {"name": "SMS OTP", "security": 3, "ux": 3, "phishing": N_("Нет"), "device": N_("Телефон (SIM)"), "cost": N_("Оплата SMS"), "time": N_("20–40 с")},
    {"name": "TOTP", "security": 4, "ux": 3, "phishing": N_("Частично"), "device": N_("Аутентификатор"), "cost": N_("Низкая"), "time": N_("12–20 с")},
    {"name": N_("QR-код"), "security": 4, "ux": 5, "phishing": N_("Частично + контекст"), "device": N_("Смартфон"), "cost": N_("Низкая"), "time": N_("4–7 с"), "ours": True},
    {"name": "FIDO2 / WebAuthn", "security": 5, "ux": 4, "phishing": N_("Полная"), "device": N_("Ключ / биометрия"), "cost": N_("Средняя"), "time": N_("3–6 с")},
]

THREATS = [
    {
        "threat": "QRLjacking",
        "desc": N_("Злоумышленник даёт жертве отсканировать свой QR-код и крадёт её сессию."),
        "measures": [
            N_("На телефоне показываются браузер, ОС, IP и время запроса"),
            N_("QR действует 60 с и меняется каждые 30 с"),
            N_("Токен привязан к fingerprint браузера-инициатора"),
            "X-Frame-Options: DENY + frame-ancestors 'none'",
        ],
        "status": "partial",
        "score": 8,
    },
    {
        "threat": N_("Replay-атака"),
        "desc": N_("Повторная отправка перехваченного токена или кода обмена."),
        "measures": [
            N_("Код обмена используется только один раз (атомарный UPDATE)"),
            N_("После подтверждения хэш QR-токена удаляется"),
            N_("Nonce + подпись HMAC"),
        ],
        "status": "protected",
        "score": 10,
    },
    {
        "threat": N_("Перехват токена"),
        "desc": N_("Кража токена в сети или из базы данных."),
        "measures": [
            N_("Только HTTPS + HSTS (production)"),
            N_("В базе хранится только хэш SHA-256"),
            N_("Код обмена доставляется только сессии-инициатору через WebSocket"),
        ],
        "status": "protected",
        "score": 9,
    },
    {
        "threat": "Brute force",
        "desc": N_("Перебор токенов или паролей."),
        "measures": [
            N_("256 бит энтропии (secrets.token_urlsafe(32))"),
            N_("Rate limiting на генерацию, сканирование, подтверждение и вход"),
            N_("Все неудачные попытки пишутся в журнал аудита"),
        ],
        "status": "protected",
        "score": 10,
    },
    {
        "threat": N_("Фишинг"),
        "desc": N_("Поддельный сайт показывает настоящий QR и обманывает пользователя."),
        "measures": [
            N_("Сканер открывает только URL этого домена"),
            N_("На экране подтверждения виден домен и контекст запроса"),
            N_("Без подтверждения пользователем вход невозможен"),
        ],
        "status": "partial",
        "score": 7,
    },
    {
        "threat": "CSRF",
        "desc": N_("Отправка запроса от имени пользователя с чужого сайта."),
        "measures": [
            N_("CSRF-токен во всех POST-запросах"),
            "SameSite=Lax cookie",
            N_("Нет GET-эндпоинтов, меняющих состояние (кроме сканирования, которое требует входа)"),
        ],
        "status": "protected",
        "score": 9,
    },
    {
        "threat": "Session fixation",
        "desc": N_("Злоумышленник подсовывает заранее известный идентификатор сессии."),
        "measures": [
            N_("После входа ключ сессии меняется (cycle_key)"),
            "HttpOnly + Secure + SameSite cookie",
            N_("Любую сессию можно завершить на странице «Активные сессии»"),
        ],
        "status": "protected",
        "score": 10,
    },
]

KPI_LABELS = {
    "avg_login": (N_("Среднее время входа"), N_("с")),
    "success_rate": (N_("Успешные входы"), "%"),
    "entropy": (N_("Энтропия токена"), N_("бит")),
    "throughput": (N_("Пропускная способность"), N_("входов/с")),
    "p95": (N_("Сервер p95"), N_("мс")),
}
SUITE_LABELS = {
    "unit": N_("Unit-тесты"),
    "integration": N_("Интеграционные тесты"),
    "load": N_("Нагрузочные сценарии"),
}
TIMING_LABELS = {"b2": "2–3", "b3": "3–4", "b4": "4–5", "b5": "5–6", "b6": "6–8", "b8": "8+"}


def _metrics(group: str) -> list[Metric]:
    return list(Metric.objects.filter(group=group))


def _metric_map(group: str) -> dict[str, Metric]:
    return {m.key: m for m in _metrics(group)}


def _security_score() -> float:
    return round(sum(t["score"] for t in THREATS) / len(THREATS), 1)


@require_GET
def home(request):
    # Scanning the hero QR opens the phone-side page of the demo on the phone.
    phone_url = absolute_public_url(request, reverse("qrauth:scanner"))
    svg, rows = render_qr(phone_url)
    return render(
        request,
        "core/home.html",
        {"hero_matrix": rows, "hero_svg": svg, "phone_url": phone_url, "security_score": _security_score()},
    )


@require_GET
def overview(request):
    return render(request, "core/overview.html", {"methods": AUTH_METHODS})


SEQ_ACTORS = {"C": (N_("Компьютер (браузер)"), 130), "S": (N_("Сервер (Django + Channels)"), 500), "P": (N_("Телефон (вошедший)"), 870)}
SEQ_MESSAGES = [
    ("C", "S", "POST /qr/api/new {fp}", "req"),
    ("S", "S", "token, nonce, sha256(token), TTL=60s", "self"),
    ("S", "C", "QR(url + HMAC) · sid", "back"),
    ("C", "S", N_("WS /ws/qr/<sid>/ (привязан к сессии)"), "req"),
    ("P", "C", N_("камера: сканирование QR"), "back"),
    ("P", "S", "GET /qr/scan/<token>/<sig>/", "req"),
    ("S", "C", "status = scanned", "back"),
    ("S", "P", N_("страница подтверждения: браузер, ОС, IP, время"), "back"),
    ("P", "S", "POST /qr/decide {confirm}", "req"),
    ("S", "C", N_("status = confirmed · одноразовый код"), "ok"),
    ("C", "S", "POST /qr/api/exchange {code, fp}", "req"),
    ("S", "C", "Set-Cookie: sessionid (HttpOnly) · 302 /cabinet", "ok"),
]


def _sequence():
    actors = [{"label": translate(label), "x": x} for label, x in SEQ_ACTORS.values()]
    messages = []
    y = 120
    for index, (src, dst, label, kind) in enumerate(SEQ_MESSAGES, start=1):
        label = translate(label)
        x1, x2 = SEQ_ACTORS[src][1], SEQ_ACTORS[dst][1]
        if src == dst:
            messages.append({"i": index, "self": True, "x": x1, "y": y, "label": label, "kind": kind,
                             "path": f"M{x1} {y - 6} h48 v18 h-44", "tx": x1 + 60, "ty": y + 8})
            y += 52
            continue
        direction = 1 if x2 > x1 else -1
        tip = x2 - direction * 2
        messages.append({
            "i": index, "self": False, "x1": x1, "x2": tip - direction * 8, "y": y, "label": label, "kind": kind,
            "arrow": f"{tip},{y} {tip - direction * 10},{y - 5} {tip - direction * 10},{y + 5}",
            "tx": (x1 + x2) / 2, "ty": y - 10,
        })
        y += 46
    return {"actors": actors, "messages": messages, "height": y + 20}


@require_GET
def how(request):
    return render(request, "core/how.html", {"seq": _sequence()})


@require_GET
def demo(request):
    scanner_url = absolute_public_url(request, reverse("qrauth:scanner"))
    svg, _ = render_qr(scanner_url)
    return render(request, "core/demo.html", {"scanner_svg": svg, "scanner_url": scanner_url})


@require_GET
def testing(request):
    sessions = QRSession.objects.all()
    live = sessions.aggregate(
        total=Count("id"),
        consumed=Count("id", filter=Q(consumed_at__isnull=False)),
        rejected=Count("id", filter=Q(status=QRStatus.REJECTED)),
        expired=Count("id", filter=Q(status=QRStatus.EXPIRED)),
        scanned=Count("id", filter=Q(scanned_at__isnull=False)),
    )
    durations = sessions.filter(consumed_at__isnull=False).annotate(d=F("consumed_at") - F("created_at"))
    avg = durations.aggregate(avg=Avg("d"))["avg"]
    live["avg_seconds"] = round(avg.total_seconds(), 1) if avg else None
    live["success_rate"] = round(100 * live["consumed"] / live["scanned"], 1) if live["scanned"] else None

    kpi = {}
    for key, metric in _metric_map("kpi").items():
        label, unit = KPI_LABELS.get(key, (metric.label, metric.unit))
        metric.label, metric.unit = translate(label), translate(unit)
        kpi[key] = metric
    suites = _metrics("suites")
    for metric in suites:
        metric.label = translate(SUITE_LABELS.get(metric.key, metric.label))
        metric.unit = t("тестов")
    return render(
        request,
        "core/testing.html",
        {
            "kpi": kpi,
            "suites": suites,
            "chart_timing": [{"label": TIMING_LABELS.get(m.key, m.key) + " " + t("с"), "value": m.value} for m in _metrics("timing")],
            "chart_daily": [{"label": m.label, "value": m.value} for m in _metrics("daily")],
            "chart_load": [{"label": t("{count} сессий", count=m.key.lstrip("n")), "value": m.value} for m in _metrics("load")],
            "load_source": next((m.source for m in _metrics("load")), "seed"),
            "live": live,
            "has_data": bool(kpi),
        },
    )


@require_GET
def security(request):
    protected = sum(1 for t in THREATS if t["status"] == "protected")
    return render(
        request,
        "core/security.html",
        {
            "threats": THREATS,
            "score": _security_score(),
            "protected": protected,
            "partial": len(THREATS) - protected,
        },
    )


@require_GET
def healthz(request):
    """Cheap liveness probe for Render's health check and the keep-awake ping."""
    from django.db import connection
    from django.http import HttpResponse

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    # Engine name only (no host/credentials): shows whether persistent storage is in use.
    return HttpResponse(f"ok {connection.vendor}", content_type="text/plain")


def page_not_found(request, exception=None):
    return render(request, "core/404.html", status=404)
