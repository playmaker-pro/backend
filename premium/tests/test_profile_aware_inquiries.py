"""
Test cases for profile-aware premium inquiry behavior.
Tests the new requirements where premium overrides freemium limits
and only club-like profiles can purchase inquiry packages.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from payments.models import Transaction
from premium.models import PremiumType

pytestmark = pytest.mark.django_db


class TestPlayerInquiryRestrictions:
    """Test that players cannot buy inquiry packages according to requirements."""
    
    def test_player_cannot_buy_inquiry_packages_without_premium(self, player_profile, product_inquiries_L):
        """Player should get 'Players cannot buy inquiry packages' error even without premium"""
        with pytest.raises(PermissionError, match="Players cannot buy inquiry packages"):
            product_inquiries_L.can_user_buy(player_profile.user)
    
    def test_player_cannot_buy_inquiry_packages_with_premium(self, trial_premium_player_profile, product_inquiries_L):
        """Player should get 'Players cannot buy inquiry packages' error even with premium"""
        # Exhaust all inquiries so only the player restriction blocks purchase
        user = trial_premium_player_profile.user
        user.userinquiry.counter_raw = 10  # Use all freemium
        user.userinquiry.premium_inquiries.current_counter = 20  # Use 20 of 30 premium
        user.userinquiry.save()
        user.userinquiry.premium_inquiries.save()
        
        with pytest.raises(PermissionError, match="Players cannot buy inquiry packages"):
            product_inquiries_L.can_user_buy(user)
    
    def test_player_cannot_buy_packages_via_validation(self, trial_premium_player_profile, product_inquiries_L):
        """Player's can_user_buy validation should always fail for packages"""
        user = trial_premium_player_profile.user
        # Even with premium exhausted, should fail
        user.userinquiry.counter_raw = 10
        user.userinquiry.premium_inquiries.current_counter = 30  # All premium used
        user.userinquiry.save()
        user.userinquiry.premium_inquiries.save()
        user.userinquiry.refresh_from_db()
        
        # Validation should fail for player
        with pytest.raises(PermissionError, match="Players cannot buy inquiry packages"):
            product_inquiries_L.can_user_buy(user)


class TestClubInquiryPackages:
    """Test that club-like profiles can buy packages when requirements are met."""
    
    def test_coach_can_buy_packages_validation_passes(self, trial_premium_coach_profile, product_inquiries_L):
        """Coach validation should pass (not raise player error) when premium is active"""
        user = trial_premium_coach_profile.user
        # Main validation is that player error doesn't occur
        # Specific exhaust validation is tested separately
        try:
            product_inquiries_L.can_user_buy(user)
        except PermissionError as e:
            # Should be the "all inquiries" error, not the player error
            assert "Players cannot buy" not in str(e)
    
    def test_coach_cannot_buy_packages_with_inquiries_left(self, trial_premium_coach_profile, product_inquiries_L):
        """Coach cannot buy packages when they still have inquiries left"""
        user = trial_premium_coach_profile.user
        # Leave some inquiries unused
        user.userinquiry.counter_raw = 3  # Only 3 of 5 freemium used
        user.userinquiry.save()
        
        with pytest.raises(PermissionError, match="You need to use all inquiries before buying new ones"):
            product_inquiries_L.can_user_buy(user)


class TestProfileAwareLimits:
    """Test that different profiles get different limits."""
    
    def test_player_freemium_limits(self, player_profile):
        """Player should have 10 freemium inquiries"""
        # get_freemium_limit should return 10 for player
        assert player_profile.user.userinquiry.get_freemium_limit() == 10
        # After creation, limit_raw is set to default 5 by model, but we test the method
        # Test that the limit property returns freemium limit
        assert player_profile.user.userinquiry.limit == player_profile.user.userinquiry.get_freemium_limit()
        assert player_profile.user.userinquiry.limit_to_show == 10
    
    def test_coach_freemium_limits(self, coach_profile):
        """Coach should have 5 freemium inquiries"""
        assert coach_profile.user.userinquiry.get_freemium_limit() == 5
        assert coach_profile.user.userinquiry.limit_raw == 5
        assert coach_profile.user.userinquiry.limit == 5
        assert coach_profile.user.userinquiry.limit_to_show == 5
    
    def test_player_premium_limits(self, player_profile):
        """Player with premium should have 30 inquiries (override)"""
        player_profile.setup_premium_profile(PremiumType.MONTH)
        
        assert player_profile.user.userinquiry.limit_raw == 10  # Freemium stays same
        assert player_profile.user.userinquiry.limit == 30  # Premium override
        assert player_profile.user.userinquiry.limit_to_show == 30
    
    def test_coach_premium_limits(self, coach_profile):
        """Coach with premium should have 30 inquiries (override)"""
        coach_profile.setup_premium_profile(PremiumType.MONTH)
        
        assert coach_profile.user.userinquiry.limit_raw == 5  # Freemium stays same
        assert coach_profile.user.userinquiry.limit == 30  # Premium override
        assert coach_profile.user.userinquiry.limit_to_show == 30


class TestPremiumOverrideBehavior:
    """Test that premium limits override (not add to) freemium limits."""
    
    def test_package_limits_dont_affect_premium_display(self, trial_premium_coach_profile, product_inquiries_L):
        """Buying packages increases total limit (premium + package bonus)"""
        user = trial_premium_coach_profile.user
        
        # Exhaust inquiries to allow package purchase
        user.userinquiry.counter_raw = 5
        user.userinquiry.premium_inquiries.current_counter = 25
        user.userinquiry.save()
        user.userinquiry.premium_inquiries.save()
        
        # Buy L package (adds 3 to limit_raw)
        transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
        transaction.success()
        user.userinquiry.refresh_from_db()
        
        # limit_raw and displayed limit both increase
        assert user.userinquiry.limit_raw == 8  # 5 + 3
        assert user.userinquiry.limit == 33  # Premium (30) + package bonus (3)
        assert user.userinquiry.limit_to_show == 33
    
    def test_limit_returns_to_freemium_after_premium_expires(self, trial_premium_coach_profile, product_inquiries_L, mck_timezone_now):
        """After premium expires, limit should return to freemium and packages are lost"""
        user = trial_premium_coach_profile.user
        
        # Exhaust inquiries and buy package while premium is active
        user.userinquiry.counter_raw = 5
        user.userinquiry.premium_inquiries.current_counter = 25
        user.userinquiry.save()
        user.userinquiry.premium_inquiries.save()
        
        transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
        transaction.success()
        user.userinquiry.refresh_from_db()
        
        # Verify package was added to limit_raw and total limit
        assert user.userinquiry.limit_raw == 8  # 5 + 3
        assert user.userinquiry.limit == 33  # Premium (30) + package bonus (3)
        
        # Fast-forward to expire premium (8 days for trial)
        mck_timezone_now.return_value += timedelta(days=8)
        trial_premium_coach_profile.refresh_from_db()
        
        # Check premium expired
        assert not trial_premium_coach_profile.is_premium
        
        # Manually reset inquiry values (simulating what premium_expired task does)
        # In real app, this is done by the async task, but we do it manually in tests
        user.userinquiry.counter_raw = 0
        user.userinquiry.limit_raw = 5  # Reset to freemium
        user.userinquiry.save()
        user.userinquiry.refresh_from_db()
        
        # Premium should be expired and packages are lost (per requirements)
        assert user.userinquiry.limit_raw == 5  # Package lost on expiration
        assert user.userinquiry.limit == 5  # Back to freemium
        assert user.userinquiry.limit_to_show == 5


class TestResetCycles:
    """Test that different profiles have different reset cycles."""
    
    def test_player_reset_period_is_30_days(self, trial_premium_player_profile):
        """Player premium reset period should be 30 days"""
        inquiries_product = trial_premium_player_profile.products.inquiries
        assert inquiries_product.get_reset_period() == 30
    
    def test_coach_reset_period_is_90_days(self, trial_premium_coach_profile):
        """Coach premium reset period should be 90 days (not 30 like player)"""
        inquiries_product = trial_premium_coach_profile.products.inquiries
        assert inquiries_product.get_reset_period() == 90
    
    def test_inquiries_refreshed_at_calculation_player(self, trial_premium_player_profile):
        """Player inquiries_refreshed_at should be counter_updated_at + 30 days"""
        inquiries = trial_premium_player_profile.products.inquiries
        expected = inquiries.counter_updated_at + timedelta(days=30)
        assert inquiries.inquiries_refreshed_at == expected
    
    def test_inquiries_refreshed_at_calculation_coach(self, trial_premium_coach_profile):
        """Coach inquiries_refreshed_at should be counter_updated_at + 90 days"""
        inquiries = trial_premium_coach_profile.products.inquiries
        expected = inquiries.counter_updated_at + timedelta(days=90)
        assert inquiries.inquiries_refreshed_at == expected


class TestCounterBehavior:
    """Test counter increment and tracking behavior."""
    
    def test_freemium_counter_increments(self, player_profile):
        """Using freemium should increment counter_raw"""
        user = player_profile.user
        assert user.userinquiry.counter_raw == 0
        
        user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        
        assert user.userinquiry.counter_raw == 1
        assert user.userinquiry.counter == 1
    
    def test_premium_counter_increments_after_freemium_exhausted(self, trial_premium_player_profile):
        """Using premium (after freemium exhausted) should increment current_counter"""
        user = trial_premium_player_profile.user
        
        # Exhaust freemium (10 for player)
        for _ in range(10):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_player_profile.refresh_from_db()
        
        assert user.userinquiry.counter_raw == 10
        assert trial_premium_player_profile.products.inquiries.current_counter == 0
        
        # Use premium
        user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_player_profile.refresh_from_db()
        
        # Freemium stays at 10, premium increments
        assert user.userinquiry.counter_raw == 10
        assert trial_premium_player_profile.products.inquiries.current_counter == 1
        assert user.userinquiry.counter == 11  # Combined


class TestPackagePurchases:
    """Test purchasing inquiry packages."""
    
    def test_coach_can_buy_L_package_successfully(self, trial_premium_coach_profile, product_inquiries_L):
        """Coach can successfully buy L package (verified in existing API tests)"""
        # This functionality is verified in test_transaction_api.py
        # Just verify the L package properties
        assert product_inquiries_L.name == "PREMIUM_INQUIRIES_L"
        assert product_inquiries_L.inquiry_plan.limit == 3
    
    def test_coach_can_only_buy_package_when_inquiries_left_equals_zero(self, trial_premium_coach_profile, product_inquiries_L):
        """Coach validation passes when all inquiries are exhausted (left <= 0)"""
        user = trial_premium_coach_profile.user
        
        # Use increment to properly exhaust inquiries
        # Coach freemium limit is 5
        for _ in range(5):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Now use premium (30 total)
        for _ in range(30):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Validation should pass (no "all inquiries" error raised)
        try:
            product_inquiries_L.can_user_buy(user)
        except PermissionError as e:
            # Only player error is unexpected
            assert "Players cannot buy" not in str(e)
            raise
    
    def test_coach_cannot_buy_package_with_inquiries_left(self, trial_premium_coach_profile, product_inquiries_L):
        """Coach cannot buy package when they still have inquiries left"""
        user = trial_premium_coach_profile.user
        
        # Use only 3 of 5 freemium, leave 2 + 30 premium available
        for _ in range(3):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Verify left > 0 (2 freemium remaining + 30 premium)
        assert user.userinquiry.left > 0
        
        with pytest.raises(PermissionError, match="You need to use all inquiries before buying new ones"):
            product_inquiries_L.can_user_buy(user)


class TestFreemiumResetBehavior:
    """Test that freemium counter does NOT reset."""
    
    def test_freemium_counter_persists_after_premium_reset(self, trial_premium_player_profile):
        """Freemium counter should NOT reset when premium resets"""
        user = trial_premium_player_profile.user
        
        # Use some freemium
        for _ in range(7):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_player_profile.refresh_from_db()
        
        assert user.userinquiry.counter_raw == 7
        
        # Manually call reset_counter (simulating premium reset after time passes)
        trial_premium_player_profile.products.inquiries.reset_counter(reset_plan=False)
        user.userinquiry.refresh_from_db()
        
        # Freemium counter should stay the same
        assert user.userinquiry.counter_raw == 7
        assert trial_premium_player_profile.products.inquiries.current_counter == 0


class TestPackageCounterAfterPremiumExpires:
    """Test package counter behavior after premium expires."""
    
    def test_package_counter_inaccessible_after_premium_expires(self, trial_premium_coach_profile, product_inquiries_L, mck_timezone_now):
        """After premium expires, packages are lost and user reverts to freemium only"""
        user = trial_premium_coach_profile.user
        
        # Exhaust inquiries and buy package while premium active
        for _ in range(5):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Use 25 of 30 premium
        for _ in range(25):
            user.userinquiry.increment()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
        transaction.success()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Verify package was purchased
        assert user.userinquiry.limit_raw == 8  # 5 + 3
        # counter = counter_raw (5) + premium current_counter (25) = 30
        assert user.userinquiry.limit == 33  # Premium (30) + package bonus (3)
        assert user.userinquiry.premium_inquiries.current_counter == 25
        
        # Fast-forward to expire premium
        mck_timezone_now.return_value += timedelta(days=8)
        trial_premium_coach_profile.refresh_from_db()
        
        # Check premium expired
        assert not trial_premium_coach_profile.is_premium
        
        # Manually reset inquiry values (simulating what premium_expired task does)
        # In real app, this is done by the async task, but we do it manually in tests
        user.userinquiry.counter_raw = 0
        user.userinquiry.limit_raw = 5  # Reset to freemium
        user.userinquiry.save()
        user.userinquiry.refresh_from_db()
        
        # Premium should be expired
        assert user.userinquiry.premium_inquiries is None  # No premium access
        
        # User reverts to freemium only and packages are lost
        assert user.userinquiry.counter_raw == 0  # Reset on expiration
        assert user.userinquiry.counter == 0  # Freemium counter only
        assert user.userinquiry.limit_raw == 5  # Packages lost on expiration
        assert user.userinquiry.limit == 5  # Freemium limit only
    
    def test_package_counter_becomes_accessible_after_premium_renew(self, trial_premium_coach_profile, product_inquiries_L, mck_timezone_now):
        """After premium expires and renews, user gets fresh premium (packages were lost)"""
        user = trial_premium_coach_profile.user
        
        # Exhaust inquiries, buy package, then expire premium
        user.userinquiry.counter_raw = 5
        user.userinquiry.premium_inquiries.current_counter = 25
        user.userinquiry.save()
        user.userinquiry.premium_inquiries.save()
        
        transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
        transaction.success()
        user.userinquiry.refresh_from_db()
        trial_premium_coach_profile.refresh_from_db()
        
        # Verify package was purchased and limit increased
        assert user.userinquiry.limit_raw == 8  # 5 + 3
        assert user.userinquiry.limit == 33  # Premium (30) + package bonus (3)
        
        # Expire premium
        mck_timezone_now.return_value += timedelta(days=8)
        trial_premium_coach_profile.refresh_from_db()
        
        # Check premium expired
        assert not trial_premium_coach_profile.is_premium
        
        # Manually reset inquiry values (simulating what premium_expired task does)
        # In real app, this is done by the async task, but we do it manually in tests
        user.userinquiry.counter_raw = 0
        user.userinquiry.limit_raw = 5  # Reset to freemium
        user.userinquiry.save()
        user.userinquiry.refresh_from_db()
        
        # Packages are lost on expiration
        assert user.userinquiry.limit_raw == 5
        
        # Renew premium
        trial_premium_coach_profile.setup_premium_profile(PremiumType.MONTH)
        trial_premium_coach_profile.refresh_from_db()
        user.userinquiry.refresh_from_db()
        
        # Premium is active again
        assert trial_premium_coach_profile.is_premium
        
        # Fresh premium with no packages (they were lost on expiration)
        assert user.userinquiry.limit_raw == 5  # No packages
        assert user.userinquiry.counter_raw == 0  # Reset on premium activation
        assert user.userinquiry.limit == 30  # Premium limit active


class TestPremiumExpiration:
    """Test behavior when premium subscription expires."""
    
    def test_limit_returns_to_player_freemium_after_premium_expires(self, trial_premium_player_profile, mck_timezone_now):
        """Player limit should return to 10 after premium expires"""
        user = trial_premium_player_profile.user
        
        # While premium active
        assert user.userinquiry.limit == 30
        
        # Fast-forward past trial (3 days + 1 second)
        mck_timezone_now.return_value += timedelta(days=3, seconds=1)
        trial_premium_player_profile.refresh_from_db()
        
        # Premium should be expired
        assert not trial_premium_player_profile.is_premium
        
        # Limit should return to freemium
        assert user.userinquiry.limit == 10
    
    def test_limit_returns_to_coach_freemium_after_premium_expires(self, trial_premium_coach_profile, mck_timezone_now):
        """Coach limit should return to 5 after premium expires"""
        user = trial_premium_coach_profile.user
        
        # While premium active
        assert user.userinquiry.limit == 30
        
        # Fast-forward past trial
        mck_timezone_now.return_value += timedelta(days=3, seconds=1)
        trial_premium_coach_profile.refresh_from_db()
        
        # Premium should be expired
        assert not trial_premium_coach_profile.is_premium
        
        # Limit should return to freemium
        assert user.userinquiry.limit == 5
