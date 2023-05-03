from django.contrib.admin import BooleanFieldListFilter, SimpleListFilter
from django.db.models import (
    BooleanField,
    Case,
    F,
    ForeignKey,
    IntegerField,
    Q,
    Value,
    When,
)


class OnlyLastVerificationFilter(SimpleListFilter):
    title = "Ostania werifickaja dla aktywnego profilu"
    parameter_name = "only_verification"

    def lookups(self, request, model_admin):
        return [
            (1, "onlyLast"),
            (2, "all"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            queryset = queryset.filter(next__isnull=True)
        if self.value() == "2":
            pass
        return queryset


class TeamNotFoundFilter(SimpleListFilter):
    title = "Team Not Found"
    parameter_name = "team_not_found"

    def lookups(self, request, model_admin):
        return [
            (1, "teamNotFound"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(club__isnull=False)
        return queryset


class HasClubObjectFilter(SimpleListFilter):
    title = "Has Club Object"
    parameter_name = "has_club_object"

    def lookups(self, request, model_admin):
        return [
            (1, "hasClub"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(club__isnull=False)
        return queryset


class HasTeamObjectFilter(SimpleListFilter):
    title = "Has Team Object"
    parameter_name = "has_team_object"

    def lookups(self, request, model_admin):
        return [
            (1, "hasTeam"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "1":
            return queryset.filter(team__isnull=False)
        return queryset


class HasTextInputFilter(SimpleListFilter):
    title = "Has text input"
    parameter_name = "has text input"

    def lookups(self, request, model_admin):
        return [
            (1, "hasTextInput"),
            (2, "emptyTextInput"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.select_related(
            "clubprofile", "coachprofile", "playerprofile"
        ).annotate(
            team_club_league_voivodeship_ver_x=Case(
                When(
                    owner__declared_role="C",
                    then=F("clubprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    owner__declared_role="T",
                    then=F("coachprofile__team_club_league_voivodeship_ver"),
                ),
                When(
                    owner__declared_role="P",
                    then=F("playerprofile__team_club_league_voivodeship_ver"),
                ),
                default=None,
            )
        )

        if self.value() == "1":
            queryset = queryset.filter(
                Q(team_club_league_voivodeship_ver_x__isnull=False)
            )
        elif self.value() == "2":
            queryset = queryset.filter(
                Q(team_club_league_voivodeship_ver_x__isnull=True)
            )
        return queryset


class HasDataMapperIdFilter(SimpleListFilter):
    title = "mapper Id"
    parameter_name = "mapper_id"

    def lookups(self, request, model_admin):
        return [
            (1, "hasMapperID"),
            (2, "noMapperID"),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.distinct()
        if self.value() == "1":
            queryset = queryset.filter(
                Q(
                    owner__declared_role="T",
                    coachprofile__mapper__mapperentity__mapper_id__isnull=False,
                    coachprofile__mapper__mapperentity__database_source="s38",
                )
                | Q(
                    owner__declared_role="P",
                    playerprofile__mapper__mapperentity__mapper_id__isnull=False,
                    playerprofile__mapper__mapperentity__database_source="s38",
                )
            )
        elif self.value() == "2":
            queryset = queryset.exclude(
                Q(
                    owner__declared_role="T",
                    coachprofile__mapper__mapperentity__mapper_id__isnull=False,
                )
                & Q(coachprofile__mapper__mapperentity__database_source="s38")
            ).exclude(
                Q(
                    owner__declared_role="P",
                    playerprofile__mapper__mapperentity__mapper_id__isnull=False,
                )
                & Q(playerprofile__mapper__mapperentity__database_source="s38")
            )
        return queryset
