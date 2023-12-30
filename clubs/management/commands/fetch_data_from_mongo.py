import logging as _logging
import typing as _typing
from functools import cached_property as _cached_property
from uuid import UUID as _UUID

from django.core.management.base import BaseCommand as _BaseCommand

import app.scrapper.schemas as _schemas
from app.scrapper.services import ScrapperHttpService as _HttpService
from clubs import models as _clubs_models
from clubs.management.commands.utils import (
    generate_club_or_team_short_name as _generate_club_or_team_short_name,
)
from mapper import models as _mapper_models
from voivodeships.models import Voivodeships as _Voivodeship

MODEL_UNION = _typing.Union[
    _clubs_models.Club,
    _clubs_models.Team,
    _clubs_models.League,
    _clubs_models.LeagueHistory,
]

logger = _logging.getLogger("commands")


class Command(_BaseCommand):
    """
    This class is a Django management command used to fetch clubs, teams, leagues from MongoDB.
    It inherits from Django's BaseCommand class.
    """

    help: str = "Fetch clubs, teams, leagues from MongoDB"
    _http_service: _HttpService = _HttpService()
    _season_range: list

    def add_arguments(self, parser):
        parser.add_argument(
            "-s",
            "--season",
            nargs="*",
            default=None,
            help="Pass seasons like: '-s 2022/2023 2023/2024'",
        )

    def handle(self, *args, **options) -> None:
        """
        This method is the main entry point for the command.
        It fetches leagues and plays, then clubs and teams from MongoDB and saves them to the local database.
        """
        self._season_range = options.get("season", None)
        self._fetch_leagues()
        self._fetch_clubs()

    def _crawl_plays_to_find_voivodeship(
        self, plays: _schemas.LeaguePlayListSchema
    ) -> _schemas.VoivodeshipSchema:
        """
        This method iterates through plays to find the voivodeship.
        """
        for play in plays:
            if play.voivodeship:
                return play.voivodeship

    def _get_team_plays(
        self, team_from_mongo: _schemas.TeamSchema
    ) -> _schemas.LeaguePlayListSchema:
        """
        This method gets all plays for a given team.
        """
        return self._http_service.get_team_plays(team_from_mongo.mapper_id)

    def _find_voivodeship_by_teams(
        self, teams_from_mongo: _schemas.TeamListSchema
    ) -> str:
        """
        This method iterates through teams to find the voivodeship.
        """
        for team_mongo in teams_from_mongo:
            team_mongo_plays: _schemas.LeaguePlayListSchema = self._get_team_plays(
                team_mongo
            )
            voivodeship_mongo: _typing.Optional[
                _schemas.VoivodeshipSchema
            ] = self._crawl_plays_to_find_voivodeship(team_mongo_plays)

            if voivodeship_mongo:
                return voivodeship_mongo.name

    def _handle_club(self, club_from_mongo: _schemas.ClubSchema) -> None:
        """
        This method handles the club data fetched from MongoDB.
        It creates a club object and saves it to the local database.
        """
        if self._season_range:
            teams = [
                team
                for team in club_from_mongo.teams
                if team.season in self._season_range
            ]
            if not teams:
                return
        else:
            teams = club_from_mongo.teams or []

        if not (club := self._exist(club_from_mongo.mapper_id, _clubs_models.Club)):
            club = _clubs_models.Club(**club_from_mongo.dict())
            club.short_name = _generate_club_or_team_short_name(club)

            if club_from_mongo.voivodeship:
                voivodeship_name: str = club_from_mongo.voivodeship.name
            else:
                voivodeship_name = self._find_voivodeship_by_teams(
                    club_from_mongo.teams
                )

            club.voivodeship_obj = self._define_voivodeship_object(voivodeship_name)

            self._make_mapper(club, club_from_mongo.mapper_id)

        for team_mongo in teams:
            if not self._exist(team_mongo.mapper_id, _clubs_models.Team):
                self._handle_team(team_mongo, club)

    def _handle_team(
        self, team_from_mongo: _schemas.TeamSchema, club_from_pg: _clubs_models.Club
    ) -> None:
        """
        This method handles the team data fetched from MongoDB.
        It creates a team object and saves it to the local database.
        """
        team = _clubs_models.Team(**team_from_mongo.dict())
        team.club = club_from_pg
        team.short_name = _generate_club_or_team_short_name(team)
        team.league: _clubs_models.League = self._get_obj(  # type: ignore
            team_from_mongo.league.mapper_id, _clubs_models.League  # type: ignore
        )
        team.season, _ = _clubs_models.Season.objects.get_or_create(
            name=team_from_mongo.season
        )

        team_matches: _schemas.MatchListSchema = self._http_service.get_team_matches(
            team_from_mongo.mapper_id
        )
        gender, league_play = team.league.gender if team.league else None, None
        for match in team_matches:
            if match.play:
                if (
                    match.league
                    and team.league
                    and match.league.mapper_id
                    == team.league.mapper.get_entity(source__name="LNP").mapper_id
                ):
                    league_play = league_play or self._get_obj(
                        match.play.mapper_id, _clubs_models.LeagueHistory
                    )
            else:
                league_play = league_play or self._get_obj(
                    match.league.mapper_id, _clubs_models.LeagueHistory
                )

            gender = gender or match.sex or match.league.gender
            # FIXME: Will be tough to find each attr based on matches (lack of data)

            if league_play and league_play.season != team.season:
                league_play = None

            if gender and league_play:
                break

        team.gender = self._db_gender(gender)
        team.seniority = self._db_seniority(team_from_mongo.seniority)

        team.league_history = league_play
        self._make_mapper(team, team_from_mongo.mapper_id)

    def _fetch_clubs(self) -> None:
        """
        This method fetches clubs from MongoDB.
        """
        clubs: _schemas.ClubListSchema = self._http_service.get_clubs()

        for club_mongo in clubs:
            self._handle_club(club_mongo)

    def _fetch_leagues(self) -> None:
        """
        This method fetches leagues from MongoDB.
        Iterate through leagues and plays to create League and LeagueHistory objects.
        """
        leagues: _schemas.LeagueListSchema = self._http_service.get_leagues()

        if self._season_range:
            leagues = _schemas.LeagueListSchema.parse_obj(
                list(filter(lambda l: l.season in self._season_range, leagues))
            )

        for league_from_mongo in leagues:
            if (
                self._season_range
                and league_from_mongo.season not in self._season_range
            ):
                continue

            if not (
                league := self._exist(league_from_mongo.mapper_id, _clubs_models.League)
            ):
                league_dict = league_from_mongo.dict()
                gender = self._db_gender(
                    league_dict.pop("gender", _schemas.Gender.MALE)
                )
                seniority = self._db_seniority(
                    league_dict.pop("seniority", _schemas.Seniority.SENIOR)
                )

                league = _clubs_models.League(
                    **league_dict, gender=gender, seniority=seniority
                )
                self._make_mapper(league, league_from_mongo.mapper_id)

            for play_from_mongo in league_from_mongo.plays or []:
                if not self._exist(
                    play_from_mongo.mapper_id, _clubs_models.LeagueHistory
                ):
                    season, _ = _clubs_models.Season.objects.get_or_create(
                        name=play_from_mongo.season
                    )
                    voivodeship_obj = (
                        self._define_voivodeship_object(
                            play_from_mongo.voivodeship.name
                        )
                        if play_from_mongo.voivodeship
                        else None
                    )

                    play = _clubs_models.LeagueHistory(
                        **play_from_mongo.dict(),
                        season=season,
                        league=league,
                        voivodeship_obj=voivodeship_obj,
                    )
                    self._make_mapper(play, play_from_mongo.mapper_id)

    def _exist(
        self, _id: _UUID, model: _typing.Type[MODEL_UNION]
    ) -> _typing.Union[MODEL_UNION, bool]:
        """Check if object with given mapper_id exists in database"""
        obj = self._get_obj(_id, model)
        if obj:
            logger.info(f"Object already exist: [{model.__name__} -- {_id}]")
            return obj

    def _get_obj(
        self, _id: _UUID, model: _typing.Type[MODEL_UNION]
    ) -> _typing.Optional[MODEL_UNION]:
        """Get object with given mapper_id"""
        try:
            return model.objects.get(mapper__mapperentity__mapper_id=_id)
        except model.DoesNotExist:
            return

    def _make_mapper(self, instance: MODEL_UNION, mapper_id: _UUID) -> None:
        """Create mapper object for given object"""
        mapper = instance.mapper or _mapper_models.Mapper.objects.create()
        mapper_entity = _mapper_models.MapperEntity.objects.create(
            target=mapper,
            mapper_id=mapper_id,
            source=_mapper_models.MapperSource.objects.get(
                name="LNP"
            ),  # FIXME: DO NOT HARDCODE
            database_source=_mapper_models.MapperEntity.MapperDataSource.MONGODB,
            related_type=instance.MAPPER_RELATED,
        )
        instance.mapper = mapper
        logger.info(
            f"New object: [{instance.__class__.__name__} -- {mapper_entity.mapper_id}]"
        )
        instance.save()

    def _define_voivodeship_object(
        self, voivodeship_name: _typing.Optional[str]
    ) -> _typing.Optional[_Voivodeship]:
        """
        This method defines a voivodeship object based on the voivodeship name.
        """
        if not voivodeship_name:
            return
        return _Voivodeship.objects.get(name__iexact=voivodeship_name)

    class Gender:
        """
        This class is used to get the gender object based on the defined value from the enum.
        """

        @_cached_property
        def male(self) -> _clubs_models.Gender:
            return _clubs_models.Gender.get_male_object()

        @_cached_property
        def female(self) -> _clubs_models.Gender:
            return _clubs_models.Gender.get_female_object()

        def __call__(self, val: _schemas.Gender) -> _clubs_models.Gender:
            """Get gender based on defined value from enum"""
            if isinstance(val, _clubs_models.Gender):
                return val
            if val in [_schemas.Gender.MALE, _schemas.Gender.MIXED]:
                return self.male
            elif val == _schemas.Gender.FEMALE:
                return self.female

    class Seniority:
        """
        This class is used to get the seniority object based on the defined value from the enum.
        """

        @_cached_property
        def senior(self) -> _clubs_models.Seniority:
            return _clubs_models.Seniority.get_senior_object()

        @_cached_property
        def junior(self) -> _clubs_models.Seniority:
            return _clubs_models.Seniority.get_junior_object()

        @_cached_property
        def clj(self) -> _clubs_models.Seniority:
            return _clubs_models.Seniority.get_clj_object()

        def __call__(self, val: _schemas.Seniority) -> _clubs_models.Seniority:
            """Get seniority based on defined value from enum"""
            if isinstance(val, _clubs_models.Seniority):
                return val
            if val == _schemas.Seniority.SENIOR:
                return self.senior
            elif val == _schemas.Seniority.JUNIOR:
                return self.junior
            elif val == _schemas.Seniority.CLJ:
                return self.clj

    _db_gender = Gender()
    _db_seniority = Seniority()
