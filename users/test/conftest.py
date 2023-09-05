import pytest

from users.apis import EmailAvailability


@pytest.fixture
def disable_email_check_throttle_for_test():
    """Disable throttling for email check endpoint."""
    original_throttle_classes = EmailAvailability.throttle_classes
    EmailAvailability.throttle_classes = []
    yield
    EmailAvailability.throttle_classes = original_throttle_classes
