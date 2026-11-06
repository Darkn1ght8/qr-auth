from django.db.models import Avg, Count, F, Q
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from core.netutils import absolute_public_url
from qrauth.models import QRSession, QRStatus
from qrauth.qrrender import render as render_qr

from .models import Metric

AUTH_METHODS = [
    # name, security, convenience, phishing resistance, extra device, cost, avg time (s)
    {"name": "Құпиясөз", "security": 2, "ux": 3, "phishing": "Жоқ", "device": "Қажет емес", "cost": "Өте төмен", "time": "8–15 с"},
    {"name": "SMS OTP", "security": 3, "ux": 3, "phishing": "Жоқ", "device": "Телефон (SIM)", "cost": "SMS үшін төлем", "time": "20–40 с"},
    {"name": "TOTP", "security": 4, "ux": 3, "phishing": "Ішінара", "device": "Аутентификатор", "cost": "Төмен", "time": "12–20 с"},
    {"name": "QR-код", "security": 4, "ux": 5, "phishing": "Ішінара + контекст", "device": "Смартфон", "cost": "Төмен", "time": "4–7 с", "ours": True},
    {"name": "FIDO2 / WebAuthn", "security": 5, "ux": 4, "phishing": "Толық", "device": "Кілт / биометрия", "cost": "Орташа", "time": "3–6 с"},
]

THREATS = [
    {
        "threat": "QRLjacking",
        "desc": "Шабуылдаушы өз QR-кодын құрбанға сканерлетіп, оның сессиясын ұрлайды.",
        "measures": [
            "Телефонда сұрау жіберген браузер, ОЖ, IP және уақыт көрсетіледі",
            "QR 60 с жарамды, 30 с сайын ауысады",
            "Токен бастамашы браузердің fingerprint-іне байланған",
            "X-Frame-Options: DENY және frame-ancestors 'none'",
        ],
        "status": "partial",
        "score": 8,
    },
    {
        "threat": "Replay шабуылы",
        "desc": "Ұсталған токенді немесе алмасу кодын қайта жіберу.",
        "measures": [
            "Алмасу коды бір рет қана қолданылады (атомарлы UPDATE)",
            "Расталғаннан кейін QR токен хэші өшіріледі",
            "Nonce + HMAC қолтаңба",
        ],
        "status": "protected",
        "score": 10,
    },
    {
        "threat": "Токенді ұстап алу",
        "desc": "Желіде немесе дерекқордан токенді ұрлау.",
        "measures": [
            "Тек HTTPS + HSTS (production)",
            "Дерекқорда тек SHA-256 хэш сақталады",
            "Алмасу коды тек бастамашы сессияға WebSocket арқылы жеткізіледі",
        ],
        "status": "protected",
        "score": 9,
    },
    {
        "threat": "Brute force",
        "desc": "Токендерді немесе құпиясөзді іріктеу.",
        "measures": [
            "256-биттік энтропия (secrets.token_urlsafe(32))",
            "Генерация, сканерлеу, растау және кіруге rate limiting",
            "Барлық сәтсіз әрекеттер аудит журналына жазылады",
        ],
        "status": "protected",
        "score": 10,
    },
    {
        "threat": "Фишинг",
        "desc": "Жалған сайт нағыз QR-ды көрсетіп, пайдаланушыны алдайды.",
        "measures": [
            "Сканер тек осы доменнің URL-дарын ашады",
            "Растау экранында домен мен сұрау контексті көрсетіледі",
            "Пайдаланушы растамайынша кіру болмайды",
        ],
        "status": "partial",
        "score": 7,
    },
    {
        "threat": "CSRF",
        "desc": "Бөтен сайттан пайдаланушы атынан сұрау жіберу.",
        "measures": [
            "Барлық POST сұрауларда CSRF токен",
            "SameSite=Lax cookie",
            "Мемлекет өзгертетін GET эндпоинттер жоқ (сканерлеуден басқа, ол логин талап етеді)",
        ],
        "status": "protected",
        "score": 9,
    },
    {
        "threat": "Session fixation",
        "desc": "Шабуылдаушы алдын ала белгілі сессия идентификаторын тықпалайды.",
        "measures": [
            "Кіргеннен кейін сессия кілті ауыстырылады (cycle_key)",
            "HttpOnly + Secure + SameSite cookie",
            "«Белсенді сессиялар» бетінен кез келген сессияны аяқтауға болады",
        ],
        "status": "protected",
        "score": 10,
    },
]


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


SEQ_ACTORS = {"C": ("Компьютер (браузер)", 130), "S": ("Сервер (Django + Channels)", 500), "P": ("Телефон (кірген)", 870)}
SEQ_MESSAGES = [
    ("C", "S", "POST /qr/api/new {fp}", "req"),
    ("S", "S", "token, nonce, sha256(token), TTL=60с", "self"),
    ("S", "C", "QR(url + HMAC) · sid", "back"),
    ("C", "S", "WS /ws/qr/<sid>/ (сессияға байланған)", "req"),
    ("P", "C", "камера: QR сканерлеу", "back"),
    ("P", "S", "GET /qr/scan/<token>/<sig>/", "req"),
    ("S", "C", "status = scanned", "back"),
    ("S", "P", "растау беті: браузер, ОЖ, IP, уақыт", "back"),
    ("P", "S", "POST /qr/decide {confirm}", "req"),
    ("S", "C", "status = confirmed · бір реттік код", "ok"),
    ("C", "S", "POST /qr/api/exchange {code, fp}", "req"),
    ("S", "C", "Set-Cookie: sessionid (HttpOnly) · 302 /cabinet", "ok"),
]


def _sequence():
    actors = [{"label": label, "x": x} for label, x in SEQ_ACTORS.values()]
    messages = []
    y = 120
    for index, (src, dst, label, kind) in enumerate(SEQ_MESSAGES, start=1):
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

    kpi = _metric_map("kpi")
    suites = _metrics("suites")
    return render(
        request,
        "core/testing.html",
        {
            "kpi": kpi,
            "suites": suites,
            "chart_timing": [{"label": m.label, "value": m.value} for m in _metrics("timing")],
            "chart_daily": [{"label": m.label, "value": m.value} for m in _metrics("daily")],
            "chart_load": [{"label": m.label, "value": m.value} for m in _metrics("load")],
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


def page_not_found(request, exception=None):
    return render(request, "core/404.html", status=404)
