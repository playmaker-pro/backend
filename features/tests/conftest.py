import pytest

from features.api_views import FeatureElementAPI


@pytest.fixture
def disable_throttle_for_feature_notification_test():
    """Disable throttling for email check endpoint."""
    original_throttle_classes = FeatureElementAPI.throttle_classes
    FeatureElementAPI.throttle_classes = []
    yield
    FeatureElementAPI.throttle_classes = original_throttle_classes
