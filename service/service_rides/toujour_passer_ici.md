# Guide de Contexte Service : Service Rides (AI Map)

Ce fichier est le point d'entrée pour toute IA ou agent travaillant sur le service centralisé de gestion des trajets (`service_rides`). Il explique la logique métier d'attribution des parcours.

---

## 1. Cartographie du Code (Où passer)

- **Logique Métier Centrale & Filtrage** :
  - `service/service_rides/logic.py` $\rightarrow$ Contient `RideDispatchService`. C'est ici que l'éligibilité d'un motard à recevoir ou accepter des requêtes de parcours est vérifiée et validée.

---

## 2. Règle Métier : Qui peut recevoir ou accepter des requêtes ?

⚠️ **RÈGLE CRITIQUE** : **Seuls les motards ayant un abonnement actif (`SubscriptionStatus.ACTIVE`) sont éligibles pour voir ou accepter des parcours.**

- **Fonctions d'évaluation** :
  - `is_motard_eligible_for_requests(motard)` : Retourne `True` uniquement si le motard a le rôle `MOTARD` et que son `subscription_status` dans son profil est `"active"`.
  - `validate_motard_for_ride_acceptance(motard)` : Lève une `ValidationError` Django si le motard n'est pas éligible. Cette fonction est appelée directement lors du processus d'acceptation d'une course dans `apps/rides/services.py`.
  - `filter_eligible_motards_for_dispatch(queryset)` : Filtre une liste d'utilisateurs pour n'en conserver que les motards disponibles et abonnés actifs.

---

## 3. Guide de Débogage Rapide

- **Le motard ne peut pas accepter de course (Erreur : "Accès refusé")** :
  1. Aller sur le profil du motard (`MotardProfile`).
  - Vérifier que son `subscription_status` est bien égal à `"active"`. S'il est à `"trial"` (en essai), `"expired"` (expiré), ou `"suspended"`, il sera bloqué par `validate_motard_for_ride_acceptance`.

  ---

  ## 4. Architecture Front-end

  Ce service fournit des logiques métier critiques (ex: éligibilité motard) qui sont consommées par les APIs. Les tableaux de bord utilisent ces résultats pour garantir une interface réactive et sans données statiques.
