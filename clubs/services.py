import datetime
import typing

from django.contrib.auth.models import User
from django.db import models as django_models
from django.db.models import F, QuerySet, ObjectDoesNotExist

from clubs import errors, models
from clubs.api.api_filters import ClubFilter


class SeasonService:
    @staticmethod
    def is_valid(season: str) -> bool:
        """Check if given season is valid. Season must be in format: YYYY/YYYY"""

        if "/" not in season:
            return False

        if len(season.split("/")) != 2:
            return False

        first_year, second_year = season.split("/")

        if (
            len(first_year) != 4
            or len(second_year) != 4
            or not first_year.isdigit()
            or not second_year.isdigit()
        ):
            return False

        if int(first_year) == int(second_year):
            return False

        # Validate that start year is not greater
        # than the current year
        if int(first_year) > datetime.date.today().year:
            return False

        # Validate end year is not greater
        # than the current year + 1
        if int(second_year) > datetime.date.today().year + 1:
            return False

        return True

    @staticmethod
    def is_current_season_parameter_valid(current_season: str) -> bool:
        """Check if given current_season parameter is valid"""
        if current_season not in ["true"]:
            return False
        return True

    @staticmethod
    def get(name) -> models.Season:
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
        queryset = (
            models.Club.objects.all()
            .prefetch_related("teams", "teams__historical")
            .order_by("name")
        )

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


class TeamHistoryCreationService:
    DEFAULT_COUNTRY_CODE = "PL"
    DEFAULT_STATUS = "not-ver"

    def initialize_model_instance(
        self, model_instance: django_models.Model, user: User
    ) -> None:
        """
        Initializes the given model instance with default attributes and saves it to the database.

        """
        model_instance.status = self.DEFAULT_STATUS
        model_instance.created_by = user
        model_instance.enabled = False
        model_instance.visible = False
        model_instance.save()

    def get_or_create(
        self, validated_data: dict, user, country_code: str
    ) -> models.Team:
        """
        Retrieves an existing team or creates a new one based on the provided data.

        The method uses the 'team_parameter' key from the validated_data. If 'team_parameter' is
        an integer, it's assumed to be the ID of the team and the team is retrieved by its ID.
        If it's a string, it's assumed to be the name of the team and the method will either retrieve
        an existing team with that name or create a new one, depending on whether a match is found.
        """
        team_parameter: typing.Union[str, int] = validated_data.get("team_parameter")

        gender: typing.Optional[models.Gender] = self.determine_gender(
            validated_data, team_parameter, country_code
        )

        # Set seniority conditionally based on the country code
        if country_code == self.DEFAULT_COUNTRY_CODE:
            seniority = self.get_seniority_from_league(
                validated_data.get("league_identifier")
            )
        else:
            seniority = None
        if isinstance(team_parameter, int):
            return self.get_team_by_id(team_parameter)
        else:
            return self.get_or_create_team_by_name(
                team_parameter, gender, seniority, user
            )

    @staticmethod
    def get_seniority_from_league(league_id: int) -> str:
        """
        Retrieve the seniority of a league based on its ID.

        This method fetches a league by its ID and returns the seniority associated with that league.
        If the league does not exist, a LeagueDoesNotExist error is raised.
        """
        league = models.League.objects.filter(id=league_id).first()
        if not league:
            raise errors.LeagueNotFoundServiceException()
        return league.seniority

    def determine_gender(
        self,
        validated_data: dict,
        team_parameter: typing.Union[str, int],
        country_code: str,
    ) -> typing.Optional[models.Gender]:
        """
        Determine the gender based on provided data, team parameter, and country code.

        For the default country code (e.g., 'PL'), the gender is determined either:
        - Directly from the team_parameter if it's an integer.
        - Or from the league identifier in the validated data.

        For other country codes, the gender is fetched from the validated data.
        """
        if country_code != self.DEFAULT_COUNTRY_CODE:
            return self.get_gender_from_data(validated_data)
        elif isinstance(team_parameter, int):
            return None
        return self.get_gender_from_league(validated_data.get("league_identifier"))

    @staticmethod
    def get_gender_from_data(validated_data: dict) -> typing.Optional[models.Gender]:
        """
        Extract and retrieve the Gender instance from the provided data.
        """
        gender_id: int = validated_data.get("gender", None)
        if not gender_id:
            return
        try:
            return models.Gender.objects.get(id=gender_id)
        except models.Gender.DoesNotExist:
            return

    @staticmethod
    def get_team_by_id(team_id: int) -> typing.Optional[models.Team]:
        """
        Retrieve a team based on its ID.
        """
        club_service = ClubService()
        team: typing.Optional[models.Team] = club_service.team_exist(team_id)
        if not team:
            raise errors.TeamNotFoundServiceException()
        return team

    def get_or_create_team_by_name(
        self, team_name: str, gender: models.Gender, seniority: str, user
    ) -> models.Team:
        """
        Retrieve an existing team by name or create a new one if it doesn't exist.

        This function first tries to get a team by its name and gender. If the team is found
        and it's marked as visible and enabled, it raises a TeamAlreadyExist error.
        If the team isn't found, a new team is created with the provided name and gender.
        The newly created team is then initialized with default values.
        """
        team = models.Team.objects.filter(
            name__iexact=team_name, gender=gender, seniority=seniority
        ).first()

        if team and team.visible and team.enabled:
            raise errors.TeamAlreadyExist()
        if not team:
            team = models.Team(name=team_name, gender=gender, seniority=seniority)
            self.initialize_model_instance(team, user)
        return team

    @staticmethod
    def get_gender_from_league(league_id: int) -> models.Gender:
        """
        Retrieve the gender associated with a league.
        """
        league = models.League.objects.filter(id=league_id).first()
        if not league:
            raise errors.LeagueNotFoundServiceException()
        return league.gender

    def create_or_get_team_history(
        self, team: models.Team, league_history: models.LeagueHistory, user
    ) -> models.TeamHistory:
        """
        Retrieve or create a history record for the given team and league history.
        """
        team_history = models.TeamHistory.objects.filter(
            team=team, league_history=league_history, season=league_history.season
        ).first()

        if not team_history:
            team_history = models.TeamHistory.objects.create(
                team=team, league_history=league_history, season=league_history.season
            )
            self.initialize_model_instance(team_history, user)

        return team_history

    def create_or_get_league_history(
        self, season_id: int, league: models.League, user, year
    ) -> models.LeagueHistory:
        """
        Retrieve or create a league history record for the given season and league.
        """
        try:
            league_history, created = (
                models.LeagueHistory.objects.get_or_create(
                    season_id=season_id, league=league
                )
                if season_id
                else models.LeagueHistory.objects.get_or_create(
                    league=league, year=year
                )
            )
        except models.LeagueHistory.MultipleObjectsReturned:
            # Get the first record as a fallback
            league_history = models.LeagueHistory.objects.filter().first()
            created = False
        except ObjectDoesNotExist:
            raise errors.SeasonDoesNotExistServiceException()

        if created:
            self.initialize_model_instance(league_history, user)
        return league_history

    def create_or_get_league_by_name(
        self, league_identifier: str, country_code: str, user, gender: models.Gender
    ) -> models.League:
        """
        Retrieve an existing league by its identifier or create a new one if it doesn't exist.

        This function attempts to get a league using the provided identifier (name).
        If a league with the given identifier isn't found, a new league is created with the
        provided identifier, country code, and gender. The newly created league is then
        initialized with default values.
        """
        league, created = models.League.objects.get_or_create(
            name=league_identifier, defaults={"country": country_code, "gender": gender}
        )
        if created:
            self.initialize_model_instance(league, user)
        return league

    def get_league_based_on_country(
        self,
        league_identifier: typing.Union[str, int],
        country_code: str,
        user,
        gender: models.Gender,
    ) -> models.League:
        """
        Retrieve a league based on its identifier and country.
        Handles logic to differentiate between local ("PL") and foreign leagues.
        """
        if country_code != self.DEFAULT_COUNTRY_CODE:
            return self.create_or_get_league_by_name(
                league_identifier, country_code, user, gender
            )

        league = models.League.objects.filter(id=league_identifier).first()
        if not league:
            raise errors.LeagueNotFoundServiceException()
        return league

    def create_or_get_league_and_history(
        self,
        league_identifier: typing.Union[str, int],
        country_code: str,
        season: int,
        user,
        data,
        year: typing.Optional[int] = None,
    ) -> typing.Tuple[models.League, models.LeagueHistory]:
        """
        Retrieve or create a league and its corresponding history record based on provided identifiers.

        This method determines the gender either from provided data (for foreign teams)
        or from the league (for Polish teams). It then retrieves or creates a league based
        on the league identifier and country code. Finally, it fetches or creates a
        league history record for the provided season.
        """
        # Determine gender based on country code
        if country_code != "PL":
            # For foreign teams, derive the gender from the provided data
            gender: typing.Optional[models.Gender] = self.get_gender_from_data(data)
        else:
            # For Polish teams, fetch gender based on the league
            gender: models.Gender = self.get_gender_from_league(league_identifier)

        # Retrieve or create the league entity based on identifier, country, and gender
        league: models.League = self.get_league_based_on_country(
            league_identifier, country_code, user, gender
        )

        # Fetch or establish a league history record for the given season and league
        league_history: models.LeagueHistory = self.create_or_get_league_history(
            season, league, user, year
        )
        # Ensure the league history is properly retrieved or created
        if not league_history:
            raise errors.LeagueHistoryNotFoundServiceException()

        return league, league_history

    @staticmethod
    def fetch_team_history_and_season(team_history_id: int) -> typing.Tuple:
        """
        Fetch the team_history and associated season based on a team_history_id.
        """
        try:
            team_history: models.TeamHistory = (
                models.TeamHistory.objects.select_related("league_history").get(
                    id=team_history_id
                )
            )

        except models.TeamHistory.DoesNotExist:
            raise errors.TeamHistoryNotFoundServiceException()

        season: int = team_history.league_history.season.id
        return team_history, season

    def create_or_get_team_history_for_player(
        self,
        season: int,
        team_parameter: typing.Union[str, int],
        league_identifier: typing.Union[str, int],
        country_code: str,
        user: User,
    ) -> models.TeamHistory:
        """
        Creates or retrieves the TeamHistory instances for a given season and round.

        The method checks if a corresponding TeamHistory exists for the provided season and round.
        If it does, the instance is returned; otherwise, a new one is created.
        """

        # Retrieve or Create the Season based on the provided season parameter
        season_obj = models.Season.objects.filter(id=season).first()
        if not season_obj:
            raise errors.SeasonDoesNotExist()

        # Retrieve or Create the League and its corresponding LeagueHistory
        league, league_history = self.create_or_get_league_and_history(
            league_identifier,
            country_code,
            season_obj.id,
            user,
            {"team_parameter": team_parameter},
        )

        # Retrieve or Create the Team
        team = self.get_or_create(
            {
                "team_parameter": team_parameter,
                "league_identifier": league_identifier,
            },
            user,
            country_code,
        )

        team_history = self.create_or_get_team_history(team, league_history, user)

        return team_history

    def create_or_get_team_history_date_based(
        self,
        start_date: datetime.date,
        end_date: typing.Union[datetime.date, None],
        team_parameter: typing.Union[str, int],
        league_identifier: typing.Union[str, int],
        country_code: str,
        user: User,
    ) -> typing.List[models.TeamHistory]:
        """
        Creates or retrieves the TeamHistory instances for a given date range.

        For each date within the range, the method checks if a corresponding TeamHistory exists. If it does,
        the instance is added to the list of results; otherwise, a new one is created. The method returns
        all TeamHistory instances corresponding to the date range.
        """
        if end_date is None:
            end_date = datetime.date.today()

        if end_date < start_date:
            raise ValueError("End date cannot be before start date.")

        cursor_date = start_date
        team_histories = []
        while cursor_date <= end_date:
            # Retrieve Season for the cursor_date
            current_season_name = models.Season.define_current_season(cursor_date)
            season_obj = models.Season.objects.filter(name=current_season_name).first()

            year = cursor_date.year if not season_obj else None

            league, league_history = self.create_or_get_league_and_history(
                league_identifier,
                country_code,
                season_obj.id if season_obj else None,
                user,
                {"team_parameter": team_parameter},
                year=year,
            )

            # Use existing method to get or create TeamHistory
            team = self.get_or_create(
                {
                    "team_parameter": team_parameter,
                    "league_identifier": league_identifier,
                },
                user,
                country_code,
            )
            team_history = self.create_or_get_team_history(team, league_history, user)

            team_histories.append(team_history)

            # Move cursor_date to the next season start. E.g., if current season is 2020/2021, move to 01-07-2021
            next_season_start_year = int(current_season_name.split("/")[1])
            cursor_date = datetime.date(next_season_start_year, 7, 1)

        return team_histories
