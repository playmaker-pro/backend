from django.contrib.admin import SimpleListFilter, BooleanFieldListFilter
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
                When(owner__declared_role="C", then=F("clubprofile__data_mapper_id")),
                When(owner__declared_role="T", then=F("coachprofile__data_mapper_id")),
                When(owner__declared_role="P", then=F("playerprofile__data_mapper_id")),
                default=None,
            )
        )

        if self.value() == "1":
            queryset = queryset.filter(Q(data_mapper_id__isnull=False))
        elif self.value() == "2":
            queryset = queryset.filter(Q(data_mapper_id__isnull=True))
        return queryset
