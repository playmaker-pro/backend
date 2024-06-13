from typing import Optional

from django.http import HttpRequest

from followers.models import GenericFollow
from profiles.models import PROFILE_MODELS, Catalog


def get_followed_object_url(
    generic_follow: GenericFollow, request: HttpRequest
) -> Optional[str]:
    """
    Generate a URL for the followed object based on its type.
    """
    content_type = generic_follow.content_type

    if content_type.model_class() == Catalog:
        catalog = Catalog.objects.get(id=generic_follow.object_id)
        base_url = request.build_absolute_uri("/api/v3/profiles/")
        formatted_slug = (
            catalog.slug if catalog.slug.startswith("?") else f"?{catalog.slug}"
        )
        return f"{base_url}{formatted_slug}"

    elif content_type.model_class() in PROFILE_MODELS:
        profile = content_type.get_object_for_this_type(
            user_id=generic_follow.object_id
        )
        return request.build_absolute_uri(f"/api/v3/profiles/{profile.uuid}")

    else:
        model = content_type.model_class()
        plural_model_name = f"{model._meta.model_name}s"
        return request.build_absolute_uri(
            f"/api/v3/{model._meta.app_label}/{plural_model_name}/{generic_follow.object_id}"
        )
