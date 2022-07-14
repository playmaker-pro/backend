import logging

import pytest
from django.test import TestCase
from inquiries import models as inquiries_models
from profiles import models as pfs_models
from roles import definitions
from users.models import User
from utils import testutils as utils

utils.silence_explamation_mark()


SKAUT_DECLARED_ROLE = definitions.SCOUT_SHORT
PLAYER_DECLARED_ROLE = definitions.PLAYER_SHORT
TEST_MAIL = "test@mail.com"
FIRST_NAME = "X"
LAST_NAME = "T"


class InitialUserCreationPlayerProfile(TestCase):
    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(
            email=TEST_MAIL,
            first_name=FIRST_NAME,
            last_name=LAST_NAME,
            declared_role=PLAYER_DECLARED_ROLE,
        )

    def test_user_is_not_roleless(self):
        assert not self.user.is_roleless

    def test_user_role_is_player__declared_role(self):
        assert self.user.declared_role == PLAYER_DECLARED_ROLE

    def test_user_role_is_player_meta_information(self):
        assert self.user.first_name == FIRST_NAME
        assert self.user.last_name == LAST_NAME

    def test_user_is_not_verifeid(self):
        assert self.user.state != User.STATE_ACCOUNT_VERIFIED
        assert not self.user.is_verified

    # def test_user_state_is_awaiting_for_data(self):
    #     assert self.user.state == User.STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA
    #     assert self.user.is_missing_verification_data

    def test_user_has_initial_inquiry_plan_setuped_with_zero_counter(self):
        assert self.user.userinquiry is not None
        assert self.user.userinquiry.counter == 0
        assert self.user.userinquiry.plan is not None

    def test_user_profile_reference_to_proper_db_table_player_profile(self):
        assert self.user.profile == self.user.playerprofile


class ProfileAssigmentDuringUserCreationTests(TestCase):
    def setUp(self):
        utils.create_system_user()

    def test_users_profile_assigment(self):
        model_map = {
            definitions.COACH_SHORT: (pfs_models.CoachProfile, "is_coach"),
            definitions.PLAYER_SHORT: (pfs_models.PlayerProfile, "is_player"),
            definitions.CLUB_SHORT: (pfs_models.ClubProfile, "is_club"),
            definitions.GUEST_SHORT: (pfs_models.GuestProfile, "is_guest"),
            definitions.SCOUT_SHORT: (pfs_models.ScoutProfile, "is_scout"),
            definitions.PARENT_SHORT: (pfs_models.ParentProfile, "is_parent"),
            definitions.MANAGER_SHORT: (pfs_models.ManagerProfile, "is_manager"),
        }

        for role, (expected_model, is_method) in model_map.items():
            print(role, expected_model, is_method)
            username = f"michal{role}"
            user = User.objects.create(email=username, declared_role=role)
            assert getattr(user, is_method) is True
            assert isinstance(user.profile, expected_model)
