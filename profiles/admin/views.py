from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.db.models import Field
from django.forms.models import ModelChoiceField
from django.http import HttpRequest

from app.utils.admin import json_filed_data_prettified
from clubs.models import League
from profiles import models
from profiles.admin import filters
from profiles.admin.actions import (
    calculate_fantasy,
    calculate_metrics,
    fetch_data_player_meta,
    refresh,
    set_team_object_based_on_meta,
    trigger_refresh_data_player_stats,
    update_pm_score,
    update_scoring,
    update_season_score,
    update_with_profile_data,
)
from profiles.models import PROFILE_TYPES_AS_STRING
from utils import linkify


class CoachLicenceInline(
    admin.TabularInline
):  # Use TabularInline or StackedInline based on your preference
    model = models.CoachLicence
    extra = 1  # Number of empty forms to display for adding new instances


@admin.register(models.ProfileVisitHistory)
class ProfileVisitHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PlayerMetrics)
class PlayerMetricsAdmin(admin.ModelAdmin):
    list_display = [
        "player",
        "games_updated",
        "games_summary_updated",
        "fantasy_updated",
        "fantasy_summary_updated",
        "season_updated",
        "season_summary_updated",
    ]
    search_fields = [
        "player__user__email",
        "player__user__first_name",
        "player__user__last_name",
    ]
    autocomplete_fields = ("player",)


@admin.register(models.PlayerPosition)
class PositionAdmin(admin.ModelAdmin):
    pass


DEFAULT_PROFILE_SEARCHABLES = ("user__email", "user__first_name", "user__last_name")
DEFAULT_PROFILE_DISPLAY_FIELDS = ("pk", linkify("user"), "slug", "active", "uuid")


class ProfileAdminBase(admin.ModelAdmin):
    search_fields = DEFAULT_PROFILE_SEARCHABLES
    display_fileds = DEFAULT_PROFILE_DISPLAY_FIELDS
    readonly_fields = ("data_prettified",)
    exclude = ("voivodeship_raw",)

    def active(self, obj):
        return obj.is_active

    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.event_log)

    active.boolean = True


@admin.register(models.ManagerProfile)
class ManagerProfileAdmin(ProfileAdminBase):
    readonly_fields = ("external_links",)


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileAdminBase):
    exclude = ("voivodeship_raw",)
    readonly_fields = ("external_links", "uuid")
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "pk",
        "user",
    )


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "club_role",
        linkify("club_object"),
    )
    search_fields = DEFAULT_PROFILE_SEARCHABLES + ("club_object__name",)
    autocomplete_fields = ("club_object",)


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

    def get_next(self, obj):
        return obj.next

    #  TODO napisac swoja metode v

    def get_owner(self, obj):
        if obj.owner is None:
            return linkify("owner")(obj)
        return linkify("profile")(obj.owner)

    get_next.short_description = "NEXT"


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "get_mapper",
        linkify("playermetrics"),
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("team_object_alt"),
        "display_league",
        "display_team",
        "display_club",
        "display_seniority",
        "display_gender",
        "meta_updated",
        "meta_last",
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

    def get_mapper(self, obj):
        if hasattr(obj, "mapper"):
            if obj.mapper is not None:
                old_mapper = obj.mapper.get_entity(
                    related_type="player", database_source="s38"
                )
                if old_mapper is not None:
                    return old_mapper.mapper_id
        return None

    autocomplete_fields = (
        "user",
        "team_object",
        "team_history_object",
        "team_object_alt",
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

    readonly_fields = ("data_prettified", "mapper", "external_links", "uuid")
    search_fields = ("uuid",)


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "get_mapper",
        linkify("team_object"),
        linkify("team_history_object"),
        linkify("team_history_object"),
        linkify("external_links"),
    )
    autocomplete_fields = ("team_object", "team_history_object", "team_history_object")
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

    readonly_fields = ("mapper", "external_links")


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
class VerificationStageAdmin(admin.ModelAdmin):
    ...


@admin.register(models.TeamContributor)
class TeamContributorAdmin(admin.ModelAdmin):
    ...


@admin.register(models.CoachLicence)
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


@admin.register(models.ProfileTransferStatus)
class ProfileTransferStatusAdmin(admin.ModelAdmin):
    """Admin for ProfileTransferStatus model."""

    form = TransferStatusForm
