import factory
from clubs import models as clubs_models
from . import utils
from .user_factories import UserFactory
from .base import CustomObjectFactory
from .consts import *


class ClubFactory(CustomObjectFactory):
    class Meta:
        model = clubs_models.Club
        django_get_or_create = ("name",)

    name = factory.Iterator(CLUB_NAMES)
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    club_phone = utils.get_random_phone_number()
    club_email = CLUB_MAIL
    stadion_address = utils.get_random_address()
    practice_stadion_address = utils.get_random_address()
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
    club = ClubFactory.get_random_or_create_subfactory()
    manager = UserFactory.random_object()
    game_bonus = utils.get_random_bool()
    gloves_shoes_refunds = utils.get_random_bool()
    scolarships = utils.get_random_bool()
    traning_gear = utils.get_random_bool()
    regular_gear = utils.get_random_bool()
    secondary_trainer = utils.get_random_bool()
    fizo = utils.get_random_bool()
    diet_suplements = utils.get_random_bool()
    travel_refunds = utils.get_random_bool()
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
