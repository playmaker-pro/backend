from typing import TYPE_CHECKING

from django.dispatch import Signal, receiver

from roles.definitions import PROFILE_TYPE_SHORT_MAP

if TYPE_CHECKING:
    from features.models import FeatureElement

update_permissions = Signal(providing_args=["instance"])
default_access_role = Signal(providing_args=["instance"])


@receiver(update_permissions)
def permissions_update(instance, **kwargs) -> None:
    if instance.pk and instance.permissions != instance.new_permissions:
        ...


@receiver(default_access_role)
def set_default_permissions(instance: "FeatureElement", **kwargs) -> None:
    """Set default permissions for a feature element if not set."""
    if not instance.permissions:
        permission_map: dict = PROFILE_TYPE_SHORT_MAP
        new_permissions_map = {key: False for key in permission_map.keys()}
        instance.permissions = new_permissions_map
