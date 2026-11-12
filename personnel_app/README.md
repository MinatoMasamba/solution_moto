# GO-MBOKA — Personnel (Linux, Android, Windows)

Une application commune, interface DG reliée au serveur Django. Aucun mode maquette ni chiffre de secours. Au lancement, la connexion est obligatoire. Les profils, indicateurs, motards, clients, gérants, commissions, notifications, tickets et positions proviennent de `/api/personnel/direction/`, réservé à la DG/staff.

## Utilisation locale

```bash
# À la racine
venv/bin/python manage.py runserver 127.0.0.1:8000
# Dans personnel_app
flutter run -d linux
```

Les identifiants de recette sont dans `.local/personnel-recette.txt` à la racine, exclus de Git. Sur Android, utiliser l'adresse réseau de l'ordinateur (ou 10.0.2.2 pour l'émulateur Android standard), pas 127.0.0.1. HTTP est autorisé en debug seulement ; utiliser HTTPS en production. Windows doit être compilé sur Windows.

## Données et actions

La commande `seed_personnel --password <mot-de-passe>` crée des comptes RECETTE, flottes, courses, paiements espèces, avis, abonnements, positions GPS et tickets. Elle est additive et idempotente ; elle ne contacte aucun opérateur Mobile Money ni destinataire externe et ne réinitialise pas les mots de passe existants. Ces enregistrements de recette ne doivent pas être présentés comme une activité commerciale réelle.

Recherche dans chaque onglet, filtres des dossiers, fiche du motard, approbation/rejet, notifications lues, traitement/réouverture des tickets, modification du profil, changement du mot de passe, déconnexion, actualisation manuelle et automatique (30 secondes). Une erreur réseau conserve la date du dernier instantané et affiche une erreur ; aucun remplacement par des données fictives.

La carte utilise un vrai fond OpenStreetMap, les positions GPS persistées et les itinéraires OSRM de la simulation serveur. Les motos, clients, arrêts et embouteillages synthétiques sont identifiés SIMULATION. Voir `apps/geoloc/SIMULATION.md` à la racine pour préparer et exécuter le worker. Les notifications sont celles stockées dans Django, sans promesse d'envoi push ou e-mail. Les commissions sont les écritures existantes, sans bouton simulant un transfert financier.

## Vérification

```bash
flutter analyze
flutter test
flutter test test/visual_test.dart --dart-define=LIVE_DG=true
```

La dernière commande requiert le serveur local et le fichier d'identifiants de recette. Elle ouvre les neuf onglets en 1440×1000 et 412×915 et produit `verification/live/`. Les captures utilisent les vraies réponses du serveur. Un test au format téléphone ne remplace pas un essai sur un appareil Android.

Backend : `venv/bin/python manage.py test portal.test_personnel --noinput`.
