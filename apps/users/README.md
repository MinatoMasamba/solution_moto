# App: Users

Ce module gère l'identité, l'authentification et les profils de tous les acteurs du système Go-Mboka.

## Responsabilités
- Gestion des comptes utilisateurs via un système basé sur le numéro de téléphone.
- Gestion des rôles : `CLIENT`, `MOTARD`, `OWNER` (Propriétaire), `FLEET_MANAGER` (Gérant de flotte), et `OPERATOR`.
- Deux points d'entrée pour l'inscription/connexion :
    - **API JWT** (`/api/v1/auth/...`) : utilisée par l'app mobile, via `serializers.py`/`views.py`.
    - **Web session Django** (`/chauffeur/...`) : formulaire d'inscription motard en 3 étapes + connexion, via `forms.py`/`views_web.py`.
- Profils spécifiques :
    - `MotardProfile` : Suivi des documents (permis, ID), adresse de résidence, statut d'abonnement, statut de validation du dossier (`application_status`) et note moyenne.
    - `OwnerProfile` : Informations sur l'entreprise du propriétaire.

## Modèles Principaux
- `User` : Modèle utilisateur personnalisé (`phone_number`, `first_name`, `last_name`, `post_nom`).
- `MotardProfile` : Extension du profil pour les motards (identité civile, adresse, pièce d'identité, documents).
- `OwnerProfile` : Extension du profil pour les propriétaires.

## Auth web motard (`/chauffeur/`)
- `forms.py` → `ChauffeurLoginForm`, `ChauffeurRegistrationForm` (validation + création `User`+`MotardProfile`).
- `views_web.py` → `ChauffeurLoginView`, `ChauffeurRegistrationView`, reset de mot de passe par code (cache local, 10 min).
- `urls_web.py` → namespace `chauffeur`, monté dans `config/urls.py`.
- Templates : `templates/chauffeur/chauffeur_auth/chauffeur_login.html` et `chauffeur_registration.html`.

## Architecture Front-end
Cette application contribue à l'écosystème front-end dynamique. Les données utilisateurs et les profils fournis par ses services sont consommés en temps réel par les tableaux de bord pour garantir une interface réactive et sans données statiques.
