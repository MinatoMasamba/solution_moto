from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User

from . import services
from .models import Payment, PaymentMethod, Subscription
from .serializers import PaymentMethodSerializer, PaymentSerializer, SubscriptionSerializer


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Subscription.objects.select_related("motard")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(motard=user)

    def perform_create(self, serializer):
        serializer.save(motard=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related("user", "subscription", "ride")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def confirm(self, request, pk=None):
        payment = self.get_object()
        payment = services.mark_payment_success(
            payment, provider_transaction_id=request.data.get("provider_transaction_id", "")
        )
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def fail(self, request, pk=None):
        payment = services.mark_payment_failed(self.get_object())
        return Response(PaymentSerializer(payment).data)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """Moyens de paiement liés au compte de l'utilisateur connecté."""

    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def _save_scoped(self, serializer):
        instance = serializer.save(user=self.request.user)
        # Un seul moyen « par défaut » par utilisateur ; le 1er créé l'est d'office.
        if instance.is_default or self.request.user.payment_methods.count() == 1:
            self.request.user.payment_methods.exclude(pk=instance.pk).update(is_default=False)
            if not instance.is_default:
                instance.is_default = True
                instance.save(update_fields=["is_default"])

    def perform_create(self, serializer):
        self._save_scoped(serializer)

    def perform_update(self, serializer):
        self._save_scoped(serializer)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        method = self.get_object()
        request.user.payment_methods.update(is_default=False)
        method.is_default = True
        method.save(update_fields=["is_default"])
        return Response(PaymentMethodSerializer(method).data)
