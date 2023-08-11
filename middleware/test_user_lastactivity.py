from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from .user_activity_middleware import UserActivityMiddleware
from users.models import User


class UserActivityMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="testuser@email.com", password="testpassword"
        )
        self.middleware = UserActivityMiddleware(
            lambda req: None
        )  # Mock the get_response

    def test_user_activity_for_authenticated_user(self):
        # Simulate a request from an authenticated user
        request = self.factory.get("/")
        request.user = self.user

        # Capture the initial last_activity before making a request
        initial_timestamp = self.user.last_activity

        self.middleware(request)
        self.user.refresh_from_db()

        # After the request, the user's last_activity should be updated
        assert self.user.last_activity != initial_timestamp

    def test_no_user_activity_for_unauthenticated_user(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()

        # Simulate a request from an unauthenticated user
        self.middleware(request)

        # Check that the user's last_activity didn't update
        self.user.refresh_from_db()
        assert self.user.last_activity is None

    def test_post_request_for_authenticated_user(self):
        request = self.factory.post("/", {"key": "value"})
        request.user = self.user

        initial_timestamp = self.user.last_activity
        self.middleware(request)
        self.user.refresh_from_db()

        assert self.user.last_activity != initial_timestamp
