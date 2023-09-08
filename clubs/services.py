import datetime
import typing

from django.db.models import F, QuerySet

from clubs.api.api_filters import ClubFilter

from . import models


class SeasonService:
    @staticmethod
    def validate_season(season: str) -> bool:
        parts = season.split("/")

        # Validate that there are at most two parts
        if len(parts) not in (1, 2):
            return False

        # Validate start year (1 to 4 digits)
        if not (1 <= len(parts[0]) <= 4 and parts[0].isdigit()):
            return False

        # Single year without trailing slash (1 to 4 digits)
        if len(parts) == 1:
            return True

        # Validate that start year is not greater
        # than the current year (if fully specified)
        if len(parts[0]) == 4:
            start_year = int(parts[0])
            if start_year > datetime.date.today().year:
                return False

        # If end year is fully specified,
        # check that it's exactly one year greater
        # than start year (if both fully specified)
        if len(parts[1]) == 4 and parts[1].isdigit() and len(parts[0]) == 4:
            start_year = int(parts[0])
            end_year = int(parts[1])
            if end_year - start_year != 1:
                return False
            return True  # Valid case for fully specified start and end year

        # If end year is partially specified, check that it's 1 or 3 digits
        elif 0 <= len(parts[1]) <= 3 and parts[1].isdigit():
            return True  # Valid case for partially specified end year

        # If end year is an empty string, it's also valid
        elif parts[1] == "":
            return True  # Valid case for single year with trailing slash

        # All other cases are invalid
        return False

    def get(self, name):
        season, _ = models.Season.objects.get_or_create(name=name)
        return season


class AdapterBase:
    def get_mapping_name(self, name: str) -> str:
        return f",,{name},,"


class TeamAdapter(AdapterBase):
    def match_name_or_mapping_with_code(
        self, name: str, code: str
    ) -> typing.Optional[models.Team]:
        try:
            return models.Team.objects.get(name__iexact=name, league__code=str(code))
        except models.Team.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return models.Team.objects.get(
                    mapping__icontains=name, league__code=str(code)
                )
            except models.Team.DoesNotExist:
                return None


class ClubService:
    def team_exist(self, team_id: int) -> typing.Optional[models.Team]:
        """Return Team with given id if exists, None otherwise"""
        try:
            return models.Team.objects.get(id=team_id)
        except models.Team.DoesNotExist:
            return

    def club_exist(self, club_id: int) -> typing.Optional[models.Club]:
        """Return Club with given id if exists, None otherwise"""
        try:
            return models.Club.objects.get(id=club_id)
        except models.Club.DoesNotExist:
            return

    def team_history_exist(self, th_id: int) -> typing.Optional[models.TeamHistory]:
        """Return TeamHistory with given id if exists, None otherwise"""
        try:
            return models.TeamHistory.objects.get(id=th_id)
        except models.TeamHistory.DoesNotExist:
            return


class LeagueService:
    def get_highest_parents(self) -> QuerySet:
        """Get all highest parents"""
        return models.League.objects.filter(highest_parent=F("id"))

    def get_leagues(self) -> QuerySet:
        """Get all leagues"""
        return models.League.objects.all()

    def filter_male(self, queryset: QuerySet) -> QuerySet:
        """Filter queryset by male gender"""
        gender = models.Gender.get_male_object()
        return queryset.filter(gender=gender)

    def filter_female(self, queryset: QuerySet) -> QuerySet:
        """Filter queryset by female gender"""
        gender = models.Gender.get_female_object()
        return queryset.filter(gender=gender)

    def filter_gender(self, queryset: QuerySet, gender: str) -> QuerySet:
        """Filter queryset by gender: {F, M}"""
        if gender.upper() == models.Gender.MALE:
            return self.filter_male(queryset)
        elif gender.upper() == models.Gender.FEMALE:
            return self.filter_female(queryset)
        else:
            return queryset

    def validate_gender(self, gender: str) -> None:
        if gender and gender.upper() not in ["M", "F"]:
            raise ValueError


class ClubTeamService:
    def get_clubs(self, filters: typing.Optional[typing.Dict] = None) -> QuerySet:
        """
        Return all clubs filtered by the provided filters.
        """
        queryset: QuerySet = models.Club.objects.all().order_by("name")
        if filters:
            filter = ClubFilter(filters, queryset=queryset)
            return filter.qs
        return queryset

    @staticmethod
    def validate_gender(gender: str) -> None:
        """
        Validate the gender.
        """
        if gender and gender.upper() not in ["M", "F"]:
            raise ValueError
