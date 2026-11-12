from .base import *  # noqa: F401,F403

DEBUG = False

# ALLOWED_HOSTS ne doit jamais être vide en prod : on prend le contenu du
# .env et on garantit un fallback pour PythonAnywhere.
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # noqa: F405
if ".pythonanywhere.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".pythonanywhere.com")

# Origines de confiance CSRF dérivées des hôtes (surchargeables via .env).
CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=[
        f"https://*{host}" if host.startswith(".") else f"https://{host}"
        for host in ALLOWED_HOSTS
    ],
)

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Envoi réel des mails (codes de réinitialisation motard). SMTP configurable
# via .env ; sans SMTP configuré, on retombe sur le backend console (silencieux
# mais visible dans le log du serveur) plutôt qu'une levée d'exception.
if env("EMAIL_HOST", default=""):  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"  # noqa: F405
    EMAIL_HOST = env("EMAIL_HOST")  # noqa: F405
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)  # noqa: F405
    EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)  # noqa: F405
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Go-Mboka <no-reply@go-mboka.cd>")  # noqa: F405
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # noqa: F405
