# Guide de Contexte d'Application (AI Map) : Users

Ce fichier est le point d'entrée pour toute IA ou agent travaillant sur l'application `users`.

---

## 1. Règle Métier Fondamentale — Abonnement & Accès aux Courses

⚠️ **RÈGLE CRITIQUE** : **Seuls les motards avec `subscription_status == 'active'` peuvent voir et accepter des courses.**

Les statuts `trial`, `expired` et `suspended` **bloquent totalement** l'accès au flux de courses.
Il n'existe **aucune exception** pour les motards en essai (`TRIAL`) : l'essai concerne la probation physique sur route (flotte), pas l'accès à l'app client.

---

## 2. Création automatique du profil à l'inscription

Dans `apps/users/serializers.py` → `RegisterSerializer.create()` :

- Si le rôle est `MOTARD` → un `MotardProfile` est créé automatiquement avec `subscription_status = 'expired'`.
- Si le rôle est `OWNER` → un `OwnerProfile` est créé automatiquement.

**Pourquoi ?** Pour que la vérification d'éligibilité dans `RideDispatchService` trouve toujours un profil et applique le bon statut (bloqué par `EXPIRED`) plutôt que de tomber sur une `None`.

---

## 3. Cartographie du Code (Où passer)

- **Inscription** : `apps/users/serializers.py` → `RegisterSerializer`
- **Profil motard** : `apps/users/models.py` → `MotardProfile` (statuts : `active`, `trial`, `expired`, `suspended`)
- **Activation d'abonnement** : `apps/users/services.py` → `activate_motard_subscription(profile, expires_at)`
- **Expiration automatique** : `apps/users/services.py` → `expire_outdated_subscriptions()` (à appeler via Celery)
- **Règle d'éligibilité centrale** : `service/service_rides/logic.py` → `RideDispatchService`

---

## 4. Guide de Débogage Rapide

- **Motard bloqué à l'accès des courses** :
  1. Vérifier `MotardProfile.subscription_status` → doit être `active`.
  2. Vérifier `MotardProfile.is_available` → doit être `True`.
  3. Vérifier `MotardProfile.subscription_expires_at` → ne doit pas être dans le passé (sinon `expire_outdated_subscriptions` le mettra à `expired`).

---

## 5. Deux flux d'inscription qui divergent — ⚠️ à connaître

Il existe **deux chemins distincts** pour créer un compte motard, qui ne collectent pas les mêmes données :

- **API JWT** (`POST /api/v1/auth/register/`, `RegisterSerializer`) : crée `User` + `MotardProfile` **vide** (juste `subscription_status='expired'`). Utilisé par l'app mobile.
- **Web session** (`POST /chauffeur/inscription/`, `ChauffeurRegistrationForm.save()`) : crée `User` + `MotardProfile` **complet** (adresse, pièce d'identité, documents uploadés) et fixe `application_status='pending'`.

**Piège** : un motard inscrit via l'API n'aura ni adresse, ni documents, ni `application_status` cohérent (`pending` par défaut au niveau modèle, mais rien ne l'a réellement soumis à validation). Si on ajoute un jour une vérification qui suppose que tout `MotardProfile` a été validé via le flux web, il faut gérer ce cas.

## 6. `application_status` n'est PAS encore un verrou métier

`MotardProfile.application_status` (`pending`/`approved`/`rejected`) est stocké et visible dans l'admin, mais **rien ne l'utilise pour bloquer quoi que ce soit** — ni la connexion, ni `RideDispatchService` (qui ne regarde que `subscription_status`, cf. section 1). Un motard `pending` peut donc déjà se connecter normalement. Si le produit veut réellement bloquer l'accès tant que le dossier n'est pas `approved`, il faut ajouter la vérification (probablement dans `RideDispatchService` et/ou à la connexion `ChauffeurLoginView`).

## 7. Auth web motard — Cartographie du Code (Où passer)

- **Formulaires** : `apps/users/forms.py` → `ChauffeurLoginForm` (téléphone + mot de passe), `ChauffeurRegistrationForm` (3 étapes fusionnées en un seul POST, validation unicité téléphone/email, taille des fichiers).
- **Vues** : `apps/users/views_web.py` → `ChauffeurLoginView` (session Django via `authenticate()`/`login()`), `ChauffeurRegistrationView`, `chauffeur_password_reset_request`/`_confirm` (endpoints JSON, code à 6 chiffres stocké dans le cache Django sous `chauffeur-password-reset:{email}`, TTL 10 min).
- **URLs** : `apps/users/urls_web.py` (namespace `chauffeur`), montées sur `path("chauffeur/", ...)` dans `config/urls.py`.
- **Templates** : `templates/chauffeur/chauffeur_auth/` — pages HTML autonomes (n'étendent pas `base.html`), stylées avec un runtime Tailwind CDN-free (`static/vendor/tailwindcss.js`) + Lucide (`static/vendor/lucide.js`), copiés depuis un autre projet et adaptés au branding Go-Mboka.
- **Le numéro "WhatsApp" du formulaire d'inscription EST `User.phone_number`** (identifiant de connexion), pas un champ à part — attention si on veut un jour un vrai numéro de contact distinct.

## 8. Angles morts connus (non traités)

- Pas de rate-limiting sur `/chauffeur/inscription/`, `/chauffeur/connexion/` ni sur la demande de code de reset (un code à 6 chiffres sans limite de tentatives est brute-forçable en pratique).
- `EMAIL_BACKEND` n'est pas configuré dans `config/settings/` → en prod, `send_mail(..., fail_silently=True)` échouera silencieusement tant qu'un backend SMTP n'est pas branché. Le code de reset est donc généré mais jamais réellement envoyé en l'état.
- Validation fichiers uploadés (`photo_piece_identite`, `permis_conduire`) : taille vérifiée côté serveur, mais pas le type MIME réel (un fichier renommé pourrait passer).
- Pas de tests automatisés (`tests.py`) pour `forms.py`/`views_web.py` — uniquement vérifié manuellement via `manage.py shell` + `django.test.Client`.

---

## 9. Architecture Front-end

Cette application contribue à l'écosystème front-end dynamique. Les données utilisateurs et les profils fournis par ses services sont consommés en temps réel par les tableaux de bord pour garantir une interface réactive et sans données statiques.

## 9. App Client — SavedPlace & résumé (ajouts)

- **`SavedPlace`** (`models.py`) : lieux enregistrés d'un client (label, adresse, lat/lng). API `/api/v1/saved-places/` (`SavedPlaceViewSet`, scopé à l'utilisateur).
- **`User.referral_code`** : propriété (pas un champ) — code de parrainage stable dérivé du prénom + id (ex. `SARAH24`).
- **`ClientSummaryView`** (`/api/v1/client/summary/`) : identité, note moyenne reçue, nb de courses terminées, code parrainage, filleuls, solde portefeuille, courses offertes. Alimente l'en-tête/accueil de `templates/client/app.html`.
- **`MeView.patch`** (`/api/v1/auth/me/`) : mise à jour `first_name`/`last_name`/`email` (écran « Modifier mon compte »).
