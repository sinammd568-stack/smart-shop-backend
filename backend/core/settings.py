"""Django settings for the AI-powered e-commerce backend."""
import os
from pathlib import Path
import dj_database_url # 👈 اضافه شد

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def env_list(name, default=""):
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]

def env_bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")

def env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default

DEFAULT_SECRET_KEY = "dev-insecure-key-change-me"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", DEFAULT_SECRET_KEY)
DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)

if not DEBUG:
    if SECRET_KEY == DEFAULT_SECRET_KEY or len(SECRET_KEY) < 32:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set (32+ chars) when DEBUG is False.")
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must not contain '*' when DEBUG is False.")

INSTALLED_APPS = [
    'daphne', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'chat',
    'store',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
ASGI_APPLICATION = "core.asgi.application"

# 👈 استفاده از دیتابیس ابری (PostgreSQL) با فال‌بک به SQLite برای لوکال
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

# ---------------- CORS ----------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOWED_ORIGIN_REGEXES = env_list("CORS_ALLOWED_ORIGIN_REGEXES")
# 👈 این خط رو اصلاح کردم تا پنل ادمین بتونه محصول و سفارش بسازه یا تغییر بده
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_CREDENTIALS = False

# ---------------- امنیت ----------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("FORCE_HTTPS", True)
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]
    SECURE_HSTS_SECONDS = env_int("HSTS_SECONDS", 2_592_000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0 if DEBUG else 1)
CHAT_MAX_CONNECTIONS_PER_IP = env_int("CHAT_MAX_CONNECTIONS_PER_IP", 5)
CHAT_MAX_MESSAGES_PER_MINUTE = env_int("CHAT_MAX_MESSAGES_PER_MINUTE", 20)

LANGUAGE_CODE = "fa"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

AUTH_USER_MODEL = 'store.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
}
