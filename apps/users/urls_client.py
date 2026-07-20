from django.urls import path
from . import views_web

app_name = "client"

urlpatterns = [
    path("dashboard/", views_web.client_dashboard_view, name="client_dashboard"),
    path("login/", views_web.ClientLoginView.as_view(), name="client_login"),
]
