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
        django_get_or_create = ("name",)

    name = factory.Iterator(SEASON_MOCK)


class LeagueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.League"

    name = "Ekstraklasa"


class LeagueHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.LeagueHistory"

    league = factory.SubFactory(LeagueFactory)
    season = factory.SubFactory(SeasonFactory)


class TeamHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "clubs.TeamHistory"

    team = factory.SubFactory(TeamFactory)
    league_history = factory.SubFactory(LeagueHistoryFactory)
