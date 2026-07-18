from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("subscriptions", views.SubscriptionViewSet, basename="subscription")
router.register("payments", views.PaymentViewSet, basename="payment")

app_name = "payments"
urlpatterns = router.urls
