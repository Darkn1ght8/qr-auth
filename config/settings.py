"""Django settings for the QR authentication project."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-key-change-me-in-production")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")
if DEBUG:
    # Development: the phone opens the site by the computer's LAN IP (192.168.x.x),
    # which is not known in advance.
    ALLOWED_HOSTS = ["*"]

# Cloud hosting (Render sets RENDER_EXTERNAL_HOSTNAME automatically).
RENDER_HOST = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")
if DEBUG:
    # Public demo links created by `manage.py runpublic` (Cloudflare) or ngrok.
    CSRF_TRUSTED_ORIGINS += ["https://*.trycloudflare.com", "https://*.ngrok-free.app"]

# Written by `manage.py runpublic`: the public https address of the running tunnel.
PUBLIC_URL_FILE = BASE_DIR / ".public_url"

# Behind ngrok / reverse proxy the original scheme arrives in X-Forwarded-Proto.
# On by default in development so the Cloudflare tunnel's https scheme is honoured.
TRUST_PROXY = env_bool("DJANGO_TRUST_PROXY", DEBUG)
if TRUST_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "core",
    "accounts",
    "qrauth",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.SessionTrackingMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
# Optional persistent database for hosting, e.g. a free PostgreSQL from neon.tech:
# DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
if os.environ.get("DATABASE_URL"):
    import dj_database_url

    DATABASES["default"] = dj_database_url.config(conn_max_age=600, conn_health_checks=True)

REDIS_URL = os.environ.get("REDIS_URL", "").strip()
if REDIS_URL:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    # Single-process fallback: works with `manage.py runserver` (daphne).
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "kk"
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Compressed (gzip/brotli) static files served by WhiteNoise; no hashed names, so
    # relative ES-module imports keep working.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:cabinet"
LOGOUT_REDIRECT_URL = "core:home"

# --- Cookies & transport security -------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7
CSRF_COOKIE_HTTPONLY = True  # JS reads the token from <meta name="csrf-token">
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"  # QR page must never be framed (QRLjacking)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]  # Render's internal health check speaks plain http
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# --- QR authentication ---------------------------------------------------------
QR_HMAC_KEY = os.environ.get("QR_HMAC_KEY", SECRET_KEY)
QR_PUBLIC_BASE_URL = os.environ.get("QR_PUBLIC_BASE_URL", "").rstrip("/")
QR_TTL_SECONDS = int(os.environ.get("QR_TTL_SECONDS", "60"))
QR_REFRESH_SECONDS = int(os.environ.get("QR_REFRESH_SECONDS", "30"))
QR_EXCHANGE_TTL_SECONDS = int(os.environ.get("QR_EXCHANGE_TTL_SECONDS", "30"))
# When a not-yet-logged-in phone opens the QR link, the request is held this long
# so the user can sign in on the phone (granted once per QR).
QR_LOGIN_GRACE_SECONDS = int(os.environ.get("QR_LOGIN_GRACE_SECONDS", "180"))
QR_LONGPOLL_TIMEOUT = 20

# (limit, window seconds)
RATE_LIMITS = {
    "qr_new": (12, 60),
    "qr_scan": (20, 60),
    "qr_decide": (10, 60),
    "qr_exchange": (10, 60),
    "password_login": (8, 300),
    "register": (5, 3600),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"qrauth": {"handlers": ["console"], "level": "INFO"}},
}
