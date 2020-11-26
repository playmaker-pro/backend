

from django.contrib import admin

from . import models


@admin.register(models.ProfileVisitHistory)
class ProfileVisitHistoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.PlayerMetrics)
class PlayerMetricsAdmin(admin.ModelAdmin):
    pass


class ProfileAdminBase(admin.ModelAdmin):
    pass


@admin.register(models.ScoutProfile)
class ScoutProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    pass


@admin.register(models.PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = ('pk', 'user', 'weight')


@admin.register(models.CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    pass


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
