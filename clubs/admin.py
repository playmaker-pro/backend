

from django.contrib import admin

from . import models


@admin.register(models.Seniority)
class SeniorityAdmin(admin.ModelAdmin):
    search_fields = ('name')


@admin.register(models.Gender)
class GenderAdmin(admin.ModelAdmin):
    search_fields = ('name')


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    search_fields = ('name')


@admin.register(models.Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin):
    search_fields = ('name')


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ('name')


@admin.register(models.Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')

    search_fields = ('name')