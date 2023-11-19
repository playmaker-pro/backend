from django.test import TestCase

from roles import definitions
from utils import testutils as utils
from utils.factories import PlayerProfileFactory

utils.silence_explamation_mark()


SKAUT_DECLARED_ROLE = definitions.SCOUT_SHORT
PLAYER_DECLARED_ROLE = definitions.PLAYER_SHORT
TEST_MAIL = "test@mail.com"
FIRST_NAME = "X"
LAST_NAME = "T"


class InitialUserCreationPlayerProfile(TestCase):
    def setUp(self):
        self.user = PlayerProfileFactory.create(
            user__email=TEST_MAIL,
            user__first_name=FIRST_NAME,
            user__last_name=LAST_NAME,
        ).user

    def test_user_is_not_roleless(self):
        assert not self.user.is_roleless

    def test_user_role_is_player__declared_role(self):
        assert self.user.declared_role == PLAYER_DECLARED_ROLE

    def test_user_role_is_player_meta_information(self):
        assert self.user.first_name == FIRST_NAME
        assert self.user.last_name == LAST_NAME

    # def test_user_is_not_verifeid(self):
    #     assert self.user.state != User.STATE_ACCOUNT_VERIFIED
    #     assert not self.user.is_verified

    # def test_user_state_is_awaiting_for_data(self):
    #     assert self.user.state == User.STATE_ACCOUNT_WAITING_FOR_VERIFICATION_DATA
    #     assert self.user.is_missing_verification_data

    def test_user_has_initial_inquiry_plan_setuped_with_zero_counter(self):
        assert self.user.userinquiry is not None
        assert self.user.userinquiry.counter == 0
        assert self.user.userinquiry.plan is not None

    def test_user_profile_reference_to_proper_db_table_player_profile(self):
        assert self.user.profile == self.user.playerprofile
