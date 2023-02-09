from clubs.models import TeamHistory
from connector.scripts.base import BaseCommand
from mapper.models import MapperEntity

CLUB_URL = "https://www.laczynaspilka.pl/rozgrywki/klub/{club_id}"
TEAM_URL = "https://www.laczynaspilka.pl/rozgrywki/druzyna/{team_id}"

LEAGUE_URL = "https://www.laczynaspilka.pl/rozgrywki?season=season_name&leagueGroup=league_group_id&leagueId=league_id&enumType=enum_type&isAdvanceMode=true&gender=gender_name"

MALE_LEAGUE_IDs = {
    "Ekstraklasa": "20505afb-3cb6-4e59-9bb1-ed56e8201bb8",
    "Piersza Liga": "59f21eb0-6b05-4af0-94c4-e665852cdf85",
    "Druga Liga": "cfcab412-50f1-441b-892d-ce8d8d9a13cc",
}

FEMALE_LEAGUE_IDs = {
    "Ekstraliga": "642d5615-721e-4586-b475-f83cb61afc30",
    "Piersza Liga": "b0a6782f-5075-4a32-8b9f-c02b257ecdb8",
    "Druga Liga": "de0b9551-ad34-48e3-840c-34a31fed1376",
}

ZPNs = {
    "Dolnośląskie": "eaa01464-22b2-422a-835f-7835bb50990a",
    "Kujawsko-pomorskie": "f8bd567f-72de-4328-8326-187ad4da031e",
    "Łódzkie": "15b4a3b3-b787-440e-9282-ee5549a97d76",
    "Lubelskie": "76fb0431-52a4-4106-9a5c-cf5af80c11a9",
    "Lubuskie": "48722694-be4b-44d6-b5af-320308f84f50",
    "Małopolskie": "e0ca38b1-1dab-47c1-a077-f9d41970e0c5",
    "Mazowieckie": "e652d9c8-57f8-442b-8573-7f450a90c0d2",
    "Opolskie": "39757eb2-3c41-47fa-b80b-8deea71e5a3e",
    "Podkarpackie": "cd81a30b-c8a3-44e0-abd6-8b5772d3137c",
    "Podlaskie": "aa1901d7-18b6-453e-92c5-17304cbdd8c4",
    "Pomorskie": "9752d270-dfa5-4035-a438-9641a0bfdb0f",
    "Śląskie": "52600a9d-dc9e-4002-9798-52d1ad8c0181",
    "Świętokrzyskie": "8e6b2e2a-2c6f-46a5-8ab6-642c3a4661d0",
    "Warmińsko-mazurskie": "e838d72f-747e-4904-942b-8dafb5bb41b5",
    "Wielkopolskie": "f3211030-22aa-4549-ab47-c99376281ac8",
    "Zachodniopomorskie": "a2d6b609-b11a-46c8-bced-fe2ebe51e9db",
}

MALE_LEAGUES = (
    {
        "id": "48f9a6d6-d38d-46cc-982b-084fede4ba0a",
        "name": "Ekstraklasa",
        "dropdowns": "None",
        "leagues": [
            {"leagueId": "20505afb-3cb6-4e59-9bb1-ed56e8201bb8", "name": "Ekstraklasa"}
        ],
    },
    {
        "id": "b4194f67-6702-4559-9d04-33240e0f8daf",
        "name": "Pierwsza liga",
        "dropdowns": "None",
        "leagues": [
            {
                "leagueId": "59f21eb0-6b05-4af0-94c4-e665852cdf85",
                "name": "Pierwsza liga",
            }
        ],
    },
    {
        "id": "df590e54-b86b-4163-afff-d7463585ea49",
        "name": "Druga liga",
        "dropdowns": "None",
        "leagues": [
            {"leagueId": "cfcab412-50f1-441b-892d-ce8d8d9a13cc", "name": "Druga liga"}
        ],
    },
    {
        "id": "6fbef42c-2da2-46fb-adbc-3d9e4bf28f9d",
        "name": "Trzecia liga",
        "dropdowns": "Play",
        "leagues": [
            {"leagueId": "5aeaceaa-680d-4164-b0b6-f5f2be4add94", "name": "Trzecia liga"}
        ],
    },
    {
        "id": "63e0b91e-f2cc-4149-813b-ea9a77919385",
        "name": "Niższe ligi",
        "subTitle": "Klasa rozgrywkowa",
        "dropdowns": "ZpnAndLeagueAndPlay",
        "leagues": [
            {
                "leagueId": "1bbf167f-ec17-4d1f-91f2-6ef0e4b8fc18",
                "name": "Czwarta liga",
            },
            {"leagueId": "79a6cf82-0e5d-46fe-ae5f-924b4f0c6ab3", "name": "Piąta liga"},
            {
                "leagueId": "50917394-d0c3-4299-b00f-7d55f3ca65f5",
                "name": "Klasa okręgowa",
            },
            {"leagueId": "733f5b9c-9ade-4011-84c4-b08d35d170b3", "name": "Klasa A"},
            {"leagueId": "8cf29fa7-fef5-45f9-9c6c-6375dbe243af", "name": "Klasa B"},
            {"leagueId": "fc4411b7-ba96-4c7f-b2b5-f1c997ee36a4", "name": "Klasa C"},
        ],
    },
    {
        "id": "5f741727-fa5b-47f3-bc32-397e9ad7d9a5",
        "name": "Centralna Liga Juniorów",
        "subTitle": "Grupa wiekowa",
        "dropdowns": "LeagueAndPlay",
        "leagues": [
            {"leagueId": "b0b6ac58-0d13-4a01-94e9-4cd1acf205bf", "name": "CLJ U-19"},
            {"leagueId": "815c0477-eefc-46d7-abda-0d693788e118", "name": "CLJ U-17"},
            {"leagueId": "21d1d997-2953-48fa-969c-1f131652c366", "name": "CLJ U-15"},
            {
                "leagueId": "ab883a84-3f05-4201-b23b-8b40c6f9e505",
                "name": "Baraże CLJ U-15 runda jesienna",
            },
        ],
    },
    {
        "id": "e91d244a-2694-4373-8263-cee24a82eaa8",
        "name": "Juniorzy",
        "subTitle": "Grupa wiekowa",
        "dropdowns": "ZpnAndLeagueAndPlay",
        "leagues": [
            {"leagueId": "ce0917de-adaa-45c7-9ec9-e46f698d1869", "name": "A1"},
            {"leagueId": "24296506-394a-433b-b744-981713d8bd8e", "name": "A2"},
            {"leagueId": "e9a56030-8035-407e-9689-57d1381a40eb", "name": "B1"},
            {"leagueId": "b6e2eca5-ee01-4c45-8a27-02be750f6d1b", "name": "B2"},
            {"leagueId": "31db1b98-2077-4668-9d05-ae37760a574f", "name": "C1"},
            {"leagueId": "0a7a1f55-9a79-4c7d-bb3b-4ea605c0123b", "name": "C2"},
        ],
    },
    {
        "id": "629faf42-0f1a-427e-832d-f477a1fdfb92",
        "name": "Futsal",
        "subTitle": "Klasa rozgrywkowa",
        "dropdowns": "LeagueAndPlay",
        "leagues": [
            {
                "leagueId": "6c7a60d7-4763-4344-9e0d-d0058becb99f",
                "name": "Futsal Ekstraklasa",
            },
            {"leagueId": "be62b6bb-aca7-4620-a9ba-e0b609dfdd4a", "name": "I Liga PLF"},
            {"leagueId": "44b113f8-9db4-4d1d-b837-461fff482f7f", "name": "II Liga PLF"},
            {
                "leagueId": "cdeaa11b-55f6-4f2b-97aa-504071658bb5",
                "name": "III Liga PLF",
            },
        ],
    },
)

FEMALE_LEAGUES = (
    {
        "id": "723b1176-c9c3-4ce1-af0b-a5c3e0dda946",
        "name": "Ekstraliga",
        "dropdowns": "None",
        "leagues": [
            {
                "leagueId": "642d5615-721e-4586-b475-f83cb61afc30",
                "name": "Ekstraliga kobiet",
            }
        ],
    },
    {
        "id": "e868ba6f-305e-4a12-8663-ad57e096fd56",
        "name": "Pierwsza liga",
        "dropdowns": "Play",
        "leagues": [
            {
                "leagueId": "b0a6782f-5075-4a32-8b9f-c02b257ecdb8",
                "name": "Pierwsza liga kobiet",
            }
        ],
    },
    {
        "id": "87fe559f-bee0-408f-b9d6-4f165b0d4148",
        "name": "Druga liga",
        "dropdowns": "Play",
        "leagues": [
            {
                "leagueId": "de0b9551-ad34-48e3-840c-34a31fed1376",
                "name": "Druga liga kobiet",
            }
        ],
    },
    {
        "id": "6fbef42c-2da2-46fb-adbc-3d9e4bf28f9d",
        "name": "Trzecia liga",
        "dropdowns": "Play",
        "leagues": [
            {
                "leagueId": "bfe5cd96-101a-4133-a751-1bd3c428d50c",
                "name": "Trzecia liga kobiet",
            }
        ],
    },
    {
        "id": "63e0b91e-f2cc-4149-813b-ea9a77919385",
        "name": "Niższe ligi",
        "subTitle": "Klasa rozgrywkowa",
        "dropdowns": "ZpnAndLeagueAndPlay",
        "leagues": [
            {
                "leagueId": "b1967e39-4ca6-4db7-b10d-083570c07428",
                "name": "Czwarta liga kobiet",
            }
        ],
    },
    {
        "id": "5f741727-fa5b-47f3-bc32-397e9ad7d9a5",
        "name": "Centralna Liga Juniorów",
        "subTitle": "Grupa wiekowa",
        "dropdowns": "LeagueAndPlay",
        "leagues": [
            {
                "leagueId": "c4b1f03a-2b98-4161-b266-51d162f44697",
                "name": "Centralna Liga Juniorek U-17",
            },
            {
                "leagueId": "a01867b4-92c7-4c85-be99-e6e5f7cebae8",
                "name": "Centralna Liga Juniorek U-15",
            },
        ],
    },
    {
        "id": "629faf42-0f1a-427e-832d-f477a1fdfb92",
        "name": "Futsal",
        "subTitle": "Klasa rozgrywkowa",
        "dropdowns": "LeagueAndPlay",
        "leagues": [
            {
                "leagueId": "505bdccf-fe17-446a-9fda-c81341ed2929",
                "name": "Ekstraliga PLF",
            },
            {
                "leagueId": "7bd775e5-5f49-47fa-a61c-4972dfcd2257",
                "name": "I Liga PLF kobiet",
            },
            {
                "leagueId": "f66f206d-9edb-4e1f-a08a-d4415682b2c9",
                "name": "II Liga PLF kobiet",
            },
        ],
    },
)


class Command(BaseCommand):
    """
    Create mocked LNP urls for mappers (club, team, league)
    Based on enums above
    """
    def handle(self) -> None:
        self.map_urls()
        self.map_league_urls(MALE_LEAGUES, "Male")
        self.map_league_urls(FEMALE_LEAGUES, "Female")

    def map_urls(self) -> None:
        """
        Create LNP urls for clubs and teams
        """
        entities = MapperEntity.objects.all()

        for entity in entities:
            entity_type = entity.related_type

            if entity_type == "club":
                url = CLUB_URL.format(club_id=entity.mapper_id)

            elif entity_type == "team history":
                url = TEAM_URL.format(team_id=entity.mapper_id)

            else:
                continue

            entity.url = url
            entity.save()

    def map_league_urls(self, leagues, gender):
        """
        create LNP urls for leagues
        it has to be separated function due leauge url complexity
        """
        for div in leagues:
            required_params = div["dropdowns"]
            for league in div["leagues"]:
                entities = MapperEntity.objects.filter(mapper_id=league["leagueId"])

                if not entities:
                    continue

                for entity in entities:
                    play_entity = entity.target.get_entity(related_type="play")
                    base_params = {
                        "gender_name": gender,
                        "enum_type": required_params,
                        "league_group_id": div["id"],
                        "season_name": entity.target.leaguehistory.season.name.replace(
                            "/", "%2F"
                        ),
                    }
                    params = {}

                    if gender == "Male":
                        try:
                            base_params["league_id"] = MALE_LEAGUE_IDs[div["name"]]
                        except KeyError:
                            base_params[
                                "league_id"
                            ] = "5aeaceaa-680d-4164-b0b6-f5f2be4add94"
                    else:
                        try:
                            base_params["league_id"] = FEMALE_LEAGUE_IDs[div["name"]]
                        except KeyError:
                            base_params[
                                "league_id"
                            ] = "bfe5cd96-101a-4133-a751-1bd3c428d50c"

                    if required_params == "LeagueAndPlay":
                        params["subLeague"] = league["leagueId"]
                        params["group"] = play_entity.mapper_id

                    elif required_params == "ZpnAndLeagueAndPlay":
                        params["subLeague"] = league["leagueId"]
                        params["group"] = play_entity.mapper_id
                        teams_in_lh = TeamHistory.objects.filter(
                            league_history=entity.target.leaguehistory,
                            team__club__voivodeship_obj__isnull=False,
                        )
                        if not teams_in_lh:
                            continue
                        zpn = teams_in_lh[0].team.club.voivodeship_obj
                        params["voivodeship"] = ZPNs[zpn.name]

                    elif required_params == "Play":
                        params["group"] = play_entity.mapper_id

                    url = LEAGUE_URL[:]

                    for key, value in base_params.items():
                        url = url.replace(key, value)

                    for key, value in params.items():
                        url += f"&{key}={value}"

                    entity.url = url
                    entity.save()

                    play_entity.url = url
                    play_entity.save()
