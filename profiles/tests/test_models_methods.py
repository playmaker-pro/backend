from django.test import TestCase

from users.models import User
from utils import testutils as utils
from utils.factories import CoachProfileFactory

utils.silence_explamation_mark()


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
