from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User

from . import services
from .models import Payment, PaymentMethod, Subscription, WalletTransaction
from .serializers import (
    PaymentMethodSerializer,
    PaymentSerializer,
    SubscriptionSerializer,
    WalletTransactionSerializer,
)


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


class WalletView(APIView):
    """Portefeuille plateforme du client : solde + historique + recharge."""

    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def _balance(user):
        return WalletTransaction.objects.filter(
            user=user, status=WalletTransaction.Status.SUCCESS
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    def get(self, request):
        txns = WalletTransaction.objects.filter(user=request.user)[:50]
        return Response({
            "balance": self._balance(request.user),
            "transactions": WalletTransactionSerializer(txns, many=True).data,
        })

    def post(self, request):
        """Recharge (top-up) via Mobile Money. Crée une transaction de crédit.
        NB : l'intégration réelle de l'opérateur reste à brancher — la transaction
        est créée en 'success' pour refléter le solde ; passez-la en 'pending' quand
        un vrai flux de confirmation Mobile Money sera connecté."""
        try:
            amount = Decimal(str(request.data.get("amount", "0")).replace(" ", ""))
        except (InvalidOperation, TypeError):
            return Response({"detail": "Montant invalide."}, status=400)
        if amount <= 0:
            return Response({"detail": "Le montant doit être positif."}, status=400)

        provider = request.data.get("provider", "")
        txn = WalletTransaction.objects.create(
            user=request.user,
            kind=WalletTransaction.Kind.TOPUP,
            amount=amount,
            status=WalletTransaction.Status.SUCCESS,
            label="Recharge Mobile Money",
            provider=provider if provider in dict(WalletTransaction._meta.get_field("provider").choices) else "",
        )
        return Response({
            "transaction": WalletTransactionSerializer(txn).data,
            "balance": self._balance(request.user),
        }, status=201)
