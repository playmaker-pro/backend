from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from utils import factories, testutils
from utils.factories import external_links_factories as external_links_factories


class ExternalLinksApiTest(APITestCase):
    def setUp(self):
        """Set up test environment."""
        testutils.create_system_user()

        # Create a user for create test
        self.user_create = factories.UserFactory(email="username", declared_role="P")
        factories.PlayerProfileFactory(user=self.user_create)
        self.link_sources = external_links_factories.LinkSourceFactory.create_batch(3)
        self.user_create.profile.save()

        # Create a user for update test
        self.user_update = factories.UserFactory(email="username123", declared_role="P")
        factories.PlayerProfileFactory(user=self.user_update)
        self.user_update.profile.external_links = (
            external_links_factories.ExternalLinksFactory.create()
        )
        # Create initial links for user_update
        external_links_factories.ExternalLinksEntityFactory(
            target=self.user_update.profile.external_links,
            source=self.link_sources[1],
            url="http://initiallink2.com",
        )
        external_links_factories.ExternalLinksEntityFactory(
            target=self.user_update.profile.external_links,
            source=self.link_sources[0],
            url="http://initiallink.com",
        )

        self.user_update.profile.save()
        self.url = "api:profiles:profile_external_links"

    def test_get_profile_external_links(self):
        """Test retrieving user's external links."""
        self.client.force_authenticate(user=self.user_create)
        url = reverse(
            "api:profiles:profile_external_links",
            kwargs={"profile_uuid": self.user_create.profile.uuid},
        )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_upsert_external_links(self):
        """Test upserting (creating or updating) external links for a user."""

        # CREATE
        self.client.force_authenticate(user=self.user_create)
        url = reverse(self.url, kwargs={"profile_uuid": self.user_create.profile.uuid})
        data_create = {
            "links": [
                {"source": self.link_sources[0].name, "url": "http://example1.com"},
                {"source": self.link_sources[1].name, "url": "http://example2.com"},
            ]
        }
        response_create = self.client.post(url, data_create, format="json")
        assert response_create.status_code == status.HTTP_201_CREATED
        # UPDATE
        self.client.force_authenticate(user=self.user_update)
        url = reverse(
            self.url,
            kwargs={"profile_uuid": self.user_update.profile.uuid},
        )
        data_update = {
            "links": [
                {
                    "source": self.link_sources[1].name,
                    "url": "http://updatedlink.com",
                },  # Update this link
                {
                    "source": self.link_sources[0].name,
                    "url": "",
                },  # Delete this link
            ]
        }
        response_update = self.client.patch(url, data_update, format="json")
        assert response_update.status_code == status.HTTP_200_OK
