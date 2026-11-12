from django.utils import timezone

from .models import MotardProfile, Notification, User


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


def notify(user, *, kind, title, body="", ride=None) -> "Notification | None":
    """Crée une notification in-app pour un utilisateur (silencieuse si None)."""
    if user is None:
        return None
    return Notification.objects.create(user=user, kind=kind, title=title, body=body, ride=ride)


def notify_many(users, *, kind, title, body="", ride=None) -> int:
    """Crée la même notification pour plusieurs utilisateurs. Renvoie le nb créé."""
    rows = [
        Notification(user=u, kind=kind, title=title, body=body, ride=ride)
        for u in users
    ]
    Notification.objects.bulk_create(rows)
    return len(rows)


def mark_notifications_read(user, ids=None) -> int:
    """Marque les notifications de l'utilisateur comme lues (toutes si ids=None)."""
    qs = user.notifications.filter(read_at__isnull=True)
    if ids is not None:
        qs = qs.filter(id__in=ids)
    return qs.update(read_at=timezone.now())
