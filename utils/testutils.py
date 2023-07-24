import logging
import typing
import pytest
from django.conf import settings
from django.test import TestCase
from clubs.models import Club, Gender, League, Seniority, Team
from profiles import models
from roles import definitions
from users.models import User
from voivodeships.models import Voivodeships
from backend.settings.environment import Environment


class RunWithDifferentEnvironment:
    """
    Imitate different environment for testing.
    Allows to change environment before running given function.
    After that, restore environment variable.
    """

    def __init__(
        self,
        destination_env: Environment,
        call: typing.Callable,
        catch_exception: bool = True,
    ) -> None:
        self.call: typing.Callable = call
        self.catch_exception: bool = catch_exception
        self.destination_env: Environment = destination_env

    def __enter__(
        self,
    ):
        """
        destination_env - environment to run something with
        call - function to call with different environment
        """
        # TODO(bartnyk): env will be changed to enum, here: https://gitlab.com/playmaker1/webapp/-/merge_requests/313
        self.current_environment: Environment = (
            settings.CONFIGURATION
        )  # save current environment
        settings.CONFIGURATION = self.destination_env  # set different environment
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore environment"""
        settings.CONFIGURATION = self.current_environment

    def run(self) -> Exception:
        """Run defined, callable function"""
        try:
            return self.call()
        except Exception as e:
            if self.catch_exception:
                return e
            else:
                raise e


def create_system_user():
    User.objects.get_or_create(email=settings.SYSTEM_USER_EMAIL)


def get_team():
    vivo, _ = Voivodeships.objects.get_or_create(name="VIVOX")
    club, _ = Club.objects.get_or_create(
        name="CLUBX", voivodeship_obj=vivo, defaults={"mapping": "XXX, YYY,"}
    )
    league, _ = League.objects.get_or_create(name="LEAGUEX")
    seniority, _ = Seniority.objects.get_or_create(name="SENIORITYX")
    gender, _ = Gender.objects.get_or_create(name="GENDERX")
    team, _ = Team.objects.get_or_create(
        club=club,
        name="TEAMX",
        league=league,
        seniority=seniority,
        gender=gender,
        defaults={"mapping": "XXX, YYY,"},
    )
    return team


def get_club():
    return get_team().club


def get_verified_user_player():
    team = get_team()

    user = User.objects.create(
        email="usernameplayer", declared_role=definitions.PLAYER_SHORT
    )
    user.profile.team_object = team
    user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
    user.profile.save()
    user.verify(silent=True)
    return user


def get_verified_user_coach():
    team = get_team()
    user = User.objects.create(
        email="usernamecoach", declared_role=definitions.COACH_SHORT
    )
    user.profile.team_object = team
    user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
    user.profile.save()
    user.verify(silent=True)
    return user


def get_verified_user_club():
    club = get_club()
    user = User.objects.create(
        email="usernameclub", declared_role=definitions.CLUB_SHORT
    )
    user.profile.club_object = club
    user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
    user.profile.save()
    user.verify(silent=True)
    return user


def silence_explamation_mark():
    logger = logging.getLogger("django.db.backends.schema")
    logger.propagate = False


def get_random_user() -> User:
    """get random user from db"""
    return User.objects.order_by("?")[0]
