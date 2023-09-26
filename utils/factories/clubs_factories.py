import factory

from clubs import models as clubs_models
from clubs.management.commands.utils import generate_club_or_team_short_name

from . import utils
from .base import CustomObjectFactory
from .consts import *
from .user_factories import UserFactory


class ClubFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Club
        django_get_or_create = ("name",)

    name = factory.Iterator(CLUB_NAMES)
    short_name = factory.LazyAttribute(lambda o: generate_club_or_team_short_name(o))
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    club_phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    club_email = CLUB_MAIL
    stadion_address = factory.LazyAttribute(lambda _: utils.get_random_address())
    practice_stadion_address = factory.LazyAttribute(
        lambda _: utils.get_random_address()
    )
    manager = UserFactory.random_object()

    @factory.post_generation
    def manager(self, *args, **kwargs) -> None:
        """Set manager, None if User is already manager of other Club"""
        if self.manager and clubs_models.Club.objects.filter(manager=self.manager):
            self.manager = None


class GenderFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Gender
        django_get_or_create = ("name",)

    name = factory.Iterator(GENDERS)


class SeniorityFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Seniority
        django_get_or_create = ("name",)

    name = factory.Iterator(SENIORITIES)
    is_senior = False

    @factory.post_generation
    def is_senior(self, create, extracted, **kwargs) -> None:
        """define is_senior based on name field"""
        self.is_senior = self.name == "Senior"


class TeamFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Team
        django_get_or_create = ("name",)

    name = factory.Iterator(TEAM_NAMES)
    short_name = factory.LazyAttribute(lambda o: generate_club_or_team_short_name(o))
    club = factory.SubFactory(ClubFactory)
    manager = UserFactory.random_object()
    game_bonus = factory.LazyAttribute(lambda _: utils.get_random_bool())
    gloves_shoes_refunds = factory.LazyAttribute(lambda _: utils.get_random_bool())
    scolarships = factory.LazyAttribute(lambda _: utils.get_random_bool())
    traning_gear = factory.LazyAttribute(lambda _: utils.get_random_bool())
    regular_gear = factory.LazyAttribute(lambda _: utils.get_random_bool())
    secondary_trainer = factory.LazyAttribute(lambda _: utils.get_random_bool())
    fizo = factory.LazyAttribute(lambda _: utils.get_random_bool())
    diet_suplements = factory.LazyAttribute(lambda _: utils.get_random_bool())
    travel_refunds = factory.LazyAttribute(lambda _: utils.get_random_bool())
    seniority = factory.SubFactory(SeniorityFactory)
    gender = factory.SubFactory(GenderFactory)

    @factory.post_generation
    def manager(self, *args, **kwargs) -> None:
        """Set manager, None if User is already manager of other Team"""
        if self.manager and clubs_models.Team.objects.filter(manager=self.manager):
            self.manager = None


class SeasonFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Season
        django_get_or_create = ("name",)

    name = factory.Iterator(SEASON_NAMES)


class LeagueFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.League
        django_get_or_create = ("name",)

    name = factory.Iterator(LEAGUE_NAMES)
    seniority = factory.SubFactory(SeniorityFactory)
    gender = factory.SubFactory(GenderFactory)
    visible = True

    @classmethod
    def create_league_as_highest_parent(cls, **kwargs) -> clubs_models.League:
        """Create League with highest_parent as self"""
        league = cls.create(**kwargs)
        league.highest_parent = league
        league.save()
        return league


class LeagueHistoryFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.LeagueHistory
        django_get_or_create = ("league", "season")

    league = factory.SubFactory(LeagueFactory)
    season = factory.SubFactory(SeasonFactory)


class TeamHistoryFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.TeamHistory
        django_get_or_create = ("team", "league_history")

    team = factory.SubFactory(TeamFactory)
    league_history = factory.SubFactory(LeagueHistoryFactory)


class ClubWithHistoryFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Club
        django_get_or_create = ("name",)

    name = factory.Iterator(CLUB_NAMES)
    short_name = factory.LazyAttribute(lambda o: generate_club_or_team_short_name(o))
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    club_phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    club_email = CLUB_MAIL
    stadion_address = factory.LazyAttribute(lambda _: utils.get_random_address())
    practice_stadion_address = factory.LazyAttribute(
        lambda _: utils.get_random_address()
    )
    manager = UserFactory.random_object()
    picture = factory.django.ImageField()

    @factory.post_generation
    def add_history(self, create: bool, extracted, **kwargs) -> None:
        """
        Post-generation method to create a historical record for a club.

        When a club is created using the factory, this method will automatically create
        a corresponding team for the club, a league history, and then associate both
        through a TeamHistory record.
        """
        if not create:
            return

        team = TeamFactory(club=self)
        league_history = LeagueHistoryFactory()
        TeamHistoryFactory(team=team, league_history=league_history)
