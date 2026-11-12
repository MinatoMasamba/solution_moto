# DG — recette sur données serveur

Le mode maquette est retiré du code exécuté. Le démarrage demande une connexion. Aucun chiffre ni marqueur de secours n'est injecté dans Flutter.

## Serveur

`GET /api/personnel/direction/` : identité DG, indicateurs, activité horaire, réseau complet, clients, gérants, écritures de commission, notifications personnelles, tickets et dernières positions enregistrées. Accès réservé DG/staff.

`POST /api/personnel/direction/` : décision de dossier, statut support, lecture de notification. Profil via `PATCH /api/v1/auth/me/`, mot de passe via `/api/account/password/`.

Le jeu de recette est enregistré dans la base locale : comptes nommés RECETTE, 6 motards, 4 clients, propriétaire, gérant, DG, motos, courses, paiements espèces, abonnements, avis, GPS, commissions et tickets. Il s'ajoute aux données préexistantes. Un deuxième passage conserve les effectifs. Sauvegarde et identifiants sous `.local/`, exclus de Git.

## Parcours vérifiés

Tests Django : refus anonyme/non-DG, isolation des notifications, instantané réel, changement de statut support enregistré, décision de dossier enregistrée, rejet d'une action invalide.

Tests Flutter : contrat JWT téléphone et jeton, état sans connexion, puis navigation des neuf onglets sur le serveur local aux formats 1440 × 1000 et 412 × 915. Captures dans `verification/live/` (non publiées dans Git car elles peuvent contenir des données existantes).

Boucle visuelle : captures, inspection, correction du rendu Material de la barre latérale, correction des montants/notes/dates et de l'encombrement GPS, nouvelles captures.

## Limites explicites

Le fond routier de la maquette n'est pas repris en faux : la carte affiche les coordonnées persistées sur une grille géographique Kinshasa, avec zoom et déplacement. Les dates GPS sont visibles ; des positions anciennes restent des positions historiques, pas une présence actuelle garantie.

Les notifications sont internes à Django. Pas de bouton simulant un paiement, un push, un e-mail ou un transfert financier. Les données RECETTE sont des exemples enregistrés, pas une activité commerciale réelle. Les réglages opérationnels incluent profil, mot de passe, actualisation et déconnexion ; photo de profil, préférences de langue et notifications externes ne sont pas implémentées.

Windows n'est pas exécuté depuis cet environnement Linux. Une capture au format téléphone ne prouve pas l'exécution Android sur appareil. La conformité graphique exacte au ZIP n'est pas déclarée acquise.
