

from django.contrib import admin
from users.queries import get_users_manger_roles
from . import models
from utils import linkify
from django.utils.html import format_html


def calculate(modeladmin, request, queryset):
    for fant in queryset:
        fant.calculate()  # save comes inside


calculate.short_description = "przelicz metryke"


@admin.register(models.PlayerFantasyRank)
class PlayerFantasyRankAdmin(admin.ModelAdmin):
    list_display = ('updated', linkify('season'), linkify('player'), 'get_profile_permalink', 'senior', 'score')
    search_fields = ('player__email',)
    autocomplete_fields = ('player',)
    actions = [calculate, ]

    def get_profile_permalink(self, obj):
        url = obj.player.profile.get_permalink
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))

    get_profile_permalink.short_description = 'Profile Link'


@admin.register(models.FantasySettings)
class FantasySettingsRankAdmin(admin.ModelAdmin):
    pass
