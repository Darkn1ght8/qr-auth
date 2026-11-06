"""E-mail backend for the Brevo HTTP API (https://www.brevo.com, free: 300 e-mails/day).

Render's free plan blocks outgoing SMTP, so mail goes over HTTPS instead.
Settings: BREVO_API_KEY, DEFAULT_FROM_EMAIL (a sender verified in Brevo).
"""
import json
import logging
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger("qrauth")
API_URL = "https://api.brevo.com/v3/smtp/email"


class BrevoEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            name, address = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
            payload = {
                "sender": {"email": address, "name": name or "QR·AUTH"},
                "to": [{"email": parseaddr(to)[1]} for to in message.to],
                "subject": message.subject,
                "textContent": message.body,
            }
            for content, mimetype in getattr(message, "alternatives", []):
                if mimetype == "text/html":
                    payload["htmlContent"] = content
            request = urllib.request.Request(
                API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"api-key": settings.BREVO_API_KEY, "content-type": "application/json", "accept": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    if 200 <= response.status < 300:
                        sent += 1
            except Exception:
                logger.exception("Brevo send failed")
                if not self.fail_silently:
                    raise
        return sent
