import factory
from .club_factory import ClubFactory

TEAM_MOCK = [
    "FC Barca",
    "ManUtd",
    "Bayern",
    "Jakisfc Team",
    "ŁśćŻźąęó"
]

class TeamFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = 'clubs.Team'

    name = factory.Iterator(TEAM_MOCK)
    club = factory.SubFactory(ClubFactory)

