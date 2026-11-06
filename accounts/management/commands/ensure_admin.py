"""Create or update the site administrator from environment variables.

    ADMIN_USERNAME  (default "admin")
    ADMIN_PASSWORD  (required in production; on Render it is generated and shown
                     only to you in the service's Environment tab)
    ADMIN_EMAIL     (optional)

Usage: python manage.py ensure_admin
Locally (DEBUG) without ADMIN_PASSWORD, a random password is generated and printed once;
in production the command never generates or prints a password.
"""
import os
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/update the administrator account from ADMIN_* environment variables."

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
        password = os.environ.get("ADMIN_PASSWORD", "")
        email = os.environ.get("ADMIN_EMAIL", "").strip()
        if not password and not settings.DEBUG:
            # Production: never invent or print a password into the server logs.
            self.stdout.write(self.style.WARNING("ADMIN_PASSWORD is not set: admin account left unchanged."))
            return
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if email:
            user.email = email
        generated = False
        if password:
            user.set_password(password)  # env value is the source of truth on every start
        elif created or not user.has_usable_password():
            password = secrets.token_urlsafe(12)
            user.set_password(password)
            generated = True
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Admin '{username}' {'created' if created else 'updated'}."))
        if generated:
            # Only happens locally (no ADMIN_PASSWORD set): show it once so you can sign in.
            self.stdout.write(f"Generated password for '{username}': {password}")
