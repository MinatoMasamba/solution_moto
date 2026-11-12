"""Passe en 'expired' les abonnements motards dont la date d'expiration est dépassée.

À exécuter périodiquement (cron PythonAnywhere : toutes les heures), ex. :
    python manage.py expire_subscriptions

Utile aussi sans cron : RideDispatchService.revérifie à la volée à chaque
consultation/acceptation de course (expiration "lazy")."""

from django.core.management.base import BaseCommand

from apps.users.services import expire_outdated_subscriptions


class Command(BaseCommand):
    help = "Expire les abonnements motards arrivés à échéance."

    def handle(self, *args, **options):
        count = expire_outdated_subscriptions()
        self.stdout.write(self.style.SUCCESS(f"{count} abonnement(s) expiré(s)."))
