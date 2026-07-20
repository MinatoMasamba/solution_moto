"""
Point d'entrée conditionnel des settings.

Avec DJANGO_SETTINGS_MODULE=config.settings (partout : local, PythonAnywhere,
Docker), l'environnement est choisi par la variable DJANGO_ENV :

- DJANGO_ENV=prod (ou production) -> config.settings.prod
- sinon (défaut)                  -> config.settings.dev

DJANGO_ENV peut venir de l'environnement système ou du fichier .env à la
racine du projet. On peut aussi continuer à pointer directement vers
config.settings.dev / config.settings.prod si on préfère être explicite.
"""

import os
from pathlib import Path

import environ

_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Charge .env dans os.environ (sans écraser les variables déjà définies),
# pour que DJANGO_ENV puisse être défini dans .env.
environ.Env.read_env(_BASE_DIR / ".env")

_DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev").strip().lower()

if _DJANGO_ENV in ("prod", "production"):
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
