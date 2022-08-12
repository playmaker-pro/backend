import os
import logging

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _


# This loads additional settings for our environemnt
CONFIGURATION = "dev"  # following options are allowed ['dev', 'production', 'staging']

# This flag allow us to see debug panel on each page.
DEBUG_PANEL = False


# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
BASE_URL = "http://localhost:8000"


VERSION = "1.3.16"


SYSTEM_USER_EMAIL = "rafal.kesik@gmail.com"


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = os.path.dirname(PROJECT_DIR)


MANAGERS = [
    ("Rafal", "rafal.kesik@gmail.com"),
]

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/


# Application definition

INSTALLED_APPS = [
    "users",
    "home",
    "search",
    "news",
    "profiles",
    "transfers",
    "contact",
    "followers",
    "inquiries",
    "clubs",
    "soccerbase",
    "notifications",
    "app",
    "marketplace",
    "products",
    "fqa",
    "fantasy",
    "plays",
    "landingpage",
    "resources",
    "data",  # external repo
    "stats",  # external repo
    "django_countries",
    "crispy_forms",
    "easy_thumbnails",
    "djcelery",
    "django_user_agents",
    "wagtail.contrib.forms",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.core",
    "wagtail.contrib.routable_page",
    "wagtail.api.v2",
    "wagtailmetadata",
    # 'comments_wagtail_xtd',
    # 'django_comments',
    "modelcluster",
    "taggit",
    "blog",
    "flex",
    "streams",
    "django_fsm",
    "phonenumber_field",
    "address",
    "compressor",
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
    "rest_framework.authtoken",  # <-- Here
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
]


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
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "app.context_processors.app_info",
                "inquiries.context_processors.get_user_info",
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
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases


DATABASE_ROUTERS = ["data.routers.DataRouter", "data.routers.DefaultDBRouter"]

# DB_ITERATOR = '11'
DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # },
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "local_pm",
        "USER": "arsen",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    },
    "datadb": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "local_data",
        "USER": "arsen",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "pl"  # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes


LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

LANGUAGES = (
    ("pl", _("Polski")),
    ("en-us", _("Angielski")),
)

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
    "compressor.finders.CompressorFinder",
]

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]

# ManifestStaticFilesStorage is recommended in production, to prevent outdated
# Javascript / CSS assets being served from cache (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/3.1/ref/contrib/staticfiles/#manifeststaticfilesstorage
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

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

# For Bootstrap 4, change error alert to 'danger'
MESSAGE_TAGS = {messages.ERROR: "danger"}

CUSTOM_URL_ENDPOINTS = {"limits": "limit"}
# Announcement app
ANNOUNCEMENT_DEFAULT_PLANS = [
    {
        "default": True,
        "limit": 1,
        "days": 14,
        "name": "Podstawowe",
        "description": "Możesz dodać jedno 14-dniowe ogłoszenie w ramach jednego półrocza. "
        "Po zakupie konta premium będziesz mógł podpiąć 3 ogłoszenia na stałe."
        "Pozwoli to na prowadzenie naboru np. dla seniorów, drugiej drużyny oraz grup młodzieżowych.",
    },
    {
        "default": False,
        "limit": 3,
        "days": 365,
        "name": "Premium",
        "description": "Możesz dodać trzy ogłoszenie w ramach jednego półrocza. "
        "Możesz jednocześnie prowadzić nabór np. dla seniorów, drugiej drużyny oraz grup młodzieżowych.",
    },
]

ANNOUNCEMENT_INITAL_PLAN = ANNOUNCEMENT_DEFAULT_PLANS[0]

SEASON_DEFINITION = {"middle": 7}

# Inquiries app
INQUIRIES_INITAL_PLANS = [
    {
        "default": True,
        "limit": 3,
        "name": "Basic Inital",
        "description": "Default inital plan, need to be created if we wont "
        "to add to each user UserInquery. In future can be alterd",
    },
    {
        "default": False,
        "limit": 5,
        "name": "Basic Inital for coaches",
        "description": "Default inital plan, need to be created if we wont "
        "to add to each user UserInquery. In future can be alterd",
    },
]

INQUIRIES_INITAL_PLAN = INQUIRIES_INITAL_PLANS[0]

INQUIRIES_INITAL_PLAN_COACH = INQUIRIES_INITAL_PLANS[1]


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
# ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
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
# ACCOUNT_USER_MODEL_USERNAME_FIELD = None
# ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"

ACCOUNT_FORMS = {"signup": "users.forms.CustomSignupForm"}
# ACCOUNT_ADAPTER = 'users.adapter.CustomAccountAdapter'


# Provider specific settings
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         # For each OAuth based provider, either add a ``SocialApp``
#         # (``socialaccount`` app) containing the required client
#         # credentials, or list them here:
#         'APP': {
#             'client_id': '123',
#             'secret': '456',
#             'key': ''
#         }
#     }
# }
# SOCIALACCOUNT_PROVIDERS = \
#     {'facebook':
#        {'METHOD': 'oauth2',
#         'SCOPE': ['email','public_profile', 'user_friends'],
#         'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
#         'FIELDS': [
#             'id',
#             'email',
#             'name',
#             'first_name',
#             'last_name',
#             'verified',
#             'locale',
#             'timezone',
#             'link',
#             'gender',
#             'updated_time'],
#         'EXCHANGE_TOKEN': True,
#         'LOCALE_FUNC': lambda request: 'kr_KR',
#         'VERIFIED_EMAIL': False,
#         'VERSION': 'v2.4'}
# }

# Blog settingss
BLOG_PAGINATION_PER_PAGE = 4


from os.path import join
import logging.config


def get_logging_structure(LOGFILE_ROOT):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(asctime)s] %(levelname)s [%(pathname)s:%(lineno)s] %(message)s",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "profiles_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "profiles.log"),
                "formatter": "verbose",
            },
            "data_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "data.log"),
                "formatter": "verbose",
            },
            "django_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "django.log"),
                "formatter": "verbose",
            },
            "proj_log_file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "project.log"),
                "formatter": "verbose",
            },
            "route_updater": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": join(LOGFILE_ROOT, "route.updater.log"),
                "formatter": "verbose",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "profiles": {
                "handlers": ["console", "profiles_file"],
                "level": "DEBUG",
            },
            "django": {
                "handlers": ["django_log_file"],
                "propagate": True,
                "level": "ERROR",
            },
            "project": {
                "handlers": ["proj_log_file"],
                "level": "DEBUG",
            },
            "route_updater": {
                "handlers": ["console", "route_updater"],
                "level": "DEBUG",
            },
        },
    }


# Reset logging
# (see http://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/)
LOGGING_CONFIG = None
LOGGING = get_logging_structure("_logs")
logging.config.dictConfig(LOGGING)

logger = logging.getLogger(f"project.{__name__}")


CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_ALWAYS_EAGER = True
CELERY_TASK_SERIALIZER = "pickle"
import djcelery

djcelery.setup_loader()
# Redis & stream activity
STREAM_REDIS_CONFIG = {
    "default": {"host": "127.0.0.1", "port": 6379, "db": 0, "password": None},
}

# https://pypi.org/project/django-address/


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}


GOOGLE_API_KEY = "AIzaSyAwISspDEfhVel-fTYm18Dh1EKtrD0xDH0xxxxx"
JQUERY_URL = False

# Django-countries

COUNTRIES_FIRST = ["PL", "GER", "CZ", "UA", "GB"]

from django.views.generic import RedirectView
from django.urls import include, path

# urlpatterns = patterns('',
#     url(r'^some-page/$', RedirectView.as_view(url='/')),
#     ...

CONSTANTS_DIR = os.path.join(BASE_DIR, "constants")


REDIRECTS_FILE_PATH = os.path.join(CONSTANTS_DIR, "redirects.yaml")


def load_redirects_file():
    import yaml

    try:
        with open(REDIRECTS_FILE_PATH) as f:
            data = yaml.load(f, Loader=yaml.FullLoader)
    except Exception as e:
        print(
            f"Loading redirects.yaml: No {REDIRECTS_FILE_PATH} file failed due to {e}"
        )
    return data


def build_redirections(redirects):
    return [
        path(f"{old}", RedirectView.as_view(url=new, permanent=True))
        for old, new in redirects.items()
    ]


REDIRECTS_LISTS = build_redirections(load_redirects_file())


SEO_FILE_PATH = os.path.join(CONSTANTS_DIR, "seo.yaml")

try:
    import yaml

    with open(SEO_FILE_PATH, encoding="utf8") as f:
        SEO_DATA = yaml.load(f, Loader=yaml.FullLoader)
        logger.info(f"SEO data loaded from {SEO_FILE_PATH}")
    print(f"SEO data loaded from {SEO_FILE_PATH}")
except Exception as e:
    print(f"Loading {SEO_FILE_PATH}: Not possible to write SEO_DATA due to: {e}")
    logger.info(f"Loading {SEO_FILE_PATH}: Not possible to write SEO_DATA due to: {e}")
    SEO_DATA = {}


# To force and replace season on whole system
# @todo(rkesik): not all elements supports that yet...
FORCED_SEASON_NAME = None

# User agents settings
USER_AGENTS_CACHE = "default"


# Loading of locally stored settings.

try:
    from backend.settings._local import *
except Exception as e:
    print(f"No local settings. {e}")


try:
    from backend.settings.data_settings import *
except Exception as e:
    print(f"No backend.settings.data_settings file. {e}")


if FORCED_SEASON_NAME is not None:
    print(f"Force to use season for dispaly metrics: {FORCED_SEASON_NAME}")


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


DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


VERIFICATION_FORM = {
    "DEFAULT_SEASON_NAME": "2021/2022"
}
