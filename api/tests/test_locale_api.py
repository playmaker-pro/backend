from django.urls import reverse
from parameterized import parameterized
from rest_framework.test import APIClient, APITestCase

from utils.factories import CityFactory


class TestLocaleCitiesView(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("api:cities_list")

    def test_list_cities(self):
        """list cities with query"""
        for city in CityFactory.create_batch(3):
            response = self.client.get(self.url, {"city": city.name})

            assert response.status_code == 200
            assert len(response.data["results"]) == 1


class TestLocaleLanguagesView(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("api:languages_list")

    def test_list_languages(self):
        """test list languages"""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data

    @parameterized.expand([["en", "English"], ["de", "Englisch"], ["uk", "Англійська"]])
    def test_list_languages_with_language_param(self, code: str, translated_name: str):
        """list languages, test language param input"""
        response = self.client.get(self.url, {"language": code})

        assert response.status_code == 200
        for language in response.data:
            if language["code"] == "en":  # English should be first iteration
                assert language["name"] == translated_name
                break

    def test_list_languages_incorrect_language_param(self):
        """test list languages with incorrect language param"""
        response = self.client.get(self.url, {"language": "foobar"})

        assert response.status_code == 400


class TestLocaleCountriesView(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("api:countries_list")

    def test_list_countries_incorrect_language_param(self):
        """test list countries with incorrect language param"""
        response = self.client.get(self.url, {"language": "foobar"})

        assert response.status_code == 400

    def test_list_countries(self):
        """list countries"""
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.data

    @parameterized.expand([["en", "Poland"], ["de", "Polen"], ["uk", "Польща"]])
    def test_list_countries_with_language_param(self, code: str, translated_name: str):
        """list countries, test language param input"""
        response = self.client.get(self.url, {"language": code})

        assert response.status_code == 200
        for country in response.data:
            if country["code"] == "PL":  # Poland should be first iteration
                assert country["country"] == translated_name
                break
