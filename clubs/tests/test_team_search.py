from django.urls import reverse
from rest_framework.test import APITestCase
from clubs.models import Team
from rest_framework.status import HTTP_200_OK
from parameterized import parameterized
from .test_club_search import ClubFactory

class TeamFactory(ClubFactory):

    def __init__(self):
        super().__init__()

        self.team1 = Team.objects.create(
            name="Barca",
            club=self.club1
            )
        self.team2 = Team.objects.create(
            name="ManUtd",
            club=self.club2
            )
        self.team3 = Team.objects.create(
            name="Bayern",
            club=self.club3
            )
        self.team4 = Team.objects.create(
            name="FC Bayern",
            club=self.club3
            )
        self.team5 = Team.objects.create(
            name="jakisfcKlub",
            club=self.club1
            )


class TeamSearchTest(APITestCase):

    team_search_url = reverse("resources:teams_search")

    def setUp(self):
        self.teams = TeamFactory()        

    def test_response_200(self):
        self.assertEqual(self.client.get(self.team_search_url).status_code, HTTP_200_OK)

    @parameterized.expand([
        ("Barca", 1),
        ("FC", 2),
        ("", 5),
        ("Bayern", 2),
        ("randomtext", 0),
        (0, 0),
        (True, 0),
        ("a", 5),
        ("Team.objects.all()", 0),
        ("Team.objects.get(id=1)", 0)
    ])
    def test_team_name_contains(self, query_param, response_obj_count):
        self.assertEqual(
            len(self.client.get(
                self.team_search_url, {"q": query_param}).data["results"]),
                response_obj_count
            )

    def test_objects_created_successfully(self):
        self.assertEqual(Team.objects.all().count(), 5)
