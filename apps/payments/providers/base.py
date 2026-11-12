"""Abstraction du module paiement Mobile Money.

Le reste du système ne connaît que cette interface : changer d'agrégateur
(FlexPay, LootPay, API directe Airtel Money / M-Pesa / Orange Money) revient à
écrire un nouveau provider dans ce dossier sans toucher aux vues ni aux services.

Contrat d'un provider :
- initiate_charge()  : initie une demande de paiement chez l'opérateur ;
- check_status()     : vérifie l'état d'une transaction initiée (polling) ;
- handle_webhook()   : interprète la notification callback envoyée par l'agrégateur.

Chaque méthode renvoie un dict normalisé :
    {"status": "pending" | "success" | "failed",
     "provider_reference": "<id opérateur>", "raw": <données brutes>}
"""

import abc


class PaymentProviderError(Exception):
    """Erreur d'appel au provider (réseau, payload invalide, opérateur absent…)."""


class BaseMobileMoneyProvider(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def initiate_charge(self, *, amount, phone_number, provider="", reference="", description=""):
        """Initie une demande de paiement. `reference` = notre id de transaction."""

    @abc.abstractmethod
    def check_status(self, reference):
        """Statut courant d'une transaction initiée via `initiate_charge`."""

    @abc.abstractmethod
    def handle_webhook(self, payload):
        """Traduit un callback de l'agrégateur en réponse normalisée."""

    @staticmethod
    def normalize(status, provider_reference="", raw=None):
        return {
            "status": status,
            "provider_reference": provider_reference or "",
            "raw": raw or {},
        }
