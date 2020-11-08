

from django.contrib import admin

from . import models


@admin.register(models.Team)
class TeamProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Club)
class ClubProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
