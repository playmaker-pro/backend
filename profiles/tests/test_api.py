from urllib.request import Request
from rest_framework.test import APITestCase, force_authenticate, APIRequestFactory
from django.urls import reverse
from parameterized import parameterized
from .utils import get_profile_by_role, get_user, get_random_user
from utils.factories.clubs_factories import TeamFactory, ClubFactory, TeamHistoryFactory
from utils.factories.user_factories import UserFactory
from profiles.apis import ProfileAPI
from utils import testutils as utils

url: str = reverse("api:profiles:create_profile")


def get_request(payload: dict) -> Request:
    """create request, disable auth and return factory request object"""
    request = APIRequestFactory().post(url, payload, format="json")
    force_authenticate(request, get_random_user())
    return request


class TestCreateProfileAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        utils.create_system_user()
        UserFactory.create_batch_force_order(5)
        ClubFactory(id=1)
        TeamHistoryFactory(team=TeamFactory(name="Drużyna FC II", id=1), id=1)

    @parameterized.expand(
        [
            [{"user_id": 0, "role": "P"}],
            [{"id_user": 1, "role": "S"}],
            [{"user": 1, "role": "S"}],
        ]
    )
    def test_incorrect_user(self, payload: dict) -> None:
        """test HTTP_400 if request has wrong defined user_id"""
        response = ProfileAPI.as_view({"post": "create"})(get_request(payload))

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
        response = ProfileAPI.as_view({"post": "create"})(get_request(payload))

        assert response.status_code == 400

    @parameterized.expand(
        [
            [
                (
                    ("user_id", 1),
                    ("role", "P"),
                    ("height", 180),
                    ("weight", 75),
                    ("practice_distance", 20),
                    ("prefered_leg", 1),
                ),
            ],
            [
                (
                    ("user_id", 2),
                    ("role", "P"),
                    ("team_object_id", 1),
                    ("team_history_object_id", 1),
                )
            ],
            [
                (
                    ("user_id", 3),
                    ("role", "T"),
                    ("licence", 1),
                    ("team_object_id", 1),
                    ("soccer_goal", 2),
                )
            ],
            [
                (
                    ("user_id", 4),
                    ("role", "C"),
                    ("club_object_id", 1),
                    ("club_role", 5),
                    ("phone", "111222333"),
                )
            ],
            [
                (
                    ("user_id", 5),
                    ("role", "S"),
                    ("soccer_goal", 2),
                )
            ],
        ],
    )
    def test_successfully_create_profile_for_new_user(
        self, payload_stub: tuple
    ) -> None:
        """Test creating profiles with correctly passed payload"""
        payload = {key: value for key, value in payload_stub}
        response = ProfileAPI.as_view({"post": "create"})(get_request(payload))

        assert response.status_code == 201
        assert response.data["user_id"] and response.data["role"]

        user = get_user(payload["user_id"])
        profile_type = get_profile_by_role(payload["role"])
        profile = profile_type.objects.get(user=user)

        for attr, val in payload.items():
            if attr != "role":
                assert getattr(profile, attr) == val

    @parameterized.expand([[{"user_id": 1, "role": "P"}]])
    def test_create_same_profile_type_twice_for_same_user(self, payload: dict) -> None:
        """Test HTTP_400 in attempt to create profile for user that has already a profile"""
        ProfileAPI.as_view({"post": "create"})(get_request(payload))
        response2 = ProfileAPI.as_view({"post": "create"})(get_request(payload))

        assert response2.status_code == 400

    @parameterized.expand(
        [
            [{"user_id": 1, "role": "P"}],
            [{"user_id": 1, "role": "S"}],
            [{"user_id": 1, "role": "C"}],
        ]
    )
    def test_create_multiple_profile_types_for_same_user(self, payload: dict) -> None:
        """Test HTTP_400 in attempt to create profile for user that has already a profile"""
        response = ProfileAPI.as_view({"post": "create"})(get_request(payload))

        user = get_user(payload["user_id"])
        profile = get_profile_by_role(payload["role"])
        assert profile.objects.get(user=user)
        assert response.status_code == 201
