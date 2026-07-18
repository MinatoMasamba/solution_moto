import logging
from django.utils import timezone
from django.db.models import Sum, Count
from apps.users.models import User, MotardProfile
from apps.rides.models import Ride
from apps.fleet.models import Agreement
from service.service_rides.logic import RideDispatchService

logger = logging.getLogger(__name__)

class MobileMotardService:
    """
    Service layer providing logic specifically aggregated for the Motard mobile app,
    minimizing mobile network request count.
    """

    @classmethod
    def get_motard_home_state(cls, user):
        """
        Aggregates profile, subscription status, active agreement details, 
        and today's statistics (rides, earnings) in a single fast call.
        """
        if user.role != User.Role.MOTARD:
            return {"status": "error", "message": "User is not a motard"}

        profile = getattr(user, "motard_profile", None)
        sub_status = profile.subscription_status if profile else "expired"
        sub_expires_at = profile.subscription_expires_at if profile else None
        is_available = profile.is_available if profile else False
        rating = float(profile.rating_average) if profile else 0.0

        # Fetch active Agreement if any (Pillars 2 or 3)
        agreement = Agreement.objects.filter(motard=user, is_active=True).first()
        agreement_data = None
        if agreement:
            agreement_data = {
                "type": agreement.agreement_type,
                "frequency": agreement.frequency,
                "periodic_amount": float(agreement.periodic_amount),
                "target_total_amount": float(agreement.target_total_amount) if agreement.target_total_amount else None,
                "amount_already_paid": float(agreement.amount_already_paid),
            }

        # Calculate statistics for today (rides completed and earnings)
        today = timezone.now().date()
        completed_rides_today = Ride.objects.filter(
            motard=user,
            status=Ride.Status.COMPLETED,
            completed_at__date=today
        )
        
        rides_count = completed_rides_today.count()
        earnings_today = completed_rides_today.aggregate(total=Sum("agreed_price"))["total"] or 0

        return {
            "profile": {
                "name": user.get_full_name(),
                "phone": user.phone_number,
                "rating": rating,
                "is_available": is_available,
            },
            "subscription": {
                "status": sub_status,
                "expires_at": sub_expires_at.isoformat() if sub_expires_at else None,
                "is_eligible_for_requests": RideDispatchService.is_motard_eligible_for_requests(user),
            },
            "agreement": agreement_data,
            "statistics": {
                "completed_rides_today": rides_count,
                "earnings_today_fc": float(earnings_today),
            }
        }

    @staticmethod
    def toggle_availability(user, is_available):
        """
        Atomically toggles a motard's availability.
        """
        profile = getattr(user, "motard_profile", None)
        if not profile:
            return {"status": "error", "message": "Motard profile not found"}

        profile.is_available = is_available
        profile.save(update_fields=["is_available"])
        logger.info(f"Motard {user.phone_number} availability set to {is_available}")
        return {
            "status": "success",
            "is_available": is_available
        }

    @staticmethod
    def get_available_requests_feed(user):
        """
        Fetch available ride requests.
        Strict Rule: Only active subscription motards can query requested rides.
        """
        # 1. Enforce business rule
        if not RideDispatchService.is_motard_eligible_for_requests(user):
            return {
                "is_eligible": False,
                "message": "Abonnement inactif. Seuls les abonnés actifs reçoivent des demandes.",
                "rides": []
            }

        # 2. Get currently requested rides (active feed)
        requested_rides = Ride.objects.filter(status=Ride.Status.REQUESTED).order_by("-requested_at")
        
        rides_data = []
        for r in requested_rides:
            rides_data.append({
                "ride_id": r.id,
                "pickup_address": r.pickup_address,
                "pickup_lat": float(r.pickup_latitude),
                "pickup_lng": float(r.pickup_longitude),
                "dropoff_address": r.dropoff_address,
                "agreed_price_fc": float(r.agreed_price) if r.agreed_price else 0.0,
                "requested_at": r.requested_at.isoformat()
            })

        return {
            "is_eligible": True,
            "rides": rides_data
        }
