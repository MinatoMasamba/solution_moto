from datetime import timedelta

from django.db import transaction as db_transaction
from django.utils import timezone

from apps.users.services import activate_motard_subscription

from .models import Payment, Subscription, WalletTransaction


def mark_payment_success(payment: Payment, provider_transaction_id: str = "") -> Payment:
    payment.status = Payment.Status.SUCCESS
    payment.confirmed_at = timezone.now()
    if provider_transaction_id:
        payment.provider_transaction_id = provider_transaction_id
    payment.save(update_fields=["status", "confirmed_at", "provider_transaction_id"])

    if payment.purpose == Payment.Purpose.SUBSCRIPTION and payment.subscription:
        activate_subscription_from_payment(payment.subscription)
    return payment


def mark_payment_failed(payment: Payment) -> Payment:
    payment.status = Payment.Status.FAILED
    payment.save(update_fields=["status"])
    return payment


def activate_subscription_from_payment(subscription: Subscription, duration_days: int = 30) -> Subscription:
    now = timezone.now()
    period_end = now + timedelta(days=duration_days)
    subscription.status = Subscription.Status.ACTIVE
    subscription.period_start = now.date()
    subscription.period_end = period_end.date()
    subscription.save(update_fields=["status", "period_start", "period_end"])

    motard_profile = getattr(subscription.motard, "motard_profile", None)
    if motard_profile is not None:
        activate_motard_subscription(motard_profile, period_end)
    return subscription


# --- Portefeuille client -----------------------------------------------------


def wallet_balance(user) -> "Decimal":
    from decimal import Decimal

    from django.db.models import Sum

    return (
        WalletTransaction.objects.filter(user=user, status=WalletTransaction.Status.SUCCESS)
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0")
    )


@db_transaction.atomic
def apply_wallet_gateway_result(txn: WalletTransaction, result: dict) -> WalletTransaction:
    """Applique la réponse du provider à une transaction wallet naissante."""
    txn.provider_reference = result.get("provider_reference", "") or txn.provider_reference
    if result.get("status") == "success":
        txn.status = WalletTransaction.Status.SUCCESS
    elif result.get("status") == "failed":
        txn.status = WalletTransaction.Status.FAILED
    txn.save(update_fields=["status", "provider_reference"])
    return txn


def confirm_wallet_transaction(txn: WalletTransaction, provider_reference: str = "") -> WalletTransaction:
    """Confirmation (callback provider / polling) d'une recharge en attente."""
    txn.status = WalletTransaction.Status.SUCCESS
    update_fields = ["status"]
    if provider_reference:
        txn.provider_reference = provider_reference
        update_fields.append("provider_reference")
    txn.save(update_fields=update_fields)
    return txn


def mark_wallet_transaction_failed(txn: WalletTransaction) -> WalletTransaction:
    txn.status = WalletTransaction.Status.FAILED
    txn.save(update_fields=["status"])
    return txn


@db_transaction.atomic
def debit_wallet_for_ride(ride, motard_user=None) -> WalletTransaction:
    """Débite le portefeuille du client à la fin de la course.

    Renvoie la transaction de débit (kind=RIDE, montant négatif) si le solde
    suffit et que le prix est connu. Si le solde est insuffisant (ou prix non
    fixé), renvoie None : le paiement se règle alors en espèces directement au
    motard (le prix reste négocié entre eux, cf. Pilier 1 du blueprint)."""
    amount = ride.agreed_price
    if amount is None or amount <= 0:
        return None
    balance = wallet_balance(ride.client)
    if balance < amount:
        return None
    return WalletTransaction.objects.create(
        user=ride.client,
        kind=WalletTransaction.Kind.RIDE,
        amount=-amount,
        status=WalletTransaction.Status.SUCCESS,
        label=f"Course #{ride.pk} — {ride.dropoff_address}",
    )
