"""Provider de simulation — environnement sans agrégateur branché.

Deux modes (env GM_PAYMENT_SIMULATION) :
- "auto" (défaut)   : la charge réussit immédiatement, comme un paiement accepté
                      par l'opérateur — le client voit son solde tout de suite ;
- "manual"          : la charge reste "pending" jusqu'à confirmation via le
                      webhook /api/v1/payments/webhook/ — sert à tester le vrai
                      flux de callback de l'agrégateur en local.
"""

import os

from .base import BaseMobileMoneyProvider


class SimulatorProvider(BaseMobileMoneyProvider):
    name = "simulator"

    def initiate_charge(self, *, amount, phone_number, provider="", reference="", description=""):
        auto = os.environ.get("GM_PAYMENT_SIMULATION", "auto").lower() != "manual"
        if auto:
            return self.normalize("success", provider_reference=f"sim-{reference}", raw={"simulated": True})
        return self.normalize("pending", provider_reference=f"sim-{reference}", raw={"simulated": True})

    def check_status(self, reference):
        return self.normalize("pending", provider_reference=f"sim-{reference}")

    def handle_webhook(self, payload):
        status = payload.get("status", "success")
        if status not in ("success", "failed"):
            status = "success"
        return self.normalize(
            status,
            provider_reference=payload.get("provider_transaction_id", ""),
            raw=payload,
        )
