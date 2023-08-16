from django.http import HttpRequest
from django.test import TestCase, RequestFactory
from .user_activity_middleware import UserActivityMiddleware
from users.models import User
from unittest.mock import patch, Mock, PropertyMock
from datetime import datetime
from typing import Optional, Dict, Any


class UserActivityMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="testuser@email.com", password="testpassword"
        )
        self.middleware = UserActivityMiddleware(
            lambda req: None
        )  # Mock the get_response

    def _assert_last_activity_updated(
        self, initial_timestamp: Optional[datetime]
    ) -> None:
        """
        Helper method to check that the user's last_activity timestamp has been updated.
        """
        # Refresh user from database to get updated last_activity
        self.user.refresh_from_db()

        # Check that the user's last_activity was updated
        assert self.user.last_activity != initial_timestamp

    def _test_request_for_authenticated_user(
        self, method: str, data: Optional[Dict[str, Any]] = None
    ):
        """
        Helper method to test an authenticated user's request.
        """
        request_method = getattr(self.factory, method.lower())
        request = request_method("/", data if data else {})
        request.user = self.user
        initial_timestamp = self.user.last_activity
        self.middleware(request)
        self._assert_last_activity_updated(initial_timestamp)

    def test_user_activity_for_authenticated_user_get(self):
        """
        Test that an authenticated user's last_activity timestamp is updated after a GET request.
        """
        self._test_request_for_authenticated_user("get")

    def test_user_activity_for_authenticated_user_post(self):
        """
        Test that an authenticated user's last_activity timestamp is updated after a POST request.
        """
        self._test_request_for_authenticated_user("post", {"key": "value"})

    def test_user_activity_for_authenticated_user_delete(self):
        """
        Test that an authenticated user's last_activity timestamp is updated after a DELETE request.
        """
        self._test_request_for_authenticated_user("delete")

    def test_patch_request_for_authenticated_user(self):
        """
        Test that an authenticated user's last_activity timestamp is updated after a PATCH request.
        """
        self._test_request_for_authenticated_user("patch", {"key": "value"})

    def test_middleware_handles_exception_gracefully(self):
        """
        Test to ensure the middleware handles exceptions thrown during the
        updating of user activity without propagating them to the caller.
        """
        with patch.object(self.user, "new_user_activity", side_effect=Exception):
            request = self.factory.get("/")
            request.user = self.user
            # Should not raise any exception
            self.middleware(request)


class LoggerTest(TestCase):
    """
    Test for ensuring the correct behavior of logging in the UserActivityMiddleware.
    """

    @patch.object(
        HttpRequest,
        "user",
        create=True,
        new_callable=PropertyMock,
        return_value=Mock(
            is_authenticated=True,
            new_user_activity=Mock(side_effect=Exception("Some error")),
        ),
    )
    @patch("webapp.middleware.user_activity_middleware.logger")
    def test_logger_error_called(self, mock_logger, mock_user):
        """
        Tests that an error is correctly logged when there's an exception while
        updating the user's activity.
        """
        # Setup conditions
        request = HttpRequest()
        middleware = UserActivityMiddleware(lambda req: None)

        # Call the middleware, which should trigger the logger
        middleware(request)

        # Check the logger call
        mock_logger.error.assert_called_once_with(
            "Error updating user activity: Some error"
        )
