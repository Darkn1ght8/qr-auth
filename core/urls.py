from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("overview/", views.overview, name="overview"),
    path("how-it-works/", views.how, name="how"),
    path("demo/", views.demo, name="demo"),
    path("testing/", views.testing, name="testing"),
    path("security/", views.security, name="security"),
    path("healthz/", views.healthz, name="healthz"),
]
