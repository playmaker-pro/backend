import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager

default_body = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "label": 1}
body_json = json.dumps(default_body)
User = get_user_model()


class TestProfileVideoAPI(APITestCase):
    def setUp(self) -> None:
        """set up object factories"""
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj: User = self.manager.create_superuser()
        self.headers: dict = self.manager.get_headers()
        self.url: str = reverse("api:profiles:modify_profile_video")

    def create_dummy_video(
        self, user: User = None, **kwargs
    ) -> factories.models.ProfileVideo:
        """
        Create and return dummy video of given user (more like for his PlayerProfile).
        If user is None, video will be created for new user - usefull for testing ownership.
        """  # noqa: E501
        if not user:
            user = factories.UserFactory.create()

        factories.ProfileVideoFactory.create(user=user, **default_body)
        return user.user_video.first()  # type: ignore


class TestCreateProfileVideoAPI(TestProfileVideoAPI):
    def test_create_video_valid_auth(self) -> None:
        """SUCCESS create video with valid authentication"""
        response = self.client.post(self.url, body_json, **self.headers)

        assert response.status_code == 201

        user_videos = self.user_obj.user_video.all()

        assert len(user_videos) == 1

        response = self.client.post(self.url, body_json, **self.headers)
        updated_user_videos = self.user_obj.user_video.all()

        assert response.status_code == 201
        assert len(updated_user_videos) == 2

    def test_create_video_invalid_auth(self) -> None:
        """FAIL create video with invalid authentication"""
        response = self.client.post(self.url, body_json, format="json")
        assert response.status_code == 401


class TestUpdateProfileVideoAPI(TestProfileVideoAPI):
    def test_patch_video_valid_auth(self) -> None:
        """SUCCESS patch video with valid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        user: factories.models.User = video.user

        assert video.url == default_body["url"]
        assert video.label == default_body["label"]

        new_label, new_url = 2, "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        body = json.dumps({"label": new_label, "url": new_url, "id": video.pk})

        response = self.client.patch(self.url, body, **self.headers)

        video: factories.models.ProfileVideo = user.user_video.first()  # noqa: E501
        assert video.url == new_url
        assert video.label == new_label

        assert response.status_code == 200

    def test_patch_video_invalid_auth(self) -> None:
        """FAIL patch video with invalid authentication"""
        response = self.client.patch(self.url, body_json, format="json")

        assert response.status_code == 401

    def test_patch_video_user_is_not_an_owner_of_video(self) -> None:
        """
        FAIL patch video with valid authentication,
        but User is not owner of given video
        """

        video: factories.models.ProfileVideo = self.create_dummy_video()
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


class TestDeleteProfileVideoAPI(TestProfileVideoAPI):
    def test_delete_video_valid_auth(self) -> None:
        """SUCCESS delete video with valid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        user: factories.models.User = video.user

        response = self.client.delete(
            reverse("api:profiles:delete_profile_video", kwargs={"video_id": video.pk}),
            **self.headers
        )

        assert not user.user_video.all()  # type: ignore
        assert response.status_code == 200

        user_videos = user.user_video.all()  # type: ignore

        assert user_videos.count() == 0

    def test_delete_video_invalid_auth(self) -> None:
        """FAIL delete video with invalid authentication"""
        video: factories.models.ProfileVideo = self.create_dummy_video(self.user_obj)
        response = self.client.delete(
            reverse("api:profiles:delete_profile_video", kwargs={"video_id": video.pk})
        )

        assert response.status_code == 401

    def test_delete_video_user_is_not_an_owner_of_video(self) -> None:
        """
        FAIL delete video with valid authentication,
        but User is not owner of given video
        """
        video: factories.models.ProfileVideo = self.create_dummy_video()

        response = self.client.delete(
            reverse("api:profiles:delete_profile_video", kwargs={"video_id": video.pk}),
            **self.headers
        )

        assert response.status_code == 400

    def test_delete_video_valid_auth_video_does_not_exist(self) -> None:
        """FAIL delete video that does not exist and valid authentication"""
        response = self.client.delete(
            reverse("api:profiles:delete_profile_video", kwargs={"video_id": 9999}),
            **self.headers
        )

        assert response.status_code == 404
