from django.test import TestCase

from profiles import models
from roles import definitions
from users.models import User
from utils import testutils as utils
from profiles.errors import (
    MultipleMainPositionError,
    TooManyAlternatePositionsError,
)
from profiles.services import PlayerProfilePositionService, PositionData
from utils.factories import PositionFactory


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


class PlayerPositionServiceTest(TestCase):
    def setUp(self):
        utils.create_system_user()
        self.user = User.objects.create(
            email="username", declared_role=definitions.PLAYER_SHORT
        )
        self.profile = self.user.profile
        PositionFactory.create(id=1)
        PositionFactory.create(id=2)
        self.position_service = PlayerProfilePositionService()
        self.positions_data = [
            PositionData(player_position=1, is_main=True),
            PositionData(player_position=2, is_main=False),
        ]

    def test_update_positions_creates_new_positions(self):
        self.position_service.manage_positions(self.profile, self.positions_data)
        positions = self.profile.player_positions.all()
        self.assertEqual(len(positions), 2)

    def test_update_positions_raises_error_for_multiple_main_positions(self):
        self.positions_data.append(
            PositionData(player_position=3, is_main=True),
        )
        with self.assertRaises(MultipleMainPositionError):
            self.position_service.manage_positions(self.profile, self.positions_data)

    def test_update_positions_raises_error_for_more_than_two_non_main_positions(self):
        self.positions_data.extend(
            [
                PositionData(player_position=4, is_main=False),
                PositionData(player_position=5, is_main=False),
            ]
        )
        with self.assertRaises(TooManyAlternatePositionsError):
            self.position_service.manage_positions(self.profile, self.positions_data)

    def test_create_position_creates_new_position(self):
        self.position_service.manage_positions(
            self.profile,
            [
                PositionData(player_position=1, is_main=True),
            ],
        )
        main_positions = self.profile.player_positions.filter(is_main=True)
        self.assertEqual(main_positions.count(), 1)

    def test_create_position_raises_error_for_multiple_main_positions(self):
        with self.assertRaises(MultipleMainPositionError):
            self.position_service.manage_positions(
                self.profile,
                [
                    PositionData(player_position=1, is_main=True),
                    PositionData(player_position=2, is_main=True),
                ],
            )

    def test_create_position_raises_error_for_more_than_two_non_main_positions(self):
        with self.assertRaises(TooManyAlternatePositionsError):
            self.position_service.manage_positions(
                self.profile,
                [
                    PositionData(player_position=1, is_main=False),
                    PositionData(player_position=2, is_main=False),
                    PositionData(player_position=3, is_main=False),
                ],
            )

    def test_delete_removed_positions(self):
        self.position_service.manage_positions(self.profile, self.positions_data)
        self.position_service.manage_positions(self.profile, [self.positions_data[0]])
        positions = self.profile.player_positions.all()
        self.assertEqual(len(positions), 1)
