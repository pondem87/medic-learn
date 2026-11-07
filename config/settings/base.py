from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
INSTALLED_APPS = [
    "config.admin.CognitoAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "medic_learn.accounts",
    "medic_learn.verification",
    "medic_learn.events",
    "medic_learn.notifications",
    "medic_learn.messages",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
if env("DATABASE_URL", default=""):
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    database_ssl_mode = env("DATABASE_SSL_MODE", default="verify-full")
    if database_ssl_mode not in {"verify-full", "disable"}:
        raise ValueError("DATABASE_SSL_MODE must be verify-full or disable")
    database_options = {"sslmode": database_ssl_mode}
    if database_ssl_mode == "verify-full":
        database_options["sslrootcert"] = env("DATABASE_SSL_ROOT_CERT")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DATABASE_NAME"),
            "USER": env("DATABASE_USER"),
            "PASSWORD": env("DATABASE_PASSWORD"),
            "HOST": env("DATABASE_HOST"),
            "PORT": 5432,
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": database_options,
        }
    }
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["medic_learn.accounts.authentication.AccountBackend"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
USE_TZ = True
TIME_ZONE = "UTC"
STATIC_URL = env("DJANGO_STATIC_URL", default="/static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/profile/"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "medic_learn.accounts.authentication.AccountJWTAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["medic_learn.accounts.authentication.Verified"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "medic_learn.accounts.api.exception_handler",
}
SPECTACULAR_SETTINGS = {"TITLE": "Medic Learn API", "VERSION": "1.0.0"}
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
SES_REGION = env("SES_REGION", default="af-south-1")
EMAIL_HOST = env("EMAIL_HOST", default="127.0.0.1")
EMAIL_PORT = env.int("EMAIL_PORT", default=1025)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@medic-learn.local")
RABBITMQ_URL = env("RABBITMQ_URL")
WHATSAPP_ENABLED = env.bool("WHATSAPP_ENABLED", default=False)
WHATSAPP_TOKEN = env("WHATSAPP_TOKEN", default="")
WHATSAPP_PHONE_ID = env("WHATSAPP_PHONE_ID", default="")
WHATSAPP_APP_SECRET = env("WHATSAPP_APP_SECRET", default="")
WHATSAPP_VERIFY_TOKEN = env("WHATSAPP_VERIFY_TOKEN", default="")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="")

DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576

# Cognito is the sole authentication provider; business permissions remain local.
AWS_REGION = env("AWS_REGION", default="af-south-1")
COGNITO_POOL_ID = env("COGNITO_POOL_ID", default="")
COGNITO_WEB_CLIENT_ID = env("COGNITO_WEB_CLIENT_ID", default="")
COGNITO_WEB_CLIENT_SECRET = env("COGNITO_WEB_CLIENT_SECRET", default="")
COGNITO_MOBILE_CLIENT_ID = env("COGNITO_MOBILE_CLIENT_ID", default="")
COGNITO_ISSUER = (
    f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_POOL_ID}" if COGNITO_POOL_ID else ""
)
COGNITO_API_SCOPE = "medic-api/access"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
# Separate Fernet key required to retain short-lived Cognito credentials in DB sessions.
COGNITO_SESSION_KEY = env("COGNITO_SESSION_KEY", default="")
EVIDENCE_BUCKET = env("EVIDENCE_BUCKET", default="")
EVIDENCE_ROOT = BASE_DIR / ".private-evidence"
DATA_UPLOAD_MAX_MEMORY_SIZE = 12 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "medic_learn.accounts.authentication.CognitoAuthentication"
]
REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ["medic_learn.accounts.authentication.VerifiedRole"]

RABBITMQ_QUEUE_TYPE = env("RABBITMQ_QUEUE_TYPE", default="classic")
