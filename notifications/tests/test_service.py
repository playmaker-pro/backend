import pytest

from notifications.services import NotificationService
from premium.models import PremiumType
from utils.factories.profiles_factories import PlayerProfileFactory


@pytest.fixture
def profile():
    """Create a player profile."""
    return PlayerProfileFactory.create()


class TestNotificationService:
    def test_welcome_notification(self, profile):
        """Test welcome notification."""

        assert profile.meta.notifications.filter(title="Witaj w PlayMaker!").exists()

    @pytest.mark.parametrize("trial_tested", [True, False])
    def test_check_trial_premium_notification(self, profile, trial_tested):
        if trial_tested:
            products = profile.products
            products.trial_tested = True
            products.save()

        NotificationService.bulk_notify_check_trial()
        notification_exists = profile.meta.notifications.filter(
            title="Skorzystaj z wersji próbnej Premium"
        ).exists()

        if trial_tested:
            profile.products.trial_tested = True
            assert notification_exists is False
        else:
            profile.products.trial_tested = False
            assert notification_exists is True

    @pytest.mark.parametrize("premium_enabled", [True, False])
    def test_go_premium_notification(self, profile, premium_enabled):
        if premium_enabled:
            profile.setup_premium_profile(
                PremiumType.YEAR,
            )

        NotificationService.bulk_notify_go_premium()
        profile.refresh_from_db()
        notification_exists = profile.meta.notifications.filter(
            title="Przejdź na Premium"
        ).exists()

        if premium_enabled:
            assert notification_exists is False
        else:
            assert notification_exists is True

    # @pytest.mark.parametrize("verification_done", [True, False])
    # def test_verify_profile_notification(self, profile):
    #     ...
    # if verification_done:
    #     profile.verification_stage = verification_stage
    #     profile.verification_stage.done = True
    #     profile.verification_stage.save()

    # NotificationService.bulk_notify_verify_profile()
    # notification_exists = profile.meta.notifications.filter(
    #     title="Zweryfikuj swój profil"
    # ).exists()

    # if verification_done:
    #     assert notification_exists is False
    # else:
    #     assert notification_exists is True
