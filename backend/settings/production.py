from .base import *  # noqa

DEBUG = False

BASE_URL = "https://be.playmaker.pro"


COMPRESS_ENABLED = True


MANAGERS = [
    ("Rafal", "rafal.kesik@gmail.com"),
    ("Jacek", "jjasinski.playmaker@gmail.com"),
]


ADMINS = MANAGERS


COMPRESS_OFFLINE = True


STATIC_ROOT = os.path.join(BASE_DIR, "public", "static")


MEDIA_ROOT = os.path.join(BASE_DIR, "public", "media")


MEMCACHED_CACHE_SOCK = None


try:
    from .local import *
except Exception as e:
    print(f"Error while importing local settings: {e}")


# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
#         "LOCATION": MEMCACHED_CACHE_SOCK,
#     }
# }
