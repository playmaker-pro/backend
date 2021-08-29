from django.contrib import admin
from users.queries import get_users_manger_roles
from app.admin_utils import json_filed_data_prettified
from . import models
from utils import linkify


def reset_history(modeladmin, request, queryset):
    for h in queryset:
        h.reset()


reset_history.short_description = 'Reset history league data.'


@admin.register(models.LeagueHistory)
class LeagueHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "season",
        "league",
        "league_slug",
        "index",
        "is_table_data",
        "is_matches_data",
        "data_updated",
        "is_data",
    )
    ordering = ("-league",)
    readonly_fields = ('data_prettified',)
    actions = [reset_history,]
    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.data, limit=150000)

    def is_data(self, obj):
        if obj.data is not None and obj.data:
            return True
        return False

    is_data.boolean = True


@admin.register(models.Season)
class SeasonAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(models.Seniority)
class SeniorityAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(models.Gender)
class GenderAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    search_fields = ("name", "slug")
    list_display = (
        "name",
        "order",
        "visible",
        "is_parent",
        "parent_of",
        "index",
        "code",
        "slug",
        "search_index",
    )

    def parent_of(self, obj):
        return obj.parent.name if obj.parent else ""

    def is_parent(self, obj):
        return obj.is_parent

    is_parent.boolean = True


@admin.register(models.Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mapping",
        "visible",
        "autocreated",
        linkify("club"),
        linkify("league"),
        linkify("gender"),
        linkify("seniority"),
        linkify("manager"),
    )
    search_fields = ("name",)
    list_filter = ("league__name", "gender__name", "seniority__name")
    autocomplete_fields = ("manager",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["manager"].queryset = get_users_manger_roles()
        form.base_fields["editors"].queryset = get_users_manger_roles()
        return form


@admin.register(models.Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mapping",
        "autocreated",
        linkify("manager"),
        linkify("voivodeship"),
        "slug",
    )
    autocomplete_fields = ("manager",)
    search_fields = ("name",)
    list_filter = ("voivodeship__name",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["manager"].queryset = get_users_manger_roles()
        form.base_fields["editors"].queryset = get_users_manger_roles()
        return form
