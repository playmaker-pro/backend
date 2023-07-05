from django.db import models
from django.utils.translation import ugettext_lazy as _

from features.signals import default_access_role, update_permissions
from roles.definitions import PROFILE_TYPE_PLAYER


class AccessPermission(models.Model):
    """
    Access permission for a given role. Additional permission for a feature element.
    Basically, it is a restriction of access to a feature element if we would like to.
    Example: We would like to restrict user with role player,
    to access the web search page to search only for players from his club.
    In this case, we would save access permission with field access='club'.
    """

    class AccessChoices(models.TextChoices):
        """Enum's representation of access permissions."""

        NONE = "none", _("none")
        ALL = "all", _("all")
        CLUB = "club", _("club")
        OWN = "own", _("own")

    # TODO: The 'role' field should be linked to a 'Role' model from the 'Users' domain (currently unavailable).
    #  role = models.ForeignKey(Role, on_delete=models.CASCADE, help_text=_("Role Foreignkey")
    role = PROFILE_TYPE_PLAYER

    access = models.CharField(
        choices=AccessChoices.choices,
        default=AccessChoices.NONE,
        max_length=15,
        help_text=_("Access permission name."),
    )


class FeatureElement(models.Model):
    """
    Feature element represents a single feature permission.
    Model represents how permission is granted to a role.
    - column name: Name representation of a feature element.
    - column permissions: JSON representation of role permissions.
        Field stores a dictionary of roles and boolean values.
        For example: {"player": true, "coach": false} means, that player and coach has access
        to a feature element.
    -column access_permissions: Access permissions list. Field stores special information
        about restrictions of access to a feature element.
    """

    name = models.CharField(
        max_length=255, unique=True, help_text=_("Feature element name")
    )
    permissions = models.JSONField(
        help_text=_("JSON representation of roles permissions."), blank=True
    )
    access_permissions = models.ManyToManyField(
        AccessPermission, help_text=_("Access permissions list."), blank=True
    )

    new_permissions = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_permissions = self.permissions

    @staticmethod
    def on_pre_save(sender: "FeatureElement", instance: "FeatureElement", **kwargs):
        """
        Send signal to set default permissions if not set.
        Call a custom signal to update permissions.
        """
        default_access_role.send(
            sender=sender, instance=instance, created=instance._state.adding
        )
        update_permissions.send(
            sender=sender,
            instance=instance,
            created=instance._state.adding,
        )
        instance.new_permissions = instance.permissions


class Feature(models.Model):
    """Feature entity."""

    name = models.CharField(max_length=255, unique=True, help_text=_("Feature name."))
    enabled = models.BooleanField(
        default=True, help_text=_("Flag that says if feature is enabled.")
    )
    keyname = models.CharField(max_length=255, help_text=_("Feature keyname."))
    elements = models.ManyToManyField(FeatureElement, help_text=_("Feature elements."))
