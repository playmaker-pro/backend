from typing import Union

from .models import ExternalLinks, ExternalLinksEntity, LinkSource

LINK_TYPES = {
    "transfermarket": "statistics",
    "min90": "statistics",
    "laczynaspilka": "statistics",
    "scoutmaker": "statistics",
    "inStat": "statistics",
    "instagram": "social",
    "linkedIn": "social",
    "tikTok": "social",
    "facebook": "social",
    "twitter": "social",
    "website": "social",
    "other": "social",
}

EXT_LINK_MODEL = Union[
    "PlayerProfile",
    "CoachProfile",
    "ScoutProfile",
    "ManagerProfile",
    "RefereeProfile",
    "Club",
    "Team",
    "LeagueHistory",
]


def create_or_update_profile_external_links(obj: EXT_LINK_MODEL) -> None:
    """
    Update or create ExternalLinks instances for a given profile object, which can be any of the following types:
    'PlayerProfile', 'CoachProfile', 'ScoutProfile', 'ManagerProfile', 'Club', 'Team', or 'League'. The function
    first updates or creates the ExternalLinks instance that represents the profile's external links. If the instance
    is created, it is associated with the profile object. It then retrieves all LinkSource objects from the database
    and collects all links from the given profile object by iterating through its fields and adding those that
    end in "_url" and have a non-empty value. For each link, it creates or updates an ExternalLinksEntity instance
    with the corresponding LinkSource and adds it to the ExternalLinks instance.
    """

    # "Update or create the ExternalLinks instance for the profile"
    model_name = type(obj).__name__.lower()
    external_links, created = ExternalLinks.objects.update_or_create(
        **{f"{model_name}": obj}
    )
    if created:
        setattr(obj, "external_links", external_links)
        obj.save()

    # "Get all link sources from the database"
    link_sources = LinkSource.objects.all()

    # "Get all link fields from the profile model"
    link_fields = [
        field.name for field in obj._meta.get_fields() if field.name.endswith("_url")
    ]

    # "Determine the related type for the ExternalLinksEntity instance based on the profile model name"
    related_type = model_name.replace("profile", "")

    # "Collect all links for the profile"
    all_links = []
    for link_field in link_fields:
        link = getattr(obj, link_field, None)
        source_name = link_field[:-4]  # Remove "_url" suffix
        link_source = link_sources.filter(name=source_name).first()
        if link and link_source:
            all_links.append((link, link_source))
        # Delete ExternalLinksEntity with empty URL when user removes URL from profile
        elif link_source:
            entity = ExternalLinksEntity.objects.filter(
                target=external_links,
                source=link_source,
                related_type=related_type,
            ).first()
            if entity:
                entity.delete()

    for link, link_source in all_links:
        entity, created = ExternalLinksEntity.objects.get_or_create(
            target=external_links,
            source=link_source,
            related_type=related_type,
            defaults={
                "creator_type": "user",
                "link_type": LINK_TYPES[link_source.name],
                "url": link,
            },
        )
        if not created:
            entity.url = link
            entity.link_type = LINK_TYPES[link_source.name]
            entity.save()
