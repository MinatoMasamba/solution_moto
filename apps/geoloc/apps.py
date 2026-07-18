from django.apps import AppConfig


class GeolocConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.geoloc"
    label = "geoloc"
    verbose_name = "Géolocalisation"
