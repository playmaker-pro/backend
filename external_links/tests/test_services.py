from django.test import TestCase

from external_links.errors import LinkSourceNotFoundServiceException
from external_links.services import ExternalLinksService
from utils.factories import PlayerProfileFactory, UserFactory
from utils.factories.external_links_factories import (
    ExternalLinksEntityFactory,
    ExternalLinksFactory,
    LinkSourceFactory,
)


class ExternalLinksServiceTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = PlayerProfileFactory(user=self.user)
        self.link_sources = LinkSourceFactory.create_batch(3)
        self.profile.external_links = ExternalLinksFactory.create()
        self.profile.save()
        self.service = ExternalLinksService()

    def test_upsert_external_links(self):
        """Test upserting external links for a user."""

        # Data to update/create links
        links_data = [
            {"source": self.link_sources[0].name, "url": "http://example1.com"},
            {"source": self.link_sources[1].name, "url": "http://example2.com"},
        ]

        modified_links, _ = self.service.upsert_links_for_user(self.profile, links_data)
        # Check that links have been correctly updated or created
        assert any(link.url == "http://example1.com" for link in modified_links)
        assert any(link.url == "http://example2.com" for link in modified_links)

    def test_upsert_existing_external_links_for_user(self):
        """Test updating external links for a user."""
        # Set up an existing external link for the user
        ExternalLinksEntityFactory.create(
            target=self.profile.external_links,
            source=self.link_sources[0],
            url="http://oldlink.com",
        )

        # Data to update the existing link
        links_data = [
            {"source": self.link_sources[0].name, "url": "http://newlink.com"},
        ]

        # Update the link using the service
        updated_links, _ = self.service.upsert_links_for_user(self.profile, links_data)

        # Check that the link has been correctly updated
        assert updated_links[0].url == "http://newlink.com"

    def test_delete_existing_external_link_for_user(self):
        """Test deleting an external link for a user."""
        # Set up an existing external link for the user
        ExternalLinksEntityFactory.create(
            target=self.profile.external_links,
            source=self.link_sources[0],
            url="http://oldlink.com",
        )

        # Data to delete the existing link
        links_data = [
            {"source": self.link_sources[0].name, "url": ""},
        ]

        # Delete the link using the service
        modified_links, _ = self.service.upsert_links_for_user(self.profile, links_data)

        # Check that the link has been deleted (i.e., not in the modified_links)
        assert not any(link.url == "http://oldlink.com" for link in modified_links)

    def test_try_delete_nonexistent_link(self):
        """Test attempting to delete a link with a non-existent link source."""
        links_data = [{"source": "nonexistent", "url": ""}]
        with self.assertRaises(LinkSourceNotFoundServiceException):
            self.service.upsert_links_for_user(self.profile, links_data)
