import factory

CLUB_MOCK = [
    "FC Barcelona",
    "FC Bayern Munich",
    "Manchester United F.C.",
    "Raków Częstochowa",
    "Klub Ąśćężźłó"
]

TEAM_MOCK = [
    "Barca",
    "ManUtd",
    "Bayern",
    "Jakisfc Team",
    "ŁśćŻźąęó"
]

class ClubFactory(factory.django.DjangoModelFactory):    
    
    class Meta:
        model = 'clubs.Club'        

    name = factory.Iterator(CLUB_MOCK)

class TeamFactory(factory.Factory):

    class Meta:
        model = 'clubs.Team'

    name = factory.Iterator(TEAM_MOCK)
    club = factory.SubFactory(ClubFactory)

