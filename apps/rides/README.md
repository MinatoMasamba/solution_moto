# App: Rides

Ce module gère le cœur du métier : la mise en relation entre clients et motards et le suivi des courses.

## Responsabilités
- Gestion du cycle de vie d'une course : `REQUESTED` $ightarrow$ `ACCEPTED` $ightarrow$ `ONGOING` $ightarrow$ `COMPLETED`/`CANCELLED`.
- Enregistrement des points de prise en charge et de destination (coordonnées GPS).
- Gestion des tarifs convenus.
- Système de notation des courses via `RideRating`.

## Modèles Principaux
- `Ride` : Représente une course individuelle.
- `RideRating` : Stocke la note et le commentaire laissés après une course.
