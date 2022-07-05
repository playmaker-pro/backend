import logging

import pytest
from clubs.models import Club, Gender, League, Seniority, Team, Voivodeship
from django.test import TestCase
from profiles import models
from roles import definitions
from users.models import User


def get_team():
    vivo, _ = Voivodeship.objects.get_or_create(name="VIVOX")
    club, _ = Club.objects.get_or_create(
        name="CLUBX", voivodeship=vivo, defaults={"mapping": "XXX, YYY,"}
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
    user.profile.VERIFICATION_FIELDS = ["bio"]
    user.profile.COMPLETE_FIELDS = ["team_raw"]  # , 'club_raw']
    user.profile.bio = "Lubie Herbate"
    user.profile.save()
    user.verify(silent=True)
    return user


def get_verified_user_coach():
    team = get_team()
    user = User.objects.create(
        email="usernamecoach", declared_role=definitions.COACH_SHORT
    )
    user.profile.team_object = team
    user.profile.VERIFICATION_FIELDS = ["bio"]
    user.profile.COMPLETE_FIELDS = ["team_raw"]  # , 'club_raw']
    user.profile.bio = "Lubie Herbate"
    user.profile.save()
    user.verify(silent=True)
    return user


def get_verified_user_club():
    club = get_club()
    user = User.objects.create(
        email="usernameclub", declared_role=definitions.CLUB_SHORT
    )
    user.profile.club_object = club
    user.profile.VERIFICATION_FIELDS = ["bio"]
    user.profile.COMPLETE_FIELDS = ["team_raw"]  # , 'club_raw']
    user.profile.bio = "Lubie Herbate"
    user.profile.save()
    user.verify(silent=True)
    return user


def silence_explamation_mark():
    logger = logging.getLogger("django.db.backends.schema")
    logger.propagate = False
