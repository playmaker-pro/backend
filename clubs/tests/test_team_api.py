import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager


class TestGetTeamAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch(5)
        team = factories.TeamFactory(name="Drużyna FC II", id=100)

        self.url = "api:clubs:get_team"
        self.team_id = team.id

    def test_get_team_and_team_does_not_exists(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"team_id": 1000000000}),
            **self.headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_team(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"team_id": self.team_id}),
            **self.headers,
        )
        assert response.status_code == status.HTTP_200_OK
        # TODO(rkesik): do more checks aginst object validation of a attributes


class TestGetTeamLabelsAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.user = UserManager(self.client)
        self.user_obj = self.user.create_superuser()
        self.headers = self.user.get_headers()
        factories.UserFactory.create_batch(5)
        team = factories.TeamFactory(name="Drużyna FC II", id=100)

        team.labels.create(label_name="label1", season_name="2018/2019")
        team.labels.create(label_name="label1", season_name="2019/2020")
        team.labels.create(label_name="label2", season_name="2019/2020")
        team.labels.create(
            label_name="label-not-visible", season_name="2019/2020", visible=False
        )

        team2 = factories.TeamFactory(name="Drużyna FC IIIs", id=101)
        team2.labels.create(label_name="label1", season_name="2018/2019")

        self.url = "api:clubs:get_team_labels"
        self.team_id = team.id

    def test_get_team_labels_and_team_does_not_exists(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"team_id": 1000000000}),
            **self.headers,
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_team_labels_all(self) -> None:
        response = self.client.get(
            reverse(self.url, kwargs={"team_id": self.team_id}),
            **self.headers,
        )
        assert len(response.data) == 3
        assert response.status_code == status.HTTP_200_OK

    def test_get_team_labels_specific_season(self) -> None:
        url: str = reverse(self.url, kwargs={"team_id": self.team_id})
        response = self.client.get(
            url + "?season_name=2019/2020",
            **self.headers,
        )
        # Then

        # we should have 2 objects out of total 3
        assert len(response.data) == 2, response.data

        # all labels should have 2019/2020 attribute value as `season_name`
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
