from apps.users.models import User

from .models import LocationPing


def record_ping(user, latitude, longitude, ride=None) -> LocationPing:
    return LocationPing.objects.create(user=user, latitude=latitude, longitude=longitude, ride=ride)


def latest_position(user):
    return LocationPing.objects.filter(user=user).order_by("-recorded_at").first()


def latest_positions_for(viewer):
    """Dernière position de chaque motard visible par `viewer` (opérateur = tous,
    gérant = sa flotte). Renvoie une liste de dicts prête pour la carte."""
    qs = LocationPing.objects.select_related("user")
    if viewer.role == User.Role.OPERATOR or viewer.is_staff:
        pass
    elif viewer.role == User.Role.FLEET_MANAGER:
        qs = qs.filter(user__assigned_motorcycle__fleet_manager=viewer)
    else:
        qs = qs.filter(user=viewer)

    latest = {}
    for ping in qs.order_by("user_id", "-recorded_at"):
        if ping.user_id not in latest:
            latest[ping.user_id] = ping

    return [
        {
            "user_id": p.user_id,
            "name": p.user.get_full_name() or p.user.phone_number,
            "latitude": float(p.latitude),
            "longitude": float(p.longitude),
            "recorded_at": p.recorded_at.isoformat(),
            "on_ride": p.ride_id is not None,
        }
        for p in latest.values()
    ]
