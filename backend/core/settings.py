"""Django settings for the AI-powered e-commerce backend."""
import os
from pathlib import Path

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
# Render یک هاست خارجی تعریف می‌کند
RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)

if not DEBUG:
    if SECRET_KEY == DEFAULT_SECRET_KEY or len(SECRET_KEY) < 32:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set (32+ chars) when DEBUG is False.")
    if "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("ALLOWED_HOSTS must not contain '*' when DEBUG is False.")

INSTALLED_APPS = [
    "daphne",  # باید اولین مورد باشد
    "django.contrib.staticfiles",
    "channels",
    "corsheaders",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"
ASGI_APPLICATION = "core.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# برای نسخه اول (یک instance) لایه درون‌حافظه‌ای کافی است.
# برای چند instance از channels-redis استفاده کنید (محدودیت‌های نرخ هم باید به Redis منتقل شوند).
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
}

# ---------------- CORS ----------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173")
# اختیاری: برای دامنه‌های پیش‌نمایش، مثلاً ^https://.*\.my-shop\.pages\.dev$
CORS_ALLOWED_ORIGIN_REGEXES = env_list("CORS_ALLOWED_ORIGIN_REGEXES")
CORS_ALLOW_METHODS = ["GET", "OPTIONS"]
CORS_ALLOW_CREDENTIALS = False

# ---------------- امنیت ----------------
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("FORCE_HTTPS", True)
    SECURE_REDIRECT_EXEMPT = [r"^api/health/$"]  # health check داخلی روی HTTP
    SECURE_HSTS_SECONDS = env_int("HSTS_SECONDS", 2_592_000)  # ۳۰ روز
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False

# تعداد پراکسی‌های مورد اعتماد جلوی برنامه (Render = 1). در لوکال ۰.
TRUSTED_PROXY_COUNT = env_int("TRUSTED_PROXY_COUNT", 0 if DEBUG else 1)

# محدودیت‌های چت
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
