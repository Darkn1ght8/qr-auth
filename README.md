# QR·AUTH — QR-код арқылы қауіпсіз аутентификация жүйесі

Дипломдық жоба: презентациялық сайт және жұмыс істейтін прототип. Пайдаланушы компьютерде
құпиясөз термейді — жүйеге бұрын кірген телефонымен QR-кодты сканерлеп, кіруді растайды.

## Архитектура

```
 Компьютер (браузер)            Сервер (Django 5 + Channels)              Телефон (кірген)
 ───────────────────            ────────────────────────────              ────────────────
 /login  ── POST /qr/api/new ─▶ token = secrets.token_urlsafe(32)
                                 БД: sha256(token), nonce, fp_hash, TTL 60 с
         ◀── QR (URL + HMAC) ── /qr/scan/<token>/<hmac>/
 WS /ws/qr/<sid>/ ─────────────▶ топқа жазылу (тек осы сессия)
                                                         ◀── GET /qr/scan/… (логин міндетті)
         ◀── status: scanned ── pending → scanned        ── растау беті: браузер, ОЖ, IP, уақыт ─▶
                                                         ◀── POST /qr/decide {confirm|reject}
         ◀── status: confirmed + бір реттік код (30 с, тек кэште)
 POST /qr/api/exchange {code, fp} ─▶ хэш + fingerprint тексеру, атомарлы «consumed»
         ◀── Set-Cookie: sessionid (HttpOnly, Secure, SameSite=Lax), сессия кілті ауысады
```

Күйлер: `pending → scanned → confirmed | rejected | expired`. QR 30 секунд сайын жаңарады
(ескі токен бірден жойылады), токен 60 секунд жарамды.

### Қауіпсіздік механизмдері

| Механизм | Қай жерде |
|---|---|
| Дерекқорда тек SHA-256 хэш (токен және алмасу коды) | `qrauth/services.py` |
| HMAC-SHA256 қолтаңба + nonce | `sign_token`, `verify_signature` |
| Бір реттік алмасу (атомарлы `UPDATE … WHERE consumed_at IS NULL`) | `services.exchange` |
| Токенді бастамашы браузерге байлау (сессия + fingerprint) | `views._bound`, `compute_fingerprint` |
| QRLjacking: телефонда сұрау контексті, `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'` | `confirm.html`, `core/middleware.py` |
| Rate limiting (генерация, сканерлеу, растау, алмасу, құпиясөз, тіркелу) | `core/ratelimit.py`, `RATE_LIMITS` |
| CSRF, HttpOnly + Secure + SameSite cookie, HSTS, SSL redirect (production) | `config/settings.py` |
| Session fixation: `login()` сессия кілтін ауыстырады | `accounts/views.py`, `qrauth/views.py` |
| Аудит журналы (барлық әрекеттер) | `accounts/audit.py`, `LoginAudit` |
| «Белсенді сессиялар»: кез келген сессияны аяқтау | `accounts/views.py`, `/cabinet/` |
| Сканер тек осы сайттың `/qr/scan/` URL-дарын ашады (фишинг) | `static/js/pages/scanner.js` |

## Жоба құрылымы

```
qr-auth/
├── config/            settings, urls, asgi (HTTP + WebSocket), wsgi
├── core/              презентация беттері, CSP middleware, rate limiter, seed/benchmark командалары
├── accounts/          тіркелу, құпиясөзбен кіру, кабинет, белсенді сессиялар, аудит
├── qrauth/            QRSession моделі, күйлер машинасы (services.py), API, WebSocket consumer, тесттер
├── templates/         Django шаблондары (қазақ тілінде)
└── static/
    ├── css/main.css   дизайн жүйесі (8pt тор, қараңғы тақырып, reduced-motion)
    └── js/            ES-модульдер: app.js, lib/*, pages/* (Three.js hero, QR бөлшектері, сканер)
```

## Жергілікті іске қосу

Python 3.12+ қажет.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # қажет болса мәндерін өзгертіңіз
python manage.py migrate
python manage.py seed_demo --benchmark
python manage.py runserver 0.0.0.0:8000
```

`daphne` орнатылғандықтан, `runserver` ASGI серверін (HTTP + WebSocket) іске қосады.
Сайт: http://localhost:8000. Демо аккаунт: логин `demo`, құпиясөз `Demo12345!` (тек демо үшін).

Redis болмаса, Channels пен кэш жадта жұмыс істейді (бір процесс). Бірнеше процесс немесе
production үшін `.env` ішінде `REDIS_URL=redis://localhost:6379/0` көрсетіңіз.

## Тұрақты хостинг (компьютер өшірулі болса да жұмыс істейді) — Render

Жоба Render үшін дайын: `render.yaml` (Blueprint), `start.sh` (migrate → seed_demo → daphne).

1. GitHub-та жаңа бос репозиторий жасаңыз (README қоспаңыз), содан кейін осы қалтадан:
   ```bash
   git remote add origin https://github.com/<логин>/qr-auth.git
   git push -u origin main
   ```
2. https://render.com → GitHub арқылы тіркеліңіз → **New → Blueprint** → репозиторийді таңдаңыз → **Apply**.
   `DATABASE_URL` сұралса — бос қалдыруға болады.
3. 3–5 минуттан кейін сайт `https://qr-auth-xxxx.onrender.com` адресінде ашылады. Барлық QR-кодтар
   осы адресті автоматты түрде қолданады. Әр `git push` сайтты автоматты түрде жаңартады.

Тегін тарифтің ерекшеліктері:
- 15 минут ешкім кірмесе, сервер «ұйықтайды»; келесі ашылуы ~30–60 секунд алады.
- SQLite дерекқоры әр қайта іске қосылғанда тазаланады (демо аккаунт `demo` қайта жасалады).
  Тіркелген пайдаланушыларды сақтау үшін тегін PostgreSQL (мысалы, neon.tech) жасап, оның
  сілтемесін Render-де `DATABASE_URL` айнымалысына жазыңыз.

## Кез келген құрылғыдан ашу (интернет арқылы, ұсынылады)

`run_public.bat` файлын екі рет басыңыз (немесе `python manage.py runpublic`). Ол сервер мен тегін
Cloudflare туннелін іске қосады да, терминалда `https://….trycloudflare.com` сілтемесін және оның
QR-кодын көрсетеді. Бұл сілтеме **кез келген** телефоннан, ноутбуктан, компьютерден ашылады —
басқа Wi-Fi немесе мобильді интернет болса да. HTTPS болғандықтан, телефонда сканердің тікелей
камерасы да жұмыс істейді. Сайттағы барлық QR-кодтар автоматты түрде осы сілтемені қолданады.

- Сілтеме компьютер мен терминал қосулы тұрғанда ғана жұмыс істейді; Ctrl+C — тоқтату.
- Әр іске қосқанда сілтеме өзгереді — досыңызға жаңасын жіберіңіз.
- `cloudflared.exe` `tools/cloudflared/` қалтасында болуы керек
  (https://github.com/cloudflare/cloudflared/releases → `cloudflared-windows-amd64.exe`).

## Телефоннан демо — ең қарапайым жол (бір Wi-Fi, HTTPS қажет емес)

1. Серверді барлық интерфейсте іске қосыңыз: `python manage.py runserver 0.0.0.0:8000`
2. Компьютерде `http://localhost:8000/login/` ашыңыз. QR ішіне `localhost` емес, компьютердің
   жергілікті IP-і (мысалы `http://192.168.1.5:8000/...`) автоматты түрде жазылады — оны QR астынан көресіз.
3. Телефон сол Wi-Fi желісінде болсын. Телефонның **кәдімгі камерасымен** QR-ды сканерлеңіз —
   сілтеме браузерде ашылады. Телефонда кірмеген болсаңыз, кіру беті ашылады: осы кезде компьютердегі
   QR «ұсталады» (3 минут), кіргеннен кейін бірден растау беті шығады.
4. Сайттағы сканер HTTP арқылы «Суретке түсіріп сканерлеу» режимінде жұмыс істейді
   (тікелей бейне камера тек HTTPS-те қолжетімді).

Windows бірінші рет іске қосқанда брандмауэр Python-ға желі рұқсатын сұрайды — **«Жеке желілер»
(Private networks)** үшін рұқсат беріңіз, әйтпесе телефон сайтты аша алмайды.

## Телефоннан демо (бір Wi-Fi желісі, HTTPS)

Браузер камераны тек HTTPS (немесе localhost) арқылы береді. Ең оңай жолы — ngrok:

1. Серверді іске қосыңыз: `python manage.py runserver 0.0.0.0:8000`
2. Басқа терминалда: `ngrok http 8000` → `https://abcd-1234.ngrok-free.app` сияқты адрес береді.
3. `.env` файлында:
   ```
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app
   DJANGO_CSRF_TRUSTED_ORIGINS=https://*.ngrok-free.app
   DJANGO_TRUST_PROXY=True
   ```
   және серверді қайта іске қосыңыз.
4. **Компьютерде де, телефонда да** ngrok адресін ашыңыз (QR ішіндегі домен компьютер ашқан доменмен бірдей болады).
5. Телефонда: тіркеліңіз немесе `demo` аккаунтымен кіріңіз → «Сканерді ашу».
6. Компьютерде: «QR арқылы кіру» → телефонмен сканерлеңіз → «Растау».

ngrok-сыз балама: `mkcert` арқылы жергілікті сертификат жасап, HTTPS проксиді (мысалы, Caddy)
қолдануға болады. HTTPS болмаса да, телефонның кәдімгі камерасымен QR-ды сканерлеуге болады
немесе сканер бетіндегі «қолмен енгізу» өрісін пайдаланыңыз.

## Тесттер

```bash
pytest
```

29 тест: 15 unit (`qrauth/tests/test_services.py` — токен генерациясы, TTL, қайта қолдану,
fingerprint, бас тарту) және 14 интеграциялық (`qrauth/tests/test_views.py` — толық HTTP ағыны,
сессияға байлау, rate limit, аудит, сессияны аяқтау).

Жүктеме өлшемі: `python manage.py benchmark_qr --sizes 10 50 100 250 500` — нәтижелері
«Тестілеу» бетіндегі графикке жазылады.

## Production ескертпелері

- `DJANGO_DEBUG=False` → HTTPS redirect, HSTS, Secure cookie автоматты қосылады.
- `python manage.py collectstatic`, сервер: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`.
- Redis (`REDIS_URL`) және PostgreSQL ұсынылады.
- Сайт GSAP, Lenis, Three.js және html5-qrcode кітапханаларын CDN-нен жүктейді. Қорғау кезінде
  интернет болмаса, оларды `static/vendor/` ішіне жүктеп, шаблондардағы сілтемелерді ауыстырыңыз.
