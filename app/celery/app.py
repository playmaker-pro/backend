import os

from celery import Celery

from backend.settings import cfg

environment = cfg.environment

if not environment:
    raise ValueError("Environment not set")

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"backend.settings.{environment}")

app = Celery("playmaker", broker=cfg.redis.url)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
