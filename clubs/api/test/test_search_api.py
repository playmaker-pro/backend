from django.urls import reverse
from rest_framework.test import APITestCase
from clubs.models import Club
from rest_framework.status import HTTP_200_OK
from parameterized import parameterized
from utils.factories.clubs.club_factory import ClubFactory


class ClubSearchTest(APITestCase):

    club_search_url = reverse("resources:clubs_search")
    
    def setUp(self):
        ClubFactory.create_batch(5)

    def test_response_200(self):
        self.assertEqual(self.client.get(self.club_search_url).status_code, HTTP_200_OK)        

    @parameterized.expand([
        ("Bayern", 1),
        ("FC", 2),
        ("Manchesterr", 0),
        ("man", 1),
        ("che", 1),
        ("", 5),
        ("ków", 1),
        ("śćężźłó", 1),
        ("Club.objects.all()", 0),
        ("Club.objects.get(id=1)", 0)
    ])
    def test_club_name_contains(self, query_param, response_obj_count):
        self.assertEqual(
            len(self.client.get(
                self.club_search_url, {"q": query_param}).data["results"]),
                response_obj_count
            )

    def test_objects_created_successfully(self):
        self.assertEqual(Club.objects.all().count(), 5)

