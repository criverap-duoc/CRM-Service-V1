from .base import *

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Mostrar emails en consola en vez de enviarlos
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
