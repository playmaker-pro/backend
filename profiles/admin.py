

from django.contrib import admin

from .models import Profile, PlayerProfile, RoleChangeRequest

@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(RoleChangeRequest)
class RoleChangeRequestAdmin(admin.ModelAdmin):
    pass
