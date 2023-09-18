from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
import uuid
from utils import factories
from utils.test.test_utils import UserManager


class TestGetProfileLabelsAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch_force_order(5)
        profile = factories.PlayerProfileFactory.create(user_id=1)
        profile.labels.create(label_name="label1", season_name="2018/2019")
        profile.labels.create(label_name="label1", season_name="2019/2020")
        profile.labels.create(label_name="label2", season_name="2019/2020")
        self.url = "api:profiles:get_profile_labels"
        self.profile_uuid = profile.uuid

    def test_get_profile_labels_and_profile_does_not_exists(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"profile_uuid": uuid.uuid4()}),
            **self.headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_profile_labels_all(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"profile_uuid": self.profile_uuid}),
            **self.headers,
        )
        assert len(response.data) == 3
        assert response.status_code == status.HTTP_200_OK

    def test_get_profile_labels_specific_season(self) -> None:
        response = self.client.get(
            f'{reverse(self.url, kwargs={"profile_uuid": self.profile_uuid})}?season_name=2019/2020',
            **self.headers,
        )
        assert len(response.data) == 2
        for d in response.data:
            assert d["season_name"] == "2019/2020"
            assert not d.get("created_at"), "created_at should not be visible"
            assert not d.get("updated_at"), "updated_at should not be visible"
            assert not d.get(
                "visible_on_profile"
            ), "visible_on_profile should not be visible"
            assert not d.get("visible_on_base"), "visible_on_base should not be visible"
            assert not d.get(
                "visible_on_main_page"
            ), "visible_on_main_page should not be visible"
        assert response.status_code == status.HTTP_200_OK
