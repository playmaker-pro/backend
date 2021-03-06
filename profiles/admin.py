

from django.contrib import admin
from utils import linkify
from app.admin_utils import json_filed_data_prettified
from . import models


@admin.register(models.ProfileVisitHistory)
class ProfileVisitHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PlayerMetrics)
class PlayerMetricsAdmin(admin.ModelAdmin):
    list_display = ['player', 'games_updated', 'games_summary_updated', 'fantasy_updated', 'fantasy_summary_updated', 'season_updated', 'season_summary_updated']
    search_fields = ['player__user__email', 'player__user__first_name', 'player__user__last_name']


@admin.register(models.PlayerPosition)
class PositionAdmin(admin.ModelAdmin):
    pass


DEFAULT_PROFILE_SEARCHABLES = ('user__email', 'user__first_name', 'user__last_name')
DEFAULT_PROFILE_DISPLAY_FIELDS = ('pk', linkify('user'), 'data_mapper_id', 'active')


class ProfileAdminBase(admin.ModelAdmin):
    search_fields = DEFAULT_PROFILE_SEARCHABLES
    display_fileds = DEFAULT_PROFILE_DISPLAY_FIELDS
    readonly_fields = ('data_prettified',)

    def active(self, obj):
        return obj.is_active

    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.event_log, reverse=True)

    active.boolean = True



@admin.register(models.ParentProfile)
class ParentProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ManagerProfile)
class ManagerProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + ('club_role', linkify('club_object'))
    search_fields = DEFAULT_PROFILE_SEARCHABLES + ('club_object',)
    autocomplete_fields = ('club_object',)


def trigger_refresh_data_player_stats(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save comes inside


trigger_refresh_data_player_stats.short_description = "1. Refresh metric data_player on -->  s38"


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


fetch_data_player_meta.short_description = '3. update meta  <--- s38'


def set_team_object_based_on_meta(modeladmin, request, queryset):
    for pp in queryset:
        pp.set_team_object_based_on_meta()  # save comes inside


set_team_object_based_on_meta.short_description = '4. set team_object based on .meta'


def refresh(modeladmin, request, queryset):
    for pp in queryset:
        pp.trigger_refresh_data_player_stats()  # save not relevant
        pp.fetch_data_player_meta(save=False)  # save comes inside
        pp.set_team_object_based_on_meta()  # saving
        pp.playermetrics.refresh_metrics()  # save not relevant


refresh.short_description = '0. Refresh( 1, 2,3,4 )'


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (
            linkify('playermetrics'),
            linkify('team_object'),
            linkify('team_object_alt'),
            'display_league',
            'display_team',
            'display_club',
            'display_seniority',
            'display_gender',
            'meta_updated',
            'meta_last',
        )

    def meta_last(self, obj):
        if obj.meta:
            return list(obj.meta.items())[-1]
        else:
            obj.meta

    autocomplete_fields = ('user', 'team_object', 'team_object_alt')

    actions = [refresh, calculate_metrics, trigger_refresh_data_player_stats, fetch_data_player_meta, set_team_object_based_on_meta, calculate_fantasy]



@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    list_display = DEFAULT_PROFILE_DISPLAY_FIELDS + (linkify('team_object'),)
    search_fields = ('team_object',)
    autocomplete_fields = ('team_object',)


@admin.register(models.RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    readonly_fields = ('current', 'approver')
    list_display = ('pk', 'user', 'approved', 'current', 'new', 'request_date', 'accepted_date')
    list_filter = ('approved',)
    actions = ['approve_requests', ]

    def approve_requests(self, request, queryset):
        queryset.update(approved=True)

    approve_requests.short_description = "Approve many requets."

    def save_model(self, request, obj, form, change):
        obj.approver = request.user
        super().save_model(request, obj, form, change)
