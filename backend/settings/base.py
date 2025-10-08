import os
from datetime import timedelta

import sentry_sdk
from celery.schedules import crontab
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from sentry_sdk import set_level
from sentry_sdk.integrations.django import DjangoIntegration

from . import cfg
from .logger import setup_logging

CONFIGURATION = cfg.environment

# This flag allow us to see debug panel on each page.
DEBUG_PANEL = False

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = "http://localhost:8000"

VERSION = "2.3.3"

SYSTEM_USER_EMAIL = "biuro@playmaker.pro"  # TODO: change soon

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = os.path.dirname(PROJECT_DIR)

ADMINS = MANAGERS = [
    ("Biuro", "biuro@playmaker.pro"),
    ("Jakub", "jakub@playmaker.pro"),
    ("Bartosz", "bartosz@playmaker.pro"),
]

DEFAULT_CACHE_LIFESPAN = 60 * 15  # in seconds (60 * 5 = 5min)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [
    "users",
    "profiles",
    "transfers",
    "followers",
    "inquiries",
    "marketplace",
    "clubs",
    "external_links",
    "soccerbase",
    "notifications",
    "app",
    "products",
    "fqa",
    "fantasy",
    "plays",
    "voivodeships",
    "mapper",
    "labels",
    "premium",
    "events",
    "mailing",
    "payments",
    "django_countries",
    "easy_thumbnails",
    "django_user_agents",
    "django_fsm",
    "phonenumber_field",
    "address",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.humanize",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "cities_light",
    "features",
    "django_extensions",
    "django_filters",
    "django_cleanup.apps.CleanupConfig",  # delete old files/images on update
    "django_celery_beat",
]

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Basic": {"type": "basic"},
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"},
    }
}


SITE_ID = 1

DATE_FORMAT = "Y-m-d"


# Reference to custom User model
AUTH_USER_MODEL = "users.User"


MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "middleware.user_activity_middleware.UserActivityMiddleware",
    # "middleware.redirect_middleware.RedirectMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, ".custom_email_templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

WSGI_APPLICATION = "backend.wsgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": cfg.postgres.db,
        "USER": cfg.postgres.user,
        "PASSWORD": cfg.postgres.password,
        "HOST": cfg.postgres.host,
        "PORT": cfg.postgres.port,
    },
}

# MongoDB configuration for user login tracking
# Note: Connection is initialized lazily in the service to avoid fork issues with Celery
MONGODB_SETTINGS = {
    "db": cfg.mongodb.db,
    "host": cfg.mongodb.host,
    "port": cfg.mongodb.port,
}

# Only add authentication if credentials are provided
if cfg.mongodb.username and cfg.mongodb.password:
    MONGODB_SETTINGS.update({
        "username": cfg.mongodb.username,
        "password": cfg.mongodb.password,
        "authentication_source": cfg.mongodb.auth_source,
    })

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa
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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "pl"  # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes


LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGES = (
    ("pl", _("Polski")),
    ("en", _("English")),
    ("de", _("Deutsch")),
    ("uk-UA", _("Українська")),
)

# Configuration for django-cities-light library.
# For more information, refer to the documentation:
# https://django-cities-light.readthedocs.io/en/stable-3.x.x/

# This setting specifies the translation languages to be included for city names.
CITIES_LIGHT_TRANSLATION_LANGUAGES = ["pl"]

# This setting specifies the countries to include when importing city data.
CITIES_LIGHT_INCLUDE_COUNTRIES = ["PL"]

CITIES_LIGHT_CITY_SOURCES = [
    "http://download.geonames.org/export/dump/cities15000.zip",  # all cities with a population > 15000  # noqa
    "http://download.geonames.org/export/dump/cities5000.zip",  # all cities with a population > 5000  # noqa
    "http://download.geonames.org/export/dump/cities1000.zip",  # all cities with a population > 1000  # noqa
    "http://download.geonames.org/export/dump/cities500.zip",  # all cities with a population > 500  # noqa
]  # more here: https://download.geonames.org/export/dump/readme.txt
# changes here require to run `python manage.py cities_light` command to import data

TIME_ZONE = "Europe/Warsaw"

USE_I18N = True

USE_L10N = False

USE_TZ = True

COMPRESS_ENABLED = False
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # "compressor.finders.CompressorFinder",  ## @dep - 2
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

# ManifestStaticFilesStorage is recommended in production, to prevent outdated
# Javascript / CSS assets being served from cache (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/3.1/ref/contrib/staticfiles/#manifeststaticfilesstorage  # noqa
# STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "/static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


# Wagtail settings

WAGTAIL_SITE_NAME = "backend"
WAGTAILADMIN_COMMENTS_ENABLED = False
# Wagtail customization
WAGTAIL_USER_EDIT_FORM = "users.forms.CustomUserEditForm"
WAGTAIL_USER_CREATION_FORM = "users.forms.CustomUserCreationForm"
WAGTAIL_USER_CUSTOM_FIELDS = []  # ['country',]

CORS_ORIGIN_ALLOW_ALL = True  # to be replaces  with CORS_ORIGIN_WHITELIST

# Allow custom headers for CORS
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-language",
]

# easy-thumbnail
THUMBNAIL_EXTENSION = "png"  # Or any extn for your thumbnails
THUMBNAIL_ALIASES = {
    "": {
        "product": {"size": (100, 100), "crop": True},
        "profile_avatar_show": {"size": (140, 140), "crop": True},
        "profile_avatar_show_mobile": {"size": (100, 100), "crop": True},
        "tables_avatar_show": {"size": (64, 64), "crop": True},
        "tables_avatar_show_small": {"size": (44, 44), "crop": True},
        "tables_avatar_show_medium": {"size": (54, 54), "crop": True},
        "profile_avatar_table": {"size": (25, 25), "crop": True},
        "nav_avatar": {"size": (25, 25), "crop": True},
        "club_small": {"size": (44, 44), "crop": True},
    },
}
# Crispy Form Theme - Bootstrap 4
CRISPY_TEMPLATE_PACK = "bootstrap4"
CRISPY_FAIL_SILENTLY = False

CUSTOM_URL_ENDPOINTS = {"limits": "limit"}
# Announcement app
ANNOUNCEMENT_DEFAULT_PLANS = [
    {
        "default": True,
        "limit": 1,
        "days": 14,
        "name": "Podstawowe",
        "description": "Możesz dodać jedno 14-dniowe ogłoszenie w ramach jednego półrocza. "  # noqa
        "Po zakupie konta premium będziesz mógł podpiąć 3 ogłoszenia na stałe."
        "Pozwoli to na prowadzenie naboru np. dla seniorów, drugiej drużyny oraz grup młodzieżowych.",  # noqa
    },
    {
        "default": False,
        "limit": 3,
        "days": 365,
        "name": "Premium",
        "description": "Możesz dodać trzy ogłoszenie w ramach jednego półrocza. "
        "Możesz jednocześnie prowadzić nabór np. dla seniorów, drugiej drużyny oraz grup młodzieżowych.",  # noqa
    },
]

ANNOUNCEMENT_INITAL_PLAN = ANNOUNCEMENT_DEFAULT_PLANS[0]

SEASON_DEFINITION = {"middle": 7}


# messages
MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}


# Authentication settings
LOGIN_URL = reverse_lazy("account_login")
LOGIN_REDIRECT_URL = reverse_lazy("profiles:show_self")

# allauth-settings
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGOUT_REDIRECT_URL = "/login/"
ACCOUNT_PRESERVE_USERNAME_CASING = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_USERNAME_BLACKLIST = []  # @todo
ACCOUNT_USERNAME_MIN_LENGTH = 3

# To enable email as indedifier
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_FORMS = {"signup": "users.forms.CustomSignupForm"}

# Blog settingss
BLOG_PAGINATION_PER_PAGE = 4


# Reset logging
# (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)
# LOGGING_CONFIG = None
# setup_logging(LOGGING_ROOTDIR)
LOGGING = setup_logging("_logs")


CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_WORKER_LOGLEVEL = "info"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TIME_LIMIT = 60 * 60
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "daily-supervisor": {
        "task": "app.celery.tasks.run_daily_supervisor",
        "schedule": crontab(hour=10, minute=0),  # Codziennie o 10:00
    },
}

# Redis & stream activity
STREAM_REDIS_CONFIG = {
    "default": {"host": "127.0.0.1", "port": 6379, "db": 0, "password": None},
}

# https://pypi.org/project/django-address/


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_CACHE_RESPONSE_TIMEOUT": DEFAULT_CACHE_LIFESPAN,
    "DEFAULT_CACHE_BACKEND": "default",
}

SPECTACULAR_SETTINGS = {
    "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    # 'SERVE_AUTHENTICATION': ['rest_framework.authentication.BasicAuthentication',],
}


GOOGLE_API_KEY = "AIzaSyAwISspDEfhVel-fTYm18Dh1EKtrD0xDH0xxxxx"
JQUERY_URL = False

# Django-countries

COUNTRIES_FIRST = ["PL", "GER", "CZ", "UA", "GB"]


# User agents settings
USER_AGENTS_CACHE = "default"

SCRAPPER = True


DEFAULT_CLUB_PICTURE_URL = "/media/default_club.png"

VOIVODESHIP_CHOICES = (
    ("Dolnośląskie", "Dolnośląskie"),
    ("Kujawsko-pomorskie", "Kujawsko-pomorskie"),
    ("Lubelskie", "Lubelskie"),
    ("Lubuskie", "Lubuskie"),
    ("Łódzkie", "Łódzkie"),
    ("Małopolskie", "Małopolskie"),
    ("Mazowieckie", "Mazowieckie"),
    ("Opolskie", "Opolskie"),
    ("Podkarpackie", "Podkarpackie"),
    ("Podlaskie", "Podlaskie"),
    ("Pomorskie", "Pomorskie"),
    ("Śląskie", "Śląskie"),
    ("Świętokrzyskie", "Świętokrzyskie"),
    ("Warmińsko-Mazurskie", "Warmińsko-Mazurskie"),
    ("Wielkopolskie", "Wielkopolskie"),
    ("Zachodniopomorskie", "Zachodniopomorskie"),
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

VERIFICATION_FORM = {"DEFAULT_SEASON_NAME": "2021/2022"}


# Setup token and refresh token lifetime.
# Refresh token is used to get new token, if auth token is expired.
# If refresh token is expired, user need to send login/ request again.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
}

GOOGLE_OAUTH2_PROJECT_ID = "playmaker-pro"
FACEBOOK_GRAPH_API_VERSION = "v17.0"

THROTTLE_EMAIL_CHECK_LIMITATION = 5
DEFAULT_THROTTLE = 5

ENABLE_SENTRY = os.getenv("ENABLE_SENTRY", False) in ["True", "true", "1", "yes"]

if ENABLE_SENTRY:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        enable_tracing=True,
        environment=os.getenv("ENVIRONMENT"),
    )
    set_level("warning")

DATETIME_FORMAT = "H:i:s d-m-Y"


# Loading of locally stored settings.
SWAGGER_PATH = os.path.join(BASE_DIR, "api", "swagger.yml")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": cfg.redis.url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

EMAIL_USE_TLS = cfg.smtp.use_tls
EMAIL_HOST = cfg.smtp.host
EMAIL_PORT = cfg.smtp.port
EMAIL_HOST_USER = cfg.smtp.host_username
DEFAULT_FROM_EMAIL = SERVER_EMAIL = cfg.smtp.outgoing_address
EMAIL_HOST_PASSWORD = cfg.smtp.password.get_secret_value()


try:
    from backend.settings.local import *  # noqa
except ImportError:
    pass
