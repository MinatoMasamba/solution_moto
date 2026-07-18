from django.core.exceptions import ValidationError

from .models import FleetRemittance, Motorcycle


def assign_motard(motorcycle: Motorcycle, motard) -> Motorcycle:
    if motorcycle.status != Motorcycle.Status.AVAILABLE:
        raise ValidationError("Cette moto n'est pas disponible pour une affectation.")
    motorcycle.assigned_motard = motard
    motorcycle.status = Motorcycle.Status.ASSIGNED
    motorcycle.save(update_fields=["assigned_motard", "status"])
    return motorcycle


def release_motard(motorcycle: Motorcycle) -> Motorcycle:
    motorcycle.assigned_motard = None
    motorcycle.status = Motorcycle.Status.AVAILABLE
    motorcycle.save(update_fields=["assigned_motard", "status"])
    return motorcycle


def assign_manager(motorcycle: Motorcycle, fleet_manager) -> Motorcycle:
    motorcycle.fleet_manager = fleet_manager
    motorcycle.save(update_fields=["fleet_manager"])
    return motorcycle


def release_manager(motorcycle: Motorcycle) -> Motorcycle:
    motorcycle.fleet_manager = None
    motorcycle.save(update_fields=["fleet_manager"])
    return motorcycle


def record_remittance(motorcycle: Motorcycle, period_start, period_end, gross_revenue) -> FleetRemittance:
    commission_amount = gross_revenue * (motorcycle.commission_rate / 100)
    net_amount = gross_revenue - commission_amount
    return FleetRemittance.objects.create(
        motorcycle=motorcycle,
        period_start=period_start,
        period_end=period_end,
        gross_revenue=gross_revenue,
        commission_amount=commission_amount,
        net_amount=net_amount,
    )
