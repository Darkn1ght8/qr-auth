from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users, name="users"),
    path("users/export.csv", views.users_export, name="users_export"),
    path("users/<int:pk>/", views.user_detail, name="user"),
    path("users/<int:pk>/action/", views.user_action, name="user_action"),
    path("users/<int:pk>/sessions/clear/", views.user_sessions_clear, name="user_sessions_clear"),
    path("sessions/", views.sessions, name="sessions"),
    path("sessions/<int:pk>/end/", views.session_end, name="session_end"),
    path("audit/", views.audit_log, name="audit"),
    path("audit/clear/", views.audit_clear, name="audit_clear"),
    path("qr/", views.qr_sessions, name="qr"),
    path("qr/clear/", views.qr_clear, name="qr_clear"),
]
