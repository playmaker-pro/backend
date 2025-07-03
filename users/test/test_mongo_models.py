from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, Mock

import pytest
from django.utils import timezone

from users.mongo_models import UserDailyLogin, UserLoginStreak
from utils.factories.user_factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserDailyLogin(TestCase):
    """Test suite for UserDailyLogin model core functionality."""
    
    def setUp(self):
        """Set up test case."""
        self.test_user = UserFactory.create()
        self.test_date = timezone.now().date()
    
    @patch('users.mongo_models.UserDailyLogin.objects')
    def test_increment_login_count_existing_record(self, mock_objects):
        """Test incrementing login count for existing record."""
        user_id = self.test_user.id
        login_date = self.test_date
        
        # Mock existing document
        existing_doc = Mock()
        existing_doc.login_count = 2
        existing_doc.update = Mock()
        existing_doc.reload = Mock()
        
        mock_objects.return_value.first.return_value = existing_doc
        
        with patch('users.mongo_models.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 0)
            mock_datetime.now.return_value.date.return_value = login_date
            
            # Test the method
            result = UserDailyLogin.increment_login_count(user_id, login_date)
            
            # Verify method calls
            mock_objects.assert_called_with(user_id=user_id, date=login_date)
            existing_doc.update.assert_called_with(
                inc__login_count=1,
                set__updated_at=datetime(2025, 1, 15, 10, 30, 0)
            )
            existing_doc.reload.assert_called_once()
            assert result == existing_doc
    
    @patch('users.mongo_models.UserDailyLogin.objects')
    def test_increment_login_count_new_record(self, mock_objects):
        """Test incrementing login count creates new record when none exists."""
        user_id = self.test_user.id
        login_date = self.test_date
        
        # Mock no existing document
        mock_objects.return_value.first.return_value = None
        
        with patch('users.mongo_models.datetime') as mock_datetime, \
             patch.object(UserDailyLogin, 'save') as mock_save:
            
            mock_datetime.now.return_value.date.return_value = login_date
            
            # Test the method
            result = UserDailyLogin.increment_login_count(user_id, login_date)
            
            # Verify new document was created
            assert isinstance(result, UserDailyLogin)
            assert result.user_id == user_id
            assert result.date == login_date
            assert result.login_count == 1
            mock_save.assert_called_once()
    
    @patch('users.mongo_models.UserDailyLogin.objects')
    def test_increment_login_count_uses_today_as_default(self, mock_objects):
        """Test that increment_login_count uses today's date when none provided."""
        user_id = self.test_user.id
        today = date(2025, 1, 15)
        
        mock_objects.return_value.first.return_value = None
        
        with patch('users.mongo_models.datetime') as mock_datetime, \
             patch.object(UserDailyLogin, 'save'):
            
            mock_datetime.now.return_value.date.return_value = today
            
            # Call without date parameter
            result = UserDailyLogin.increment_login_count(user_id)
            
            # Verify today's date was used
            mock_objects.assert_called_with(user_id=user_id, date=today)
            assert result.date == today


class TestUserLoginStreak(TestCase):
    """Test suite for UserLoginStreak model core functionality."""
    
    def setUp(self):
        """Set up test case."""
        self.test_user = UserFactory.create()
        self.test_date = date(2025, 1, 15)
        self.test_timestamp = datetime(2025, 1, 15, 10, 30, 0)
    
    def test_add_login_date_new_date(self):
        """Test adding a new login date."""
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[],
            current_streak=0,
            max_streak=0
        )
        
        with patch.object(streak, 'save') as mock_save, \
             patch.object(streak, '_calculate_current_streak') as mock_calc:
            
            # Add a new login date
            streak.add_login_date(self.test_date, self.test_timestamp)
            
            # Verify date was added
            assert self.test_date in streak.login_dates
            assert streak.last_login == self.test_timestamp
            mock_calc.assert_called_once()
            mock_save.assert_called_once()
    
    def test_add_login_date_duplicate_ignored(self):
        """Test that duplicate login dates are ignored."""
        existing_date = date(2025, 1, 10)
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[existing_date],
            current_streak=1,
            max_streak=1
        )
        
        with patch.object(streak, 'save') as mock_save, \
             patch.object(streak, '_calculate_current_streak') as mock_calc:
            
            # Try to add the same date again
            streak.add_login_date(existing_date, self.test_timestamp)
            
            # Verify only one instance exists
            assert streak.login_dates.count(existing_date) == 1
            mock_calc.assert_called_once()
    
    def test_calculate_current_streak_empty_dates(self):
        """Test streak calculation with no login dates."""
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[],
            current_streak=5  # Should be reset to 0
        )
        
        streak._calculate_current_streak()
        assert streak.current_streak == 0
    
    def test_calculate_current_streak_consecutive_days(self):
        """Test streak calculation with consecutive login days."""
        today = date(2025, 1, 15)
        yesterday = date(2025, 1, 14)
        day_before = date(2025, 1, 13)
        
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[day_before, yesterday, today]
        )
        
        with patch('users.mongo_models.datetime') as mock_datetime:
            mock_datetime.now.return_value.date.return_value = today
            
            streak._calculate_current_streak()
            
            # Should have 3-day streak
            assert streak.current_streak == 3
    
    def test_calculate_current_streak_gap_breaks_streak(self):
        """Test that gaps in login dates break the streak."""
        today = date(2025, 1, 15)
        three_days_ago = date(2025, 1, 12)  # Gap of 2 days
        
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[three_days_ago]
        )
        
        with patch('users.mongo_models.datetime') as mock_datetime:
            mock_datetime.now.return_value.date.return_value = today
            
            streak._calculate_current_streak()
            
            # Streak should be broken due to gap
            assert streak.current_streak == 0
    
    def test_calculate_current_streak_with_gaps_in_history(self):
        """Test streak calculation stops at first gap."""
        today = date(2025, 1, 15)
        yesterday = date(2025, 1, 14)
        # Gap here - no login on 2025-1-13
        two_days_ago = date(2025, 1, 12)
        three_days_ago = date(2025, 1, 11)
        
        streak = UserLoginStreak(
            user_id=self.test_user.id,
            login_dates=[three_days_ago, two_days_ago, yesterday, today]
        )
        
        with patch('users.mongo_models.datetime') as mock_datetime:
            mock_datetime.now.return_value.date.return_value = today
            
            streak._calculate_current_streak()
            
            # Should only count consecutive days from most recent (today + yesterday = 2)
            assert streak.current_streak == 2
    
    @patch('users.mongo_models.UserLoginStreak.objects')
    def test_update_user_streak_existing_user(self, mock_objects):
        """Test updating streak for existing user."""
        user_id = self.test_user.id
        
        # Mock existing streak document
        existing_streak = Mock()
        existing_streak.add_login_date = Mock()
        existing_streak.save = Mock()
        mock_objects.return_value.first.return_value = existing_streak
        
        with patch('users.mongo_models.datetime') as mock_datetime:
            mock_datetime.now.return_value.date.return_value = self.test_date
            mock_datetime.now.return_value = self.test_timestamp
            
            # Test the method
            result = UserLoginStreak.update_user_streak(user_id, self.test_date, self.test_timestamp)
            
            # Verify existing document was updated
            mock_objects.assert_called_with(user_id=user_id)
            existing_streak.add_login_date.assert_called_with(self.test_date, self.test_timestamp)
            existing_streak.save.assert_called_once()
            assert result == existing_streak
    
    @patch('users.mongo_models.UserLoginStreak.objects')
    def test_update_user_streak_new_user(self, mock_objects):
        """Test creating streak for new user."""
        user_id = self.test_user.id
        
        # Mock no existing document
        mock_objects.return_value.first.return_value = None
        
        with patch('users.mongo_models.datetime') as mock_datetime, \
             patch.object(UserLoginStreak, 'add_login_date') as mock_add_date, \
             patch.object(UserLoginStreak, 'save') as mock_save:
            
            mock_datetime.now.return_value.date.return_value = self.test_date
            mock_datetime.now.return_value = self.test_timestamp
            
            # Test the method
            result = UserLoginStreak.update_user_streak(user_id, self.test_date, self.test_timestamp)
            
            # Verify new document was created
            assert isinstance(result, UserLoginStreak)
            assert result.user_id == user_id
            assert result.login_dates == []
            assert result.current_streak == 0
            assert result.max_streak == 0
