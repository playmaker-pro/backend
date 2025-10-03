import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestMailingApi:
    def test_get_preferences(self, api_client, player_profile):
        """Test retrieving mailing preferences."""
        api_client.force_authenticate(user=player_profile.user)
        response = api_client.get(reverse("api:mailing:mailing_preferences"))
        assert response.status_code == 200
        assert response.data == {"system": True, "marketing": True}

    def test_update_preferences(self, api_client, player_profile):
        """Test updating mailing preferences."""
        api_client.force_authenticate(user=player_profile.user)
        response = api_client.patch(
            reverse("api:mailing:mailing_preferences"),
            {"system": False, "marketing": True},
        )
        assert response.status_code == 200
        assert response.data == {"system": False, "marketing": True}

        # Verify the changes in the database
        player_profile.user.mailing.refresh_from_db()
        assert player_profile.user.mailing.preferences.system is False
        assert player_profile.user.mailing.preferences.marketing is True

    @pytest.mark.parametrize("mailing_type", ["SYSTEM", "MARKETING"])
    def test_direct_update_preferences(self, player_profile, api_client, mailing_type):
        """Test direct update of mailing preferences via token."""
        token = str(player_profile.user.mailing.preferences.uuid)
        api_client.force_authenticate(user=None)
        response = api_client.get(
            reverse(
                "api:mailing:update_preferences_directly",
                kwargs={"preferences_uuid": token, "mailing_type": mailing_type},
            ),
        )
        assert response.status_code == 200
        assert (
            response.content.decode()
            == "<h1><center>Preferencje zostały zaktualizowane</center></h1>"
        )

        # Verify the changes in the database
        player_profile.user.mailing.refresh_from_db()
        assert (
            getattr(player_profile.user.mailing.preferences, mailing_type.lower())
            is False
        )
