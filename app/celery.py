import os

from celery import Celery
from django.conf import settings

from backend.settings.environment import Environment

config = Environment.DEV

try:
    from backend.settings import local

    config = local.CONFIGURATION
except:
    pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{config}")

app = Celery("playmaker", broker=settings.ENV_CONFIG.redis.url)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
