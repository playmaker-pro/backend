import factory

TEAM_MOCK = ["FC Barca", "ManUtd", "Bayern", "Jakisfc Team", "ŁśćŻźąęó"]

CLUB_MOCK = [
    "FC Barcelona",
    "FC Bayern Munich",
    "Manchester United F.C.",
    "Raków Częstochowa",
    "Klub Ąśćężźłó",
]

SEASON_MOCK = ["2022/2023", "2021/2022", "2020/2021", "2019/2020"]


class ClubFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.Club"

    name = factory.Iterator(CLUB_MOCK)


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.Team"

    name = factory.Iterator(TEAM_MOCK)
    club = factory.SubFactory(ClubFactory)


class SeasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.Season"

    name = factory.Iterator(SEASON_MOCK)
