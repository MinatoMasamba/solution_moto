from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Mails (codes de réinitialisation…) affichés dans la console en dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_browser_reload"]  # noqa: F405
MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]
