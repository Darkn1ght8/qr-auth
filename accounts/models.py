from django.conf import settings
from django.db import models
from django.utils import timezone


class LoginMethod(models.TextChoices):
    PASSWORD = "password", "Құпиясөз"
    QR = "qr", "QR-код"


class AuditEvent(models.TextChoices):
    QR_CREATED = "qr_created", "QR жасалды"
    QR_SCANNED = "qr_scanned", "QR сканерленді"
    QR_CONFIRMED = "qr_confirmed", "QR расталды"
    QR_REJECTED = "qr_rejected", "QR бас тартылды"
    QR_EXPIRED = "qr_expired", "QR мерзімі өтті"
    QR_INVALID = "qr_invalid", "Жарамсыз QR"
    REPLAY_BLOCKED = "replay_blocked", "Қайталау бұғатталды"
    FINGERPRINT_MISMATCH = "fingerprint_mismatch", "Fingerprint сәйкес емес"
    LOGIN_SUCCESS = "login_success", "Сәтті кіру"
    LOGIN_FAILED = "login_failed", "Сәтсіз кіру"
    LOGOUT = "logout", "Шығу"
    RATE_LIMITED = "rate_limited", "Лимит асты"
    SESSION_REVOKED = "session_revoked", "Сессия аяқталды"
    REGISTERED = "registered", "Тіркелді"


class LoginAudit(models.Model):
    """Immutable journal of every authentication-related attempt."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries"
    )
    event = models.CharField(max_length=32, choices=AuditEvent.choices, db_index=True)
    method = models.CharField(max_length=16, choices=LoginMethod.choices, blank=True)
    success = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Аудит жазбасы"
        verbose_name_plural = "Аудит журналы"

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.event}"


class UserSession(models.Model):
    """Mirror of an authenticated Django session, used for the active-sessions page."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tracked_sessions")
    session_key = models.CharField(max_length=40, unique=True)
    method = models.CharField(max_length=16, choices=LoginMethod.choices, default=LoginMethod.PASSWORD)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=64, blank=True)
    os = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_seen"]
        verbose_name = "Пайдаланушы сессиясы"
        verbose_name_plural = "Пайдаланушы сессиялары"

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    def __str__(self) -> str:
        return f"{self.user} · {self.browser} · {self.os}"
