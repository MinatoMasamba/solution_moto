from django.core.exceptions import ValidationError
from django.utils import timezone

from service.service_rides.logic import RideDispatchService
from .models import Ride


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
