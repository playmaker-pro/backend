

from django.contrib import admin

from . import models


@admin.register(models.Seniority)
class SeniorityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Gender)
class SeniorityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
