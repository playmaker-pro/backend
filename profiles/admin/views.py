import logging

from django.contrib import admin
from django.db.models import Field, QuerySet
from django.forms.models import ModelChoiceField
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from app.utils.admin import json_filed_data_prettified
from clubs.models import League
from profiles import models
from profiles.admin.actions import *
from profiles.admin.mixins import RemoveM2MDuplicatesMixin
from profiles.services import ProfileService
from utils import linkify

logger = logging.getLogger(__name__)


class CoachLicenceInline(admin.TabularInline):
    model = models.CoachLicence
    extra = 1


@admin.register(models.ProfileVisitHistory)
class ProfileVisitHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        linkify("user"),
        "user_logged_in",
        "counter_playerprofile",
        "counter_clubprofile",
        "counter_coachprofile",
        "counter_scoutprofile",
        "counter_managerprofile",
        "counter_guestprofile",
        "counter_refereeprofile",
        "counter_anonymoususer",
        "created_at",
    )
    list_filter = ("user_logged_in", "created_at")
    search_fields = ("user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user")


@admin.register(models.PlayerMetrics)
class PlayerMetricsAdmin(admin.ModelAdmin):
    list_display = ["player", "pm_score", "pm_score_history", "get_user_display"]
    search_fields = [
        "player__user__email",
        "player__user__first_name",
        "player__user__last_name",
    ]
    list_filter = ["pm_score_state", "pm_score_updated"]
    fields = (
        "player",
        "pm_score",
        "pm_score_history",
        "pm_score_state",
        "pm_score_updated",
    )
    readonly_fields = ("player", "pm_score_updated")
    autocomplete_fields = ("player",)
    ordering = ("-pm_score",)

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("player__user")

    def get_user_display(self, obj):
        """Get user display name."""
        if obj.player and obj.player.user:
            user = obj.player.user
            return f"{user.first_name} {user.last_name}"
        return "-"

    get_user_display.short_description = "User"


@admin.register(models.PlayerPosition)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "shortcut", "shortcut_pl", "ordering")
    search_fields = ("name", "shortcut", "shortcut_pl")
    list_filter = ("ordering",)
    ordering = ("ordering", "name")


DEFAULT_PROFILE_DISPLAY_FIELDS = ("pk", linkify("user"), "slug", "active", "uuid")
DEFAULT_PROFILE_SEARCHABLES = (
    "uuid",
    "user__email",
    "user__first_name",
    "user__last_name",
    "slug",
)


class ProfileAdminBase(admin.ModelAdmin):
    """Base admin class for profile models that inherit from BaseProfile."""

    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS
    readonly_fields = (
        "uuid",
        "premium_products",
        "visitation",
        "verification_stage",
        "meta",
        "user",
    )
    search_fields = DEFAULT_PROFILE_SEARCHABLES
    autocomplete_fields = ("user",)

    def get_queryset(self, request):
        """Optimize queryset with common select_related and prefetch_related."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            "user",
            "verification_stage",
            "premium_products",
            "visitation",
            "meta",
        )
        return queryset

    def has_delete_permission(self, request, obj=None):
        """Disable delete permission for profiles."""
        return False

    def active(self, obj):
        """Display active status as boolean."""
        return obj.is_active

    def data_prettified(self, instance):
        """Display prettified event log data."""
        return json_filed_data_prettified(instance.event_log)

    def get_user_display(self, obj):
        """Get user display name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name} ({obj.user.email})"
        return "-"

    get_user_display.short_description = "User"
    active.boolean = True
    data_prettified.short_description = "Event Log"


class ProfileWithExternalLinksAdminBase(ProfileAdminBase):
    """Base admin for profiles that have external_links field."""

    readonly_fields = ProfileAdminBase.readonly_fields + ("external_links",)
    autocomplete_fields = ProfileAdminBase.autocomplete_fields + ("external_links",)


class ProfileWithTeamAdminBase(ProfileWithExternalLinksAdminBase):
    """Base admin for profiles that have team-related fields."""

    autocomplete_fields = ProfileWithExternalLinksAdminBase.autocomplete_fields + (
        "team_object",
        "team_history_object",
    )


class ProfileWithAddressAdminBase(ProfileWithTeamAdminBase):
    """Base admin for profiles that have address and voivodeship fields."""

    autocomplete_fields = ProfileWithTeamAdminBase.autocomplete_fields + (
        "voivodeship_obj",
        "address",
    )


@admin.register(models.ManagerProfile)
class ManagerProfileAdmin(ProfileWithTeamAdminBase):
    pass


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileWithAddressAdminBase):
    pass


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileWithTeamAdminBase):
    pass


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileWithTeamAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "club_role",
        linkify("club_object"),
    )
    search_fields = DEFAULT_PROFILE_SEARCHABLES + ("club_object__name",)
    autocomplete_fields = ProfileWithTeamAdminBase.autocomplete_fields + (
        "club_object",
    )


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileWithAddressAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        linkify("playermetrics"),
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("team_object_alt"),
        "display_league",
        "display_team",
        "display_club",
        "display_seniority",
        "display_gender",
        linkify("external_links"),
    )

    autocomplete_fields = ProfileWithAddressAdminBase.autocomplete_fields + (
        "team_object_alt",
    )
    readonly_fields = ProfileWithAddressAdminBase.readonly_fields + ("mapper",)

    actions = [
        update_pm_score,
        update_season_score,
        update_scoring,
        refresh,
        calculate_metrics,
        trigger_refresh_data_player_stats,
        fetch_data_player_meta,
        set_team_object_based_on_meta,
        calculate_fantasy,
    ]

    def team_object_linkify(self, obj=None):
        if obj.team_object:
            return linkify("team_object")(obj)
        else:
            return "-"

    team_object_linkify.short_description = "team_object"


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileWithAddressAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "get_mapper",
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("external_links"),
    )
    readonly_fields = ProfileWithAddressAdminBase.readonly_fields + ("mapper",)
    exclude = ("voivodeship", "user__email")

    def get_mapper(self, obj):
        if hasattr(obj, "mapper"):
            if obj.mapper is not None:
                old_mapper = obj.mapper.get_entity(
                    related_type="coach", database_source="s38"
                )
                if old_mapper is not None:
                    return old_mapper.mapper_id
        return None


@admin.register(models.ProfileVideo)
class ProfileVideoAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "title", "label", "date_created", "get_user_display")
    list_filter = ("label", "date_created")
    search_fields = ("user__email", "user__first_name", "user__last_name", "title")
    readonly_fields = ("date_created",)
    autocomplete_fields = ("user",)
    date_hierarchy = "date_created"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user")

    def get_user_display(self, obj):
        """Get user display name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return "-"

    get_user_display.short_description = "User Name"


@admin.register(models.PlayerProfilePosition)
class PlayerProfilePositionAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        linkify("player_profile"),
        "player_position",
        "is_main",
        "get_email",
        "get_user_id",
        "get_user_display",
    )
    list_filter = ("is_main", "player_position")
    search_fields = (
        "player_profile__user__email",
        "player_profile__user__first_name",
        "player_profile__user__last_name",
    )
    autocomplete_fields = ("player_profile", "player_position")

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return (
            super()
            .get_queryset(request)
            .select_related("player_profile__user", "player_position")
        )

    def get_user_id(self, obj: models.PlayerProfilePosition) -> int:
        """Return user id."""
        return obj.player_profile.user.id

    def get_email(self, obj: models.PlayerProfilePosition) -> str:
        """Return user email."""
        return obj.player_profile.user.email

    def get_user_display(self, obj: models.PlayerProfilePosition) -> str:
        """Return user display name."""
        user = obj.player_profile.user
        return f"{user.first_name} {user.last_name}"

    get_user_id.short_description = "User id"
    get_email.short_description = "User email"
    get_user_display.short_description = "User Name"


@admin.register(models.Language)
class LanguageAdmin(admin.ModelAdmin):
    pass


@admin.register(models.RefereeLevel)
class RefereeLevelAdmin(admin.ModelAdmin):
    readonly_fields = ("level_name",)

    def formfield_for_foreignkey(
        self, db_field: Field, request: HttpRequest, **kwargs
    ) -> ModelChoiceField:
        """
        Override the formfield for the 'level' foreign key to only include league highest parent.
        """  # noqa: E501
        if db_field.name == "level":
            kwargs["queryset"] = League.objects.filter(parent=None)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.RefereeProfile)
class RefereeProfileAdmin(ProfileWithExternalLinksAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (linkify("external_links"),)


@admin.register(models.LicenceType)
class LicenceTypeAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "key", "order")
    search_fields = ("name", "key")
    list_filter = ("order",)
    ordering = ("order", "name")


@admin.register(models.VerificationStage)
class VerificationStageAdmin(admin.ModelAdmin):
    list_display = ("pk",)
    # Add more fields as they become available in the model


@admin.register(models.TeamContributor)
class TeamContributorAdmin(RemoveM2MDuplicatesMixin, admin.ModelAdmin):
    list_display = (
        "pk",
        "get_name",
        "get_team",
        "get_team_pk",
        "get_profile_uuid",
        "is_primary",
        "start_date",
        "end_date",
    )
    search_fields = ("profile_uuid",)
    list_filter = ("is_primary", "start_date", "end_date")

    def get_queryset(self, request) -> QuerySet:
        """Optimize queryset with prefetch_related."""
        return super().get_queryset(request).prefetch_related("team_history")

    def get_team(self, obj: models.TeamContributor) -> str:
        """Return team with admin link."""
        team_history = obj.team_history.first()
        if team_history is None:
            return "-"
        try:
            view_name = f"admin:{team_history._meta.app_label}_{team_history.__class__.__name__.lower()}_change"
            link_url = reverse(view_name, args=[team_history.pk])
            return format_html(f'<a href="{link_url}">{team_history}</a>')
        except Exception as e:
            logger.error(f"Error creating team link for {obj}: {e}")
            return str(team_history)

    def get_team_pk(self, obj: models.TeamContributor) -> str:
        """Return team pk."""
        team_history = obj.team_history.first()
        return team_history.pk if team_history else "-"

    def get_name(self, obj: models.TeamContributor) -> str:
        """Return name with admin link."""
        return mark_safe(f'<a href="{obj.pk}">{obj}</a>')

    def get_profile_uuid(self, obj: models.TeamContributor) -> str:
        """Return profile uuid with admin link."""
        try:
            profile_service = ProfileService()
            profile = profile_service.get_profile_by_uuid(obj.profile_uuid)
            view_name = f"admin:{profile._meta.app_label}_{profile.__class__.__name__.lower()}_change"
            link_url = reverse(view_name, args=[profile.pk])
            return format_html(f'<a href="{link_url}">{profile.uuid}</a>')
        except Exception as e:
            logger.error(f"Error getting profile UUID for {obj}: {e}")
            return str(obj.profile_uuid)

    # Set short descriptions
    get_team.short_description = "Team"
    get_team_pk.short_description = "Team id"
    get_name.short_description = "Name"
    get_profile_uuid.short_description = "Profile uuid"


# @admin.register(models.CoachLicence)
class CoachLicenceAdmin(admin.ModelAdmin):
    autocomplete_fields = ("owner",)


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "release_year", "owner", "get_owner_display")
    list_filter = ("release_year",)
    search_fields = ("name", "owner__email", "owner__first_name", "owner__last_name")
    autocomplete_fields = ("owner",)

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("owner")

    def get_owner_display(self, obj):
        """Get owner display name."""
        if obj.owner:
            return f"{obj.owner.first_name} {obj.owner.last_name}"
        return "-"

    get_owner_display.short_description = "Owner Name"


# class ContentTypeMixin:
#     def get_content_type(
#         self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
#     ) -> str:
#         """
#         Retrieves the content type of the given ProfileTransferStatus object and returns
#         a formatted HTML string.

#         This method gets the model associated with the content type of the
#         ProfileTransferStatus object, retrieves the corresponding profile,
#         and generates a URL to the admin page for that profile. It then returns a
#         formatted HTML string that contains a hyperlink to the admin page.
#         """

#         Model: Type[BaseProfile] = apps.get_model(  # noqa
#             "profiles", obj.content_type.model
#         )
#         profile = Model.objects.get(pk=obj.object_id)
#         view_name = (
#             f"admin:{profile._meta.app_label}_"  # noqa
#             f"{profile.__class__.__name__.lower()}_change"
#         )
#         link_url = reverse(view_name, args=[profile.pk])
#         return format_html(f'<a href="{link_url}">{profile}</a>')

#     get_content_type.short_description = "Profile"

#     def profile_type(
#         self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
#     ) -> str:
#         """Return profile type."""

#         Model: Type[BaseProfile] = apps.get_model(  # noqa
#             "profiles", obj.content_type.model
#         )
#         profile = Model.objects.get(pk=obj.object_id)
#         return profile.__class__.__name__

#     profile_type.short_description = "Profile type"

#     def get_user_email(
#         self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
#     ) -> str:
#         """Return user email."""
#         return mark_safe(f'<a href="{obj.pk}">{obj}</a>')

#     get_user_email.short_description = "Transfer object"

#     def get_profile_uuid(
#         self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
#     ) -> str:
#         """Return profile uuid."""
#         Model: Type[BaseProfile] = apps.get_model(  # noqa
#             "profiles", obj.content_type.model
#         )
#         profile = Model.objects.get(pk=obj.object_id)
#         return profile.uuid

#     get_profile_uuid.short_description = "Profile uuid"


@admin.register(models.Catalog)
class CatalogAdmin(admin.ModelAdmin):
    """Admin for Catalog model."""

    list_display = ("pk", "name", "slug", "description")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}

    def slug(self, obj: models.Catalog) -> str:
        """Get the slug for display in the admin."""
        return obj.slug

    slug.short_description = "Catalog Slug"


@admin.register(models.ProfileMeta)
class ProfileMetaAdmin(admin.ModelAdmin):
    """Admin for ProfileMeta model."""

    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    list_display = (
        "pk",
        linkify("profile"),
        "get_user_display",
        "get_profile_type",
    )
    list_filter = ("_profile_class",)
    readonly_fields = ("_profile_class", "user")
    actions = [bind_reccurrent_notifications]

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("user")

    def get_user_display(self, obj):
        """Get user display name."""
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name} ({obj.user.email})"
        return "-"

    def get_profile_type(self, obj):
        """Get profile type."""
        return obj._profile_class or "-"

    get_user_display.short_description = "User"
    get_profile_type.short_description = "Profile Type"
