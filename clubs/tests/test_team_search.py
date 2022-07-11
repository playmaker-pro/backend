from django.urls import reverse
from rest_framework.test import APITestCase
from clubs.models import Team, Club
from rest_framework.status import HTTP_200_OK

class TeamSearchTest(APITestCase):

    url = reverse("resources:teams_search")

    def setUp(self):
        self.team1 = Team.objects.create(
            name="Barca",
            club=Club.objects.create(
               name="FC Barcelona",
               country="ES"
                )
            )
        self.team2 = Team.objects.create(
            name="ManUtd",
            club=Club.objects.create(
               name="Manchester United F.C.",
               country="EN"
                )
            )
        self.team3 = Team.objects.create(
            name="Bayern",
            club=Club.objects.create(
               name="FC Bayern Munchen",
               country="DE"
                )
            )
        self.team4 = Team.objects.create(
            name="FC Bayern",
            club=Club.objects.create(
               name="FC Bayern",
               country="DE"
                )
            )
        self.team5 = Team.objects.create(
            name="jakisfcKlub",
            club=Club.objects.create(
               name="Jakis Klub",
               country="PL"
                )
            )


    def test_response_200(self):
        self.assertEqual(self.client.get(self.url).status_code, HTTP_200_OK)


    def test_name_contains(self):       
        case1 = self.client.get(self.url, {"q": "Barca"})
        case2 = self.client.get(self.url, {"q": "FC"})
        case3 = self.client.get(self.url, {"q": ""})
        case4 = self.client.get(self.url, {"q": "Bayern"})
        case5 = self.client.get(self.url, {"q": "somerandomtext"})
        case6 = self.client.get(self.url, {"q": "0"})
        case7 = self.client.get(self.url, {"q": True})
        case8 = self.client.get(self.url, {"q": "F" + "C"})
        case9 = self.client.get(self.url, {"q": self.team4})

        self.assertEqual(len(case1.data["results"]), 1)
        self.assertEqual(len(case2.data["results"]), 2)
        self.assertEqual(len(case3.data["results"]), 5)
        self.assertEqual(len(case4.data["results"]), 2)
        self.assertEqual(len(case5.data["results"]), 0)
        self.assertEqual(len(case6.data["results"]), 0)
        self.assertEqual(len(case7.data["results"]), 0)
        self.assertEqual(len(case8.data["results"]), 2)
        self.assertEqual(len(case9.data["results"]), 0)


    def test_objects_created_successfully(self):
        self.assertEqual(Team.objects.all().count(), 5)
