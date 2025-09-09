from datetime import timedelta
from unittest import TestCase
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone

from users.mongo_login_service import MongoLoginService
from utils.factories.user_factories import UserFactory

pytestmark = pytest.mark.django_db


class TestMongoLoginService(TestCase):
    """Test suite for MongoLoginService core functionality."""

    def setUp(self):
        """Set up test case with mocked MongoDB operations."""
        self.test_user = UserFactory.create()

        # Mock MongoDB-related functionality
        self.mongodb_patcher = patch("users.mongo_login_service.mongoengine")
        self.settings_patcher = patch("users.mongo_login_service.settings")

        self.mock_mongoengine = self.mongodb_patcher.start()
        self.mock_settings = self.settings_patcher.start()

        # Mock MongoDB settings
        self.mock_settings.MONGODB_SETTINGS = {
            "db": "test_db",
            "host": "localhost",
            "port": 27017,
        }

        # Initialize service with mocked MongoDB
        self.service = MongoLoginService()

    def tearDown(self):
        """Clean up after each test."""
        self.mongodb_patcher.stop()
        self.settings_patcher.stop()

    @patch("users.mongo_login_service.UserDailyLogin")
    @patch("users.mongo_login_service.UserLoginStreak")
    def test_track_user_login_success(self, mock_streak_class, mock_daily_login_class):
        """Test successful user login tracking."""
        user_id = self.test_user.id

        # Mock successful database operations
        mock_daily_login_class.increment_login_count.return_value = Mock(
            login_count=1, date=timezone.now().date()
        )
        mock_streak_class.update_user_streak.return_value = Mock(
            current_streak=1, max_streak=1
        )

        # Test the service method
        result = self.service.track_user_login(user_id)

        # Verify result and method calls
        assert result is True
        mock_daily_login_class.increment_login_count.assert_called_once()
        mock_streak_class.update_user_streak.assert_called_once()

    @patch("users.mongo_login_service.UserDailyLogin")
    def test_track_user_login_database_error(self, mock_daily_login_class):
        """Test login tracking handles database errors gracefully."""
        user_id = self.test_user.id

        # Mock database error
        mock_daily_login_class.increment_login_count.side_effect = Exception(
            "Database error"
        )

        # Test error handling
        result = self.service.track_user_login(user_id)

        assert result is False

    @patch("users.mongo_login_service.UserDailyLogin")
    def test_get_user_login_count_found(self, mock_daily_login_class):
        """Test getting login count for existing user."""
        user_id = self.test_user.id
        target_date = timezone.now().date()

        # Mock finding a login record
        mock_login = Mock()
        mock_login.login_count = 5
        mock_daily_login_class.objects.return_value.first.return_value = mock_login

        # Test the method
        count = self.service.get_user_login_count(user_id, target_date)

        assert count == 5
        mock_daily_login_class.objects.assert_called_with(
            user_id=user_id, date=target_date
        )

    @patch("users.mongo_login_service.UserDailyLogin")
    def test_get_user_login_count_not_found(self, mock_daily_login_class):
        """Test getting login count when no record exists."""
        user_id = self.test_user.id

        # Mock no record found
        mock_daily_login_class.objects.return_value.first.return_value = None

        # Test the method
        count = self.service.get_user_login_count(user_id)

        assert count == 0

    @patch("users.mongo_login_service.UserLoginStreak")
    def test_get_user_login_streak_found(self, mock_streak_class):
        """Test getting login streak for existing user."""
        user_id = self.test_user.id

        # Mock streak record
        mock_streak = Mock()
        mock_streak.current_streak = 7
        mock_streak._calculate_current_streak = Mock()
        mock_streak.save = Mock()
        mock_streak_class.objects.return_value.first.return_value = mock_streak

        # Test the method
        streak = self.service.get_user_login_streak(user_id)

        assert streak == 7
        mock_streak._calculate_current_streak.assert_called_once()
        mock_streak.save.assert_called_once()

    @patch("users.mongo_login_service.UserDailyLogin")
    def test_get_all_users_login_history(self, mock_daily_login_class):
        """Test getting paginated login history for all users."""
        start_date = timezone.now().date() - timedelta(days=7)
        end_date = timezone.now().date()

        # Mock login records
        mock_login1 = Mock(user_id=1, date=end_date, login_count=2)
        mock_login2 = Mock(user_id=2, date=end_date, login_count=1)

        # Mock the query chain
        mock_limit = Mock()
        mock_limit.__iter__ = lambda x: iter([mock_login1, mock_login2])

        mock_skip = Mock()
        mock_skip.limit.return_value = mock_limit

        mock_order_by = Mock()
        mock_order_by.skip.return_value = mock_skip

        mock_query = Mock()
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_order_by

        mock_daily_login_class.objects.return_value = mock_query

        # Test the method
        result = self.service.get_all_users_login_history(start_date, end_date)

        # Test the paginated response structure
        assert isinstance(result, dict)
        assert "data" in result
        assert "total_count" in result
        assert "limit" in result
        assert "offset" in result
        assert "has_more" in result

        # Test the actual data
        history = result["data"]
        assert len(history) == 2
        assert history[0]["user_id"] == 1
        assert history[1]["user_id"] == 2

        # Test pagination metadata
        assert result["total_count"] == 2
        assert result["limit"] == 1000  # Default limit
        assert result["has_more"] is False

    @patch("users.mongo_login_service.UserDailyLogin")
    def test_get_user_login_history_paginated(self, mock_daily_login_class):
        """Test getting paginated login history for a specific user."""
        user_id = self.test_user.id

        # Mock login records
        mock_login1 = Mock(date=timezone.now().date(), login_count=3)
        mock_login2 = Mock(
            date=timezone.now().date() - timedelta(days=1), login_count=2
        )

        # Mock the query chain
        mock_limit = Mock()
        mock_limit.__iter__ = lambda x: iter([mock_login1, mock_login2])

        mock_skip = Mock()
        mock_skip.limit.return_value = mock_limit

        mock_order_by = Mock()
        mock_order_by.skip.return_value = mock_skip

        mock_query = Mock()
        mock_query.count.return_value = 10  # Total records
        mock_query.order_by.return_value = mock_order_by

        mock_daily_login_class.objects.return_value = mock_query

        # Test the method with pagination
        result = self.service.get_user_login_history_paginated(
            user_id, limit=2, offset=0
        )

        # Test the paginated response structure
        assert "data" in result
        assert "total_count" in result
        assert "has_more" in result

        # Test pagination metadata
        assert result["total_count"] == 10
        assert result["has_more"] is True

    @patch("users.mongo_login_service.mongoengine")
    def test_service_with_mocked_connection(self, mock_mongoengine):
        """Test MongoLoginService initialization with new connection logic."""
        # Reset class-level flags to force reconnection
        MongoLoginService._connection_tested = False

        # Mock the connection health check to force reconnection logic
        with patch.object(
            MongoLoginService, "_is_connection_healthy", return_value=False
        ):
            # Mock the internal connection test to simulate success
            with patch.object(MongoLoginService, "_test_connection", return_value=True):
                MongoLoginService()

                # Verify that a new connection was attempted
                mock_mongoengine.connect.assert_called_once()

                # Get the actual arguments passed to connect()
                args, kwargs = mock_mongoengine.connect.call_args

                # Verify the connection alias and optimization settings
                assert kwargs["alias"] == "user_login_tracking"
                assert "maxPoolSize" in kwargs
                assert "minPoolSize" in kwargs

        # Verify that subsequent calls don't reconnect if healthy
        with patch.object(
            MongoLoginService, "_is_connection_healthy", return_value=True
        ):
            mock_mongoengine.reset_mock()
            MongoLoginService()
            mock_mongoengine.connect.assert_not_called()
