import os
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = cast(str, os.getenv("SECRET_KEY"))

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_BASE_URL = os.getenv(
    "WEATHER_API_BASE_URL", "https://api.openweathermap.org/data/2.5/weather"
)
WEATHER_CACHE_TTL = int(os.getenv("WEATHER_CACHE_TTL", "300"))

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS", "30"))
RATE_PERIOD = int(os.getenv("RATE_PERIOD", "60"))

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "cities_light",
    "weather",
    "health_check",
    "health_check.db",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "app.middlewares.rate_limit.RateLimitMiddleware",
    "app.middlewares.logging_middleware.LoggingMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "App",
    "SERVE_INCLUDE_SCHEMA": False,
    "SECURITY": [{"Authentication": []}],
}


WSGI_APPLICATION = "app.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CITIES_LIGHT_TRANSLATION_LANGUAGES = os.getenv(
    "CITIES_LIGHT_TRANSLATION_LANGUAGES", "en"
).split(",")
CITIES_LIGHT_INCLUDE_COUNTRIES = os.getenv(
    "CITIES_LIGHT_COUNTRIES", "US,BY"
).split(",")
CITIES_LIGHT_INCLUDE_CITY_TYPES = ["PPL", "PPLA", "PPLA2", "PPLA3", "PPLA4", "PPLC"]
CITIE_LIGHT_INDEX_SEARCH_NAMES = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": (
                '{"time":"%(asctime)s", "level":"%(levelname)s", '
                '"logger":"%(name)s", "message":%(message)s}'
            ),
            "style": "%",
        },
        "verbose": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "request_logger": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "cities_light": {
            "handlers": ["console"],
            "propagate": True,
            "level": "INFO",
        },
        "django": {
            "handlers": ["console"],
            "propagate": True,
            "level": "INFO",
        },
        "weather": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
