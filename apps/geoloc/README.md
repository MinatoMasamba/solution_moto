# App: Geoloc

Ce module gère la dimension spatiale et le suivi en temps réel des motards.

## Responsabilités
- Enregistrement des "pings" de localisation (`LocationPing`).
- Fourniture des données de position pour la carte en temps réel du tableau de bord.
- Analyse historique des déplacements si nécessaire.

## Modèles Principaux
- `LocationPing` : Stocke la position GPS d'un utilisateur à un instant T.
