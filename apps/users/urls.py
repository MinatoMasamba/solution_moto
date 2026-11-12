from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("motard-profiles", views.MotardProfileViewSet, basename="motard-profile")
router.register("owner-profiles", views.OwnerProfileViewSet, basename="owner-profile")
router.register("support-tickets", views.SupportTicketViewSet, basename="support-ticket")
router.register("saved-places", views.SavedPlaceViewSet, basename="saved-place")

app_name = "users"

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.ThrottledTokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("client/summary/", views.ClientSummaryView.as_view(), name="client_summary"),
    path("notifications/", views.NotificationsView.as_view(), name="notifications"),
    path("", include(router.urls)),
]
