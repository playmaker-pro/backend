from typing import Dict, List, Tuple, Union

from django.db.models import QuerySet

from external_links import models
from external_links.errors import LinkSourceNotFoundServiceException
from profiles.models import PROFILE_MODELS
from profiles.services import ProfileService

profile_service = ProfileService()


class ExternalLinksService:
    def upsert_links_for_user(
        self, profile: PROFILE_MODELS, links_data: List[Dict[str, Union[str, None]]]
    ) -> Tuple[List[models.ExternalLinksEntity], bool]:
        """
        Upsert (insert or update) external links for a user profile.
        """
        related_type = profile_service.get_related_type_from_profile(profile)
        external_links_instance = profile.external_links
        existing_links = models.ExternalLinksEntity.objects.filter(
            target=external_links_instance
        )
        link_sources_dict = self.fetch_link_sources(links_data)
        links_to_delete, links_to_create_or_update = self.determine_links_operations(
            links_data, link_sources_dict, external_links_instance, related_type
        )

        self.perform_bulk_delete(existing_links, links_to_delete)
        modified_links, was_any_link_created = self.perform_bulk_upsert(
            links_to_create_or_update
        )

        return modified_links, was_any_link_created

    @staticmethod
    def fetch_link_sources(
        links_data: List[Dict[str, Union[str, None]]],
    ) -> Dict[str, models.LinkSource]:
        """
        Fetches LinkSource objects based on the provided links_data and
        returns a dictionary with the source names as keys.
        """
        link_sources = models.LinkSource.objects.filter(
            name__in=[link_data.get("source") for link_data in links_data]
        )
        return {source.name: source for source in link_sources}

    @staticmethod
    def determine_links_operations(
        links_data: List[Dict[str, Union[str, None]]],
        link_sources_dict: Dict[str, models.LinkSource],
        external_links_instance,
        related_type,
    ) -> Tuple[List[int], List[Dict]]:
        """
        Determines which links to delete and which to create or update
        based on the provided data.
        Returns a tuple containing a list of link IDs to delete
        and a list of link data for upsert operations.
        """
        links_to_delete = []
        links_to_create_or_update = []

        for link_data in links_data:
            source_name = link_data.get("source")
            link_source = link_sources_dict.get(source_name)

            if not link_source:
                raise LinkSourceNotFoundServiceException(source_name)

            url = link_data.get("url")

            if not url:
                links_to_delete.append(link_source.id)
                continue

            links_to_create_or_update.append({
                "target": external_links_instance,
                "source": link_source,
                "related_type": related_type,
                "creator_type": "user",
                "link_type": "statistics",
                "url": url,
            })

        return links_to_delete, links_to_create_or_update

    @staticmethod
    def perform_bulk_delete(
        existing_links: QuerySet, links_to_delete: List[int]
    ) -> None:
        """
        Deletes a batch of links from the database based on the provided list of link IDs.
        """
        existing_links.filter(source__in=links_to_delete).delete()

    @staticmethod
    def perform_bulk_upsert(
        links_to_create_or_update,
    ) -> Tuple[List[models.ExternalLinksEntity], bool]:
        """
        Performs bulk upsert operations (either create or update) on external links based
        on the provided data.
        Returns a tuple containing the list of modified link instances and a boolean
        indicating if any link was newly created.
        """
        modified_links = []
        was_any_link_created = False

        for link in links_to_create_or_update:
            link_instance, created = models.ExternalLinksEntity.objects.get_or_create(
                target=link["target"],
                source=link["source"],
                related_type=link["related_type"],
                defaults={
                    "creator_type": link["creator_type"],
                    "link_type": link["link_type"],
                },
            )

            if created:
                was_any_link_created = True

            link_instance.url = link["url"]
            link_instance.save()
            modified_links.append(link_instance)

        return modified_links, was_any_link_created
