import json
import uuid
from datetime import datetime

import pytest
from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from profiles.schemas import PlayerProfileGET
from profiles.services import ProfileService
from profiles.tests import utils
from roles.definitions import CLUB_ROLE_TEAM_LEADER, COACH_SHORT, PLAYER_SHORT
from users.models import User
from utils import factories, testutils
from utils.factories import SEASON_NAMES, UserPreferencesFactory
from utils.test.test_utils import UserManager


class TestGetProfileAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        self.url = lambda profile_uuid: reverse(
            "api:profiles:get_or_update_profile", kwargs={"profile_uuid": profile_uuid}
        )

    def test_get_profile_valid_without_authentication(self) -> None:
        """correct get request with valid uuid, no need to authentie"""
        profile_uuid = factories.PlayerProfileFactory.create(
            user_id=self.user_obj.pk
        ).uuid
        response = self.client.get(self.url(profile_uuid), **self.headers)
        assert response.status_code == 200

    def test_get_profile_invalid(self) -> None:
        """get request shouldn't pass with fake uuid"""
        fake_uuid = uuid.uuid4()
        response = self.client.get(self.url(fake_uuid), **self.headers)
        assert response.status_code == 404

    def test_get_profile_valid_schema(self) -> None:
        """get request should return valid schema"""
        profile_uuid = factories.PlayerProfileFactory.create(
            user_id=self.user_obj.pk
        ).uuid
        fields_schema = list(PlayerProfileGET.__fields__.keys())
        response = self.client.get(self.url(profile_uuid), **self.headers)

        assert response.status_code == 200
        for field in fields_schema:
            assert field in list(response.data.keys())

    def test_get_profile_valid_schema_not_required_field(self) -> None:
        """get request should return valid schema for user without required fields"""
        profile_uuid = factories.PlayerProfileFactory.create(
            user_id=self.user_obj.pk,
            playermetrics=None,
            team_object=None,
            transfer_status=None,
        ).uuid
        fields_schema = list(PlayerProfileGET.__fields__.keys())
        response = self.client.get(self.url(profile_uuid), **self.headers)

        assert response.status_code == 200
        for field in fields_schema:
            assert field in list(response.data.keys())


class TestCreateProfileAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        factories.ClubFactory(id=1)
        factories.TeamHistoryFactory(
            team=factories.TeamFactory(name="Drużyna FC II", id=1), id=1
        )
        self.url = reverse("api:profiles:create_or_list_profiles")

    @parameterized.expand(
        [
            [{"role": "Piłkarz"}],
            [{"role": "s"}],
            [{"r0l3": "P"}],
        ]
    )
    def test_post_incorrect_role(self, payload: dict) -> None:
        """Test HTTP_400 if request has wrong defined role"""
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 400

    @parameterized.expand(
        [
            [
                {
                    "role": "P",
                    "height": 180,
                    "weight": 75,
                    "practice_distance": 20,
                    "prefered_leg": 1,
                },
            ],
            [
                {
                    "role": "P",
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                }
            ],
            [
                {
                    "role": "T",
                    "licence": 1,
                    "team_object_id": 1,
                    "soccer_goal": 2,
                }
            ],
            [
                {
                    "role": "C",
                    "club_object_id": 1,
                    "club_role": CLUB_ROLE_TEAM_LEADER,
                    "phone": "111222333",
                }
            ],
            [{"role": "S", "soccer_goal": 2, "bio": "jakiesbio"}],
        ]
    )
    def test_successfully_create_profile_for_new_user(self, payload: dict) -> None:
        """Test creating profiles with correctly passed payload"""
        self.manager.login(self.user_obj)
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 201
        assert response.data["user_id"] and response.data["role"]

        profile_type = utils.get_profile_by_role(payload["role"])
        profile = profile_type.objects.get(user=self.user_obj)

        for attr, val in payload.items():
            if attr != "role":
                assert getattr(profile, attr) == val

    @parameterized.expand([[{"role": "P"}]])
    def test_create_same_profile_type_twice_for_same_user(self, payload: dict) -> None:
        """
        Test HTTP_400 in attempt to create profile
        for user that has already a profile
        """
        self.client.post(self.url, json.dumps(payload), **self.headers)
        response = self.client.post(self.url, json.dumps(payload), **self.headers)

        assert response.status_code == 400

    # @parameterized.expand( # TODO(bartnyk) NOT READY, USER CAN HAVE JUST ONE PROFILE YET   # noqa: E501
    #     [
    #         [{"user_id": 1, "role": "P"}],
    #         [{"user_id": 1, "role": "S"}],
    #         [{"user_id": 1, "role": "C"}],
    #     ]
    # )
    # def test_create_multiple_profile_types_for_same_user(self, payload: dict) -> None:
    #     """
    #     Test HTTP_400 in attempt to create profile
    #     for user that has already a profile
    #     """
    #     response = ProfileAPI.as_view(
    #     {"post": "create_profile"})(get_request(payload)
    #     )
    #
    #     user = get_user(payload["user_id"])
    #     profile = get_profile_by_role(payload["role"])
    #     assert profile.objects.get(user=user)
    #     assert response.status_code == 201

    def test_post_need_authentication(self) -> None:
        """post request should require authentication"""
        response = self.client.post(
            self.url,
            json.dumps({"user_id": 1, "role": "S"}),
            format="json",
        )

        assert response.status_code == 401

    def test_post_request_need_body(self) -> None:
        """post require request's body, fail if empty"""
        response = self.client.post(self.url, {}, **self.headers)

        assert response.status_code == 400


class TestUpdateProfileAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        factories.TeamHistoryFactory(
            team=factories.TeamFactory(name="Drużyna FC II", id=1), id=1
        )
        self.url = lambda profile_uuid: reverse(
            "api:profiles:get_or_update_profile", kwargs={"profile_uuid": profile_uuid}
        )

        factories.CityFactory(pk=1)
        factories.ClubFactory(pk=100)
        factories.LanguageFactory(pk=1)

    def test_patch_user_is_not_an_owner_of_profile(self) -> None:
        """request should return 400 if requestor is not an owner of updated profile"""
        dummy_user = factories.UserFactory.create()
        profile = utils.create_empty_profile(
            **{
                "user_id": dummy_user.pk,
                "role": "P",
            }
        )
        profile_uuid = str(profile.uuid)
        response = self.client.patch(self.url(profile_uuid), {}, **self.headers)

        assert response.status_code == 400

    def test_patch_need_authentication(self) -> None:
        """patch request should require authentication"""
        profile = utils.create_empty_profile(
            **{
                "user_id": self.user_obj.pk,
                "role": "S",
            }
        )
        profile_uuid = str(profile.uuid)
        response = self.client.patch(
            self.url(profile_uuid),
            {},
        )

        assert response.status_code == 401

    def test_patch_fake_uuid(self) -> None:
        """patch request with fake uuid shouldn't pass"""
        fake_uuid = uuid.uuid4()
        self.manager.login(self.user_obj)
        response = self.client.patch(self.url(str(fake_uuid)), {}, **self.headers)

        assert response.status_code == 404

    @parameterized.expand(
        [
            [
                {
                    "role": "P",
                },
                {
                    "height": 180,
                    "weight": 75,
                    "prefered_leg": 1,
                },
            ],
            [
                {
                    "role": "P",
                },
                {
                    "user": {
                        "first_name": "LukaszLukasinski",
                        "last_name": "Lukasinski",
                    },
                    "training_ready": 1,
                },
            ],
            [
                {
                    "role": "C",
                },
                {
                    "club_role": "brzeczyszczykiewicz",
                    "user": {"userpreferences": {"birth_date": "1990-01-01"}},
                },
            ],
            [
                {
                    "role": "S",
                },
                {
                    "user": {
                        "first_name": "scout",
                        "last_name": "test",
                    },
                },
            ],
            [
                {
                    "role": "M",
                },
                {
                    "agency_phone": "+1234567890",
                    "agency_email": "example@example.com",
                    "agency_transfermarkt_url": "https://www.transfermarkt.com/example",
                },
            ],
        ]
    )
    def test_successfully_patch_profile_for_new_user(
        self, init_profile: dict, payload: dict
    ) -> None:
        """Test updating profiles with correctly passed payload"""
        profile = utils.create_empty_profile(**init_profile, user_id=self.user_obj.pk)
        UserPreferencesFactory.create(user=profile.user)

        profile_uuid = profile.uuid
        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )
        profile = utils.profile_service.get_profile_by_uuid(profile_uuid)

        assert response.status_code == 200
        for attr, val in payload.items():
            if attr == "user":
                user: User = getattr(profile, attr)
                for element in val:
                    if element == "userpreferences":
                        for key, value in val[element].items():
                            assert (
                                getattr(user.userpreferences, key)
                                == datetime.strptime(value, "%Y-%m-%d").date()
                            )
                    else:
                        assert getattr(user, element) == val[element]
            else:
                assert getattr(profile, attr) == val

    def test_coach_profile_patch_method_complex_payload(self) -> None:
        """Test updating coach profiles with correctly passed payload"""
        profile = utils.create_empty_profile(
            **{
                "user_id": self.user_obj.pk,
                "role": "T",
            }
        )
        payload = {
            "coach_role": "IIC",
        }

        expected_response = {
            "coach_role": {"id": "IIC", "name": "Drugi trener"},
        }
        expected_model_data = {"coach_role": "IIC"}

        response = self.client.patch(
            self.url(str(profile.uuid)), json.dumps(payload), **self.headers
        )
        profile = utils.profile_service.get_profile_by_uuid(profile.uuid)

        assert response.status_code == 200
        for attr, val in expected_model_data.items():
            assert getattr(profile, attr) == val

        for attr, val in expected_response.items():
            assert response.data.get(attr) == val

    @parameterized.expand(
        [
            ("birth_date", "2001-11-14"),
            ("localization", 1),
            ("spoken_languages", ["PL"]),
            ("citizenship", ["UA"]),
            ("gender", "M"),
        ]
    )
    def test_patch_user_userpreferences(self, key, val) -> None:
        """Test updating userpreferences with correctly passed payload"""
        factories.UserPreferencesFactory.create(user_id=self.user_obj.pk, gender=None)
        profile = utils.create_empty_profile(role="P", user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload = {"user": {"userpreferences": {key: val}}}

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )
        assert response.status_code == 200
        assert response.data["user"]["userpreferences"][key]

    @pytest.mark.skip("Not implemented yet, because of new player profile structure")
    def test_patch_visit_history(self) -> None:
        """Test updating visit history with correctly passed payload"""
        profile = utils.create_empty_profile(role="P", user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload = {"history": {"counter": 10, "counter_coach": 20, "counter_scout": 30}}

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )

        assert response.status_code == 200
        assert response.data["history"] == payload["history"]

    def test_patch_player_positions(self) -> None:
        """Test updating player positions with correctly passed payload"""
        profile = utils.create_empty_profile(role="P", user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload = {
            "player_positions": [
                {"player_position": 8, "is_main": False},
                {"player_position": 2, "is_main": True},
            ]
        }

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )

        assert response.status_code == 200
        assert len(response.data["player_positions"]) == len(
            payload["player_positions"]
        )

    def test_patch_verification_stage(self) -> None:
        """Test updating verification stage with correctly passed payload"""
        profile = utils.create_empty_profile(role="P", user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload = {"verification_stage": {"step": 5, "done": False}}

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )

        assert response.status_code == 200
        assert response.data["verification_stage"]["step"] == 5
        assert response.data["verification_stage"]["done"] is False

    def test_patch_verification_stage_not_in_response(self) -> None:
        """Test if verification stage is not in response as it has status done"""
        profile = utils.create_empty_profile(role="P", user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        payload = {"verification_stage": {"step": 5, "done": True}}

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )

        assert response.status_code == 200
        assert "verification_stage" not in response.data


class ProfileTeamsApiTest(APITestCase):
    def setUp(self):
        """Set up test environment."""
        testutils.create_system_user()
        self.user = User.objects.create(email="username", declared_role=PLAYER_SHORT)
        self.non_player_user = User.objects.create(
            email="nonplayer@example.com", declared_role=COACH_SHORT
        )

        self.service = ProfileService()
        self.league = factories.LeagueFactory.create()
        self.team_contributor = factories.TeamContributorFactory.create(
            profile_uuid=self.user.profile.uuid
        )
        self.non_player_team_contributor = factories.TeamContributorFactory.create(
            profile_uuid=self.non_player_user.profile.uuid
        )
        all_seasons = [
            factories.SeasonFactory.create(name=season_name)
            for season_name in SEASON_NAMES
        ]
        self.team_history = factories.TeamHistoryFactory.create()
        self.season = all_seasons[0]

    def test_get_profiles_teams(self):
        """Test retrieving profile's teams."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                "api:profiles:profiles_teams",
                kwargs={"profile_uuid": self.user.profile.uuid},
            )
        )

        assert response.status_code == 200

    def test_get_non_player_profiles_teams(self):
        """Test retrieving non-player profile's teams."""
        self.client.force_authenticate(user=self.non_player_user)

        response = self.client.get(
            reverse(
                "api:profiles:profiles_teams",
                kwargs={"profile_uuid": self.non_player_user.profile.uuid},
            )
        )

        assert response.status_code == 200

    def test_add_team_to_profile(self):
        """Test adding a team to a profile."""
        self.client.force_authenticate(user=self.user)

        data = {
            "league_identifier": self.league.pk,
            "season": self.season.pk,
            "team_parameter": "Test Team",
            "round": "wiosenna",
        }
        response = self.client.post(
            reverse(
                "api:profiles:add_team_to_profile",
                kwargs={"profile_uuid": self.user.profile.uuid},
            ),
            data,
        )

        assert response.status_code == 201

    def test_add_team_to_non_player_profile(self):
        """Test adding a team to a non-player profile."""
        self.client.force_authenticate(user=self.non_player_user)

        data = {
            "league_identifier": self.league.pk,
            "start_date": "2021-01-01",
            "is_primary": True,
            "team_parameter": "Test Team for Non-Player",
            "role": "IC",
        }

        response = self.client.post(
            reverse(
                "api:profiles:add_team_to_profile",
                kwargs={"profile_uuid": self.non_player_user.profile.uuid},
            ),
            data,
        )

        assert response.status_code == 201
        assert response.data["end_date"] is None

    def test_patch_team_history(self):
        """Test updating (patching) a team history."""
        self.client.force_authenticate(user=self.user)

        data = {
            "team_history": self.team_history.id,
            "round": "jesienna",
        }
        response = self.client.patch(
            reverse(
                "api:profiles:update_or_delete_team_contributor",
                kwargs={
                    "profile_uuid": self.user.profile.uuid,
                    "team_contributor_id": self.team_contributor.pk,
                },
            ),
            data,
        )

        assert response.status_code == 200
        assert response.data["team_name"] == self.team_history.team.name
        assert (
            response.data["league_name"] == self.team_history.league_history.league.name
        )

    def test_patch_team_for_non_player_profile(self):
        """Test updating (patching) a team for a non-player profile."""
        self.client.force_authenticate(user=self.non_player_user)

        data = {
            "team_history": self.team_history.id,
            "start_date": "2021-02-01",
            "end_date": "2021-12-31",
            "role": "IIC",
        }

        response = self.client.patch(
            reverse(
                "api:profiles:update_or_delete_team_contributor",
                kwargs={
                    "profile_uuid": self.non_player_user.profile.uuid,
                    "team_contributor_id": self.non_player_team_contributor.pk,
                },
            ),
            data,
        )

        assert response.status_code == 200
        assert response.data["team_name"] == self.team_history.team.name
        assert (
            response.data["league_name"] == self.team_history.league_history.league.name
        )
        assert response.data["role"] == data["role"]

    def test_delete_team_history(self):
        """Test deleting a team history."""
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(
            reverse(
                "api:profiles:update_or_delete_team_contributor",
                kwargs={
                    "profile_uuid": self.user.profile.uuid,
                    "team_contributor_id": self.team_contributor.id,
                },
            ),
        )

        assert response.status_code == 204

    def test_get_team_contributor_or_404(self):
        """
        Test the endpoint to retrieve team contributor based on profile ID.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                "api:profiles:profiles_teams",
                kwargs={"profile_uuid": self.user.profile.uuid},
            )
        )
        assert response.status_code == 200
        assert (
            response.data[0]["team_name"]
            == self.team_contributor.team_history.first().team.name
        )
        assert (
            response.data[0]["league_name"]
            == self.team_contributor.team_history.first().league_history.league.name
        )

    def test_get_non_player_team_contributor_or_404(self):
        """Test retrieving team contributor for non-player based on profile ID."""
        self.client.force_authenticate(user=self.non_player_user)

        response = self.client.get(
            reverse(
                "api:profiles:profiles_teams",
                kwargs={"profile_uuid": self.non_player_user.profile.uuid},
            )
        )
        assert response.status_code == 200
        assert (
            response.data[0]["team_name"]
            == self.non_player_team_contributor.team_history.first().team.name
        )
        assert (
            response.data[0]["league_name"]
            == self.non_player_team_contributor.team_history.first().league_history.league.name  # noqa: E501
        )

    def test_unset_previous_primary_for_non_player(self):
        """Test that setting a new team as primary unsets the previous primary for a non-player profile."""
        self.client.force_authenticate(user=self.non_player_user)

        # Set the first contributor as primary
        data1 = {
            "team_history": self.team_history.id,
            "start_date": "2021-02-01",
            "is_primary": True,
            "role": "IC",
        }
        response1 = self.client.patch(
            reverse(
                "api:profiles:update_or_delete_team_contributor",
                kwargs={
                    "profile_uuid": self.non_player_user.profile.uuid,
                    "team_contributor_id": self.non_player_team_contributor.pk,
                },
            ),
            data1,
        )
        assert response1.status_code == 200
        assert response1.data["is_primary"] is True
        assert response1.data["end_date"] is None

        # Unset the primary status for the current team contributor
        data2 = {"is_primary": False}
        response2 = self.client.patch(
            reverse(
                "api:profiles:update_or_delete_team_contributor",
                kwargs={
                    "profile_uuid": self.non_player_user.profile.uuid,
                    "team_contributor_id": self.non_player_team_contributor.pk,
                },
            ),
            data2,
        )

        assert response2.status_code == 200

        self.non_player_team_contributor.refresh_from_db()

        assert self.non_player_team_contributor.is_primary is False
        assert self.non_player_team_contributor.end_date == datetime.today().date()


class TestSetMainProfileAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.url = reverse("api:profiles:set_main_profile")

    @parameterized.expand(["P", "C", "T"])
    def test_set_main_profile(self, role: str) -> None:
        """Test setting declared_role on user"""
        assert self.user_obj.declared_role != role
        utils.create_empty_profile(
            **{
                "user_id": self.user_obj.pk,
                "role": role,
            }
        )
        response = self.client.post(
            self.url,
            json.dumps({"declared_role": role}),
            **self.headers,
        )

        assert response.status_code == 204
        self.user_obj.refresh_from_db()
        assert self.user_obj.declared_role == role

    def test_user_has_no_given_profile(self) -> None:
        """Test setting declared_role while user hasn't this type of profile"""
        assert self.user_obj.declared_role != "P"
        response = self.client.post(
            self.url,
            json.dumps({"declared_role": "P"}),
            **self.headers,
        )

        assert response.status_code == 400

    def test_given_role_does_not_exist(self) -> None:
        """Test setting incorrect declared_role"""
        response = self.client.post(
            self.url,
            json.dumps({"declared_role": "somerandomstring"}),
            **self.headers,
        )

        assert response.status_code == 400
