"""
Main configuration file for pytest. Due to the nature of the Pytest,
parser configuration works only when conftest.py is in the root directory:
https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_addoption.

Functions below are taken from the official documentation.

Main purpose of functions is to skip marked tests when running with specific flag (--runslow).
"""  # noqa: E501
from unittest.mock import patch

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from utils.factories import UserFactory


def pytest_addoption(parser):
    """Add custom option to pytest."""
    parser.addoption(
        "--allow-skipped", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    """Add additional marker to pytest."""
    config.addinivalue_line("markers", "mute: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests if --allow-skipped flag is not given."""
    if config.getoption("--allow-skipped"):
        return
    skip_slow = pytest.mark.skip(reason="need --allow-skipped option to run")
    for item in items:
        if "mute" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(autouse=True)
def system_user():
    """Create system user before running tests."""
    with patch("django.db.models.signals.post_save", return_value=None) as mck:
        UserFactory.create(email=settings.SYSTEM_USER_EMAIL)


@pytest.fixture(autouse=True)
def api_client():
    """Create api client before running tests."""
    return APIClient()
