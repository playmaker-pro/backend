import json

from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from utils import factories
from utils.test.test_utils import UserManager


class TestGetCreateCoachLicenceAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.url = reverse("api:profiles:coach_licences")

    def test_list_licence_choices(self) -> None:
        """test list all available licence types"""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data

    def test_success_create_licence_for_coach(self) -> None:
        """test create licence for coach"""
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "licence_id": 1,
                    "expiry_date": "2025-01-01",
                }
            ),
            **self.headers
        )

        assert response.status_code == 201

    def test_create_licence_for_coach_with_invalid_licence_id(self) -> None:
        """test create licence for coach with invalid licence id"""
        response = self.client.post(
            self.url,
            data={
                "licence_id": 100,
                "expiry_date": "2025-01-01",
            },
            **self.headers
        )

        assert response.status_code == 400

    def test_create_licence_for_coach_with_invalid_expire_date(self) -> None:
        """test create licence for coach with invalid expire date"""
        response = self.client.post(
            self.url,
            data={
                "licence_id": 2,
                "expiry_date": "01-01-01",
            },
            **self.headers
        )

        assert response.status_code == 400

    def test_create_licence_for_coach_with_empty_licence_id(self) -> None:
        """test create licence for coach with empty licence id"""
        response = self.client.post(
            self.url,
            data={
                "licence_id": "",
                "expiry_date": "2025-01-01",
            },
            **self.headers
        )

        assert response.status_code == 400

    def test_create_licence_for_coach_unauthenticated(self) -> None:
        """test create licence for coach without authentication"""
        response = self.client.post(
            self.url,
            data={
                "licence_id": 1,
                "expiry_date": "2025-01-01",
            },
        )

        assert response.status_code == 401

    def test_create_same_licence_twice_for_coach(self) -> None:
        """test create same licence twice for coach"""
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    "licence_id": 2,
                    "expiry_date": "2025-01-01",
                }
            ),
            **self.headers
        )

        assert response.status_code == 201

        response = self.client.post(
            self.url,
            data={
                "licence_id": 1,
                "expiry_date": "2025-01-01",
            },
            **self.headers
        )

        assert response.status_code == 400


class TestUpdateDeleteCoachLicenceAPI(APITestCase):
    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.manager = UserManager(self.client)
        self.user_obj = self.manager.create_superuser()
        self.headers = self.manager.get_headers()
        self.licence = factories.CoachLicenceFactory(owner=self.user_obj, pk=1)
        self.url = lambda licence_id: reverse(
            "api:profiles:coach_licences_modify", kwargs={"licence_id": licence_id}
        )

    def test_patch_licence_for_user(self) -> None:
        """test patch licence for user"""
        response = self.client.patch(
            self.url(self.licence.pk),
            data=json.dumps(
                {
                    "expiry_date": "2025-01-01",
                    "is_in_progress": True,
                    "release_year": 2010,
                }
            ),
            **self.headers
        )

        assert response.status_code == 200

    def test_patch_licence_for_user_with_invalid_licence_id(self) -> None:
        """test patch licence for user with invalid licence id"""
        response = self.client.patch(
            self.url(100),
            data={"expiry_date": "2025-01-01", "release_year": 2010},
            **self.headers
        )

        assert response.status_code == 404

    def test_patch_licence_for_user_with_invalid_expire_date(self) -> None:
        """test patch licence for user with invalid expire date"""
        response = self.client.patch(
            self.url(self.licence.pk),
            data=json.dumps({"expiry_date": "01-01-01", "release_year": 2010}),
            **self.headers
        )

        assert response.status_code == 400

    def test_patch_licence_for_user_unauthenticated(self) -> None:
        """test patch licence for user without authentication"""
        response = self.client.patch(
            self.url(self.licence.pk),
            data={
                "expiry_date": "2025-01-01",
            },
        )

        assert response.status_code == 401

    def test_patch_licence_assing_already_owned_licence(self) -> None:
        """test patch licence to already owned licence"""
        second_licence = factories.CoachLicenceFactory(owner=self.user_obj)

        response = self.client.patch(
            self.url(second_licence.pk),
            data={"licence_id": self.licence.licence.pk},
            **self.headers
        )

        assert response.status_code == 400

    def test_patch_somebody_licence(self) -> None:
        """test patch licence to somebody else licence"""
        another_user = factories.UserFactory.create()
        another_user_licence = factories.CoachLicenceFactory(owner=another_user)

        response = self.client.patch(
            self.url(another_user_licence.pk), data={"licence_id": 2}, **self.headers
        )

        assert response.status_code == 400

    def test_delete_licence_for_user(self) -> None:
        """test delete licence for user"""
        response = self.client.delete(self.url(self.licence.pk), **self.headers)

        assert response.status_code == 204

    def test_delete_licence_for_somebody_else(self) -> None:
        """test delete licence for somebody else"""
        another_user = factories.UserFactory.create()
        another_user_licence = factories.CoachLicenceFactory(owner=another_user)

        response = self.client.delete(self.url(another_user_licence.pk), **self.headers)

        assert response.status_code == 400

    def test_delete_licence_for_user_unauthenticated(self) -> None:
        """test delete licence for user without authentication"""
        response = self.client.delete(self.url(self.licence.pk))

        assert response.status_code == 401
