from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("rides", views.RideViewSet, basename="ride")
router.register("ride-ratings", views.RideRatingViewSet, basename="ride-rating")

app_name = "rides"
urlpatterns = router.urls
