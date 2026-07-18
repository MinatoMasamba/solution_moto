from datetime import timedelta

from django.utils import timezone

from apps.users.services import activate_motard_subscription

from .models import Payment, Subscription


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
