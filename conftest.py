"""
Main configuration file for pytest. Due to the nature of the Pytest,
parser configuration works only when conftest.py is in the root directory:
https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_addoption.

Functions below are taken from the official documentation.

Main purpose of functions is to skip marked tests when running with specific flag (--runslow).
"""  # noqa: E501
from typing import Callable, Optional
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
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
    with patch(
        "django.db.models.signals.post_save", return_value=None
    ) as mck:  # noqa: F841, E501
        UserFactory.create(email=settings.SYSTEM_USER_EMAIL)


@pytest.fixture(autouse=True)
def api_client():
    """Create api client before running tests."""
    return APIClient()


@pytest.fixture
def uploaded_file(tmpdir) -> SimpleUploadedFile:
    """Create a temporary file with content for testing purposes"""
    file_content = b"Test file content"
    file_path = tmpdir.join("test_file.txt")
    file_path.write(file_content)
    # Create an instance of SimpleUploadedFile to simulate an uploaded file
    return SimpleUploadedFile("test_file.txt", file_content)


@pytest.fixture
def user_factory_fixture() -> Callable:
    """Create a user for testing purposes."""

    def return_user(password: Optional[str] = None):
        if password is None:
            return UserFactory.create()
        return UserFactory.create(password=password)

    return return_user


@pytest.fixture
def mute_signals(request):
    # Skip applying, if marked with `enabled_signals`
    if "enable_signals" in request.keywords:
        return

    signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
    restore = {}
    for signal in signals:
        # Temporally remove the signal's receivers (a.k.a attached functions)
        restore[signal] = signal.receivers
        signal.receivers = []

    def restore_signals():
        # When the test tears down, restore the signals.
        for signal, receivers in restore.items():
            signal.receivers = receivers

    # Called after a test has finished.
    request.addfinalizer(restore_signals)
