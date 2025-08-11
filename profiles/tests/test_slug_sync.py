import json
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from utils.test.test_utils import UserManager
from profiles.tests import utils

class TestSlugSynchronization(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.get_profile_by_slug_url = lambda slug: reverse(
            "api:profiles:get_profile_by_slug", kwargs={"profile_slug": slug}
        )
        self.update_profile_url = lambda profile_uuid: reverse(
            "api:profiles:get_or_update_profile", kwargs={"profile_uuid": profile_uuid}
        )

    def test_profile_meta_slug_updates_on_name_change(self) -> None:
        # Create a profile
        profile = utils.create_empty_profile(user_id=self.user_obj.pk, role="G")
        self.user_obj.refresh_from_db()
        profile.refresh_from_db()

        initial_profile_slug = profile.slug
        initial_meta_slug = profile.meta._slug

        # Assert initial slugs are the same
        assert initial_profile_slug == initial_meta_slug

        # Update user's first name to trigger slug change
        new_first_name = "NewFirstName"
        payload = {"user": {"first_name": new_first_name}}

        self.manager.login(self.user_obj)
        response = self.client.patch(
            self.update_profile_url(str(profile.uuid)), json.dumps(payload), **self.headers
        )
        assert response.status_code == 200

        profile.refresh_from_db()
        self.user_obj.refresh_from_db()

        updated_profile_slug = profile.slug
        updated_meta_slug = profile.meta._slug

        # Assert profile slug has changed
        assert initial_profile_slug != updated_profile_slug
        # Assert meta slug has updated to match the new profile slug
        assert updated_profile_slug == updated_meta_slug

        # Verify profile can be retrieved by the new slug via API
        response = self.client.get(self.get_profile_by_slug_url(updated_profile_slug), **self.headers)
        assert response.status_code == 200
        assert response.data["slug"] == updated_profile_slug
