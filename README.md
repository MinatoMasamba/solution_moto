# GO-MBOKA

Plateforme numérique de gestion de taxi-motos à Kinshasa. Elle relie clients, motards, propriétaires de flottes et opérateurs : mise en relation, suivi GPS des courses, gestion des motos, abonnements motards, notifications in-app et paiements Mobile Money.

## Lancer en local

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Endpoints principaux :
- Portail : `/`
- App client (PWA) : `/client/app/` — installable sur Android/iOS
- App motard : `/chauffeur/connexion/`
- API : `/api/v1/...` (health: `/api/v1/health/`)
- Admin : `/admin/`

## Paiements Mobile Money

Le module est isolé dans `apps/payments/providers/` derrière une interface unique
(`initiate_charge` / `check_status` / `handle_webhook`). En l'absence d'agrégateur
branché, le **simulator** est actif : la charge est acceptée immédiatement
(`GM_PAYMENT_SIMULATION=auto`) ou reste en attente d'un webhook
(`GM_PAYMENT_SIMULATION=manual`).

Brancher un vrai agrégateur (FlexPay, LootPay, API directe Airtel/M-Pesa/Orange) :
1. créer `apps/payments/providers/<nom>.py` héritant de `BaseMobileMoneyProvider` ;
2. l'enregistrer dans `_PROVIDERS` (`apps/payments/providers/__init__.py`) ;
3. définir `PAYMENT_PROVIDER=<nom>` + credentials dans `.env` ;
4. configurer le callback de l'agrégateur sur `POST /api/v1/payments/webhook/`
   avec le header `X-Webhook-Token: $PAYMENTS_WEBHOOK_TOKEN`.

Flux couverts : recharge du portefeuille client (`POST /api/v1/wallet/`),
débit automatique du solde à la fin de la course (sinon paiement en espèces),
paiement de l'abonnement motard (`POST /api/v1/subscriptions/<id>/pay/`).

## Tâches périodiques (cron)

```bash
python manage.py expire_subscriptions   # toutes les heures
```

Sans cron, l'expiration des abonnements est aussi vérifiée « lazy » à chaque
consultation/acceptation de courses (`RideDispatchService`).

## Tests

```bash
python manage.py test apps.payments apps.rides apps.users apps.geoloc
```

## Déploiement (PythonAnywhere)

1. `DJANGO_ENV=prod` dans le `.env` serveur + `SECRET_KEY`, `ALLOWED_HOSTS`.
2. Pointer le fichier WSGI vers `config.wsgi` (settings par défaut = prod).
3. `python manage.py migrate && python manage.py collectstatic`
4. Configurer le cron `expire_subscriptions`.
5. HTTPS obligatoire pour l'installation PWA (SECURE_SSL_REDIRECT=True par défaut en prod).
