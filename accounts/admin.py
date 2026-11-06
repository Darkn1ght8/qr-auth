from django.contrib import admin

from .models import LoginAudit, UserSession


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    list_display = ("created_at", "event", "user", "method", "success", "ip_address")
    list_filter = ("event", "method", "success")
    search_fields = ("user__username", "ip_address")
    readonly_fields = [f.name for f in LoginAudit._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "method", "browser", "os", "ip_address", "created_at", "last_seen", "ended_at")
    list_filter = ("method",)
