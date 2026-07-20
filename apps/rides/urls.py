from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views, views_web

router = DefaultRouter()
router.register("rides", views.RideViewSet, basename="ride")
router.register("ride-ratings", views.RideRatingViewSet, basename="ride-rating")

app_name = "rides"
urlpatterns = router.urls + [
    path("web/create/", views_web.create_ride_view, name="create_ride_view"),
]
