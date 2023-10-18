import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from profiles.models import ProfileVideo
from utils import factories
from utils.test.test_utils import UserManager

default_body = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "label": "player_short",
}
body_json = json.dumps(default_body)
User = get_user_model()


class TestProfileVideoLabels(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url = reverse("api:profiles:profile_video_labels")

    @parameterized.expand(
        [
            ["P", ProfileVideo.PlayerLabels.choices],
            ["T", ProfileVideo.CoachLabels.choices],
            ["C", ProfileVideo.ClubLabels.choices],
            [None, ProfileVideo.LABELS],
        ]
    )
    def test_get_labels(self, param, labels) -> None:
        """Test get video labels with param or without"""
        response = self.client.get(self.url, {"role": param} if param else {})

        assert response.status_code == 200
        assert [item["id"] for item in response.data] == [item[0] for item in labels]


class TestProfileVideoAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj: User = self.manager.create_superuser()
        self.headers: dict = self.manager.get_headers()
        self.url = lambda video_id: reverse(
            "api:profiles:modify_profile_video", kwargs={"video_id": video_id}
        )

    def create_dummy_video(
        self, user: User = None, **kwargs
    ) -> factories.models.ProfileVideo:
        """
        Create and return dummy video of given user (more like for his PlayerProfile).
        If user is None, video will be created for new user - usefull for testing ownership.
        """
        if not user:
            user: User = factories.UserFactory.create(**kwargs)
        return factories.ProfileVideoFactory.create(user=user, **default_body)  # type: ignore


class TestCreateProfileVideoAPI(TestProfileVideoAPI):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("api:profiles:create_profile_video")

    def test_create_video_valid_auth(self) -> None:
        """SUCCESS create video with valid authentication"""
        response = self.client.post(self.url, body_json, **self.headers)

        assert response.status_code == 201
        assert self.user_obj.user_video.count() == 1

        response = self.client.post(self.url, body_json, **self.headers)

        assert response.status_code == 201
        assert self.user_obj.user_video.count() == 2

    def test_create_video_invalid_auth(self) -> None:
        """FAIL create video with invalid authentication"""
        response = self.client.post(self.url, body_json, format="json")

        assert response.status_code == 401


class TestUpdateProfileVideoAPI(TestProfileVideoAPI):
    def test_patch_video_valid_auth(self) -> None:
        """SUCCESS patch video with valid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        new_label, new_url = (
            "player_goal",
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        )
        body = json.dumps({"label": new_label, "url": new_url})
        response = self.client.patch(self.url(video.pk), body, **self.headers)
        video.refresh_from_db()

        assert video.url == new_url
        assert video.label == new_label
        assert response.status_code == 200

    def test_patch_video_invalid_auth(self) -> None:
        """FAIL patch video with invalid authentication"""
        response = self.client.patch(self.url(self.create_dummy_video().pk), {})

        assert response.status_code == 401

    def test_patch_video_user_is_not_an_owner_of_video(self) -> None:
        """FAIL patch video with valid authentication, but User is not owner of given video"""
        video: factories.models.ProfileVideo = self.create_dummy_video()
        response = self.client.patch(self.url(video.pk), json.dumps({}), **self.headers)

        assert response.status_code == 400

    def test_patch_video_valid_auth_video_does_not_exist(self) -> None:
        """FAIL patch video that does not exist with valid authentication"""
        response = self.client.patch(self.url, json.dumps({"id": 9999}), **self.headers)

        assert response.status_code == 404


class TestDeleteProfileVideoAPI(TestProfileVideoAPI):
    def test_delete_video_valid_auth(self) -> None:
        """SUCCESS delete video with valid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        user: User = video.user

        response = self.client.delete(self.url(video.pk), **self.headers)

        assert not user.user_video.all()  # type: ignore
        assert response.status_code == 204

    def test_delete_video_invalid_auth(self) -> None:
        """FAIL delete video with invalid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        response = self.client.delete(
            self.url(video.pk),
        )

        assert response.status_code == 401

    def test_delete_video_user_is_not_an_owner_of_video(self) -> None:
        """FAIL delete video with valid authentication, but User is not owner of given video"""
        video: factories.models.ProfileVideo = self.create_dummy_video()

        response = self.client.delete(self.url(video.pk), **self.headers)

        assert response.status_code == 400

    def test_delete_video_valid_auth_video_does_not_exist(self) -> None:
        """FAIL delete video that does not exist and valid authentication"""
        response = self.client.delete(self.url(9999), **self.headers)

        assert response.status_code == 404
