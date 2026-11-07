from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured

from .base import *

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


if len(SECRET_KEY) < 32:
    raise ImproperlyConfigured("Set a random Django secret of at least 32 characters.")
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

if not all(
    [
        COGNITO_POOL_ID,
        COGNITO_WEB_CLIENT_ID,
        COGNITO_WEB_CLIENT_SECRET,
        COGNITO_MOBILE_CLIENT_ID,
        COGNITO_SESSION_KEY,
        EVIDENCE_BUCKET,
    ]
):
    raise ImproperlyConfigured(
        "Configure Cognito, encrypted session storage and private S3 evidence storage."
    )
try:
    Fernet(COGNITO_SESSION_KEY.encode())
except ValueError as exc:
    raise ImproperlyConfigured("COGNITO_SESSION_KEY must be a Fernet key.") from exc

# Only ALB can reach container port 8000; ALB supplies X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = [r"^health/$"]
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": env("MEDIA_BUCKET", default=EVIDENCE_BUCKET),
            "region_name": AWS_REGION,
            "default_acl": None,
            "location": "uploads",
            "file_overwrite": False,
            "querystring_auth": True,
            "querystring_expire": 60,
            "object_parameters": {"ServerSideEncryption": "AES256"},
        },
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"},
}
