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
        Business Rules:
        - Only motards with an ACTIVE subscription can receive or accept ride requests;
        - leur dossier d'application doit être VALIDÉ (approved) par la Direction.
        La connexion reste autorisée pour compléter son profil et payer l'abonnement.
        """
        if not motard or motard.role != User.Role.MOTARD:
            return False

        # Expiration "lazy" : un abonnement actif dont la date est passée est
        # basculé en 'expired' ici même, même si le cron (management command
        # expire_subscriptions) n'a pas encore tourné.
        from apps.users.services import expire_outdated_subscriptions
        expire_outdated_subscriptions()

        # Re-fetch explicite : la relation inverse motard_profile peut être
        # mise en cache par Django avec un statut périmé (ex. profil créé dans
        # la même requête) alors que la DB vient d'être mise à jour.
        profile = MotardProfile.objects.filter(user=motard).first()
        if not profile:
            return False

        if profile.subscription_status != MotardProfile.SubscriptionStatus.ACTIVE:
            return False
        return profile.application_status == MotardProfile.ApplicationStatus.APPROVED

    @classmethod
    def validate_motard_for_ride_acceptance(cls, motard):
        """
        Enforce eligibility at transaction level. Throws ValidationError if not allowed.
        """
        if not cls.is_motard_eligible_for_requests(motard):
            from apps.users.models import MotardProfile as _MotardProfile

            profile = _MotardProfile.objects.filter(user=motard).first()
            if profile is None:
                raise ValidationError(
                    "Accès refusé : votre dossier motard doit d'abord être validé par la Direction."
                )
            if profile.application_status != MotardProfile.ApplicationStatus.APPROVED:
                raise ValidationError(
                    "Accès refusé : votre dossier d'inscription doit être validé par la Direction avant de pouvoir accepter des courses."
                )
            raise ValidationError(
                "Accès refusé : seuls les motards ayant un abonnement actif peuvent accepter des demandes de parcours."
            )

    @classmethod
    def filter_eligible_motards_for_dispatch(cls, queryset):
        """
        Filters a queryset of users to return only those eligible to receive ride requests.
        """
        from apps.users.services import expire_outdated_subscriptions
        expire_outdated_subscriptions()

        return queryset.filter(
            role=User.Role.MOTARD,
            motard_profile__subscription_status=MotardProfile.SubscriptionStatus.ACTIVE,
            motard_profile__application_status=MotardProfile.ApplicationStatus.APPROVED,
            motard_profile__is_available=True
        )
