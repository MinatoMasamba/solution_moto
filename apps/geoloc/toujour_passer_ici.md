# Guide de Contexte d'Application (AI Map) : Geoloc

Ce fichier est le point d'entrée pour toute IA ou agent travaillant sur l'application `geoloc`. Il indique où trouver chaque composant et comment déboguer les fonctionnalités géospatiales.

---

## 1. Cartographie du Code (Où passer)

Si vous cherchez un bug, une modification ou un comportement précis, voici l'index :

- **Ingestion GPS (Microcontrôleurs / Trackers matériels)** :
  - `apps/geoloc/service_motard/api.py` $\rightarrow$ Contient `TrackerPingView`, l'endpoint HTTP (`GET`/`POST`) appelé par les trackers physiques.
- **Logique de traitement & Gestion Redis/Postgres** :
  - `apps/geoloc/service_motard/logic.py` $\rightarrow$ Contient `MotardHardwareService` qui résout l'IMEI, met à jour la position en temps réel (Redis "Hot Data") et archive dans la base de données (PostgreSQL "Cold Data").
- **Modèle de stockage historique** :
  - `apps/geoloc/models.py` $\rightarrow$ Contient `LocationPing`, la table historique reliant les positions GPS aux motards.
- **Enregistrement de l'IMEI/Matériel** :
  - Le `device_id` (IMEI) est stocké directement sur la moto, dans `apps/fleet/models.py` sur le modèle `Motorcycle`.

---

## 2. Flux de Données GPS

```text
[Tracker Moto] 
     │ (HTTP POST imei, lat, lng)
     ▼
[TrackerPingView] (apps/geoloc/service_motard/api.py)
     │
     ▼
[MotardHardwareService.process_ping] (apps/geoloc/service_motard/logic.py)
     │
     ├─► [Redis / Clé "moto_pos:{id}"] (Temps réel pour Dashboard Operator 1a)
     │
     └─► [PostgreSQL / LocationPing] (Historique de déplacement)
```

---

## 3. Guide de Débogage Rapide

- **Le tracker envoie sa position mais elle n'apparaît pas** :
  1. Vérifier si l'IMEI (`device_id`) envoyé par le tracker est bien configuré sur la moto dans la table `Motorcycle`.
  2. Vérifier si la moto est assignée à un motard (`assigned_motard`). Si aucune personne n'est assignée, l'archivage PostgreSQL (`LocationPing`) est ignoré, seule la position Redis est mise à jour.
- **Format des paramètres** :
  L'API attend :
  - `imei` : chaîne de caractères (IMEI du tracker).
  - `lat` : nombre décimal (Latitude).
  - `lng` : nombre décimal (Longitude).
  - `speed` : optionnel (Vitesse en km/h).
  - `batt` : optionnel (Pourcentage de batterie du tracker).

---

## 4. Architecture Front-end

Cette application contribue à l'écosystème front-end dynamique. Les données fournies par ses services sont consommées en temps réel par les tableaux de bord pour garantir une interface réactive et sans données statiques.
