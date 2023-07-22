import factory
from django.contrib.auth import get_user_model
from .clubs_factories import (
    TeamHistoryFactory,
    ClubFactory,
    UserFactory,
)
from .base import CustomObjectFactory
from profiles import models
from utils.factories.mapper_factories import MapperFactory
import random
from . import utils

User = get_user_model()


class ProfileFactory(CustomObjectFactory):
    user = factory.SubFactory(UserFactory)
    bio = factory.Faker("paragraph", nb_sentences=3)

    class Meta:
        abstract = True


class PlayerMetricsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PlayerMetrics

    games_summary = {"games": "summary"}
    season_summary = {"season": "summary"}
    ...  # TODO(bartnyk): add scoring after merge to master


class ProfileVisitHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProfileVisitHistory

    counter = utils.get_random_int(0, 1000)
    counter_coach = utils.get_random_int(0, 100)
    counter_scout = utils.get_random_int(0, 100)


class PlayerProfileFactory(ProfileFactory):
    class Meta:
        model = models.PlayerProfile

    mapper = factory.SubFactory(MapperFactory)
    team_history_object = TeamHistoryFactory.random_object()
    height = utils.get_random_int(150, 200)
    weight = utils.get_random_int(60, 100)
    birth_date = utils.get_random_date(start_date="-50y", end_date="-15y")
    prefered_leg = random.choice(models.PlayerProfile.LEG_CHOICES)[0]
    transfer_status = random.choice(models.PlayerProfile.TRANSFER_STATUS_CHOICES)[0]
    card = random.choice(models.PlayerProfile.CARD_CHOICES)[0]
    soccer_goal = random.choice(models.PlayerProfile.GOAL_CHOICES)[0]
    about = factory.Faker("paragraph", nb_sentences=3)
    phone = utils.get_random_phone_number()
    agent_phone = utils.get_random_phone_number()
    practice_distance = utils.get_random_int(30, 100)
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    address = utils.get_random_address()
    playermetrics = factory.RelatedFactory(
        PlayerMetricsFactory, factory_related_name="player"
    )
    history = factory.SubFactory(ProfileVisitHistoryFactory)

    @classmethod
    def set_subfactories(cls) -> None:
        """Overwrite fields with subfactories"""
        cls.team_history_object = factory.SubFactory(TeamHistoryFactory)


class CoachProfileFactory(ProfileFactory):
    class Meta:
        model = models.CoachProfile

    mapper = factory.SubFactory(MapperFactory)
    licence = random.choice(models.CoachProfile.LICENCE_CHOICES)[0]
    club_role = random.choice(models.CoachProfile.CLUB_ROLE)[0]
    team_history_object = TeamHistoryFactory.random_object()
    soccer_goal = random.choice(models.CoachProfile.GOAL_CHOICES)[0]
    phone = utils.get_random_phone_number()
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    address = utils.get_random_address()

    @classmethod
    def set_subfactories(cls) -> None:
        """Overwrite fields with subfactories"""
        cls.team_history_object = factory.SubFactory(TeamHistoryFactory)


class ClubProfileFactory(ProfileFactory):
    class Meta:
        model = models.ClubProfile

    phone = utils.get_random_phone_number()
    club_object = ClubFactory.random_object()
    club_role = random.choice(models.ClubProfile.CLUB_ROLE)[0]


class ScoutProfileFactory(ProfileFactory):
    class Meta:
        model = models.ScoutProfile

    soccer_goal = random.choice(models.ScoutProfile.GOAL_CHOICES)[0]

    practice_distance = utils.get_random_int(30, 100)
    address = utils.get_random_address()


class GuestProfileFactory(ProfileFactory):
    class Meta:
        model = models.GuestProfile
