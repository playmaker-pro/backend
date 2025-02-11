import pytest
from celery.contrib.testing.worker import start_worker

from app.celery import app as celery_app


@pytest.fixture(scope="session")
def celery_enable_logging():
    """Włącza logowanie Celery w testach"""
    return True


@pytest.fixture(scope="session")
def celery_worker(request):
    """Uruchamia Celery w tle podczas testów"""
    with start_worker(celery_app, perform_ping_check=False) as worker:
        yield worker
