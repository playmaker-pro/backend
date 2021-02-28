

from django.contrib import admin
from users.queries import get_users_manger_roles
from . import models
from utils import linkify


def calculate(modeladmin, request, queryset):
    for fant in queryset:
        fant.calculate()  # save comes inside


calculate.short_description = "przelicz metryke"


@admin.register(models.PlayerFantasyRank)
class PlayerFantasyRankAdmin(admin.ModelAdmin):
    list_display = ('updated', linkify('season'), linkify('player'), 'senior', 'score')
    search_fields = ('player__email',)
    autocomplete_fields = ('player',)
    actions = [calculate, ]


@admin.register(models.FantasySettings)
class FantasySettingsRankAdmin(admin.ModelAdmin):
    pass
