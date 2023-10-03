import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager

default_body = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "label": 1}
body_json = json.dumps(default_body)
User = get_user_model()


class TestPlayerVideoAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj: User = self.manager.create_superuser()
        self.headers: dict = self.manager.get_headers()
        self.url: str = reverse("api:profiles:modify_player_video")

    def create_dummy_video(
        self, user: User = None, **kwargs
    ) -> factories.models.PlayerVideo:
        """
        Create and return dummy video of given user (more like for his PlayerProfile).
        If user is None, video will be created for new user - usefull for testing ownership.
        """  # noqa: E501
        if user:
            kwargs["user"] = user

        dummy_player: factories.models.PlayerProfile = (
            factories.PlayerProfileFactory.create(**kwargs)
        )
        factories.PlayerVideoFactory.create(player=dummy_player, **default_body)
        return dummy_player.player_video.first()  # type: ignore


class TestCreatePlayerVideoAPI(TestPlayerVideoAPI):
    def test_create_video_valid_auth(self) -> None:
        """SUCCESS create video with valid authentication"""
        profile: factories.models.PlayerProfile = factories.PlayerProfileFactory.create(
            user=self.user_obj
        )
        response = self.client.post(self.url, body_json, **self.headers)

        assert response.status_code == 201
        assert len(response.data["player_video"]) == 1
        assert profile.player_video.count() == 1

        response = self.client.post(self.url, body_json, **self.headers)

        assert response.status_code == 201
        assert len(response.data["player_video"]) == 2
        assert profile.player_video.count() == 2

    def test_create_video_invalid_auth(self) -> None:
        """FAIL create video with invalid authentication"""
        response = self.client.post(self.url, body_json, format="json")

        assert response.status_code == 401

    def test_create_video_user_has_no_player_profile(self) -> None:
        """FAIL create video with valid authentication, but User has no PlayerProfile"""
        response = self.client.post(self.url, body_json, **self.headers)
        assert response.status_code == 400


class TestUpdatePlayerVideoAPI(TestPlayerVideoAPI):
    def test_patch_video_valid_auth(self) -> None:
        """SUCCESS patch video with valid authentication"""
        video: factories.models.PlayerVideo = self.create_dummy_video(self.user_obj)
        profile: factories.models.PlayerProfile = video.player

        assert video.url == default_body["url"]
        assert video.label == default_body["label"]

        new_label, new_url = 2, "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        body = json.dumps({"label": new_label, "url": new_url, "id": video.pk})

        response = self.client.patch(self.url, body, **self.headers)

        video: factories.models.PlayerVideo = profile.player_video.first()  # noqa: E501
        assert video.url == new_url
        assert video.label == new_label

        assert response.status_code == 200
        assert len(response.data["player_video"]) == 1

    def test_patch_video_invalid_auth(self) -> None:
        """FAIL patch video with invalid authentication"""
        response = self.client.patch(self.url, body_json, format="json")

        assert response.status_code == 401

    def test_patch_video_user_is_not_an_owner_of_video(self) -> None:
        """
        FAIL patch video with valid authentication,
        but User is not owner of given video
        """
        video: factories.models.PlayerVideo = self.create_dummy_video()
        response = self.client.patch(
            self.url, json.dumps({"id": video.pk}), **self.headers
        )

        assert response.status_code == 400

    def test_patch_video_valid_auth_incomplete_body(self) -> None:
        """FAIL patch video with empty body and valid authentication"""
        response = self.client.patch(self.url, json.dumps({}), **self.headers)

        assert response.status_code == 400

    def test_patch_video_valid_auth_video_does_not_exist(self) -> None:
        """FAIL patch video that does not exist with valid authentication"""
        response = self.client.patch(self.url, json.dumps({"id": 9999}), **self.headers)

        assert response.status_code == 404


class TestDeletePlayerVideoAPI(TestPlayerVideoAPI):
    def test_delete_video_valid_auth(self) -> None:
        """SUCCESS delete video with valid authentication"""
        video: factories.models.PlayerVideo = self.create_dummy_video(self.user_obj)
        profile: factories.models.PlayerProfile = video.player

        response = self.client.delete(
            reverse("api:profiles:delete_player_video", kwargs={"video_id": video.pk}),
            **self.headers
        )

        assert not profile.player_video.all()  # type: ignore
        assert response.status_code == 200
        assert len(response.data["player_video"]) == 0

    def test_delete_video_invalid_auth(self) -> None:
        """FAIL delete video with invalid authentication"""
        video: factories.models.PlayerVideo = self.create_dummy_video(self.user_obj)
        response = self.client.delete(
            reverse("api:profiles:delete_player_video", kwargs={"video_id": video.pk})
        )

        assert response.status_code == 401

    def test_delete_video_user_is_not_an_owner_of_video(self) -> None:
        """
        FAIL delete video with valid authentication,
        but User is not owner of given video
        """
        video: factories.models.PlayerVideo = self.create_dummy_video()

        response = self.client.delete(
            reverse("api:profiles:delete_player_video", kwargs={"video_id": video.pk}),
            **self.headers
        )

        assert response.status_code == 400

    def test_delete_video_valid_auth_video_does_not_exist(self) -> None:
        """FAIL delete video that does not exist and valid authentication"""
        response = self.client.delete(
            reverse("api:profiles:delete_player_video", kwargs={"video_id": 9999}),
            **self.headers
        )

        assert response.status_code == 404
