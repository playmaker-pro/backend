import random

import factory
from cities_light.models import City
from django.contrib.auth import get_user_model

from profiles import models
from utils.factories.mapper_factories import MapperFactory

from . import clubs_factories, user_factories, utils
from .base import CustomObjectFactory

User = get_user_model()


class PlayerPositionFactory(CustomObjectFactory):
    class Meta:
        model = models.PlayerPosition

    name = factory.Sequence(lambda n: f"position_{n}")


class PlayerVideoFactory(CustomObjectFactory):
    class Meta:
        model = models.PlayerVideo


class PlayerProfilePositionFactory(CustomObjectFactory):
    class Meta:
        model = models.PlayerProfilePosition
        django_get_or_create = ("player_profile", "player_position")

    player_position = factory.SubFactory(PlayerPositionFactory)
    player_profile = factory.SubFactory(
        "utils.factories.profiles.factories.PlayerProfileFactory"
    )


class VerificationStageFactory(CustomObjectFactory):
    class Meta:
        model = models.VerificationStage


class ProfileFactory(CustomObjectFactory):
    user = factory.SubFactory(user_factories.UserFactory)
    bio = factory.Faker("paragraph", nb_sentences=3)

    class Meta:
        abstract = True

    @classmethod
    def create(cls, **kwargs) -> models.PROFILE_TYPE:
        """Override just for typing purposes"""
        return super().create(**kwargs)


class PlayerMetricsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PlayerMetrics

    games_summary = {"games": "summary"}
    season_summary = {"season": "summary"}
    pm_score = factory.LazyAttribute(lambda _: utils.get_random_int(0, 100))
    season_score = {
        "2022/2023": 67,
        "2023/2024": 45,
    }


class ProfileVisitHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProfileVisitHistory

    counter = factory.LazyAttribute(lambda _: utils.get_random_int(0, 1000))
    counter_coach = factory.LazyAttribute(lambda _: utils.get_random_int(0, 100))
    counter_scout = factory.LazyAttribute(lambda _: utils.get_random_int(0, 100))


class PlayerProfileFactory(ProfileFactory):
    class Meta:
        model = models.PlayerProfile

    mapper = factory.SubFactory(MapperFactory)
    team_history_object = (
        clubs_factories.TeamHistoryFactory.get_random_or_create_subfactory()
    )
    team_object = clubs_factories.TeamFactory.get_random_or_create_subfactory()
    height = factory.LazyAttribute(lambda _: utils.get_random_int(150, 200))
    weight = factory.LazyAttribute(lambda _: utils.get_random_int(60, 100))
    birth_date = factory.LazyAttribute(
        lambda _: utils.get_random_date(start_date="-50y", end_date="-15y")
    )
    prefered_leg = factory.LazyAttribute(
        lambda _: random.choice(models.PlayerProfile.LEG_CHOICES)[0]
    )
    transfer_status = factory.LazyAttribute(
        lambda _: random.choice(models.PlayerProfile.TRANSFER_STATUS_CHOICES)[0]
    )
    card = factory.LazyAttribute(
        lambda _: random.choice(models.PlayerProfile.CARD_CHOICES)[0]
    )
    soccer_goal = factory.LazyAttribute(
        lambda _: random.choice(models.PlayerProfile.GOAL_CHOICES)[0]
    )
    about = factory.Faker("paragraph", nb_sentences=3)
    phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    agent_phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    practice_distance = factory.LazyAttribute(lambda _: utils.get_random_int(30, 100))
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    address = factory.LazyAttribute(lambda _: utils.get_random_address())
    playermetrics = factory.RelatedFactory(
        PlayerMetricsFactory, factory_related_name="player"
    )
    history = factory.SubFactory(ProfileVisitHistoryFactory)

    @classmethod
    def set_subfactories(cls) -> None:
        """Overwrite fields with subfactories"""
        cls.team_history_object = factory.SubFactory(clubs_factories.TeamHistoryFactory)

    @factory.post_generation
    def set_team(self, *args, **kwargs) -> None:
        """Set team_object based on team_history_object"""
        if self.team_history_object:
            self.team_object = self.team_history_object.team

    @classmethod
    def create_with_birth_date(cls, birth_date, **kwargs) -> models.PlayerProfile:
        """Create PlayerProfile with predefined birth_date"""
        obj = super().create(**kwargs)
        user_factories.UserPreferencesFactory(user=obj.user, birth_date=birth_date)
        return obj

    @classmethod
    def create_with_position(
        cls, position_str: str, is_main: bool = True, **kwargs
    ) -> models.PlayerProfile:
        """Create PlayerProfile with predefined position"""
        obj = super().create(**kwargs)
        PlayerProfilePositionFactory(
            player_profile=obj, player_position__shortcut=position_str, is_main=is_main
        )
        return obj

    @classmethod
    def create_with_localization(
        cls, localization: City, **kwargs
    ) -> models.PlayerProfile:
        """Create PlayerProfile with predefined localization"""
        obj = super().create(**kwargs)
        user_factories.UserPreferencesFactory(user=obj.user, localization=localization)
        return obj

    @classmethod
    def create_with_citizenship(
        cls, country_codes: list, **kwargs
    ) -> models.PlayerProfile:
        """Create PlayerProfile with predefined citizenship"""
        obj = super().create(**kwargs)
        user_factories.UserPreferencesFactory(user=obj.user, citizenship=country_codes)
        return obj

    @classmethod
    def create_with_language(
        cls, language_codes: list, **kwargs
    ) -> models.PlayerProfile:
        """Create PlayerProfile with predefined language"""
        obj = super().create(**kwargs)
        languages = models.Language.objects.filter(code__in=language_codes)
        user_factories.UserPreferencesFactory.create(
            user=obj.user
        ).spoken_languages.set(languages)
        return obj

    @classmethod
    def create_with_empty_metrics(self, **kwargs) -> models.PlayerProfile:
        """Create PlayerProfile with empty metrics"""
        obj = super().create(**kwargs)
        obj.playermetrics.wipe_metrics()
        return obj


class CoachProfileFactory(ProfileFactory):
    class Meta:
        model = models.CoachProfile

    mapper = factory.SubFactory(MapperFactory)
    licence = factory.LazyAttribute(
        lambda _: random.choice(models.CoachProfile.LICENCE_CHOICES)[0]
    )
    club_role = factory.LazyAttribute(
        lambda _: random.choice(models.CoachProfile.CLUB_ROLE)[0]
    )
    team_history_object = (
        clubs_factories.TeamHistoryFactory.get_random_or_create_subfactory()
    )
    team_object = clubs_factories.TeamFactory.get_random_or_create_subfactory()
    soccer_goal = factory.LazyAttribute(
        lambda _: random.choice(models.CoachProfile.GOAL_CHOICES)[0]
    )
    phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    voivodeship_obj = factory.LazyAttribute(lambda _: utils.get_random_voivo())
    address = factory.LazyAttribute(lambda _: utils.get_random_address())

    @classmethod
    def set_subfactories(cls) -> None:
        """Overwrite fields with subfactories"""
        cls.team_history_object = factory.SubFactory(clubs_factories.TeamHistoryFactory)

    @factory.post_generation
    def set_team(self, *args, **kwargs) -> None:
        """Set team_object based on team_history_object"""
        if self.team_history_object:
            self.team_object = self.team_history_object.team


class ClubProfileFactory(ProfileFactory):
    class Meta:
        model = models.ClubProfile

    phone = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    club_object = factory.LazyAttribute(
        lambda _: clubs_factories.ClubFactory.random_object()
    )
    club_role = factory.LazyAttribute(
        lambda _: random.choice(models.ClubProfile.CLUB_ROLE)[0]
    )


class ScoutProfileFactory(ProfileFactory):
    class Meta:
        model = models.ScoutProfile

    soccer_goal = factory.LazyAttribute(
        lambda _: random.choice(models.ScoutProfile.GOAL_CHOICES)[0]
    )
    practice_distance = factory.LazyAttribute(lambda _: utils.get_random_int(30, 100))
    address = factory.LazyAttribute(lambda _: utils.get_random_address())


class GuestProfileFactory(ProfileFactory):
    class Meta:
        model = models.GuestProfile


class PositionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PlayerPosition
        django_get_or_create = ("id",)

    name = factory.Iterator(["Napastnik", "Skrzydłowy", "Obrońca prawy", "Bramkarz"])


class LicenceTypeFactory(CustomObjectFactory):
    class Meta:
        model = models.LicenceType

    name = factory.Sequence(lambda n: f"licence_{n}")
    order = factory.Sequence(lambda n: 100 + n)


class CoachLicenceFactory(CustomObjectFactory):
    class Meta:
        model = models.CoachLicence

    licence = factory.SubFactory(LicenceTypeFactory)
    expiry_date = factory.LazyAttribute(
        lambda _: utils.get_random_date(start_date="-15y", end_date="today")
    )
    owner = factory.SubFactory(user_factories.UserFactory)
    is_in_progress = factory.LazyAttribute(lambda _: utils.get_random_bool())
    release_year = factory.LazyAttribute(lambda _: utils.get_random_int(2000, 2021))


class CourseFactory(CustomObjectFactory):
    class Meta:
        model = models.Course

    name = factory.Sequence(lambda n: f"course_{n}")
    release_year = factory.LazyAttribute(lambda _: utils.get_random_int(2000, 2021))
    owner = factory.SubFactory(user_factories.UserFactory)


class LanguageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Language
        django_get_or_create = ("name",)

    name = factory.Iterator(["Polski", "Angielski", "Niemiecki", "Francuski"])
