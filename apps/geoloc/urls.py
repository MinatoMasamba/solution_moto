from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("location-pings", views.LocationPingViewSet, basename="location-ping")

app_name = "geoloc"
urlpatterns = router.urls
