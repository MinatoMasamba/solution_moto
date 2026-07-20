# Guide de Contexte (AI Map) : App Client (`templates/client/`)

Point d'entrée pour toute IA/agent travaillant sur l'interface **client** (commande de courses).

## 1. Rôle du dossier
- `app.html` — application mobile du client (une seule page à panneaux), servie sur **`/client/app/`** (vue `portal.views.ClientAppView`, réservée au rôle `CLIENT`). Étend `gm/base.html`, cadre téléphone responsive (media query ≤560px → plein écran).

## 2. Panneaux (`data-panel`) et navigation
Navigation gérée par **`static/js/gm-client.js`** (`go(view)`), via la tab-bar (`.gm-navi[data-view]`) et les boutons `[data-goto]`.
- `home` (solde, courses offertes, lieux rapides, parrainage) · `create` (départ/destination → demander) · `searching` (attente d'un motard) · `ontrip` (motard assigné + position) · `rate` (notation) · `places` (lieux enregistrés) · `wallet` (solde + transactions) · `topup` (recharge Mobile Money) · `referral` (code parrainage) · `notifs` · `profil` · `compte` · `motdepasse`.

## 3. Endpoints consommés (tous réels)
- `GET /api/v1/client/summary/` → identité, note, nb courses, code parrainage, solde, courses offertes.
- `GET/POST/DELETE /api/v1/saved-places/` → lieux enregistrés (scopé à l'utilisateur).
- `POST /api/v1/rides/` → créer la demande (logique : `apps/rides/services.create_ride_request`).
- `GET /api/v1/rides/current/` → course active + motard + dernière position GPS (polling 5 s).
- `POST /api/v1/ride-ratings/` → noter la course terminée.
- `GET/POST /api/v1/wallet/` → solde + historique + recharge (modèle `payments.WalletTransaction`).
- `GET /api/v1/auth/me/` (+ `PATCH`) · `POST /api/account/password/`.

## 4. Règles / limites connues
- **Coordonnées** : le client saisit une adresse texte ; les lat/lng sont optionnelles (défaut 0). Le **départ** peut venir du GPS navigateur (`navigator.geolocation`). Pas de géocodage de la destination → `motard_position` alimente le suivi, mais pas d'itinéraire calculé.
- **Prix** : `agreed_price` reste négocié motard ↔ client (pas d'estimation serveur).
- **Recharge Mobile Money** : `WalletTransaction` créée en `success` — l'intégration réelle de l'opérateur (confirmation USSD) reste à brancher (passer alors en `pending`).
- **Notifications** : pas d'endpoint client dédié → état vide honnête.
- **Débit du solde à la course** : pas encore implémenté (le solde se crédite via recharge, mais aucune course ne le débite pour l'instant).

## 5. Débogage rapide
- « Impossible de demander une course » → le client a déjà une course active (règle d'unicité dans `create_ride_request`) ; ou le rôle n'est pas `CLIENT`.
- L'écran reste sur « Recherche… » → aucun motard **abonné actif + disponible** n'a accepté (cf. `service/service_rides/logic.py`).
