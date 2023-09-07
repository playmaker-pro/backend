from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from utils import factories
from utils.test.test_utils import UserManager


class TestGetTeamLabelsAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch_force_order(5)
        team = factories.TeamFactory(name="Drużyna FC II", id=100)

        team.labels.create(label_name="label1", season_name="2018/2019")
        team.labels.create(label_name="label1", season_name="2019/2020")
        team.labels.create(label_name="label2", season_name="2019/2020")

        self.url = "api:clubs:get_team_labels"
        self.team_id = team.id

    def test_get_team_labels_all(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"team_id": self.team_id}),
            **self.headers,
        )
        assert len(response.data) == 3
        assert response.status_code == status.HTTP_200_OK

    def test_get_team_labels_specific_season(self) -> None:
        response = self.client.get(
            f'{reverse(self.url, kwargs={"team_id": self.team_id })}?season_name=2019/2020',
            **self.headers,
        )
        assert len(response.data) == 2
        for d in response.data:
            assert d["season_name"] == "2019/2020"
        assert response.status_code == status.HTTP_200_OK
