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
]
