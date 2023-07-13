from django.core.management.base import BaseCommand, CommandParser
from pydantic import typing
from backend.settings.config import Configuration
from utils import factories
from utils.factories import CustomObjectFactory, clubs_models
from voivodeships.services import VoivodeshipService
from django.conf import settings
from django.db import connection
from app import errors


class Command(BaseCommand):
    """
    Script creates multiple objects based on given params.
    Insert mocked objects to current database.
    It is recommended to run script on empty database.
    Script will validate current environment and database
    to forbid use in production. Voivodeships are initialized for mocks.
    Script creates superuser for easy management.
    """

    help = "Create mocked objects to database"

    def __init__(self) -> None:
        super().__init__()
        self.env, self.database_name = self.fetch_system_data()
        self.teams_mocked: bool = False
        self.leagues_mocked: bool = False
        self.count: int = 0

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Parse arguments into script
        passing --all overwrites any other model-based argument
        default count of objects: 4 (4 objects per model)
        """
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create all models, overwrite other method based flags",
        )
        parser.add_argument(
            "--profiles",
            action="store_true",
            default=False,
            help="Create players, coaches, scouts, guests and clubs profiles",
        )
        parser.add_argument(
            "--users",
            action="store_true",
            default=False,
            help="Create blank users",
        )
        parser.add_argument(
            "--teams",
            action="store_true",
            default=False,
            help="Create teams with their clubs",
        )
        parser.add_argument(
            "--leagues",
            action="store_true",
            default=False,
            help="Create leagues",
        )
        parser.add_argument(
            "--histories",
            action="store_true",
            default=False,
            help="Create seasons, leagues, league_histories, team_histories with their teams and clubs",
        )
        parser.add_argument(
            "-count", action="store", default=4, help="How many objects per model?"
        )

    def create_batch(
        self,
        factory_class: typing.Type[CustomObjectFactory],
        count: int = None,
        **kwargs,
    ) -> list:
        """Create batch of objects for given factory"""
        return factory_class.create_batch(count or self.count, **kwargs)

    def mock_users(self) -> None:
        """Create blank users"""
        self.create_batch(factories.UserFactory)

    def mock_player_profiles(self) -> None:
        """Create player profiles with users"""
        self.create_batch(factories.PlayerProfileFactory)

    def mock_coach_profiles(self) -> None:
        """Create coach profiles with users"""
        self.create_batch(factories.CoachProfileFactory)

    def mock_club_profiles(self) -> None:
        """Create club profiles with users"""
        self.create_batch(factories.ClubProfileFactory)

    def mock_scout_profiles(self) -> None:
        """Create scout profiles with users"""
        self.create_batch(factories.ScoutProfileFactory)

    def mock_guest_profiles(self) -> None:
        """Create guest profiles with users"""
        self.create_batch(factories.GuestProfileFactory)

    def mock_seasons(self) -> None:
        """Create seasons"""
        self.create_batch(factories.SeasonFactory, 4)

    def mock_leagues(self, history: bool = True) -> None:
        """Create leagues"""
        leagues: typing.List[clubs_models.League] = self.create_batch(
            factories.LeagueFactory
        )
        self.leagues_mocked = True
        if history:
            self.mock_league_histories(leagues)

    def mock_league_histories(
        self, leagues: typing.List[clubs_models.League] = None
    ) -> None:
        """
        Create league histories
        Each newly created league per season
        """
        for league in leagues or self.get_mocked_leagues():
            self.create_batch(factories.LeagueHistoryFactory, league=league)

    def mock_clubs(self) -> None:
        """Create clubs"""
        self.create_batch(factories.ClubFactory)

    def mock_teams(self, history: bool = True) -> None:
        """Create teams"""
        teams: typing.List[clubs_models.Team] = self.create_batch(factories.TeamFactory)
        self.teams_mocked = True
        if history:
            self.mock_team_histories(teams)

    def mock_team_histories(self, teams: typing.List[clubs_models.Team] = None) -> None:
        """
        Create team histories
        Each newly created team per season
        """
        for team in teams or self.get_mocked_teams():
            self.create_batch(factories.TeamHistoryFactory, team=team)

    def init_validation(self) -> None:
        """
        Verify this isn't either production database or production environment
        Raise exception if so
        """
        print(f"---\tDATABASE: {self.database_name}, ENVIRONMENT: {self.env}\t---")
        if self.env is Configuration.PRODUCTION:
            raise errors.ForbiddenInProduction
        if self.database_name == "p1008_production":
            raise errors.ForbiddenWithProductionDatabase

    def create_admin_user(self) -> None:
        """
        Create admin user
        login: admin@playmaker.pro
        password: database password
        """
        factories.UserFactory.create_admin_user(
            password=connection.settings_dict["PASSWORD"]
        )

    def set_voivodeships(self) -> None:
        """Create initial voivodeships from mock"""
        manager = VoivodeshipService()
        if not manager.get_voivodeships:
            manager.save_to_db()

    def set_objects_count(self, count: int) -> None:
        """Set how many objects per model should be created"""
        self.count = int(count)

    def fetch_system_data(self) -> (str, str):
        """Get app environment and current database name"""
        return settings.CONFIGURATION, connection.settings_dict["NAME"]

    def mock_profiles(self) -> None:
        """Mock all profiles"""
        self.mock_player_profiles()
        self.mock_coach_profiles()
        self.mock_club_profiles()
        self.mock_scout_profiles()
        self.mock_guest_profiles()

    def mock_clubs_and_teams(self, history: bool = True) -> None:
        """Mock teams and clubs without creating teamhistory"""
        self.mock_clubs()
        self.mock_teams(history=history)

    def mock_historical(self) -> None:
        """
        Mock seasons, league_histories (leagues if needed),
        team_histories (teams and clubs if needed)
        """
        self.mock_seasons()

        if not self.teams_mocked:
            self.mock_clubs_and_teams()
        else:
            self.mock_team_histories()

        if not self.leagues_mocked:
            self.mock_leagues()
        else:
            self.mock_league_histories()

    def get_mocked_teams(self) -> typing.List[clubs_models.Team]:
        """Get teams previously created by script"""
        return clubs_models.Team.objects.filter(name__in=factories.TEAM_NAMES)

    def get_mocked_leagues(self) -> typing.List[clubs_models.League]:
        """Get leagues previously created by script"""
        return clubs_models.League.objects.filter(name__in=factories.LEAGUE_NAMES)

    def handle(self, *args, **options) -> None:
        """
        Insert mocked objects to current database.
        It is recommended to run script on empty database.
        Script will validate current environment and database
        to forbid use in production. Voivodeships are initialized for mocks.
        Script creates superuser for easy management.
        """
        self.init_validation()
        self.set_voivodeships()
        self.create_admin_user()
        self.set_objects_count(options.get("count"))
        mock_all = options.get("all")

        (options.get("users") or mock_all) and self.mock_users()
        (options.get("profiles") or mock_all) and self.mock_profiles()
        (options.get("leagues") or mock_all) and self.mock_leagues(history=False)
        (options.get("teams") or mock_all) and self.mock_clubs_and_teams(history=False)
        (options.get("histories") or mock_all) and self.mock_historical()
