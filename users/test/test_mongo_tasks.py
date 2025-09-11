from unittest import TestCase
from unittest.mock import patch

import pytest

from users.tasks import track_user_login_task
from utils.factories.user_factories import UserFactory

pytestmark = pytest.mark.django_db


class TestMongoLoginTasks(TestCase):
    """Test suite for MongoDB login tracking Celery tasks."""

    def setUp(self):
        """Set up test case."""
        self.test_user = UserFactory.create()

    @patch("users.tasks.mongo_login_service")
    def test_track_user_login_task_success(self, mock_service_class):
        """Test successful execution of track_user_login_task."""
        # Mock service instance and its methods
        mock_service_class.track_user_login.return_value = True

        user_id = self.test_user.id

        # Execute task - should complete without raising exceptions
        track_user_login_task(user_id)

        # Verify service was created and method called
        mock_service_class.track_user_login.assert_called_once_with(user_id)

    @patch("users.tasks.mongo_login_service")
    @patch("users.tasks.logger")
    def test_track_user_login_task_service_returns_false(
        self, mock_logger, mock_service_class
    ):
        """Test task when service returns False (warning should be logged)."""
        # Mock service to return False
        mock_service_class.track_user_login.return_value = False

        user_id = self.test_user.id

        # Execute task - should not raise exception despite False return
        track_user_login_task(user_id)

        # Verify service was called and warning was logged
        mock_service_class.track_user_login.assert_called_once_with(user_id)
        mock_logger.warning.assert_called_once()

    @patch("users.tasks.mongo_login_service")
    @patch("users.tasks.logger")
    def test_track_user_login_task_service_exception(
        self, mock_logger, mock_service_class
    ):
        """Test task when service raises an exception."""
        # Mock service to raise exception
        mock_service_class.track_user_login.side_effect = Exception(
            "MongoDB connection failed"
        )

        user_id = self.test_user.id

        # Execute task - should not raise exception but log error
        track_user_login_task(user_id)

        # Verify service was called and error was logged
        mock_service_class.track_user_login.assert_called_once_with(user_id)
        mock_logger.error.assert_called_once()
