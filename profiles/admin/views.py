from typing import Type, Union

from django import forms
from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Field, QuerySet
from django.forms.models import ModelChoiceField
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from app.utils.admin import json_filed_data_prettified
from clubs.models import League
from profiles import models
from profiles.admin import filters
from profiles.admin.actions import *
from profiles.admin.mixins import RemoveM2MDuplicatesMixin
from profiles.models import PROFILE_TYPES_AS_STRING, BaseProfile
from profiles.services import ProfileService
from utils import linkify


class CoachLicenceInline(
    admin.TabularInline
):  # Use TabularInline or StackedInline based on your preference
    model = models.CoachLicence
    extra = 1  # Number of empty forms to display for adding new instances


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


@admin.register(models.PlayerMetrics)
class PlayerMetricsAdmin(admin.ModelAdmin):
    list_display = ["player", "pm_score", "pm_score_history"]
    search_fields = [
        "player__user__email",
        "player__user__first_name",
        "player__user__last_name",
    ]
    fields = (
        "player",
        "pm_score",
        "pm_score_history",
        "pm_score_state",
        "pm_score_updated",
    )
    readonly_fields = ("player",)
    autocomplete_fields = ("player",)
    ordering = ("pm_score",)


@admin.register(models.PlayerPosition)
class PositionAdmin(admin.ModelAdmin):
    pass


DEFAULT_PROFILE_SEARCHABLES = ("user__email", "user__first_name", "user__last_name")
DEFAULT_PROFILE_DISPLAY_FIELDS = ("pk", linkify("user"), "slug", "active", "uuid")


class ProfileAdminBase(admin.ModelAdmin):
    search_fields = DEFAULT_PROFILE_SEARCHABLES
    display_fields = DEFAULT_PROFILE_DISPLAY_FIELDS
    readonly_fields = ("data_prettified",)

    def active(self, obj):
        return obj.is_active

    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.event_log)

    active.boolean = True


@admin.register(models.ManagerProfile)
class ManagerProfileAdmin(ProfileAdminBase):
    readonly_fields = (
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification_stage",
        "verification",
    )
    autocomplete_fields = (
        "user",
        "external_links",
        "team_object",
        "team_history_object",
        "user",
    )


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileAdminBase):
    readonly_fields = (
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification",
        "verification_stage",
    )
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "pk",
        "user",
    )
    autocomplete_fields = (
        "user",
        "external_links",
        "team_object",
        "team_history_object",
        "user",
        "voivodeship_obj",
        "address",
    )


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS
    readonly_fields = (
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification",
        "verification_stage",
    )
    autocomplete_fields = (
        "user",
        "external_links",
        "team_object",
        "team_history_object",
        "user",
    )


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "club_role",
        linkify("club_object"),
    )
    search_fields = DEFAULT_PROFILE_SEARCHABLES + ("club_object__name",)
    autocomplete_fields = (
        "club_object",
        "user",
        "external_links",
        "team_object",
        "team_history_object",
        "user",
    )
    readonly_fields = (
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification",
        "verification_stage",
    )


@admin.register(models.ProfileVerificationStatus)
class ProfileVerificationStatusAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_owner",
        "has_team",
        "team_not_found",
        "club",
        "team",
        "text",
        "status",
        "set_by",
        "created_at",
        "updated_at",
        linkify("previous"),
        "get_next",
    )
    autocomplete_fields = ("owner", "team", "club", "set_by")
    list_filter = (
        "owner__declared_role",
        "status",
        filters.OnlyLastVerificationFilter,
        filters.HasDataMapperIdFilter,
        filters.HasTextInputFilter,
        ("has_team", admin.BooleanFieldListFilter),
        ("team_not_found", admin.BooleanFieldListFilter),
        filters.HasTeamObjectFilter,
        filters.HasClubObjectFilter,
    )
    actions = [update_with_profile_data]
    search_fields = ("owner__first_name", "owner__last_name")

    def get_next(self, obj):
        return obj.next

    def get_owner(self, obj):
        if obj.owner is None:
            return linkify("owner")(obj)
        return linkify("profile")(obj.owner)

    get_next.short_description = "NEXT"


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        # "get_mapper",
        linkify("playermetrics"),
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("team_object_alt"),
        "display_league",
        "display_team",
        "display_club",
        "display_seniority",
        "display_gender",
        # "meta_updated",
        # "meta_last",
        linkify("verification"),
        linkify("external_links"),
    )

    def team_object_linkify(self, obj=None):
        if obj.team_object:
            return linkify("team_object")(obj)
        else:
            return "-"

    team_object_linkify.short_description = "team_object"

    def meta_last(self, obj):
        if obj.meta:
            return list(obj.meta.items())[-1]
        else:
            obj.meta

    # def get_mapper(self, obj):
    #     if hasattr(obj, "mapper"):
    #         if obj.mapper is not None:
    #             old_mapper = obj.mapper.get_entity(
    #                 related_type="player", database_source="s38"
    #             )
    #             if old_mapper is not None:
    #                 return old_mapper.mapper_id
    #     return None

    autocomplete_fields = (
        "user",
        "external_links",
        "team_object",
        "team_history_object",
        "team_object_alt",
        "user",
        "voivodeship_obj",
        "address",
    )

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

    readonly_fields = (
        "data_prettified",
        "mapper",
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification_stage",
    )
    search_fields = ("uuid", "user__email", "user__first_name", "user__last_name")


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "get_mapper",
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("team_history_object"),
        linkify("external_links"),
    )
    autocomplete_fields = (
        "user",
        "team_object",
        "team_history_object",
        "user",
        "voivodeship_obj",
        "address",
    )
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

    readonly_fields = (
        "mapper",
        "external_links",
        "uuid",
        "premium_products",
        "visitation",
        "verification",
        "verification_stage",
    )


@admin.register(models.RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    readonly_fields = ("current", "approver")
    list_display = (
        "pk",
        "user",
        "approved",
        "current",
        "new",
        "request_date",
        "accepted_date",
    )
    list_filter = ("approved",)
    actions = [
        "approve_requests",
    ]

    def approve_requests(self, request, queryset):
        queryset.update(approved=True)

    approve_requests.short_description = "Approve many requets."

    def save_model(self, request, obj, form, change):
        obj.approver = request.user
        super().save_model(request, obj, form, change)


@admin.register(models.ProfileVideo)
class ProfileVideoAdmin(admin.ModelAdmin):
    autocomplete_fields = ("user",)


@admin.register(models.PlayerProfilePosition)
class PlayerProfilePositionAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        linkify("player_profile"),
        "player_position",
        "is_main",
        "get_email",
        "get_user_id",
    )

    def get_user_id(self, obj: models.PlayerProfilePosition) -> int:
        """Return user id."""
        return obj.player_profile.user.id

    def get_email(self, obj: models.PlayerProfilePosition) -> str:
        """Return user email."""
        return obj.player_profile.user.email

    get_user_id.short_description = "User id"
    get_email.short_description = "User email"


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
class RefereeProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (linkify("external_links"),)
    readonly_fields = ("external_links",)


@admin.register(models.LicenceType)
class LicenceTypeAdmin(ProfileAdminBase):
    pass


@admin.register(models.VerificationStage)
class VerificationStageAdmin(admin.ModelAdmin): ...


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

    def get_team(self, obj: models.TeamContributor) -> str:
        """Return user email."""
        team_history = obj.team_history.first()
        if team_history is None:
            return None
        view_name = (
            f"admin:{team_history._meta.app_label}_"  # noqa
            f"{team_history.__class__.__name__.lower()}_change"
        )
        link_url = reverse(view_name, args=[team_history.pk])
        return format_html(f'<a href="{link_url}">{team_history}</a>')

    get_team.short_description = "Team"

    def get_team_pk(self, obj: models.TeamContributor) -> str:
        """Return user email."""
        team_history = obj.team_history.first()
        return team_history.pk if team_history else None

    get_team_pk.short_description = "Team id"

    def get_name(self, obj: models.TeamContributor) -> str:
        """Return user email."""
        return mark_safe(f'<a href="{obj.pk}">{obj}</a>')

    get_name.short_description = "Name"

    def get_profile_uuid(self, obj: models.TeamContributor) -> str:
        """Return profile uuid."""
        profile_service = ProfileService()
        profile = profile_service.get_profile_by_uuid(obj.profile_uuid)
        view_name = (
            f"admin:{profile._meta.app_label}_"  # noqa
            f"{profile.__class__.__name__.lower()}_change"
        )
        link_url = reverse(view_name, args=[profile.pk])
        return format_html(f'<a href="{link_url}">{profile.uuid}</a>')

    get_profile_uuid.short_description = "Profile uuid"

    def get_queryset(self, request) -> QuerySet:
        """Due to m2m field problem, we have to override this method."""
        queryset = super().get_queryset(request).prefetch_related("team_history")
        return queryset


# @admin.register(models.CoachLicence)
class CoachLicenceAdmin(admin.ModelAdmin):
    autocomplete_fields = ("owner",)


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ("owner",)


class TransferStatusForm(forms.ModelForm):
    class Meta:
        model = models.ProfileTransferStatus
        exclude = []

    def __init__(self, *args, **kwargs):
        """
        Override the formfield for the 'content_type'
        foreign key to only include profiles.
        """
        super().__init__(*args, **kwargs)
        self.fields["content_type"].queryset = ContentType.objects.filter(
            app_label="profiles",
            model__in=[
                obj[0].lower() for obj in PROFILE_TYPES_AS_STRING
            ],  # Include the model names you want
        )


class ContentTypeMixin:
    def get_content_type(
        self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
    ) -> str:
        """
        Retrieves the content type of the given ProfileTransferStatus object and returns
        a formatted HTML string.

        This method gets the model associated with the content type of the
        ProfileTransferStatus object, retrieves the corresponding profile,
        and generates a URL to the admin page for that profile. It then returns a
        formatted HTML string that contains a hyperlink to the admin page.
        """

        Model: Type[BaseProfile] = apps.get_model(  # noqa
            "profiles", obj.content_type.model
        )
        profile = Model.objects.get(pk=obj.object_id)
        view_name = (
            f"admin:{profile._meta.app_label}_"  # noqa
            f"{profile.__class__.__name__.lower()}_change"
        )
        link_url = reverse(view_name, args=[profile.pk])
        return format_html(f'<a href="{link_url}">{profile}</a>')

    get_content_type.short_description = "Profile"

    def profile_type(
        self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
    ) -> str:
        """Return profile type."""

        Model: Type[BaseProfile] = apps.get_model(  # noqa
            "profiles", obj.content_type.model
        )
        profile = Model.objects.get(pk=obj.object_id)
        return profile.__class__.__name__

    profile_type.short_description = "Profile type"

    def get_user_email(
        self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
    ) -> str:
        """Return user email."""
        return mark_safe(f'<a href="{obj.pk}">{obj}</a>')

    get_user_email.short_description = "Transfer object"

    def get_profile_uuid(
        self, obj: Union[models.ProfileTransferStatus, models.ProfileTransferRequest]
    ) -> str:
        """Return profile uuid."""
        Model: Type[BaseProfile] = apps.get_model(  # noqa
            "profiles", obj.content_type.model
        )
        profile = Model.objects.get(pk=obj.object_id)
        return profile.uuid

    get_profile_uuid.short_description = "Profile uuid"


@admin.register(models.ProfileTransferStatus)
class ProfileTransferStatusAdmin(admin.ModelAdmin, ContentTypeMixin):
    """Admin for ProfileTransferStatus model."""

    form = TransferStatusForm
    list_display = (
        "pk",
        "get_user_email",
        "get_content_type",
        "get_profile_uuid",
        "profile_type",
        "created_at",
        "updated_at",
    )


@admin.register(models.ProfileTransferRequest)
class ProfileTransferRequestAdmin(admin.ModelAdmin, ContentTypeMixin):
    """Admin for ProfileTransferRequest model."""

    list_display = (
        "pk",
        "get_user_email",
        "get_content_type",
        "get_profile_uuid",
        "profile_type",
        "created_at",
        "updated_at",
        "voivodeship",
    )
    form = TransferStatusForm


@admin.register(models.Catalog)
class CatalogAdmin(admin.ModelAdmin):
    """Admin for Catalog model."""

    list_display = ("name", "slug", "description")

    def slug(self, obj: models.Catalog) -> str:
        """Get the slug for display in the admin."""
        return obj.slug

    slug.short_description = "Catalog Slug"

    class Meta:
        model = models.Catalog


# @admin.register(models.Visitation)
class VisitationAdmin(admin.ModelAdmin):
    """Admin for Visitation model."""

    ...


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
    )
    readonly_fields = ("_profile_class", "user")
    actions = [bind_reccurrent_notifications]
