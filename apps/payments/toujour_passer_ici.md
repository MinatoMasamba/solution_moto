# Guide de Contexte d'Application (AI Map) : Payments

Ce fichier est le point d'entrée pour toute IA ou agent travaillant sur l'application `payments`.

---

## 1. Architecture Front-end

Cette application contribue à l'écosystème front-end dynamique. Les données financières fournies par ses services sont consommées en temps réel par les tableaux de bord pour garantir une interface réactive et sans données statiques.

## 2. Modèles (`models.py`)
- **`Provider`** : `airtel_money`, `mpesa`, `orange_money`, `cash`.
- **`Subscription`** : abonnement mensuel motard (Pilier 1) — conditionne l'accès aux courses (cf. guide `apps/users`).
- **`Payment`** : paiement entrant (`purpose` abonnement/course/reversement, `provider`, `status`).
- **`PaymentMethod`** : moyen de paiement **lié** au compte (Mobile Money `provider`+`phone_number`, ou banque). `is_default`. API `/api/v1/payment-methods/` (+ action `set_default`). Sert aux reversements (propriétaire) et retraits (motard).
- **`WalletTransaction`** : solde plateforme d'un **client**. `amount` **signé** (positif = crédit). Solde = somme des `amount` en `success`.

## 3. Endpoints
- ViewSets : `/api/v1/subscriptions/`, `/api/v1/payments/`, `/api/v1/payment-methods/`.
- `/api/v1/wallet/` (`WalletView`) — `GET` solde + transactions ; `POST` recharge. Utilisé par l'app client (`templates/client/`).

## 4. Angles morts connus
- Aucune intégration réelle d'agrégateur Mobile Money : la recharge crée une `WalletTransaction` en `success` sans confirmation opérateur.
- Débit du solde à la fin d'une course : pas encore implémenté (à ajouter dans `apps/rides/services.complete_ride`).
