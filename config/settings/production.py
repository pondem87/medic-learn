from django.core.exceptions import ImproperlyConfigured

from .base import *

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


if len(SECRET_KEY) < 32 or len(PROOF_KEY) < 32 or SECRET_KEY == PROOF_KEY:
    raise ImproperlyConfigured("Set separate random secrets of at least 32 characters.")
if not env.list("DJANGO_ALLOWED_HOSTS") or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Set explicit production hosts.")
if WHATSAPP_ENABLED and not all(
    [
        WHATSAPP_TOKEN,
        WHATSAPP_PHONE_ID,
        WHATSAPP_APP_SECRET,
        WHATSAPP_VERIFY_TOKEN,
        WHATSAPP_API_VERSION,
    ]
):
    raise ImproperlyConfigured("Configure all WhatsApp credentials before enabling the adapter.")
