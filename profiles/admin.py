

from django.contrib import admin

from .models import StandardProfile, PlayerProfile, RoleChangeRequest, CoachProfile


@admin.register(StandardProfile)
class StandardProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(CoachProfile)
class CoachProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    pass
