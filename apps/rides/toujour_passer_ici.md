# Guide de Contexte d'Application (AI Map) : Rides

Ce fichier est le point d'entrée pour toute IA ou agent travaillant sur l'application `rides`. Il spécifie les règles métier strictes concernant la distribution des courses.

---

## 1. Règle Métier Fondamentale (La Règle d'Or)

⚠️ **RÈGLE CRITIQUE** : **Seuls les motards ayant un abonnement actif (`subscription_status == 'active'`) ont le droit de recevoir ou d'accepter des demandes de parcours (courses clients via l'application).**

### Pourquoi cette règle ?
- **Pilier 1 (Abonnement)** : Le motard paie pour recevoir les clients de l'application. C'est son canal d'acquisition.
- **Piliers 2 & 3 (Gérance / Allocation)** : Ces motards travaillent en dehors du flux de l'application (prospection physique) et remboursent leur contrat (Rental ou Hire Purchase) de manière journalière/hebdomadaire. Ils ne reçoivent pas les requêtes de l'app.
- **Motards en essai (`TRIAL`)** : Bien qu'ils fassent l'objet d'une probation sur route, ils ne reçoivent pas les demandes automatisées de l'application générale réservée aux abonnés payants.

---

## 2. Cartographie du Code (Où passer)

Si vous cherchez un bug ou devez modifier la logique des courses :

- **Cycle de vie des courses (Acceptation, Démarrage, Clôture)** :
  - `apps/rides/services.py` $\rightarrow$ Contient les fonctions d'application dont `accept_ride`. Celle-ci appelle `RideDispatchService.validate_motard_for_ride_acceptance` pour rejeter toute acceptation par un motard non abonné actif.
- **Vues de l'API & requêtes** :
  - `apps/rides/views.py` $\rightarrow$ Contient `RideViewSet`. La méthode `get_queryset` filtre les demandes de parcours disponibles (`status=REQUESTED`) afin de ne les afficher **que** si le motard connecté possède un abonnement actif (`RideDispatchService.is_motard_eligible_for_requests`).
- **Modèle de données principal** :
  - `apps/rides/models.py` $\rightarrow$ Contient le modèle `Ride` et `RideRating`.

---

## 3. Guide de Débogage Rapide

- **Un motard se plaint de ne pas voir ou de ne pas pouvoir accepter de demandes de parcours** :
  1. Vérifier si son `subscription_status` dans `MotardProfile` est bien à `active`. S'il est à `trial`, `expired` ou `suspended`, il ne verra pas le flux et l'API rejettera ses tentatives d'acceptation.
  - Vérifier si `is_available` est activé à `True`.

  ---

  ## 4. Architecture Front-end

  Cette application contribue à l'écosystème front-end dynamique. Les données de courses en temps réel fournies par ses services sont consommées par les tableaux de bord pour garantir une interface réactive et sans données statiques.
