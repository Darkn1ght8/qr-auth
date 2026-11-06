from django.urls import path

from . import views

app_name = "qrauth"

urlpatterns = [
    path("login/", views.qr_login, name="login"),
    path("qr/api/new/", views.api_new, name="api_new"),
    path("qr/api/status/<uuid:sid>/", views.api_status, name="api_status"),
    path("qr/api/exchange/", views.api_exchange, name="api_exchange"),
    path("qr/scanner/", views.scanner, name="scanner"),
    path("qr/scan/", views.scan_redirect, name="scan_root"),
    path("qr/scan/<str:token>/<str:signature>/", views.scan, name="scan"),
    path("qr/decide/", views.decide, name="decide"),
]
