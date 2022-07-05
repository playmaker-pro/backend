from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin  # as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from utils import linkify
from django.contrib.admin import SimpleListFilter, ChoicesFieldListFilter
from . import models
from django.db.models import (
    Q,
    Value,
    BooleanField,
    Case,
    When,
    ForeignKey,
    IntegerField,
    F,
)


def verify_one(modeladmin, request, queryset):
    f = queryset.first()
    f.verify()
    f.save()


class VerificationFilter(ChoicesFieldListFilter):
    title = "Werifikacja"
    parameter_name = "Werifikacja"

    def lookups(self, request, model_admin):
        return [
            (1, '{player,coach} - dropdown - "" - hasMapperID'),
            (2, '{player,coach} - dropdown - "" - noMapperID'),
            (3, "{player,coach} - input - noTeamInDropdown - hasMapperID"),
            (4, "{player,coach} - input - noTeamInDropdown - noMapperID"),
            (5, "{player,coach} - input - hasNoTeamNow - noMapperID"),
            (6, "{player,coach} - input - hasNoTeamNow - hasMapperID"),
            (7, "{player,coach} - input - hasNoTeamNever - noMapperID"),
            (8, "{player,coach} - input - hasNoTeamNever - hasMapperID"),
            (9, '{club} - dropdown - "" - ""'),
            (10, '{club} - input - noTeamInDropdown - ""'),
            (11, '{club} - input - hasNoTeamNow - ""'),
            (12, '{club} - input - hasNoTeamNever - ""'),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related(
            "clubprofile", "coachprofile", "playerprofile"
        ).annotate(
            data_mapper_id=Case(
                When(declared_role="C", then=F("clubprofile__data_mapper_id")),
                When(declared_role="T", then=F("coachprofile__data_mapper_id")),
                When(declared_role="P", then=F("playerprofile__data_mapper_id")),
            ),
            team_club_league_voivodeship_ver=Case(
                When(
                    declared_role="C",
                    then=F("clubprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="T",
                    then=F("coachprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="P",
                    then=F("playerprofile__team_club_league_voivodeship_ver"),
                ),
            ),
        )

        # if self.value() in ['9', '10', '11', '12']:
        #     query = Q(declared_role__in=['C'])
        #     # queryset = queryset.filter(declared_role__in=['T', 'P'])
        # else:
        #     # queryset = queryset.filter(declared_role__in=['C'])
        #     query = Q(declared_role__in=['T', 'P'])

        if self.value() in ["1", "3", "6", "8"]:
            query = Q(data_mapper_id__isnull=False)
        else:
            query = Q(data_mapper_id__isnull=False)
            # queryset = queryset.filter(data_mapper_id__isnull=False)

        # if self.value() in ['3', '4', '5', '6', '7', '8', '10', '11', '12']:
        #     query &= Q(team_club_league_voivodeship_ver__isnull=False)
        # queryset = queryset.filter(team_club_league_voivodeship_ver__isnull=False)

        return queryset.filter(query)


class VerificationInputTypeFilter(SimpleListFilter):
    title = "VerificationInputType"
    parameter_name = "VerificationInputType"

    def lookups(self, request, model_admin):
        return [
            (1, "HasTextInput"),
            (2, "HasTeamObject"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related(
            "clubprofile", "coachprofile", "playerprofile"
        ).annotate(
            text_input=Case(
                When(
                    declared_role="C",
                    then=F("clubprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="T",
                    then=F("coachprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    declared_role="P",
                    then=F("playerprofile__team_club_league_voivodeship_ver"),
                ),
                default=None,
            ),
            team_object=Case(
                When(declared_role="C", then=F("clubprofile__club_object")),
                When(declared_role="T", then=F("coachprofile__team_object")),
                When(declared_role="P", then=F("playerprofile__team_object")),
                default=None,
            ),
        )

        if self.value() == "1":
            queryset = queryset.filter(text_input__isnull=False)
        elif self.value() == "2":
            queryset = queryset.filter(team_object__isnull=False)
        return queryset


class HasDataMapperIdFilter(SimpleListFilter):
    title = "Data mapper id"
    parameter_name = "data_mapper_id"

    def lookups(self, request, model_admin):
        return [
            (1, "hasMapperID"),
            (2, "noMapperID"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related(
            "clubprofile", "coachprofile", "playerprofile"
        ).annotate(
            data_mapper_id=Case(
                When(declared_role="C", then=F("clubprofile__data_mapper_id")),
                When(declared_role="T", then=F("coachprofile__data_mapper_id")),
                When(declared_role="P", then=F("playerprofile__data_mapper_id")),
                default=None,
            )
        )

        if self.value() == "1":
            query = Q(data_mapper_id__isnull=False)
        else:
            query = Q(data_mapper_id__isnull=True)
        return queryset.filter(query)


@admin.register(models.User)
class UserAdminPanel(UserAdmin):
    fieldsets = (
        (None, {"fields": ("password",)}),  # 'username',
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Piłkarskie fakty"),
            {"fields": ("declared_role", "state", "picture", "declared_club")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    list_display = (
        "username",
        "first_name",
        "last_name",
        "state",
        "is_active",
        "last_login",
        "date_joined",
        "get_profile",
        "get_profile_permalink",
        linkify("profile"),
        "get_profile_percentage",
        "declared_role",
        "get_data_mapper_id",
        "get_team_object",
        "get_team_club_league_voivodeship_ver",
    )
    list_filter = ("state", "declared_role")
    search_fields = ("username", "first_name", "last_name", "declared_role")

    actions = [verify_one]

    def get_team_object(self, obj):
        if obj.is_club:
            if obj.profile.club_object:
                return obj.profile.club_object
        elif obj.is_coach or obj.is_player:
            if obj.profile.team_object:
                return obj.profile.team_object

    def get_team_club_league_voivodeship_ver(self, obj):
        try:
            return obj.profile.team_club_league_voivodeship_ver
        except:
            return ""

    def get_data_mapper_id(self, obj):
        return obj.profile.data_mapper_id

    def get_profile_percentage(self, obj):
        percentage = obj.profile.percentage_completion
        return format_html(
            f"""
            <progress value="{percentage}" max="100"></progress>
            <span style="font-weight:bold">{percentage}%</span>
            """
        )

    get_profile_percentage.short_description = "Profile %"

    def get_profile_permalink(self, obj):
        url = obj.profile.get_permalink
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))

    get_profile_permalink.short_description = "Profile Link"

    def get_profile(self, obj):
        if obj.profile is not None:
            return obj.profile.PROFILE_TYPE
        else:
            return "missing profile"

    get_profile.short_description = "Profile Type"
