from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("motorcycles", views.MotorcycleViewSet, basename="motorcycle")
router.register("fleet-remittances", views.FleetRemittanceViewSet, basename="fleet-remittance")
router.register("motard-trials", views.MotardTrialViewSet, basename="motard-trial")
router.register("trial-daily-logs", views.TrialDailyLogViewSet, basename="trial-daily-log")
router.register("agreements", views.AgreementViewSet, basename="agreement")

app_name = "fleet"
urlpatterns = router.urls
