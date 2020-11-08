

from django.contrib import admin

from .models import StandardProfile, PlayerProfile, RoleChangeRequest, CoachProfile, GuestProfile, ClubProfile


class ProfileAdminBase(admin.ModelAdmin):
    pass


@admin.register(StandardProfile)
class StandardProfileAdmin(ProfileAdminBase):
    pass


@admin.register(GuestProfile)
class GuestProfileAdmin(ProfileAdminBase):
    pass


@admin.register(ClubProfile)
class ClubProfileAdmin(ProfileAdminBase):
    pass


@admin.register(PlayerProfile)
class PlayerProfileAdmin(ProfileAdminBase):
    list_display = ('pk', 'user', 'weight')


@admin.register(CoachProfile)
class CoachProfileAdmin(ProfileAdminBase):
    pass


@admin.register(RoleChangeRequest)
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
