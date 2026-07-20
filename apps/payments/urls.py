from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("subscriptions", views.SubscriptionViewSet, basename="subscription")
router.register("payments", views.PaymentViewSet, basename="payment")
router.register("payment-methods", views.PaymentMethodViewSet, basename="payment-method")

app_name = "payments"
urlpatterns = [
    path("wallet/", views.WalletView.as_view(), name="wallet"),
    *router.urls,
]
