from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APITestCase

from clubs.models import Team
from utils.factories.clubs_factories import TeamFactory


class TeamSearchTest(APITestCase):
    team_search_url = reverse("resources:teams_search")

    def setUp(self):
        TeamFactory.create_batch(5)

    def test_response_200(self):
        self.assertEqual(self.client.get(self.team_search_url).status_code, HTTP_200_OK)

    @parameterized.expand(
        [
            ("FC", 2),
            ("", 5),
            ("Bayern", 1),
            ("randomtext", 0),
            ("fc T", 1),
            ("ŁśćŻźąęó", 1),
            ("a", 4),
            ("Team.objects.all()", 0),
            ("Team.objects.get(id=1)", 0),
        ]
    )
    def test_team_name_contains(self, query_param, response_obj_count):
        self.assertEqual(
            len(
                self.client.get(self.team_search_url, {"q": query_param}).data[
                    "results"
                ]
            ),
            response_obj_count,
        )

    def test_objects_created_successfully(self):
        self.assertEqual(Team.objects.all().count(), 5)
