import datetime

import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from api.consts import ChoicesTuple
from profiles import models
from profiles.api.errors import (
    MultipleMainPositionError,
    TooManyAlternatePositionsError,
)
from profiles.errors import TeamContributorNotFoundServiceException
from profiles.services import (
    PlayerProfilePositionService,
    PositionData,
    ProfileService,
    TeamContributorService,
    TransferStatusService,
)
from roles import definitions
from roles.definitions import TRANSFER_STATUS_CHOICES
from utils import testutils as utils
from utils.factories import (
    SEASON_NAMES,
    LeagueFactory,
    PlayerProfileFactory,
    PositionFactory,
    SeasonFactory,
    TeamContributorFactory,
    TeamHistoryFactory,
    UserFactory,
)

team_contributor_service = TeamContributorService()
utils.silence_explamation_mark()


class VerificationServiceTest(TestCase):
    def setUp(self):
        self.user = PlayerProfileFactory.create(user__email="username").user
        self.user.profile.VERIFICATION_FIELDS = ["bio"]
        self.user.profile.COMPLETE_FIELDS = ["team"]  # , 'club_raw']
        self.user.profile.bio = "Lubie Herbate"

        self.user.profile.save()
        self.user.verify(silent=True)
        assert self.user.is_verified is True

    def test__1__changing_role_to_coach_from_player_cause_user_sate_to_missing_verification_data(  # noqa: 501
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
        self.user = PlayerProfileFactory.create(user__email="username").user
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


class TeamContributorServiceTests(TestCase):
    def setUp(self):
        """Set up the test environment."""
        PlayerProfileFactory.create_batch(2)
        self.users = UserFactory.create_batch(5, declared_role=definitions.PLAYER_SHORT)
        for user in self.users:
            PlayerProfileFactory.create(user=user)
        self.user = self.users[0]
        self.user_2 = self.users[1]
        self.service = ProfileService()
        self.team_contributor_service = TeamContributorService()
        self.league = LeagueFactory.create()
        self.team_contributor = TeamContributorFactory.create(
            profile_uuid=self.user.profile.uuid
        )
        seasons = [SeasonFactory.create() for _ in SEASON_NAMES]

        self.season = seasons[0]

    def test_get_team_contributor_or_404_existing_id(self):
        """Test fetching an existing team contributor by its ID."""
        retrieved_contributor = (
            self.team_contributor_service.get_team_contributor_or_404(
                self.team_contributor.pk
            )
        )
        self.assertEqual(retrieved_contributor, self.team_contributor)

    def test_get_team_contributor_or_404_non_existing_id(self):
        """Test fetching a non-existing team contributor should raise an exception."""
        with self.assertRaises(TeamContributorNotFoundServiceException):
            self.team_contributor_service.get_team_contributor_or_404(
                9999
            )  # Assuming 9999 doesn't exist

    def test_get_teams_for_profile(self):
        """Test fetching teams associated with a given profile."""
        teams = team_contributor_service.get_teams_for_profile(self.user.profile.uuid)
        assert self.team_contributor in teams

    def test_create_or_get_team_contributor_create(self):
        """Test creating a new team contributor when it doesn't already exist."""
        team_history = TeamHistoryFactory.create()

        (
            team_contributor,
            was_created,
        ) = team_contributor_service.create_or_get_team_contributor(
            self.user.profile.uuid, team_history, role="IIC"
        )

        assert team_contributor.pk is not None
        assert was_created
        assert team_contributor.profile_uuid == self.user.profile.uuid
        assert team_contributor.role == "IIC"
        assert team_contributor.team_history.filter(id=team_history.id).exists()

    # TODO: kgarczewski: FUTURE ADDITION: Reference: PM 20-697[SPIKE]
    # def test_create_or_get_team_contributor_get(self):
    #     """
    #     Test fetching an existing team contributor instead of creating a new one.
    #     """
    #     team_history = TeamHistoryFactory.create()
    #     existing_team_contributor = TeamContributorFactory.create(
    #         profile_uuid=self.user.profile.uuid,
    #         team_history=[team_history],
    #         role="IC"
    #     )
    #     (
    #         team_contributor,
    #         was_created,
    #     ) = team_contributor_service.create_or_get_team_contributor(
    #         self.user.profile.uuid, team_history, role="IC"
    #     )
    #     assert existing_team_contributor == team_contributor

    def test_create_or_get_all_related_entities(self):
        """
        Test creating or fetching all related entities for a given team contributor.
        """
        data = {
            "league_identifier": self.league.pk,
            "country": "PL",
            "season": self.season.pk,
            "team_parameter": "Test Team",
            "round": "wiosenna",
            "is_primary": True,
        }

        team_contributor = team_contributor_service.create_contributor(
            self.user.profile.uuid, data, "player"
        )

        assert (
            team_contributor.pk is not None
        )  # Ensures the object is saved to the database
        assert team_contributor.profile_uuid == self.user.profile.uuid

    def test_create_or_get_all_related_entities_with_team_history(self):
        """Test creating or fetching related entities, including team history."""
        team_history = TeamHistoryFactory.create()
        data = {
            "team_parameter": "Test Team",
            "league_identifier": self.league.pk,
            "country": "PL",
            "season": self.season.pk,
            "team_history": [team_history],
            "round": "wiosenna",
            "is_primary": False,
        }

        team_contributor = team_contributor_service.create_contributor(
            self.user.profile.uuid, data, "player"
        )

        assert team_contributor.pk is not None

    def test_create_non_player_contributor(self):
        """Test creating a team contributor for non-player profiles."""
        data = {
            "league_identifier": self.league.pk,
            "team_parameter": "Test Team",
            "start_date": datetime.date(2020, 1, 1),
            "role": "IC",
            "end_date": datetime.date(2022, 1, 1),
        }

        team_contributor = team_contributor_service.create_contributor(
            self.user.profile.uuid, data, "non-player"
        )

        assert (
            team_contributor.pk is not None
        )  # Ensures the object is saved to the database
        assert team_contributor.profile_uuid == self.user.profile.uuid

    def test_is_owner_of_team_contributor(self):
        """Test if a user is the owner of a specific team contributor."""
        assert self.team_contributor_service.is_owner_of_team_contributor(
            self.user.profile.uuid, self.team_contributor
        )

    def test_is_not_owner_of_team_contributor(self):
        """Test if a user isn't the owner of a specific team contributor."""
        assert not self.team_contributor_service.is_owner_of_team_contributor(
            self.user_2.profile.uuid, self.team_contributor
        )

    def test_profile_fields_update_on_contributor_creation(self):
        """
        Test that profile fields are updated when a primary team contributor is created.
        """
        team_history = TeamHistoryFactory.create()
        data = {
            "team_history": team_history,
            "is_primary": True,
        }
        team_contributor = self.team_contributor_service.create_contributor(
            self.user.profile.uuid, data, "player"
        )
        profile_instance = models.PlayerProfile.objects.get(uuid=self.user.profile.uuid)
        assert (
            profile_instance.team_object == team_contributor.team_history.all()[0].team
        )
        assert (
            profile_instance.team_history_object
            == team_contributor.team_history.all()[0]
        )

    def test_profile_fields_reset_on_contributor_deletion(self):
        """
        Test that profile fields are reset when a primary team contributor is deleted.
        """
        # Create a primary team contributor
        team_contributor = TeamContributorFactory.create(
            profile_uuid=self.user.profile.uuid, is_primary=True
        )
        # Delete the primary team contributor
        self.team_contributor_service.delete_team_contributor(team_contributor)
        profile_instance = models.PlayerProfile.objects.get(uuid=self.user.profile.uuid)
        assert profile_instance.team_object is None
        assert profile_instance.team_history_object is None


@pytest.mark.django_db
class TestTransferStatusService:
    """Test transfer status service."""

    @pytest.fixture(autouse=True)
    def service(self):
        """Provide TransferStatusService instance."""
        return TransferStatusService()

    @pytest.fixture(autouse=True)
    def profile(self):
        """Provide profile instance."""
        user = PlayerProfileFactory.create(user__email="username").user
        return user.profile

    def test_create_prepare_generic_type_content(self, service, profile):
        """Test prepare generic type content."""
        data = {"contact_email": "some_email"}
        data = service.prepare_generic_type_content(content=data, profile=profile)
        assert data["object_id"] == profile.pk
        assert isinstance(data["content_type"], ContentType)

    @pytest.mark.parametrize(
        "transfer_id",
        [1, 2, 3, 4],
    )
    def test_get_transfer_status_by_id(self, transfer_id, service):
        """Test get transfer status by id."""
        obj = service.get_transfer_status_by_id(transfer_status_id=transfer_id)
        expected = [
            ChoicesTuple(*transfer)._asdict()
            for transfer in TRANSFER_STATUS_CHOICES
            if transfer[0] == str(transfer_id)
        ]

        assert obj == expected[0]

    def test_get_list_transfer_statutes(self, service):
        """Test get list transfer status."""
        obj = service.get_list_transfer_statutes()
        expected = [
            ChoicesTuple(*transfer)._asdict() for transfer in TRANSFER_STATUS_CHOICES
        ]
        assert obj == expected
