from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.users.models import User
from service.service_rides.logic import RideDispatchService
from .models import Ride

# Statuts pour lesquels une course est considérée « en cours » (non terminée).
ACTIVE_RIDE_STATUSES = (Ride.Status.REQUESTED, Ride.Status.ACCEPTED, Ride.Status.ONGOING)


def create_ride_request(
    client,
    *,
    pickup_address,
    dropoff_address,
    pickup_latitude=0,
    pickup_longitude=0,
    dropoff_latitude=0,
    dropoff_longitude=0,
    agreed_price=None,
) -> Ride:
    """Crée une demande de course pour un client.

    Règles métier :
    - seul un utilisateur au rôle CLIENT (ou le staff, pour les tests) peut demander une course ;
    - un client ne peut avoir qu'une seule course active à la fois
      (REQUESTED / ACCEPTED / ONGOING) ;
    - la course naît au statut REQUESTED et devient alors visible pour les
      motards abonnés actifs (cf. RideViewSet.get_queryset / RideDispatchService).
    """
    if client.role != User.Role.CLIENT and not client.is_staff:
        raise ValidationError("Seuls les clients peuvent demander une course.")

    if Ride.objects.filter(client=client, status__in=ACTIVE_RIDE_STATUSES).exists():
        raise ValidationError(
            "Vous avez déjà une course en cours ou en attente. Terminez-la ou annulez-la avant d'en demander une autre."
        )

    return Ride.objects.create(
        client=client,
        status=Ride.Status.REQUESTED,
        pickup_address=pickup_address,
        pickup_latitude=pickup_latitude,
        pickup_longitude=pickup_longitude,
        dropoff_address=dropoff_address,
        dropoff_latitude=dropoff_latitude,
        dropoff_longitude=dropoff_longitude,
        agreed_price=agreed_price,
    )


def eligible_motards_count() -> int:
    """Nombre de motards actuellement éligibles à recevoir une demande (dispo + abonnés actifs)."""
    return RideDispatchService.filter_eligible_motards_for_dispatch(User.objects.all()).count()


def accept_ride(ride: Ride, motard) -> Ride:
    if ride.status != Ride.Status.REQUESTED:
        raise ValidationError("Cette course n'est plus disponible.")
        
    # Enforce active subscription requirement
    RideDispatchService.validate_motard_for_ride_acceptance(motard)
    
    ride.motard = motard
    ride.status = Ride.Status.ACCEPTED
    ride.accepted_at = timezone.now()
    ride.save(update_fields=["motard", "status", "accepted_at"])
    return ride


def start_ride(ride: Ride) -> Ride:
    if ride.status != Ride.Status.ACCEPTED:
        raise ValidationError("La course doit être acceptée avant de démarrer.")
    ride.status = Ride.Status.ONGOING
    ride.started_at = timezone.now()
    ride.save(update_fields=["status", "started_at"])
    return ride


def complete_ride(ride: Ride, agreed_price=None) -> Ride:
    if ride.status != Ride.Status.ONGOING:
        raise ValidationError("La course doit être en cours pour être terminée.")
    ride.status = Ride.Status.COMPLETED
    ride.completed_at = timezone.now()
    if agreed_price is not None:
        ride.agreed_price = agreed_price
    ride.save(update_fields=["status", "completed_at", "agreed_price"])
    return ride


def cancel_ride(ride: Ride) -> Ride:
    if ride.status in (Ride.Status.COMPLETED, Ride.Status.CANCELLED):
        raise ValidationError("Cette course ne peut plus être annulée.")
    ride.status = Ride.Status.CANCELLED
    ride.cancelled_at = timezone.now()
    ride.save(update_fields=["status", "cancelled_at"])
    return ride
