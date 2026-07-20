from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("motard-profiles", views.MotardProfileViewSet, basename="motard-profile")
router.register("owner-profiles", views.OwnerProfileViewSet, basename="owner-profile")
router.register("support-tickets", views.SupportTicketViewSet, basename="support-ticket")

app_name = "users"

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/me/", views.MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
