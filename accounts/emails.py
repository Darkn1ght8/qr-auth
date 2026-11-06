"""Password e-mails: one-time reset link and "your password was changed" notice."""
import logging

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode

from core.i18n import t
from core.netutils import absolute_public_url

logger = logging.getLogger("qrauth")


def email_enabled() -> bool:
    return bool(getattr(settings, "EMAIL_ENABLED", False))


def reset_link(request, user) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return absolute_public_url(request, reverse("accounts:password_reset_confirm", args=[uid, token]))


def _send(subject: str, text: str, html: str, to: str) -> bool:
    if not email_enabled() or not to:
        return False
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to])
    message.attach_alternative(html, "text/html")
    try:
        return message.send() == 1
    except Exception:  # a mail outage must never break the page
        logger.exception("password e-mail to user failed")
        return False


def _html(title: str, paragraphs: list[str], button: tuple[str, str] | None = None) -> str:
    body = "".join(f'<p style="margin:0 0 16px;color:#C7CFDF">{escape(p)}</p>' for p in paragraphs)
    if button:
        label, url = button
        body += (f'<p style="margin:24px 0"><a href="{escape(url)}" style="display:inline-block;padding:14px 24px;'
                 f'border-radius:999px;background:#00E5FF;color:#021014;font-weight:700;text-decoration:none">{escape(label)}</a></p>'
                 f'<p style="margin:0;color:#8C96AB;font-size:13px;word-break:break-all">{escape(url)}</p>')
    return (f'<div style="background:#07090F;padding:32px;font-family:Arial,sans-serif">'
            f'<div style="max-width:520px;margin:0 auto;background:#0E121C;border:1px solid #1F2635;border-radius:16px;padding:32px">'
            f'<p style="margin:0 0 8px;color:#00E5FF;font-size:12px;letter-spacing:.16em">QR·AUTH</p>'
            f'<h1 style="margin:0 0 20px;color:#E9EEF8;font-size:22px">{escape(title)}</h1>{body}</div></div>')


def send_reset_email(request, user) -> bool:
    url = reset_link(request, user)
    minutes = settings.PASSWORD_RESET_TIMEOUT // 60
    title = t("Сброс пароля")
    lines = [
        t("Здравствуйте, {name}!", name=user.get_short_name() or user.username),
        t("Кто-то (возможно, вы) запросил сброс пароля для аккаунта {username}.", username=user.username),
        t("Ссылка одноразовая и действует {minutes} минут.", minutes=minutes),
        t("Если вы не запрашивали сброс, просто проигнорируйте это письмо — пароль не изменится."),
    ]
    text = "\n\n".join([lines[0], lines[1], url, lines[2], lines[3]])
    return _send(f"QR·AUTH — {title}", text, _html(title, lines, (t("Задать новый пароль"), url)), user.email)


def send_password_changed_notice(request, user) -> bool:
    title = t("Пароль изменён")
    lines = [
        t("Здравствуйте, {name}!", name=user.get_short_name() or user.username),
        t("Пароль аккаунта {username} только что был изменён.", username=user.username),
        t("Если это были не вы, сразу сбросьте пароль и завершите чужие сессии в личном кабинете."),
    ]
    return _send(f"QR·AUTH — {title}", "\n\n".join(lines), _html(title, lines), user.email)
