from django.contrib import admin
from utils import linkify
from app.utils.admin import json_filed_data_prettified
from profiles import models
from .filters import (
    OnlyLastVerificationFilter,
    HasDataMapperIdFilter,
    HasTeamObjectFilter,
    HasClubObjectFilter,
    HasTextInputFilter,
)


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


@admin.register(models.PlayerPosition)
class PositionAdmin(admin.ModelAdmin):
    pass


DEFAULT_PROFILE_SEARCHABLES = ("user__email", "user__first_name", "user__last_name")
DEFAULT_PROFILE_DISPLAY_FIELDS = (
    "pk",
    linkify("user"),
    "data_mapper_id",
    "slug",
    "active",
)


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


@admin.register(models.ParentProfile)
class ParentProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ManagerProfile)
class ManagerProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileAdminBase):
    exclude = ("voivodeship_raw",)


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
        "club_role",
        linkify("club_object"),
    )
    search_fields = DEFAULT_PROFILE_SEARCHABLES + ("club_object__name",)
    autocomplete_fields = ("club_object",)


def trigger_refresh_data_player_stats(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save comes inside


trigger_refresh_data_player_stats.short_description = (
    "1. Refresh metric data_player on -->  s38"
)


def calculate_metrics(modeladmin, request, queryset):
    for pp in queryset:
        pp.playermetrics.refresh_metrics()  # save comes inside


calculate_metrics.short_description = "2. Calculate Playermeteics <-- s38"


def calculate_fantasy(modeladmin, request, queryset):
    for pp in queryset:
        pp.calculate_fantasy_object()  # save comes inside


calculate_fantasy.short_description = "Calculate fantasy"


def fetch_data_player_meta(modeladmin, request, queryset):
    for pp in queryset:
        pp.fetch_data_player_meta()  # save comes inside


fetch_data_player_meta.short_description = "3. update meta  <--- s38"


def set_team_object_based_on_meta(modeladmin, request, queryset):
    for pp in queryset:
        pp.set_team_object_based_on_meta()  # save comes inside


set_team_object_based_on_meta.short_description = "4. set team_object based on .meta"


def refresh(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save not relevant
        pp.fetch_data_player_meta(save=False)  # save comes inside
        pp.set_team_object_based_on_meta()  # saving
        pp.playermetrics.refresh_metrics()  # save not relevant


refresh.short_description = "0. Refresh( 1, 2,3,4 )"


def update_with_profile_data(modeladmin, request, queryset):
    for ver in queryset:
        ver.update_with_profile_data(requestor=request.user)


update_with_profile_data.short_description = (
    "Updated selected verification object with Profles data"
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
    list_filter = (
        "owner__declared_role",
        "status",
        OnlyLastVerificationFilter,
        HasDataMapperIdFilter,
        HasTextInputFilter,
        ("has_team", admin.BooleanFieldListFilter),
        ("team_not_found", admin.BooleanFieldListFilter),
        HasTeamObjectFilter,
        HasClubObjectFilter,
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
        linkify("playermetrics"),
        "team_object_linkify",
        linkify("team_object_alt"),
        "display_league",
        "display_team",
        "display_club",
        "display_seniority",
        "display_gender",
        "meta_updated",
        "meta_last",
        linkify("verification"),
    )

    def team_object_linkify(self, obj=None):
        if obj.team_object: 
            return linkify("team_object")(
                obj, obj.team_object.name_with_league_full
            )
        else: return "-"
    
    team_object_linkify.short_description = "team_object"

    def meta_last(self, obj):
        if obj.meta:
            return list(obj.meta.items())[-1]
        else:
            obj.meta

    autocomplete_fields = ("user", "team_object", "team_object_alt")

    actions = [
        refresh,
        calculate_metrics,
        trigger_refresh_data_player_stats,
        fetch_data_player_meta,
        set_team_object_based_on_meta,
        calculate_fantasy,
    ]


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + ("team_object_linkify",)
    autocomplete_fields = ("team_object",)

    def team_object_linkify(self, obj=None):
        if obj.team_object: 
            return linkify("team_object")(
                obj, obj.team_object.name_with_league_full
            )
        else: return "-"
    
    team_object_linkify.short_description = "team_object"


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


@admin.register(models.PlayerVideo)
class PlayerVideoAdmin(admin.ModelAdmin):
    pass