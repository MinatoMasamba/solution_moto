# App: Payments

Ce module gère tous les flux financiers du système Go-Mboka.

## Responsabilités
- Gestion des abonnements motards (`Subscription`).
- Traçabilité de tous les paiements via le modèle `Payment`.
- Intégration des modes de paiement : Airtel Money, M-Pesa, Orange Money et Espèces.
- Lien entre les paiements et leurs finalités (Abonnement, Course, ou Reversement de flotte).

## Modèles Principaux
- `Subscription` : Suivi des périodes d'abonnement.
- `Payment` : Registre universel des transactions financières.
