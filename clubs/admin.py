from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from users.queries import get_users_manger_roles
from app.utils.admin import json_filed_data_prettified
from . import models
from utils import linkify
from django.utils.safestring import mark_safe
from typing import Sequence, Optional, Union


def reset_history(modeladmin, request, queryset):
    for h in queryset:
        h.reset()


reset_history.short_description = "Reset history league data."


@admin.action(description="Aktualizuj visible team")
def update_team_visibility(modeladmin, request, queryset):
    for object in queryset:
        object.visible = object.should_be_visible or False
        object.save()


@admin.action(description="Zaznacz visible = True")
def set_visibility(modeladmin, request, queryset):
    for object in queryset:
        object.visible = True
        object.save()


def resave(modeladmin, request, queryset):
    for object in queryset:
        object.save()


resave.short_description = "Save objects again."


@admin.register(models.LeagueHistory)
class LeagueHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "season",
        "league",
        "get_league_slug",
        "index",
        "is_table_data",
        "is_matches_data",
        "data_updated",
        "is_data",
    )
    ordering: Optional[Sequence[str]] = ("-league",)
    search_fields = ("league",)
    autocomplete_fields = ("league",)
    readonly_fields = ("data_prettified",)
    actions = [
        reset_history,
    ]

    def get_league_slug(self, obj):
        return obj.league.slug

    def data_prettified(self, instance):
        return json_filed_data_prettified(instance.data, limit=150000)

    def is_data(self, obj):
        if obj.data is not None and obj.data:
            return True
        return False

    is_data.boolean = True


@admin.register(models.Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display: Sequence = ("name", "is_current", "is_in_verify_form",)
    search_fields: Sequence = ("name",)
    exclude: Optional[Sequence[str]] = ("is_current",)

@admin.register(models.LeagueGroup)
class LeagueGroupAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.Seniority)
class SeniorityAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.Region)
class RegionAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.Gender)
class GenderAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.JuniorLeague)
class JuniorLeagueAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.SectionGrouping)
class SectionGroupingAdmin(admin.ModelAdmin):
    search_fields: Sequence = ("name",)


@admin.register(models.League)
class LeagueAdmin(admin.ModelAdmin):
    search_fields: Sequence[str]  = ("name", "slug")
    readonly_fields: Sequence[str]  = ("slug", "search_tokens", "virtual", "is_parent")
    actions = [resave]
    list_display = (
        "get_slicer",
        "section",
        "name",
        "get_data_seasons",
        "virtual",
        "order",
        "visible",
        "isparent",
        "is_parent",
        "standalone",
        "league_history",
        "country",
        "parent",
        "childs_no",
        "seniority",
        "gender",
        "index",
        "group",
        "code",
        "slug",
        "search_tokens",
        linkify("highest_parent"),
    )

    def get_slicer(self, obj):
        return f"{obj.get_upper_parent_names()}"

    def get_data_seasons(self, obj):
        return "\n".join([season.name for season in obj.data_seasons.all()])

    def league_history(self, obj):
        return mark_safe(
            "\n".join(
                [
                    f'<a href="{h.get_admin_url()}">{h.season.name}</a>'
                    for h in obj.historical.all()
                ]
            )
        )

    def childs_no(self, obj):
        return obj.get_childs.count()

    def standalone(self, obj):
        return obj.standalone

    def is_parent(self, obj):
        return obj.is_parent

    is_parent.short_description = "is_parent()"
    standalone.boolean = True
    is_parent.boolean = True


@admin.register(models.Voivodeship)
class VoivodeshipAdmin(admin.ModelAdmin):
    search_fields: Sequence[str]  = ("name",)


@admin.register(models.TeamHistory)
class TeamHistoryAdmin(admin.ModelAdmin):
    list_display: Sequence[str] = (
        "id",
        linkify("team"),
        linkify("league_history"),
        "get_season",
        "visible",
        "autocreated",
        )
    search_fields: Sequence[str] = ("team__name",)
    autocomplete_fields: Sequence[str] = ("team", "league_history")
    list_filter: Sequence[str] = (
        "league_history__season__name",
        ("league_history__league__highest_parent", admin.RelatedOnlyFieldListFilter),
        "team__club__voivodeship",
        )

    def get_season(self, obj):
        if obj.league_history.season:
            return obj.league_history.season
        else:
            return None

    get_season.short_description = "Season"
    get_season.admin_order_field = 'league_history__season__name'


class HasManagerFilter(SimpleListFilter):
    title = "hasManager"
    parameter_name = "manager"

    def lookups(self, request, model_admin):

        return [
            ("true", "True"),
            ("false", "False"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.distinct().filter(manager__isnull=False)
        if self.value():
            return queryset.distinct().filter(manager__isnull=True)


@admin.register(models.Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "mapping",
        linkify("club"),
        "junior_group",
        "full_league_linkify",
        linkify("gender"),
        linkify("seniority"),
        linkify("manager"),
        "visible",
        "autocreated",
        "scrapper_autocreated",
    )
    search_fields = ("name",)
    list_filter = ("gender__name", "seniority__name", "visible", HasManagerFilter,)
    actions = [update_team_visibility, set_visibility]
    autocomplete_fields = ("manager", "club", "league",)

    def full_league_linkify(self, obj=None):
        if obj:
            return linkify("league")(obj)        

    full_league_linkify.short_description = "league"

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
        "scrapper_autocreated",
        linkify("manager"),
        linkify("voivodeship_obj"),
        "slug",
    )
    autocomplete_fields: Sequence[str] = ("manager",)
    search_fields: Sequence[str] = ("name",)
    list_filter: Sequence[str] = ("voivodeship_obj__name", HasManagerFilter,)
    exclude: Sequence[str] = ("voivodeship_raw",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["manager"].queryset = get_users_manger_roles()
        form.base_fields["editors"].queryset = get_users_manger_roles()
        return form


@admin.register(models.JuniorAgeGroup)
class JuniorAgeGroupAdmin(admin.ModelAdmin):
    ...
