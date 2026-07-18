from django.utils import timezone

from .models import MotardProfile, User


def mark_user_verified(user: User) -> User:
    user.is_verified = True
    user.save(update_fields=["is_verified"])
    return user


def activate_motard_subscription(profile: MotardProfile, expires_at) -> MotardProfile:
    profile.subscription_status = MotardProfile.SubscriptionStatus.ACTIVE
    profile.subscription_expires_at = expires_at
    profile.save(update_fields=["subscription_status", "subscription_expires_at"])
    return profile


def expire_outdated_subscriptions() -> int:
    now = timezone.now()
    return MotardProfile.objects.filter(
        subscription_status=MotardProfile.SubscriptionStatus.ACTIVE,
        subscription_expires_at__lt=now,
    ).update(subscription_status=MotardProfile.SubscriptionStatus.EXPIRED)
