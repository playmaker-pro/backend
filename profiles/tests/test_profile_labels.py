import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager


class TestGetProfileLabelsAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch(5)
        self.profile = factories.PlayerProfileFactory.create(user=self.user_obj)
        self.profile_uuid = self.profile.uuid
        label_def1 = factories.LabelDefinitionFactory(label_name="label1")
        label_def2 = factories.LabelDefinitionFactory(label_name="label2")
        factories.LabelFactory(
            label_definition=label_def1,
            object_id=self.profile.user.id,
            visible_on_profile=True,
            start_date="2021-01-01",
            season_name=None,
        )
        factories.LabelFactory(
            label_definition=label_def2,
            object_id=self.profile.user.id,
            visible_on_profile=True,
            start_date="2021-01-01",
            season_name=None,
        )

        self.url = "api:profiles:get_profile_labels"

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
        assert len(response.data) == 2
        assert response.status_code == status.HTTP_200_OK
