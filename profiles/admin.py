

from django.contrib import admin
from utils import linkify

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


class ProfileAdminBase(admin.ModelAdmin):
    search_fields = ['user__email', 'user__first_name', 'user__last_name']


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
    list_display = ('pk', 'user', 'club_object')
    search_fields = ('club_object',)
    autocomplete_fields = ('club_object',)


def calculate_metrics(modeladmin, request, queryset):
    for pp in queryset:
        pp.playermetrics.refresh_metrics()  # save comes inside


calculate_metrics.short_description = "Calculate metrics"


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = ('pk', 'user', 'data_mapper_id', linkify('playermetrics'), 'team_object')
    autocomplete_fields = ('team_object',)
    search_fields = ('team_object',)
    actions = [calculate_metrics]


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    list_display = ('pk', 'user', 'team_object')
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
