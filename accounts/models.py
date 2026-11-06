from django.conf import settings
from django.db import models
from django.utils import timezone

from core.i18n import t_lazy


class LoginMethod(models.TextChoices):
    PASSWORD = "password", t_lazy("Пароль")
    QR = "qr", t_lazy("QR-код")


class AuditEvent(models.TextChoices):
    QR_CREATED = "qr_created", t_lazy("QR создан")
    QR_SCANNED = "qr_scanned", t_lazy("QR отсканирован")
    QR_CONFIRMED = "qr_confirmed", t_lazy("QR подтверждён")
    QR_REJECTED = "qr_rejected", t_lazy("QR отклонён")
    QR_EXPIRED = "qr_expired", t_lazy("QR истёк")
    QR_INVALID = "qr_invalid", t_lazy("Недействительный QR")
    REPLAY_BLOCKED = "replay_blocked", t_lazy("Повтор заблокирован")
    FINGERPRINT_MISMATCH = "fingerprint_mismatch", t_lazy("Fingerprint не совпал")
    LOGIN_SUCCESS = "login_success", t_lazy("Успешный вход")
    LOGIN_FAILED = "login_failed", t_lazy("Неудачный вход")
    LOGOUT = "logout", t_lazy("Выход")
    RATE_LIMITED = "rate_limited", t_lazy("Превышен лимит")
    SESSION_REVOKED = "session_revoked", t_lazy("Сессия завершена")
    REGISTERED = "registered", t_lazy("Регистрация")
    ADMIN_ACTION = "admin_action", t_lazy("Действие администратора")
    PASSWORD_CHANGED = "password_changed", t_lazy("Пароль изменён")
    PASSWORD_RESET_REQUESTED = "password_reset_requested", t_lazy("Запрошен сброс пароля")
    PASSWORD_RESET_DONE = "password_reset_done", t_lazy("Пароль сброшен")


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
