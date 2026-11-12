from decimal import Decimal, InvalidOperation

from django.db.models import Sum
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User

from . import services
from .models import Payment, PaymentMethod, Provider, Subscription, WalletTransaction
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

    @action(detail=False, methods=["get"])
    def price(self, request):
        """Montant mensuel de l'abonnement (piloté par settings/env)."""
        from django.conf import settings
        return Response({"amount": settings.SUBSCRIPTION_MONTHLY_AMOUNT})

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Paiement Mobile Money d'un abonnement motard.

        Initie la charge via le provider (simulateur en dev, agrégateur en prod).
        En succès immédiat, l'abonnement est activé automatiquement ; en attente,
        il le sera à la réception du webhook /api/v1/payments/webhook/."""
        from django.conf import settings
        from apps.users.services import notify
        from . import providers
        from apps.users.models import MotardProfile

        subscription = self.get_object()
        if subscription.motard != request.user:
            return Response({"detail": "Cet abonnement n'est pas le vôtre."}, status=403)
        if subscription.status == Subscription.Status.ACTIVE:
            return Response({"detail": "Cet abonnement est déjà actif."}, status=400)

        provider_name = request.data.get("provider", "")
        mobile_providers = {k: v for k, v in Provider.choices if k != Provider.CASH}
        if provider_name not in mobile_providers:
            provider_name = Provider.MPESA
        phone_number = (request.data.get("phone_number") or "").strip()
        if not phone_number:
            default_method = request.user.payment_methods.filter(kind=PaymentMethod.Kind.MOBILE_MONEY).first()
            phone_number = default_method.phone_number if default_method else request.user.phone_number

        payment = Payment.objects.create(
            user=request.user,
            subscription=subscription,
            purpose=Payment.Purpose.SUBSCRIPTION,
            provider=provider_name,
            amount=subscription.amount,
            status=Payment.Status.PENDING,
        )

        gateway = providers.get_provider()
        try:
            result = gateway.initiate_charge(
                amount=subscription.amount,
                phone_number=phone_number,
                provider=provider_name,
                reference=f"pay-{payment.pk}",
                description=f"Abonnement GO-MBOKA #{subscription.pk}",
            )
        except providers.PaymentProviderError as exc:
            services.mark_payment_failed(payment)
            return Response({"detail": f"Initiation du paiement impossible : {exc}"}, status=502)

        payment.provider_transaction_id = result.get("provider_reference", "") or payment.provider_transaction_id
        if result.get("status") == "success":
            payment = services.mark_payment_success(payment, payment.provider_transaction_id)
            subscription.refresh_from_db()
            profile = getattr(request.user, "motard_profile", None)
            if profile and profile.subscription_status == MotardProfile.SubscriptionStatus.ACTIVE:
                notify(request.user, kind="subscription", title="Abonnement activé",
                       body="Votre abonnement est actif. Vous pouvez accepter des courses.", ride=None)
        payment.save(update_fields=["provider_transaction_id"])
        return Response({
            "payment": PaymentSerializer(payment).data,
            "subscription": SubscriptionSerializer(subscription).data,
            "status": payment.status,
        })


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
        """Recharge (top-up) via Mobile Money.

        La transaction naît en 'pending' et la charge est initiée via le provider
        (simulateur en dev, agrégateur réel en prod). Si le provider renvoie
        'success' tout de suite (mode simulation auto), la transaction est
        confirmée dans la foulée ; sinon le client doit rafraîchir son solde
        jusqu'à confirmation du callback (webhook ou polling)."""
        from . import providers

        try:
            amount = Decimal(str(request.data.get("amount", "0")).replace(" ", ""))
        except (InvalidOperation, TypeError):
            return Response({"detail": "Montant invalide."}, status=400)
        if amount <= 0:
            return Response({"detail": "Le montant doit être positif."}, status=400)

        provider_name = request.data.get("provider", "")
        if provider_name not in dict(WalletTransaction._meta.get_field("provider").choices):
            provider_name = ""
        phone_number = (request.data.get("phone_number") or "").strip()

        txn = WalletTransaction.objects.create(
            user=request.user,
            kind=WalletTransaction.Kind.TOPUP,
            amount=amount,
            status=WalletTransaction.Status.PENDING,
            label="Recharge Mobile Money",
            provider=provider_name,
        )

        gateway = providers.get_provider()
        try:
            result = gateway.initiate_charge(
                amount=amount,
                phone_number=phone_number,
                provider=provider_name,
                reference=str(txn.pk),
                description=f"Recharge wallet GO-MBOKA #{txn.pk}",
            )
        except providers.PaymentProviderError as exc:
            services.mark_wallet_transaction_failed(txn)
            return Response({"detail": f"Initiation du paiement impossible : {exc}"}, status=502)

        txn = services.apply_wallet_gateway_result(txn, result)
        return Response({
            "transaction": WalletTransactionSerializer(txn).data,
            "balance": self._balance(request.user),
        }, status=201)


class PaymentWebhookView(APIView):
    """Callback de l'agrégateur Mobile Money.

    Authentification : header X-Webhook-Token (ou ?token=) égal à
    settings.PAYMENTS_WEBHOOK_TOKEN. Payload minimal attendu :
        {"reference": "<id WalletTransaction>", "status": "success" | "failed",
         "provider_transaction_id": "..."}
    Le provider branché (providers.get_provider()) traduit les champs bruts."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.conf import settings
        from . import providers

        token = request.headers.get("X-Webhook-Token") or request.query_params.get("token", "")
        if not token or token != getattr(settings, "PAYMENTS_WEBHOOK_TOKEN", ""):
            return Response({"detail": "Token webhook invalide."}, status=403)

        try:
            result = providers.get_provider().handle_webhook(request.data)
        except providers.PaymentProviderError as exc:
            return Response({"detail": str(exc)}, status=400)

        reference = request.data.get("reference", "")
        target_kind = request.data.get("kind", "")

        if target_kind == "payment":
            target = Payment.objects.filter(pk=reference).first()
            if target is None:
                return Response({"detail": "Paiement introuvable."}, status=404)
            if result["status"] == "success":
                services.mark_payment_success(target, result["provider_reference"])
            elif result["status"] == "failed":
                services.mark_payment_failed(target)
            return Response({"reference": reference, "kind": "payment", "status": target.status})

        # Défaut : transaction portefeuille (recharge).
        txn = WalletTransaction.objects.filter(pk=reference).first()
        if txn is None:
            return Response({"detail": "Transaction introuvable."}, status=404)

        if result["status"] == "success":
            services.confirm_wallet_transaction(txn, provider_reference=result["provider_reference"])
        elif result["status"] == "failed":
            services.mark_wallet_transaction_failed(txn)
        return Response({"reference": txn.pk, "kind": "wallet", "status": txn.status})
