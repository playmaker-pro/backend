from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase
from clubs.models import Club
from utils.factories import ClubFactory, consts


class ClubSearchTest(APITestCase):
    club_search_url = reverse("api:clubs:clubs_search")

    def setUp(self):
        ClubFactory.create_batch(5)

    def test_response_200(self):
        self.assertEqual(self.client.get(self.club_search_url).status_code, HTTP_200_OK)

    @parameterized.expand(
        [
            *[(club_name, 1) for club_name in consts.CLUB_NAMES],
            (consts.CLUB_NAMES[0] + "random_string", 0),
            ("random_string", 0),
            ("Club.objects.all()", 0),
            ("Club.objects.get(id=1)", 0),
        ]
    )
    def test_club_name_contains(self, query_param, response_obj_count):
        self.assertEqual(
            len(
                self.client.get(self.club_search_url, {"q": query_param}).data[
                    "results"
                ]
            ),
            response_obj_count,
        )

    def test_objects_created_successfully(self):
        self.assertEqual(Club.objects.all().count(), 5)
