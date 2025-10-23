"""
Tests for automatic trial activation on profile creation.
"""
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.utils.timezone import make_aware

from premium.models import (
    PremiumInquiriesProduct,
    PremiumProduct,
    PremiumProfile,
    PremiumType,
)
from utils.factories.profiles_factories import (
    ClubProfileFactory,
    CoachProfileFactory,
    PlayerProfileFactory,
)

pytestmark = [pytest.mark.django_db, pytest.mark.enable_signals]


@pytest.fixture
def timezone_now():
    with patch(
        "django.utils.timezone.now",
        return_value=make_aware(datetime(2025, 1, 1, 12, 0, 0)),
    ) as mock:
        yield mock


class TestAutoTrialActivation:
    """Test automatic trial activation when profiles are created."""

    def test_player_profile_auto_activates_trial(self, timezone_now):
        """Test that creating a player profile automatically activates trial."""
        # Create player profile - signal will trigger auto trial activation
        player = PlayerProfileFactory.create()

        # Refresh from DB to get updated data
        player.refresh_from_db()
        products = player.products

        # Verify trial was activated
        assert products.trial_tested is True
        assert products.is_profile_premium is True
        assert hasattr(products, "premium")

        premium = products.premium
        assert premium.is_trial is True
        assert premium.period == 3  # 3 days
        assert premium.is_active is True

        # Verify dates
        expected_valid_until = timezone_now.return_value + timedelta(days=3)
        assert premium.valid_since.date() == timezone_now.return_value.date()
        assert premium.valid_until.date() == expected_valid_until.date()

    def test_coach_profile_auto_activates_trial(self, timezone_now):
        """Test that creating a coach profile automatically activates trial."""
        coach = CoachProfileFactory.create()

        coach.refresh_from_db()
        products = coach.products

        # Verify trial was activated
        assert products.trial_tested is True
        assert products.is_profile_premium is True
        assert products.premium.is_trial is True
        assert products.premium.period == 3

    def test_club_profile_auto_activates_trial(self, timezone_now):
        """Test that creating a club profile automatically activates trial."""
        club = ClubProfileFactory.create()

        club.refresh_from_db()
        products = club.products

        # Verify trial was activated
        assert products.trial_tested is True
        assert products.is_profile_premium is True
        assert products.premium.is_trial is True

    def test_trial_inquiries_limit_is_10(self, timezone_now):
        """Test that trial comes with 10 queries limit."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # Verify inquiries product exists and has correct limit
        assert hasattr(products, "inquiries")
        inquiries = products.inquiries
        assert inquiries.INQUIRIES_LIMIT == 10
        assert inquiries.current_counter == 0
        assert inquiries.is_active is True
        assert inquiries.can_use_premium_inquiries is True

    def test_trial_activates_promotion(self, timezone_now):
        """Test that trial also activates profile promotion."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # Verify promotion was activated
        assert hasattr(products, "promotion")
        assert products.is_profile_promoted is True
        promotion = products.promotion
        assert promotion.is_active is True
        assert promotion.days_count == 3

    def test_player_gets_pm_score_calculation(self, timezone_now):
        """Test that player profiles get PM score calculation product."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # Verify PM score calculation exists (only for players)
        assert hasattr(products, "calculate_pm_score")

    def test_non_player_does_not_get_pm_score(self, timezone_now):
        """Test that non-player profiles don't get PM score calculation."""
        coach = CoachProfileFactory.create()

        coach.refresh_from_db()
        products = coach.products

        # Verify PM score calculation does not exist
        with pytest.raises(AttributeError):
            products.calculate_pm_score

    def test_trial_can_only_be_used_once(self, timezone_now):
        """Test that trial_tested flag prevents using trial twice."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # First trial should already be activated (via signal)
        assert products.trial_tested is True

        # Attempting to activate trial again should raise error
        with pytest.raises(ValueError, match="Trial already tested"):
            player.setup_premium_profile(PremiumType.TRIAL)

    def test_trial_duration_exactly_3_days(self, timezone_now):
        """Test that trial duration is exactly 3 days."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        premium = player.products.premium

        # Calculate actual duration
        actual_duration = (premium.valid_until - premium.valid_since).days

        assert actual_duration == 3
        assert premium.subscription_lifespan.days == 3

    def test_inquiries_counter_reset_on_trial_start(self, timezone_now):
        """Test that inquiries counter is reset when trial starts."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        inquiries = player.products.inquiries

        # Counter should be reset to 0
        assert inquiries.current_counter == 0
        assert inquiries.counter_updated_at is not None

    def test_all_premium_products_created_automatically(self, timezone_now):
        """Test that all premium products are created during trial activation."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # Verify all products exist
        assert PremiumProduct.objects.filter(pk=products.pk).exists()
        assert PremiumProfile.objects.filter(product=products).exists()
        assert PremiumInquiriesProduct.objects.filter(product=products).exists()

    def test_premium_products_linked_to_user(self, timezone_now):
        """Test that premium products are linked to the correct user."""
        player = PlayerProfileFactory.create()

        player.refresh_from_db()
        products = player.products

        # Verify user linkage
        assert products.user == player.user
        assert products.profile == player
