import pytest
from django.urls import reverse

from notifications.models import Notification
from notifications.services import NotificationService


@pytest.fixture
def profile_with_notifications(coach_profile):
    """Create a profile with notifications."""
    service = NotificationService(coach_profile.meta)
    service.notify_check_trial()
    service.notify_pm_rank()
    coach_profile.refresh_from_db()
    return coach_profile


class TestApi:
    def test_list_notifications(self, api_client, profile_with_notifications):
        """Test listing notifications."""
        api_client.force_authenticate(user=profile_with_notifications.user)
        url = reverse("api:notifications:get_notifications")
        response = api_client.get(url)

        assert response.status_code == 200
        assert len(response.data) == 3
        assert {
            "Skorzystaj z wersji próbnej Premium",
            "Ranking PM",
            "Witaj w PlayMaker!",
        } == {n["title"] for n in response.data}
        assert all([n for n in response.data if n["seen"] is False])

    def test_mark_notification_as_seen(self, api_client, profile_with_notifications):
        """Test marking a notification as seen."""
        api_client.force_authenticate(user=profile_with_notifications.user)
        seen_id = profile_with_notifications.meta.notifications.first().id
        url = reverse(
            "api:notifications:mark_as_read",
            args=[seen_id],
        )
        response = api_client.post(url)

        assert response.status_code == 200
        assert response.data["seen"] is True
        assert Notification.objects.get(id=seen_id).seen
