"""
Main configuration file for pytest. Due to the nature of the Pytest,
parser configuration works only when conftest.py is in the root directory:
https://docs.pytest.org/en/6.2.x/reference.html#pytest.hookspec.pytest_addoption.

Functions below are taken from the official documentation.

Main purpose of functions is to skip marked tests when running with specific flag (--runslow).
"""  # noqa: E501

import pytest


def pytest_addoption(parser):
    """Add custom option to pytest."""
    parser.addoption(
        "--allow-skipped", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    """Add additional marker to pytest."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    """Skip slow tests if --allow-skipped flag is not given."""
    if config.getoption("--allow-skipped"):
        return
    skip_slow = pytest.mark.skip(reason="need --allow-skipped option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
