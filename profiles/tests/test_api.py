import uuid
from rest_framework.test import APITestCase
from django.urls import reverse
from parameterized import parameterized
from profiles.tests import utils
from utils.factories.clubs_factories import TeamFactory, ClubFactory, TeamHistoryFactory
from utils.factories.user_factories import UserFactory
from utils.factories.profiles_factories import PositionFactory
from utils.factories.api_request_factory import RequestFactory, MethodsSet
from profiles.apis import ProfileAPI
from utils import testutils
from profiles.models import PlayerProfile

url_create_or_update: str = "api:profiles:create_or_update_profile"
url_get: str = "api:profiles:get_profile"

methods = MethodsSet(
    GET="get_profile_by_uuid",
    POST="create_profile",
    PATCH="update_profile",
)
request = RequestFactory(ProfileAPI, methods)


class TestCreateProfileAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        testutils.create_system_user()
        UserFactory.create_batch_force_order(5)
        ClubFactory(id=1)
        PositionFactory(id=1)
        PositionFactory(id=2)
        TeamHistoryFactory(team=TeamFactory(name="Drużyna FC II", id=1), id=1)

    def test_get_profile_valid_without_authentication(self) -> None:
        """correct get request with valid uuid, no need to authenticate"""
        profile_uuid = PlayerProfile.objects.create(user_id=1).uuid
        response = request.get(
            reverse(url_get, kwargs={"profile_uuid": profile_uuid}),
            profile_uuid=profile_uuid,
            force_authentication=False,
        )
        assert response.status_code == 200

    def test_get_profile_invalid(self) -> None:
        """get request shouldn't pass with fake uuid"""
        fake_uuid = uuid.uuid4()
        response = request.get(
            reverse(url_get, kwargs={"profile_uuid": fake_uuid}),
            profile_uuid=fake_uuid,
        )
        assert response.status_code == 404

    @parameterized.expand(
        [
            [{"user_id": 0, "role": "P"}],
            [{"user_id": 100000, "role": "P"}],
        ]
    )
    def test_incorrect_user(self, payload: dict) -> None:
        """test HTTP_400 if request has wrong defined user_id"""
        response = request.post(reverse(url_create_or_update), payload)

        assert response.status_code == 404

    @parameterized.expand(
        [
            [{"id_user": 1, "role": "S"}],
            [{"role": "S"}],
            [{"user": 1, "role": "S"}],
        ]
    )
    def test_user_not_defined(self, payload: dict) -> None:
        """test HTTP_400 if request has wrong defined user_id"""
        response = request.post(reverse(url_create_or_update), payload)

        assert response.status_code == 400

    @parameterized.expand(
        [
            [{"user_id": 1, "role": "Piłkarz"}],
            [{"user_id": 1, "role": "s"}],
            [{"user_id": 1, "r0l3": "P"}],
        ]
    )
    def test_incorrect_role(self, payload: dict) -> None:
        """Test HTTP_400 if request has wrong defined role"""
        response = request.post(reverse(url_create_or_update), payload)

        assert response.status_code == 400

    @parameterized.expand(
        [
            [
                {
                    "user_id": 1,
                    "role": "P",
                    "height": 180,
                    "weight": 75,
                    "practice_distance": 20,
                    "prefered_leg": 1,
                    "player_positions": [
                        {"player_position": 1, "is_main": True},
                        {"player_position": 2, "is_main": False},
                    ],
                },
            ],
            [
                {
                    "user_id": 2,
                    "role": "P",
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                }
            ],
            [
                {
                    "user_id": 3,
                    "role": "T",
                    "licence": 1,
                    "team_object_id": 1,
                    "soccer_goal": 2,
                }
            ],
            [
                {
                    "user_id": 4,
                    "role": "C",
                    "club_object_id": 1,
                    "club_role": 5,
                    "phone": "111222333",
                }
            ],
            [{"user_id": 5, "role": "S", "soccer_goal": 2, "bio": "jakiesbio"}],
        ]
    )
    def test_successfully_create_profile_for_new_user(self, payload: dict) -> None:
        """Test creating profiles with correctly passed payload"""
        response = request.post(reverse(url_create_or_update), payload)

        assert response.status_code == 201
        assert response.data["user_id"] and response.data["role"]

        user = utils.get_user(payload["user_id"])
        profile_type = utils.get_profile_by_role(payload["role"])
        profile = profile_type.objects.get(user=user)

        for attr, val in payload.items():
            if attr != "role" and attr != "player_positions":
                assert getattr(profile, attr) == val

    @parameterized.expand([[{"user_id": 1, "role": "P"}]])
    def test_create_same_profile_type_twice_for_same_user(self, payload: dict) -> None:
        """Test HTTP_400 in attempt to create profile for user that has already a profile"""
        request.post(reverse(url_create_or_update), payload)
        response = request.post(reverse(url_create_or_update), payload)

        assert response.status_code == 400

    # @parameterized.expand( # TODO(bartnyk) NOT READY, USER CAN HAVE JUST ONE PROFILE YET
    #     [
    #         [{"user_id": 1, "role": "P"}],
    #         [{"user_id": 1, "role": "S"}],
    #         [{"user_id": 1, "role": "C"}],
    #     ]
    # )
    # def test_create_multiple_profile_types_for_same_user(self, payload: dict) -> None:
    #     """Test HTTP_400 in attempt to create profile for user that has already a profile"""
    #     response = ProfileAPI.as_view({"post": "create_profile"})(get_request(payload))
    #
    #     user = get_user(payload["user_id"])
    #     profile = get_profile_by_role(payload["role"])
    #     assert profile.objects.get(user=user)
    #     assert response.status_code == 201

    @parameterized.expand(
        [
            [
                {
                    "user_id": 1,
                    "role": "P",
                },
                {
                    "height": 180,
                    "weight": 75,
                    "practice_distance": 20,
                    "prefered_leg": 1,
                    "player_positions": [
                        {"player_position": 1, "is_main": True},
                        {"player_position": 2, "is_main": False},
                    ],
                },
            ],
            [
                {
                    "user_id": 2,
                    "role": "P",
                },
                {
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                },
            ],
            [
                {
                    "user_id": 3,
                    "role": "T",
                },
                {
                    "licence": 1,
                    "team_object_id": 1,
                    "soccer_goal": 2,
                },
            ],
            [
                {
                    "user_id": 4,
                    "role": "C",
                },
                {
                    "club_object_id": 1,
                    "club_role": 5,
                    "phone": "111222333",
                },
            ],
            [
                {
                    "user_id": 5,
                    "role": "S",
                },
                {
                    "soccer_goal": 2,
                    "bio": "jakiesbio",
                },
            ],
        ]
    )
    def test_successfully_patch_profile_for_new_user(
        self, init_profile: dict, payload: dict
    ) -> None:
        """Test creating profiles with correctly passed payload"""
        profile = utils.create_empty_profile(init_profile)
        profile_uuid = profile.uuid
        payload["uuid"] = profile_uuid
        response = request.patch(reverse(url_create_or_update), payload)
        profile = utils.profile_service.get_profile_by_uuid(profile_uuid)

        assert response.status_code == 200
        for attr, val in payload.items():
            if attr != "role" and attr != "player_positions":
                assert getattr(profile, attr) == val

        if "player_positions" in payload:
            for pos in payload["player_positions"]:
                assert profile.player_positions.filter(
                    player_position_id=pos["player_position"]
                ).exists()

    def test_patch_fake_uuid(self) -> None:
        """patch request with fake uuid shouldn't pass"""
        fake_uuid = uuid.uuid4()
        response = request.patch(reverse(url_create_or_update), {"uuid": fake_uuid})

        assert response.status_code == 404

    def test_patch_invalid_uuid(self) -> None:
        """patch request with invalid uuid shouldn't pass"""
        response = request.patch(
            reverse(url_create_or_update), {"uuid": "invalid-uuid-1234"}
        )

        assert response.status_code == 400

    def test_post_need_authentication(self) -> None:
        """post request should require authentication"""
        response = request.post(
            reverse(url_create_or_update),
            {"user_id": 1, "role": "S"},
            force_authentication=False,
        )

        assert response.status_code == 401

    def test_patch_need_authentication(self) -> None:
        """patch request should require authentication"""
        profile = utils.create_empty_profile(
            {
                "user_id": 1,
                "role": "S",
            }
        )
        profile_uuid = profile.uuid
        response = request.patch(
            reverse(url_create_or_update),
            {"uuid": profile_uuid},
            force_authentication=False,
        )

        assert response.status_code == 401

    def test_post_request_need_body(self) -> None:
        """post require request's body, fail if empty"""
        response = request.post(reverse(url_create_or_update), {})

        assert response.status_code == 400

    def test_patch_request_need_body(self) -> None:
        """patch require request's body, fail if empty"""
        response = request.patch(reverse(url_create_or_update), {})

        assert response.status_code == 400

    def test_update_positions(self) -> None:
        """Test updating player positions"""
        # Create an initial profile
        initial_payload = {
            "user_id": 1,
            "role": "P",
            "height": 180,
            "weight": 75,
            "practice_distance": 20,
            "prefered_leg": 1,
            "player_positions": [
                {"player_position": 1, "is_main": True},
                {"player_position": 2, "is_main": False},
            ],
        }
        response = request.post(reverse(url_create_or_update), initial_payload)
        assert response.status_code == 201
        profile_uuid = response.data["uuid"]

        # Update profile with multiple main positions
        updated_payload = {
            "uuid": profile_uuid,
            "player_positions": [
                {"player_position": 1, "is_main": True},
                {"player_position": 2, "is_main": True},
            ],
        }
        response = request.patch(reverse(url_create_or_update), updated_payload)

        # Expected to fail due to multiple main positions
        assert response.status_code == 400
        assert "detail" in response.data
        assert response.data["detail"] == "A player can have only one main position."
        # Update profile with more than two non-main positions
        updated_payload = {
            "uuid": profile_uuid,
            "player_positions": [
                {"player_position": 1, "is_main": True},
                {"player_position": 2, "is_main": False},
                {"player_position": 3, "is_main": False},
                {"player_position": 4, "is_main": False},
            ],
        }
        response = request.patch(reverse(url_create_or_update), updated_payload)

        # Expected to fail due to more than two non-main positions
        assert response.status_code == 400
        assert "detail" in response.data
        assert (
            response.data["detail"]
            == "A player can have a maximum of two alternate positions."
        )
