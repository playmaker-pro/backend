from django.test import TestCase

from users.models import User
from utils import testutils as utils
from utils.factories import CoachProfileFactory, PlayerProfileFactory

utils.silence_explamation_mark()


class TestProfilePercentageTests(TestCase):
    def setUp(self):
        user = PlayerProfileFactory.create(user__email="username", bio=None).user
        user.profile.VERIFICATION_FIELDS = ["bio"]
        user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
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
        """This scenario cannot occure. Only by overwriting base code of profile model."""  # noqa: E501
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
        self.profile.team = "Team Hello"
        self.profile.save()
        assert self.profile.percentage_completion == 50
        assert self.profile.percentage_left_verified == 50

    def test_all_filed(self):
        self.profile.team = "Team Hello"
        self.profile.bio = "My aweseome bio"
        self.profile.save()
        assert self.profile.percentage_completion == 100
        assert self.profile.percentage_left_verified == 0

    def test_summary_of_left_verify_and_completion_need_to_give_100(self):
        self.profile.team = "Team Hello"  # complete 50%
        # left ver 50%
        self.profile.save()
        assert (
            self.profile.percentage_completion + self.profile.percentage_left_verified
            == 100
        )


class InitialBaseProfileCreationTests(TestCase):
    """Idea is to create any profile and check if statuses are corectly behaved"""

    def setUp(self):
        user = CoachProfileFactory.create(user__email="username").user
        user.profile.VERIFICATION_FIELDS = ["bio"]
        self.profile = user.profile

    def test__has_data_id__should_be_false(self):
        assert self.profile.has_data_id is False


class ProfileVerificationExistingProfileWithReadyForVerificationTests(TestCase):
    """Freshly created user is modifing profile fields which are Verification fields."""

    def setUp(self):
        self.user = CoachProfileFactory.create(user__email="username").user
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.bio = "bbbb"
        self.user.profile.save()

    def test_user_and_profile_statuses_should_indicate_ready_for_verification(self):
        assert self.user.is_waiting_for_verification is False
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
        assert self.user.is_waiting_for_verification is False
        # assert self.user.profile.is_ready_for_verification() is True

    def test_modification_of_non_ver_field_will_not_cause_user_state_change(self):
        self.user.profile.facebook_url = "https://fb.com"
        self.user.profile.save()
        assert self.user.is_waiting_for_verification is False
        # assert self.user.profile.is_ready_for_verification() is True

    def test_clears_one_of_verification_fields_should_cause_status_change(self):
        #  second scenario
        self.user.profile.bio = None
        self.user.profile.save()
        assert (
            self.user.is_missing_verification_data is False
        )  # @todo think about altering this behavior
        # assert self.user.profile.is_ready_for_verification() is False


class ProfileUserIsVerifiedAndModifiesVerificationFields(TestCase):
    def setUp(self):
        self.user = CoachProfileFactory.create(user__email="username").user
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

        assert self.user.is_verified is True
        # assert self.user.profile.is_ready_for_verification() is True


class ProfileCompletnesTests(TestCase):
    def test_profile_is_complete(self):
        user = CoachProfileFactory.create(user__email="username", bio=None).user
        user.profile.COMPLETE_FIELDS = ["bio"]
        user.profile.VERIFICATION_FIELDS = []
        assert user.profile.is_complete is False
        assert user.profile.percentage_completion == 0
        user.profile.bio = "bbbbbbb"
        user.profile.save()
        assert user.profile.is_complete is True
        assert user.profile.percentage_completion == 100
