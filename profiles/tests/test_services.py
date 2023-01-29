from django.test import TestCase
from profiles import models
from roles import definitions
from users.models import User
from utils import testutils as utils


utils.silence_explamation_mark()


class VerificationServiceTest(TestCase):
    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(
            email="username", declared_role=definitions.PLAYER_SHORT
        )
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
        self.user.profile.bio = "Lubie Herbate"

        self.user.profile.save()
        self.user.verify(silent=True)
        assert self.user.is_verified is True

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
        assert self.user.is_verified is False
        assert self.user.is_waiting_for_verification is True
