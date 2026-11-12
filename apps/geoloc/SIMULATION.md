# Simulation de trajets — Kinshasa

Les coordonnées et les tracés sont calculés par Django. Flutter reçoit les positions, vitesses, phases et géométries ; il ne génère aucun mouvement local.

## Exécuter

```bash
venv/bin/python manage.py migrate
# Premier calcul : 6 requêtes OSRM, géométries conservées en base.
venv/bin/python manage.py simulate_trips --prepare --ticks 600 --interval 1 --speed 15
# Reprendre une session conservée (numéro affiché par la commande).
venv/bin/python manage.py simulate_trips --run-id 1 --ticks 600 --speed 15
# Rejouer les routes en nouvelle session, sans appel OSRM.
venv/bin/python manage.py simulate_trips --replay 1 --ticks 600 --speed 15
```

Une seule commande worker par session. `--interval` est le temps réel entre deux mises à jour ; `--speed` est le facteur d'accélération du temps simulé. Le pas simulé est limité à 120 secondes. Après le nombre de ticks demandé, la session se met en pause. Une session terminée se rejoue avec `--replay`. Le worker doit rester actif pour que « Reprendre » dans la carte redémarre le mouvement ; « Avancer de 10 s » fonctionne sans worker.

## Itinéraires et événements

Trois couples moto/client : Gombe → Limete, Lingwala → Lemba, Matete → Ndjili. Approche du client à 24 km/h, prise en charge immobile 25 s, course à 30 km/h, embouteillage à 5 km/h sur une portion, arrêt de 18 s, puis arrivée exacte au dernier point. Le client attend au point de prise en charge puis suit la moto. Les routes, positions, états et 2 000 dernières images sont conservés dans `SimulationRun`.

Le profil OSRM `driving` suit le réseau routier automobile ; il ne garantit pas les restrictions spécifiques aux motos. Pas de substitution en ligne droite si OSRM échoue. Les positions de routage à plus de 400 m du réseau sont refusées. Le service de routage peut être remplacé via `SIMULATION_ROUTER_URL` dans les settings Django.

Les contrôles et l'instantané sont réservés DG/staff via `/api/personnel/direction/`. Un GET n'avance jamais le temps. Pause et reprise sont conservées en base, avec verrou transactionnel pour chaque tick. La simulation ne crée aucun utilisateur, aucune vraie course, aucun paiement et aucun `LocationPing` réel.

## Carte

L'onglet « Carte temps réel » interroge le serveur toutes les 2 secondes. Bleu : approche ; violet : trajet prévu ; vert : trace parcourue. Motos violettes/orange selon l'événement ; clients bleus ; destinations signalées par un drapeau. GPS existants et simulation portent des légendes distinctes. Un filtre permet de masquer la simulation.

Tuiles OpenStreetMap avec attribution visible et identification de l'application, cache natif de flutter_map. Le fournisseur est configurable à la compilation avec `--dart-define=MAP_TILE_URL=https://…/{z}/{x}/{y}.png`. Pas de préchargement de zone. Réseau requis pour les tuiles non mises en cache. Les embouteillages et arrêts sont synthétiques, pas des observations du trafic réel.

## Vérification

```bash
venv/bin/python manage.py test apps.geoloc.test_simulation portal.test_personnel --noinput
```

Sources : https://project-osrm.org/docs/v5.24.0/api/ ; https://docs.fleaflet.dev/ ; https://operations.osmfoundation.org/policies/tiles/ .

## Sélection d'une seule moto

Les icônes simulées mesurent 26 × 24 pixels. Cliquer sur une moto ou sa ligne isole sa position, son client, ses routes et sa trace ; les autres motos et tracés sont masqués. « Afficher toutes les motos » rétablit l'ensemble. Pour une moto GPS réelle, le clic affiche uniquement ses 500 derniers points enregistrés, reliés dans l'ordre chronologique. Aucun parcours routier non enregistré n'est inventé entre ces échantillons.

Vérification native Linux : `flutter run -d linux -t tool/preview_server.dart`, depuis `personnel_app`, avec le serveur et les identifiants locaux de recette. Le helper capture directement la carte à 15 et 30 secondes dans `verification/live/native-road-*.png`. Les tests de widgets isolent les erreurs de transport des tuiles externes et ne constituent pas une preuve de chargement du fond de carte ; celui-ci est vérifié séparément dans l'application native.
