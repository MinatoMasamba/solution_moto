from django.urls import path

from . import views_web
from .views_web import client_dashboard_view  # Importer la nouvelle vue

app_name = "chauffeur"

urlpatterns = [
    path("client/dashboard/", client_dashboard_view, name="client_dashboard"), # Ajout
    path("connexion/", views_web.ChauffeurLoginView.as_view(), name="chauffeur_login"),
    path("inscription/", views_web.ChauffeurRegistrationView.as_view(), name="chauffeur_registration"),
    path("app/", views_web.ChauffeurAppView.as_view(), name="chauffeur_app"),
    path(
        "mot-de-passe/demande/",
        views_web.chauffeur_password_reset_request,
        name="chauffeur_password_reset_request",
    ),
    path(
        "mot-de-passe/confirmation/",
        views_web.chauffeur_password_reset_confirm,
        name="chauffeur_password_reset_confirm",
    ),
]
