import logging
from django.core.exceptions import ValidationError
from apps.users.models import User, MotardProfile

logger = logging.getLogger(__name__)

class RideDispatchService:
    """
    Core business logic for ride matchmaking, dispatching and eligibility.
    """

    @staticmethod
    def is_motard_eligible_for_requests(motard):
        """
        Business Rule: Only motards with an ACTIVE subscription can receive or accept ride requests.
        """
        if not motard or motard.role != User.Role.MOTARD:
            return False
        
        # Check if they have a motard profile and if the subscription status is 'active'
        profile = getattr(motard, "motard_profile", None)
        if not profile:
            return False
            
        return profile.subscription_status == MotardProfile.SubscriptionStatus.ACTIVE

    @classmethod
    def validate_motard_for_ride_acceptance(cls, motard):
        """
        Enforce eligibility at transaction level. Throws ValidationError if not allowed.
        """
        if not cls.is_motard_eligible_for_requests(motard):
            raise ValidationError(
                "Accès refusé : Seuls les motards ayant un abonnement actif peuvent accepter des demandes de parcours."
            )

    @classmethod
    def filter_eligible_motards_for_dispatch(cls, queryset):
        """
        Filters a queryset of users to return only those eligible to receive ride requests.
        """
        return queryset.filter(
            role=User.Role.MOTARD,
            motard_profile__subscription_status=MotardProfile.SubscriptionStatus.ACTIVE,
            motard_profile__is_available=True
        )
