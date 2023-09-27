import json
import uuid

from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from profiles.services import ProfileService
from profiles.tests import utils
from roles.definitions import CLUB_ROLE_TEAM_LEADER
from utils import factories
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
        """correct get request with valid uuid, no need to authenticate"""
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
        factories.ClubFactory(pk=1)
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
                    "practice_distance": 20,
                    "prefered_leg": 1,
                },
            ],
            [
                {
                    "role": "P",
                },
                {
                    "team_object_id": 1,
                    "team_history_object_id": 1,
                },
            ],
            [
                {
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
                    "role": "C",
                },
                {
                    "club_object_id": 1,
                    "club_role": "Kierownik",
                    "phone": "111222333",
                },
            ],
            [
                {
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
        """Test updating profiles with correctly passed payload"""
        profile = utils.create_empty_profile(**init_profile, user_id=self.user_obj.pk)
        profile_uuid = profile.uuid
        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )
        profile = utils.profile_service.get_profile_by_uuid(profile_uuid)

        assert response.status_code == 200
        for attr, val in payload.items():
            if attr == "uuid":
                val = uuid.UUID(val)
            assert getattr(profile, attr) == val

    @parameterized.expand(
        [
            ("birth_date", "2001-11-14"),
            ("localization", 1),
            ("spoken_languages", [1]),
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
        payload = {"verification_stage": {"step": 5, "done": True}}

        response = self.client.patch(
            self.url(str(profile_uuid)), json.dumps(payload), **self.headers
        )

        assert response.status_code == 200
        assert response.data["verification_stage"]["step"] == 5
        assert response.data["verification_stage"]["done"] == True
