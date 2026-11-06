from django.contrib import admin

from .models import QRSession


@admin.register(QRSession)
class QRSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "scanned_by", "initiator_browser", "initiator_os", "created_at", "consumed_at")
    list_filter = ("status",)
    readonly_fields = [f.name for f in QRSession._meta.fields]
    exclude = ()

    def has_add_permission(self, request):
        return False
