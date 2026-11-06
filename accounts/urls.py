from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/password/", views.password_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("cabinet/", views.cabinet, name="cabinet"),
    path("cabinet/sessions/<int:pk>/end/", views.revoke_session, name="revoke"),
    path("cabinet/sessions/end-others/", views.revoke_others, name="revoke_others"),
    path("api/session/", views.session_status, name="session_status"),
    path("cabinet/password/", views.password_change, name="password_change"),
    path("password/reset/", views.password_reset_request, name="password_reset"),
    path("password/reset/sent/", views.password_reset_sent, name="password_reset_sent"),
    path("password/reset/<str:uidb64>/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
]
