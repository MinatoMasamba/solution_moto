"""Fabrique du provider Mobile Money.

Brancher un vrai agrégateur :
1. créer un module dans ce dossier (ex. flexpay.py) avec une classe héritant de
   BaseMobileMoneyProvider (méthodes initiate_charge / check_status / handle_webhook) ;
2. ajouter son nom dans _PROVIDERS ci-dessous ;
3. définir PAYMENT_PROVIDER=<nom> dans .env (+ ses credentials via env).
"""

from .base import BaseMobileMoneyProvider, PaymentProviderError
from .simulator import SimulatorProvider

_PROVIDERS = {
    SimulatorProvider.name: SimulatorProvider,
}


def get_provider() -> BaseMobileMoneyProvider:
    from django.conf import settings

    name = getattr(settings, "PAYMENT_PROVIDER", SimulatorProvider.name)
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise PaymentProviderError(
            f"Provider de paiement inconnu : '{name}'. Providers disponibles : {', '.join(_PROVIDERS)}"
        )
    return cls()
