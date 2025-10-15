import os
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
from django.conf import settings
from django.utils import timezone

from followers.services import FollowService
from inquiries.models import InquiryRequest
from notifications.models import Notification
from notifications.services import NotificationService
from notifications.templates import NotificationBody
from premium.models import PremiumType
from profiles.models import ProfileVisitation
from profiles.services import NotificationService
from utils import factories

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_timezone_now():
    with patch("django.utils.timezone.now", return_value=timezone.now()) as mock:
        yield mock


class TestNotifications:
    def assert_notification(self, template, meta):
        notification = Notification.objects.filter(
            title=template["title"],
            description=template["description"],
            href=template["href"],
            icon=template.get("icon"),
            target=meta,
        )
        assert notification.exists()

    def test_notify_check_trial(self, player_profile, coach_profile):
        """
        Test the notify_check_trial function.
        """
        coach_profile.premium_products.trial_tested = True
        coach_profile.premium_products.save()
        coach_profile.refresh_from_db()

        NotificationService.bulk_notify_check_trial()

        self.assert_notification(
            {
                "title": "Skorzystaj z wersji próbnej Premium",
                "description": "Wypróbuj 3 dni premium za darmo!",
                "href": "/premium",
                "icon": "premium",
            },
            player_profile.meta,
        )
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Skorzystaj z wersji próbnej Premium"
        ).exists()

    def test_notify_go_premium(self, player_profile, coach_profile) -> None:
        """
        Test the notify_go_premium function.
        """
        coach_profile.setup_premium_profile(PremiumType.MONTH)
        NotificationService.bulk_notify_go_premium()
        self.assert_notification(
            {
                "title": "Przejdź na Premium",
                "description": "Sprawdź wszystkie możliwości i zyskaj przewagę!",
                "href": "/premium",
                "icon": "premium",
            },
            player_profile.meta,
        )
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Przejdź na Premium"
        ).exists()

    def test_notify_verify_profile(self, player_profile, coach_profile) -> None:
        """
        Test the notify_verify_profile function.
        """
        factories.ExternalLinksEntityFactory.create(
            target=player_profile.external_links
        )
        NotificationService.bulk_notify_verify_profile()
        assert not Notification.objects.filter(
            target=player_profile.meta, title="Zweryfikuj swój profil"
        ).exists()
        self.assert_notification(
            {
                "title": "Zweryfikuj swój profil",
                "description": "Dodaj linki do profili piłkarskich i zweryfikuj swój profil.",
                "href": "/ustawienia",
                "icon": "links",
            },
            coach_profile.meta,
        )

    def test_notify_profile_hidden(self, player_profile, coach_profile) -> None:
        """
        Test the notify_profile_hidden function.
        """
        player_profile.user.display_status = "Niewyświetlany"
        player_profile.user.save()
        NotificationService.bulk_notify_profile_hidden()
        self.assert_notification(
            {
                "title": "Profil tymczasowo ukryty",
                "description": "Popraw informacje w profilu (imię, nazwisko, zdjęcie), aby przywrócić widoczność.",
                "href": "?modal=profile-hidden",
                "icon": "hidden",
            },
            player_profile.meta,
        )
        assert not Notification.objects.filter(
            target=coach_profile.meta, title="Profil tymczasowo ukryty"
        ).exists()

    def test_notify_premium_just_expired(
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
        self.assert_notification(
            {
                "title": "Ranking PM",
                "description": "Sprawdź, kto ma najwyższy PM Score w tym miesiacu",
                "href": "/premium",
                "icon": "pm-rank",
            },
            player_profile.meta,
        )
        self.assert_notification(
            {
                "title": "Ranking PM",
                "description": "Sprawdź, kto ma najwyższy PM Score w tym miesiacu",
                "href": "/premium",
                "icon": "pm-rank",
            },
            coach_profile.meta,
        )

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
            title="Już {visited_by_count} osób wyświetliło Twój profil!",
            description="Kliknij tutaj, aby zobaczyc kto to.",
            href="/wyswietlenia",
            icon="eye",
        ).exists()
        assert not Notification.objects.filter(
            target=coach_profile.meta,
            title__icontains="osób wyświetliło Twój profil!",
        ).exists()
        assert Notification.objects.filter(
            target=guest_profile.meta,
            title="Już {visited_by_count} osób wyświetliło Twój profil!",
            description="Kliknij tutaj, aby zobaczyc kto to.",
            href="/wyswietlenia",
            icon="eye",
        ).exists()
        assert Notification.objects.filter(
            target=scout_profile.meta,
            title="Już {visited_by_count} osób wyświetliło Twój profil!",
            description="Kliknij tutaj, aby zobaczyc kto to.",
            href="/wyswietlenia",
            icon="eye",
        ).exists()

    def test_notify_welcome(self, player_profile):
        """
        Test the notify_welcome function.
        """
        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Witaj w PlayMaker!",
            description="Dziękujemy za dołączenie do społeczności, Twoja podróż zaczyna się tutaj! Sprawdź, co daje Ci PlayMaker!",
            href="?modal=welcome",
            icon="playmaker",
        ).exists()

    def test_notify_new_follower(self, player_profile, coach_profile):
        """
        Test the notify_new_follower function.
        """
        FollowService().follow_profile(player_profile.uuid, coach_profile.user)

        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Ktoś Cię obserwuje",
            description="Zobacz kto zaobserwował Twój profil.",
            href="/obserwowani?tab=obserwatorzy",
            icon="star",
        ).exists()

    def test_notify_inquiry_accepted(self, player_profile, coach_profile):
        """
        Test the notify_inquiry_accepted function.
        """
        inquiry = InquiryRequest.objects.create(
            sender=coach_profile.user, recipient=player_profile.user
        )
        inquiry.accept()
        inquiry.save()

        assert Notification.objects.filter(
            target=coach_profile.meta,
            title__icontains="zaakceptował twoje zaproszenie",
            description="Kliknij, aby sprawdzic odpowiedz.",
            href="/kontakty?tab=kontakty",
            icon="inquiry-accepted",
        ).exists()

    def test_notify_inquiry_rejected(self, player_profile, coach_profile):
        """
        Test the notify_inquiry_rejected function.
        """
        inquiry = InquiryRequest.objects.create(
            sender=coach_profile.user, recipient=player_profile.user
        )
        inquiry.reject()
        inquiry.save()

        assert Notification.objects.filter(
            target=coach_profile.meta,
            title__icontains="odrzucił twoje zaproszenie",
            description="Kliknij, aby sprawdzic odpowiedz.",
            href="/kontakty?tab=zapytania&subtab=wyslane",
            icon="inquiry-rejected",
        ).exists()

    def test_notify_inquiry_read(self, player_profile, coach_profile):
        """
        Test the notify_inquiry_read function.
        """
        inquiry = InquiryRequest.objects.create(
            sender=coach_profile.user, recipient=player_profile.user
        )
        inquiry.read()
        inquiry.save()

        assert Notification.objects.filter(
            target=coach_profile.meta,
            title__icontains="odczytał twoje zaproszenie",
            description="Kliknij, aby sprawdzic odpowiedz.",
            href="/kontakty?tab=zapytania&subtab=wyslane",
            icon="inquiry",
        ).exists()

    def test_notify_profile_visited(self, player_profile, coach_profile):
        """
        Test the notify_profile_visited function.
        """
        ProfileVisitation.upsert(player_profile, coach_profile)

        notiification = Notification.objects.filter(
            title="Wyświetlono twój profil",
            description="Kliknij tutaj, aby zobaczyc kto to.",
            href="/wyswietlenia",
            icon="eye",
        )
        assert not notiification.filter(target=player_profile.meta).exists()
        assert notiification.filter(target=coach_profile.meta).exists()

    def test_notify_set_transfer_requests(
        self, player_profile, coach_profile, scout_profile, guest_profile, club_profile
    ):
        """
        Test the notify_set_transfer_requests function.
        """
        NotificationService.bulk_notify_set_transfer_requests()
        notification = Notification.objects.filter(
            title="Ustaw zapotrzebowanie transferowe!",
            description="Kliknij tutaj, aby ustawic swoje zapotrzebowanie.",
            href="/profil",
            icon="transfer",
        )

        assert not notification.filter(target=player_profile.meta).exists()
        assert notification.filter(target=coach_profile.meta).exists()
        assert not notification.filter(target=scout_profile.meta).exists()
        assert not notification.filter(target=guest_profile.meta).exists()
        assert notification.filter(target=club_profile.meta).exists()

    def test_notify_set_status(
        self, player_profile, coach_profile, scout_profile, guest_profile, club_profile
    ):
        """
        Test the notify_set_status function.
        """
        NotificationService.bulk_notify_set_status()
        notification = Notification.objects.filter(
            title="Ustaw status transferowy",
            description="Kliknij tutaj, aby ustawic swój status.",
            href="/profil",
            icon="transfer",
        )

        assert notification.filter(target=player_profile.meta).exists()
        assert not notification.filter(target=coach_profile.meta).exists()
        assert not notification.filter(target=scout_profile.meta).exists()
        assert not notification.filter(target=guest_profile.meta).exists()
        assert not notification.filter(target=club_profile.meta).exists()

    def test_notify_invite_friends(self, player_profile):
        """
        Test the notify_invite_friends function.
        """
        NotificationService(player_profile.meta).notify_invite_friends()
        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Zaproś znajomych",
            description="Zapraszaj i wygrywaj nagrody!",
            href="/moje-konto/zapros",
            icon="send",
        ).exists()

    @pytest.mark.parametrize(
        "fixture_name,has_links",
        (
            ("player_profile", True),
            ("coach_profile", True),
            ("scout_profile", False),
            ("club_profile", True),
            ("guest_profile", False),
        ),
    )
    def test_notify_add_links(self, fixture_name, request, has_links):
        """
        Test the notify_add_links function.
        """
        profile = request.getfixturevalue(fixture_name)
        if has_links:
            profile.external_links.links.create(url="https://example.com")
        else:
            profile.external_links.links.all().delete()

        NotificationService.bulk_notify_add_links()
        assert (
            Notification.objects.filter(
                target=profile.meta,
                title="Dodaj linki",
                description="Kliknij tutaj, aby przejść do profilu.",
                href="/profil#sekcja-linki",
                icon="links",
            ).exists()
            is not has_links
        )

    @pytest.mark.parametrize(
        "fixture_name, should_receive_notification, has_video",
        (
            (
                "player_profile",
                True,
                False,
            ),  # PlayerProfile without video should get notification
            (
                "player_profile",
                False,
                True,
            ),  # PlayerProfile with video should NOT get notification
            (
                "coach_profile",
                False,
                False,
            ),  # CoachProfile should never get notification
            (
                "scout_profile",
                False,
                False,
            ),  # ScoutProfile should never get notification
            ("club_profile", False, False),  # ClubProfile should never get notification
            (
                "guest_profile",
                False,
                False,
            ),  # GuestProfile should never get notification
        ),
    )
    def test_notify_add_video(
        self, fixture_name, request, should_receive_notification, has_video
    ):
        """
        Test the notify_add_video function - should only notify PlayerProfile users without videos.
        """
        profile = request.getfixturevalue(fixture_name)
        if has_video:
            profile.user.user_video.create(url="https://example.com/video.mp4")
        else:
            profile.user.user_video.all().delete()  # Ensure no videos exist

        NotificationService.bulk_notify_add_video()
        notification_exists = Notification.objects.filter(
            target=profile.meta,
            title="Dodaj video",
            description="Kliknij tutaj, aby przejść do profilu.",
            href="/profil#sekcja-video-z-gry",
            icon="video",
        ).exists()

        assert notification_exists == should_receive_notification

    @pytest.mark.parametrize(
        "fixture_name,has_team_history",
        (
            ("player_profile", True),
            ("coach_profile", False),
            ("scout_profile", False),
            ("club_profile", False),
            ("guest_profile", False),
        ),
    )
    def test_notify_assign_club(self, fixture_name, request, has_team_history):
        """
        Test the notify_assign_club function.
        """
        profile = request.getfixturevalue(fixture_name)
        profile.team_history_object = (
            factories.TeamHistoryFactory.create() if has_team_history else None
        )
        profile.save()

        NotificationService(profile.meta).bulk_notify_assign_club()
        assert (
            Notification.objects.filter(
                target=profile.meta,
                title="Dodaj aktualną drużynę",
                description="Kliknij tutaj, aby przejść do profilu.",
                href="/profil#sekcja-kariera",
                icon="club",
            ).exists()
            is not has_team_history
        )

    def test_notify_new_inquiry(self, player_profile, coach_profile):
        """
        Test the notify_new_inquiry function.
        """
        InquiryRequest.objects.create(
            sender=coach_profile.user, recipient=player_profile.user
        )

        assert Notification.objects.filter(
            target=player_profile.meta,
            title__icontains="Otrzymałeś/aś nowe zapytanie",
            description__icontains="wysłał Ci zapytanie o kontakt.",
            href="/kontakty?tab=zapytania",
            icon="inquiry",
        ).exists()

    def test_notify_profile_verified(self, player_profile):
        """
        Test the notify_profile_verified function.
        """
        NotificationService(player_profile.meta).notify_profile_verified()
        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Twój profil został zweryfikowany!",
            description="Potwierdziliśmy Twoją tożsamość. Korzystaj z PLAYMAKER.pro bez ograniczeń!",
            href="/profil",
            icon="success",
        ).exists()

    def test_profile_verified_after_setting_the_links(self, player_profile):
        """
        Test that profile verification notification is sent after setting links.
        """
        assert not Notification.objects.filter(
            target=player_profile.meta,
            title="Twój profil został zweryfikowany!",
            description="Potwierdziliśmy Twoją tożsamość. Korzystaj z PLAYMAKER.pro bez ograniczeń!",
            href="/profil",
            icon="success",
        ).exists()

        player_profile.external_links.links.create(
            url="https://example.com", target=player_profile.external_links
        )

        assert Notification.objects.filter(
            target=player_profile.meta,
            title="Twój profil został zweryfikowany!",
            description="Potwierdziliśmy Twoją tożsamość. Korzystaj z PLAYMAKER.pro bez ograniczeń!",
            href="/profil",
            icon="success",
        ).exists()

    def test_notification_with_picture(self, player_profile):
        """
        Test that notification with picture is created correctly.
        """
        with NamedTemporaryFile(dir=settings.MEDIA_ROOT, suffix=".jpg") as temp_file:
            temp_file.write(b"fake image data")
            temp_file.flush()
            picture_filename = os.path.basename(temp_file.name)
            body = {
                "title": "Test Notification",
                "description": "This is a test notification with a picture.",
                "href": "/test",
                "icon": "test-icon",
                "picture": picture_filename,
                "picture_profile_role": "P",
            }
            NotificationService(player_profile.meta).create_notification(
                NotificationBody(**body)
            )

            notification = Notification.objects.filter(
                title=body["title"],
            ).first()

            assert notification is not None
            assert notification.icon == "test-icon"
            assert notification.picture == picture_filename
            assert notification.picture_profile_role == "P"
