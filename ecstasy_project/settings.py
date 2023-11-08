"""
Django settings for EcstasyProject project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import _locale
import logging
import os
import re
from datetime import timedelta, datetime
from pathlib import Path

import orjson
import urllib3
from pyzabbix.api import logger as zabbix_api_logger
from urllib3.exceptions import InsecureRequestWarning

from gathering.ftp import FTPCollector

_locale._getdefaultlocale = lambda *args: ["en_US", "utf8"]

# Отключает warnings для `Unverified HTTPS request`
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

X_FRAME_OPTIONS = "SAMEORIGIN"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "1238710892y3u1h0iud0q0dhb0912bd1-2")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG") == "1"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1").split()

# Application definition
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "drf_yasg",
    "check",
    "net_tools",
    "maps",
    "app_settings",
    "gathering",
    "django.contrib.humanize",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "ring_manager",
    "dbbackup",
    "django_celery_beat",
    "gpon",
]

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "./db-backup"}


# Эта переменная используется, чтобы определить, какой класс сборщика FTP использовать для сбора данных с FTP-серверов.
FTP_COLLECTOR_CLASS = FTPCollector
# По умолчанию установлено значение `FPTCollector`, но его можно переопределить, если требуется другой класс коллектора.
# Он должен наследоваться от `AbstractFTPCollector`.


REMOTE_DEVICE_CLASS = "devicemanager.remote.connector.RemoteDevice"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ecstasy_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
            BASE_DIR / "media/templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "libraries": {
                "gpon_perms": "gpon.templatetags.gpon_perms",
            },
        },
    },
]

WSGI_APPLICATION = "ecstasy_project.wsgi.application"

DATABASES = orjson.loads(
    os.getenv("DATABASES", "{}").replace("'", '"').replace(" ", "").replace("\n", "")
)
if not DATABASES:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "db.sqlite3",
            "OPTIONS": {
                "timeout": 20,
            },
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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "Europe/Moscow"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"

if os.getenv("DJANGO_COLLECT_STATIC", "0") == "1":
    STATIC_ROOT = BASE_DIR / "static"
else:
    STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

NON_ABON_INTERFACES_PATTERN = re.compile(
    r"power_monitoring|[as]sw\d|dsl|co[pr]m|msan|core|cr\d|nat|mx-\d|dns|bras|voip|fttb|honet",
    re.IGNORECASE,
)

# ================= CACHE ===================

if DEBUG:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        },
    }

else:

    REDIS_CACHE_URL = os.getenv("REDIS_CACHE_URL", "localhost:6379/0")

    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{REDIS_CACHE_URL}",
            "KEY_PREFIX": os.getenv("CACHE_KEY_PREFIX", "ecstasy_dev"),
        }
    }

# ================ REST FRAMEWORK =================

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "drf_orjson_renderer.renderers.ORJSONRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "drf_orjson_renderer.parsers.ORJSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ],
}

# ================= SWAGGER ==================

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        }
    }
}


# ================= CELERY ==================

REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "localhost:6379/1")

CELERY_TIMEZONE = TIME_ZONE
CELERY_BROKER_URL = f"redis://{REDIS_BROKER_URL}"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL


# ========== CONFIGURATION STORAGE ===========

config_dir = os.getenv("CONFIG_STORAGE_DIR")

if config_dir:
    CONFIG_STORAGE_DIR = Path(config_dir)
else:
    CONFIG_STORAGE_DIR = BASE_DIR / "configs"

# ================= LOGGING ==================


LOGGING_DIR = BASE_DIR / "logs"
LOGGING_DIR.mkdir(parents=True, exist_ok=True)

zabbix_api_logger.setLevel(logging.ERROR)

if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{asctime} {levelname} {module} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{asctime} {levelname} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": LOGGING_DIR / "debug.log",
                "formatter": "verbose",
                "when": "midnight",
                "backupCount": 30,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": True,
        },
        # "loggers": {
        #     "django": {
        #         "level": "INFO",
        #         "handlers": ["file", "console"],
        #         "propagate": True,
        #     }
        # },
    }

# ================= JWT ===================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS512",
    "SIGNING_KEY": SECRET_KEY[::-1],
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": "ecstasy",
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}

JAZZMIN_SETTINGS = {
    "site_title": "Панель администратора",
    "site_header": "Ecstasy",
    "site_brand": "Ecstasy",
    "site_icon": "flavico.ico",
    "site_logo": "flavico.ico",
    "welcome_sign": "Добро пожаловать в панель администратора",
    "copyright": "ig-rudenko",
    "topmenu_links": [
        {"name": "Вернуться на сайт", "url": "/"},
        {"name": "Документация API", "url": "swagger-ui", "new_window": True},
        {"model": "auth.User"},
    ],
    "related_modal_active": True,
    "navigation_expanded": False,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "check.AuthGroup": "fas fa-key",
        "check.Bras": "fas fa-box",
        "check.DeviceGroup": "fas fa-object-group",
        "check.Devices": "fas fa-server",
        "check.Profile": "fas fa-id-card",
        "check.UsersActions": "fas fa-font",
        "check.DeviceMedia": "fas fa-images",
        "app_settings.LogsElasticStackSettings": "fas fas fa-wrench",
        "app_settings.ZabbixConfig": "fas fas fa-wrench",
        "app_settings.VlanTracerouteConfig": "fas fas fa-wrench",
        "gathering.MacAddress": "fas fa-ethernet",
        "maps.Layers": "fas fa-layer-group",
        "maps.Maps": "fas fa-map",
        "net_tools.VlanName": "fas fa-network-wired",
        "net_tools.DevicesForMacSearch": "fas fa-server",
    },
}
JAZZMIN_UI_TWEAKS = {
    "theme": "litera",
    "dark_mode_theme": "darkly",
}
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL")
CONTACT_NAME = os.getenv("CONTACT_NAME")
