from django.test import TestCase
from profiles import models
from roles import definitions
from users.models import User
from utils import testutils as utils


utils.silence_explamation_mark()


class ChangeRoleTests(TestCase):
    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(
            email="username", declared_role=definitions.PLAYER_SHORT
        )
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.COMPLETE_FIELDS = ["team_raw"]  # , 'club_raw']
        self.user.profile.bio = "Lubie Herbate"

        self.user.profile.save()
        self.user.verify(silent=True)
        assert self.user.is_verified is True
        print(f"----> setUp {self.user.state}")

    def test__1__changing_role_to_coach_from_player_cause_user_sate_to_missing_verification_data(
        self,
    ):
        assert self.user.is_verified is True
        print(f"----> before  {self.user.state}")

        change = models.RoleChangeRequest.objects.create(
            user=self.user, new=definitions.COACH_SHORT
        )

        assert self.user.is_verified is True

        change.approved = True
        change.save()
        self.user.refresh_from_db()
        print(f"----> after {self.user.state}")
        assert self.user.is_verified is True
        assert self.user.is_missing_verification_data is False

    def test_changing_role_to_geust_from_player_cause_user_to_be_still_verified(self):
        assert self.user.is_verified is True
        change = models.RoleChangeRequest.objects.create(
            user=self.user, new=definitions.GUEST_SHORT
        )
        assert self.user.is_verified is True
        change.approved = True
        change.save()
        self.user.refresh_from_db()
        print(f"---->  {self.user.state}")
        assert self.user.is_verified is True

    def test_changing_role_to_scout_from_unverifed_player_cause_user_to_be_auto_verified(
        self,
    ):
        assert self.user.is_verified is True
        self.user.profile.bio = None
        self.user.profile.save()
        assert self.user.is_verified is True
        print(f"---->  before {self.user.state}")
        change = models.RoleChangeRequest.objects.create(
            user=self.user, new=definitions.SCOUT_SHORT
        )
        change.approved = True
        change.save()
        self.user.refresh_from_db()

        print(f"---->  after {self.user.state}")
        assert self.user.is_verified is True
        assert self.user.is_missing_verification_data is False

    def test_changing_role_to_guest_from_unverifed_player_cause_user_to_be_auto_verified(
        self,
    ):
        assert self.user.is_verified is True
        self.user.profile.bio = None
        self.user.profile.save()
        assert self.user.is_verified is True
        print(f"---->  before {self.user.state}")
        change = models.RoleChangeRequest.objects.create(
            user=self.user, new=definitions.GUEST_SHORT
        )

        # statuses should remain
        assert self.user.is_verified is True

        change.approved = True
        change.save()
        self.user.refresh_from_db()

        print(f"---->  after {self.user.state}")
        assert self.user.is_verified is True
        assert self.user.is_missing_verification_data is False


class TestProfilePercentageTests(TestCase):
    def setUp(self):
        user = User.objects.create(email="username", declared_role="P")
        user.profile.VERIFICATION_FIELDS = ["bio"]
        user.profile.COMPLETE_FIELDS = ["team_raw"]  # , 'club_raw']
        self.profile = user.profile

    def test_initialy_percentages(self):
        assert len(self.profile.VERIFICATION_FIELDS) == 1
        assert self.profile.percentage_completion == 0
        assert self.profile.percentage_left_verified == 50

    def test_initialy_no_verification_fields_and_complete_fields(self):
        self.profile.VERIFICATION_FIELDS = []
        self.profile.COMPLETE_FIELDS = []
        assert self.profile.percentage_completion == 100
        assert self.profile.percentage_left_verified == 0

    def test_initialy_only_complete_fields(self):
        self.profile.VERIFICATION_FIELDS = []
        assert self.profile.percentage_completion == 0
        assert self.profile.percentage_left_verified == 0

    def test_initialy_only_verification_fields(self):
        """This scenario cannot occure. Only by overwriting base code of profile model."""
        self.profile.COMPLETE_FIELDS = []
        assert self.profile.percentage_completion == 0  # here
        # with pytest.raises(models.VerificationCompletionFieldsWrongSetup):
        assert self.profile.percentage_left_verified == 100

    def test_fill_field_for_ver_and_complete(self):
        self.profile.bio = "Hello World"
        self.profile.save()
        assert self.profile.percentage_completion == 50
        assert self.profile.percentage_left_verified == 0

    def test_fill_only_complete_field(self):
        self.profile.team_raw = "Team Hello"
        self.profile.save()
        assert self.profile.percentage_completion == 50
        assert self.profile.percentage_left_verified == 50

    def test_all_filed(self):
        self.profile.team_raw = "Team Hello"
        self.profile.bio = "My aweseome bio"
        self.profile.save()
        assert self.profile.percentage_completion == 100
        assert self.profile.percentage_left_verified == 0

    def test_summary_of_left_verify_and_completion_need_to_give_100(self):
        self.profile.team_raw = "Team Hello"  # complete 50%
        # left ver 50%
        self.profile.save()
        assert (
            self.profile.percentage_completion + self.profile.percentage_left_verified
            == 100
        )


class InitialBaseProfileCreationTests(TestCase):
    """Idea is to create any profile and check if statuses are corectly behaved"""

    def setUp(self):
        user = User.objects.create(email="username", declared_role="T")
        user.profile.VERIFICATION_FIELDS = ["bio"]
        self.profile = user.profile

    def test__has_data_id__should_be_false(self):
        assert self.profile.has_data_id is False

    # def test_initial_state_of_fresh_profile_is_not_ready(self):
    #     assert self.profile.is_ready_for_verification() is False


class InitalPlayerProfileCreationTests(TestCase):
    """Idea is to create PLAYER profile and check if statuses are corectly behaved"""

    def setUp(self):
        user = User.objects.create(email="username", declared_role="P")
        self.profile = user.profile

    def test_initial_paramters(self):
        assert self.profile.position_fantasy is None

    def test_player_profile_set__position__should_affect__fantasy_position(self):
        """FANTASY_MAPPING = {
        1: FANTASY_GOAL_KEEPER,
        ...
        """
        for number, result in self.profile.FANTASY_MAPPING.items():
            self.profile.position_raw = number
            self.profile.save()
            # assert isinstance(number, int)
            assert isinstance(result, str)
            assert self.profile.position_fantasy is not None
            assert self.profile.position_fantasy == result
            print(
                f"position:{self.profile.position_raw} ({number}, {result}) fantasy:{self.profile.position_fantasy}"
            )


class ProfileVerificationExistingProfileWithReadyForVerificationTests(TestCase):
    """Freshly created user is modifing profile fields which are Verification fields."""

    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(email="username", declared_role="T")
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.bio = "bbbb"
        self.user.profile.save()

    def test_user_and_profile_statuses_should_indicate_ready_for_verification(self):
        assert self.user.is_waiting_for_verification is True
        print(f"--> user role {self.user.state}")
        # assert self.user.profile.is_ready_for_verification() is True

    def test_user_alter_one_of_verification_fields_should_statuses_should_stay_the_same(
        self,
    ):
        self.user.profile.bio = "aaaa"
        self.user.profile.save()
        print(f'--> user role before "{self.user.state}"')
        assert self.user.profile.bio == "aaaa"
        self.user.profile.save()
        print(f"--> user role after {self.user.state}")
        assert self.user.is_waiting_for_verification is True
        # assert self.user.profile.is_ready_for_verification() is True

    def test_modification_of_non_ver_field_will_not_cause_user_state_change(self):
        self.user.profile.facebook_url = "https://fb.com"
        self.user.profile.save()
        assert self.user.is_waiting_for_verification is True
        # assert self.user.profile.is_ready_for_verification() is True

    def test_clears_one_of_verification_fields_should_cause_status_change(self):
        #  second scenario
        self.user.profile.bio = None
        self.user.profile.save()
        assert (
            self.user.is_missing_verification_data is True
        )  # @todo think about altering this behavior
        # assert self.user.profile.is_ready_for_verification() is False


class ProfileUserIsVerifiedAndModifiesVerificationFields(TestCase):
    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(email="username", declared_role="T")
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.bio = "bbbb"
        self.user.profile.save()
        print(f"user:state {self.user.state}")
        self.user.state = (
            User.STATE_ACCOUNT_VERIFIED
        )  # @tood we cannot change NEW=>Acc Ver

    def test_initial_statuses(self):
        assert self.user.is_verified is True
        # assert self.user.profile.is_ready_for_verification() is False

    def test_user_alter_one_of_verification_fields_should_alter_statuses(self):
        self.user.profile.bio = "aaaa"
        self.user.profile.save()
        assert self.user.profile.bio == "aaaa"

        assert self.user.is_verified is False
        assert self.user.profile._is_verification_fields_filled() is True
        # assert self.user.profile.is_ready_for_verification() is True


class ProfileCompletnesTests(TestCase):
    def test_profile_is_complete(self):
        utils.create_system_user()
        user = User.objects.create(email="username", declared_role="T")
        user.profile.COMPLETE_FIELDS = ["bio"]
        user.profile.VERIFICATION_FIELDS = []
        assert user.profile.is_complete is False
        assert user.profile.percentage_completion == 0
        user.profile.bio = "bbbbbbb"
        user.profile.save()
        assert user.profile.is_complete is True
        assert user.profile.percentage_completion == 100
