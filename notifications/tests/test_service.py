from unittest.mock import patch

import pytest
from django.utils import timezone

from notifications.models import Notification
from notifications.services import NotificationService
from premium.models import PremiumType
from profiles.models import ProfileVisitation
from utils.factories.external_links_factories import ExternalLinksEntityFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_timezone_now():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mock:
        yield mock


class TestNotifications:
    def test_notify_check_trial(self, player_profile, coach_profile) -> None:
        """
        Test the notify_check_trial function.
        """
        coach_profile.premium_products.trial_tested = True
        coach_profile.premium_products.save()
        coach_profile.refresh_from_db()

        NotificationService.bulk_notify_check_trial()

        assert Notification.objects.filter(
            target=player_profile.meta, title="Skorzystaj z wersji próbnej Premium"
        ).exists()
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Skorzystaj z wersji próbnej Premium"
        ).exists()

    def test_notify_go_premium(self, player_profile, coach_profile) -> None:
        """
        Test the notify_go_premium function.
        """
        coach_profile.setup_premium_profile(PremiumType.MONTH)
        NotificationService.bulk_notify_go_premium()

        assert Notification.objects.filter(
            target=player_profile.meta, title="Przejdź na Premium"
        ).exists()
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Przejdź na Premium"
        ).exists()

    def test_notify_verify_profile(self, player_profile, coach_profile) -> None:
        """
        Test the notify_verify_profile function.
        """
        ExternalLinksEntityFactory.create(target=player_profile.external_links)
        NotificationService.bulk_notify_verify_profile()

        assert not Notification.objects.filter(
            target=player_profile.meta, title="Zweryfikuj swój profil"
        ).exists()
        assert Notification.objects.filter(
            target=coach_profile.meta, title="Zweryfikuj swój profil"
        ).exists()

    def test_notify_profile_hidden(self, player_profile, coach_profile) -> None:
        """
        Test the notify_profile_hidden function.
        """
        player_profile.user.display_status = "Niewyświetlany"
        player_profile.user.save()
        NotificationService.bulk_notify_profile_hidden()

        assert Notification.objects.filter(
            target=player_profile.meta, title="Profil tymczasowo ukryty"
        ).exists()
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Profil tymczasowo ukryty"
        ).exists()

    def test_notyfy_premium_just_expired(
        self, coach_profile, mock_timezone_now
    ) -> None:
        """
        Test the notify_premium_just_expired function.
        """
        coach_profile.setup_premium_profile(PremiumType.MONTH)

        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Twoje konto Premium wygasło!"
        ).exists()

        mock_timezone_now.return_value = timezone.now() + timezone.timedelta(days=40)

        assert not coach_profile.is_premium
        assert Notification.objects.filter(
            target=coach_profile.meta, title="Twoje konto Premium wygasło!"
        ).exists()

    def test_notify_pm_rank(self, player_profile, coach_profile) -> None:
        """
        Test the notify_pm_rank function.
        """
        NotificationService.bulk_notify_pm_rank()

        assert Notification.objects.filter(
            target=player_profile.meta, title="Ranking PM"
        ).exists()
        assert Notification.objects.filter(
            target=coach_profile.meta, title="Ranking PM"
        ).exists()

    def test_notify_visits_summary(
        self, player_profile, coach_profile, guest_profile, scout_profile
    ) -> None:
        """
        Test the notify_visits_summary function.
        """
        ProfileVisitation.upsert(coach_profile, player_profile)
        ProfileVisitation.upsert(player_profile, guest_profile)
        ProfileVisitation.upsert(coach_profile, guest_profile)
        ProfileVisitation.upsert(scout_profile, guest_profile)
        ProfileVisitation.upsert(guest_profile, scout_profile)
        ProfileVisitation.upsert(scout_profile, player_profile)
        NotificationService.bulk_notify_visits_summary()

        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Już 2 osób wyświetliło Twój profil!",
        ).exists()
        assert not Notification.objects.filter(
            target=coach_profile.meta,
            title__icontains="osób wyświetliło Twój profil!",
        ).exists()
        assert Notification.objects.filter(
            target=guest_profile.meta,
            title="Już 3 osób wyświetliło Twój profil!",
        ).exists()
        assert Notification.objects.filter(
            target=scout_profile.meta,
            title="Już 1 osób wyświetliło Twój profil!",
        ).exists()
