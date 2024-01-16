import random

import factory
from django.contrib.auth import get_user_model
from factory import post_generation
from faker import Faker

from profiles import models
from profiles.models import PlayerPosition
from profiles.services import TransferStatusService
from roles import definitions
from utils.factories.mapper_factories import MapperFactory

from . import clubs_factories, user_factories, utils
from .base import CustomObjectFactory

User = get_user_model()


class PlayerPositionFactory(CustomObjectFactory):
    class Meta:
        model = models.PlayerPosition

    name = factory.Sequence(lambda n: f"position_{n}")


class ProfileVideoFactory(CustomObjectFactory):
    class Meta:
        model = models.ProfileVideo


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

    done = factory.LazyAttribute(lambda _: Faker().boolean())


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
    player_positions = factory.RelatedFactory(
        PlayerProfilePositionFactory, "player_profile"
    )
    verification_stage = factory.SubFactory(VerificationStageFactory)

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
    def create_with_language(
        cls, language_codes: list, **kwargs
    ) -> models.PlayerProfile:
        """Create PlayerProfile with predefined language"""
        obj = super().create(**kwargs)
        languages = models.Language.objects.filter(code__in=language_codes)
        obj.user.userpreferences.spoken_languages.set(languages)
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


class ManagerProfileFactory(ProfileFactory):
    class Meta:
        model = models.ManagerProfile

    facebook_url = factory.Faker("url")
    other_url = factory.Faker("url")
    agency_phone = factory.Sequence(lambda n: f"+4812345{n:04d}")
    dial_code = factory.Sequence(lambda n: f"+{n%99:02d}")
    agency_email = factory.Faker("email")
    agency_transfermarkt_url = factory.Faker("url")
    agency_website_url = factory.Faker("url")
    agency_instagram_url = factory.Faker("url")
    agency_twitter_url = factory.Faker("url")
    agency_facebook_url = factory.Faker("url")
    agency_other_url = factory.Faker("url")

    @factory.post_generation
    def post_create(self, create, extracted, **kwargs):
        """
        This method is called after a new instance is created with the factory.
        It is used to perform additional actions or setup that is not covered by
        the default factory creation process.
        """
        if not create:
            return


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


class TeamContributorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TeamContributor

    profile_uuid = factory.LazyAttribute(lambda o: PlayerProfileFactory().uuid)
    is_primary = False

    @factory.post_generation
    def team_history(obj, create, extracted, **kwargs):
        """
        Post-generation hook to associate TeamHistory objects with the TeamContributor
        instance.

        If the `extracted` argument is provided, it uses the given TeamHistory
        instances.
        Otherwise, it creates and associates a new TeamHistory instance.
        """
        if not create:
            return

        if extracted:
            for team_hist in extracted:
                obj.team_history.add(team_hist)
        else:
            obj.team_history.add(clubs_factories.TeamFactory())


class TransferStatusFactory(factory.django.DjangoModelFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferStatus

    contact_email = factory.Faker("email")
    phone_number = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    status = 1
    additional_info = factory.List(
        [factory.Iterator([info[0] for info in definitions.TRANSFER_STATUS_ADDITIONAL_INFO_CHOICES])]
    )
    number_of_trainings = factory.Iterator(
        [training[0] for training in definitions.TRANSFER_TRAININGS_CHOICES]
    )
    salary = factory.Iterator(
        [salary[0] for salary in definitions.TRANSFER_SALARY_CHOICES]
    )

    class Params:
        profile = None
        leagues = factory.List([])

    @classmethod
    def create(cls, **kwargs) -> models.PROFILE_TYPE:
        """Override for GenericForeignKey and ManyToMany fields handling."""
        leagues = kwargs.pop(
            "leagues", None
        )  # Extract leagues before instance creation
        profile = kwargs.pop("profile", None)

        if not profile:
            profile = PlayerProfileFactory.create()

        kwargs = TransferStatusService.prepare_generic_type_content(kwargs, profile)
        transfer_status_instance = super().create(**kwargs)  # Create the instance

        # Set the leagues using the set method, if leagues are provided
        if leagues is not None:
            transfer_status_instance.league.set(leagues)

        return transfer_status_instance


class TransferRequestFactory(factory.django.DjangoModelFactory):
    """Transfer status factory"""

    class Meta:
        model = models.ProfileTransferRequest

    contact_email = factory.Faker("email")
    phone_number = factory.LazyAttribute(lambda _: utils.get_random_phone_number())
    status = "1"
    benefits = [1, 2]
    requesting_team = factory.SubFactory(TeamContributorFactory)
    gender = "M"
    number_of_trainings = "1"
    salary = "1"
    dial_code = factory.Faker("pyint", min_value=0, max_value=1000)

    class Params:
        profile = None

    @classmethod
    def create(cls, **kwargs) -> models.PROFILE_TYPE:
        """Override for GenericForeignKey purposes."""
        if not kwargs.get("profile"):
            profile = PlayerProfileFactory.create()
        else:
            profile = kwargs.pop("profile")
        kwargs = TransferStatusService.prepare_generic_type_content(kwargs, profile)
        return super().create(**kwargs)

    @post_generation
    def player_position(self, create, extracted, **kwargs):  # noqa
        if not create:
            return
        if not self.player_position.all().exists():  # noqa
            positions = PlayerPosition.objects.all()
            random_positions = random.sample(list(positions), 2)
            for random_position in random_positions:
                self.player_position.add(random_position.pk)  # noqa
