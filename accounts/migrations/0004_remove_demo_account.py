"""Remove the old demo account and the fake audit history that `seed_demo` used to create.

The seed ran on every start, so a deleted demo user and the cleared journal entries
(fake 192.168.1.x addresses) kept coming back. That command no longer exists.
"""
from django.conf import settings
from django.db import migrations

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@example.kz"


def remove_demo(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    LoginAudit = apps.get_model("accounts", "LoginAudit")

    # Seeded entries were marked {"seed": true} and used this user agent.
    LoginAudit.objects.filter(user_agent="Mozilla/5.0 (seed)").delete()
    demo = User.objects.filter(username=DEMO_USERNAME, email=DEMO_EMAIL)
    LoginAudit.objects.filter(user__in=demo).delete()
    demo.delete()  # its tracked sessions are removed by CASCADE


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_i18n_and_password_events"),
    ]

    operations = [
        migrations.RunPython(remove_demo, migrations.RunPython.noop),
    ]
