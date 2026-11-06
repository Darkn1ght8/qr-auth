import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class QRStatus(models.TextChoices):
    PENDING = "pending", "Күтуде"
    SCANNED = "scanned", "Сканерленді"
    CONFIRMED = "confirmed", "Расталды"
    REJECTED = "rejected", "Бас тартылды"
    EXPIRED = "expired", "Мерзімі өтті"


class QRSession(models.Model):
    """One QR login attempt initiated by a desktop browser.

    Only SHA-256 hashes of the QR token and of the exchange code are stored;
    both are wiped once the attempt is consumed or invalidated.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True, null=True, blank=True)
    nonce = models.CharField(max_length=32)
    fingerprint_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=QRStatus.choices, default=QRStatus.PENDING, db_index=True)

    initiator_ip = models.GenericIPAddressField(null=True, blank=True)
    initiator_user_agent = models.TextField(blank=True)
    initiator_browser = models.CharField(max_length=64, blank=True)
    initiator_os = models.CharField(max_length=64, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    opened_at = models.DateTimeField(null=True, blank=True)  # link opened on a phone that still has to log in
    scanned_at = models.DateTimeField(null=True, blank=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="qr_sessions"
    )
    scanner_ip = models.GenericIPAddressField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    exchange_code_hash = models.CharField(max_length=64, null=True, blank=True)
    exchange_expires_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "QR сессия"
        verbose_name_plural = "QR сессиялар"

    def __str__(self) -> str:
        return f"{self.pk} [{self.status}]"

    @property
    def group_name(self) -> str:
        return f"qr_{self.pk.hex}"

    @property
    def is_terminal(self) -> bool:
        return self.status in {QRStatus.REJECTED, QRStatus.EXPIRED} or self.consumed_at is not None

    def seconds_left(self) -> int:
        return max(0, int((self.expires_at - timezone.now()).total_seconds()))

    @property
    def login_duration(self) -> float | None:
        if self.consumed_at:
            return (self.consumed_at - self.created_at).total_seconds()
        return None
