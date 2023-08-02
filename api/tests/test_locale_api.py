from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from utils.factories import CityFactory


class TestLocaleDataView(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

    def test_list_countries(self):
        """list countries"""
        response = self.client.get(reverse("api:countries_list"))

        assert response.status_code == 200
        assert response.data

    def test_list_cities(self):
        """list cities with query"""
        for city in CityFactory.create_batch(3):
            response = self.client.get(reverse("api:cities_list"), {"city": city.name})

            assert response.status_code == 200
            assert len(response.data) == 1

    def test_list_languages(self):
        response = self.client.get(reverse("api:languages_list"))

        assert response.status_code == 200
        assert response.data
