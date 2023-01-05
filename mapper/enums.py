from clubs.models import JuniorAgeGroup

SENIOR_MALE_LEAGUES = {
    "Ekstraklasa": "Ekstraklasa",
    "Pierwsza liga": "1 Liga",
    "Druga liga": "2 liga",
    "Trzecia liga": "3 Liga",
    "Czwarta liga": "4 Liga",
    "Piąta liga": "5 Liga",
    "Klasa okręgowa": "Klasa Okręgowa",
    "Klasa A": "A Klasa",
    "Klasa B": "B Klasa",
    "Klasa C": "C Klasa",
}

FUTSAL_MALE_LEAGUES = {
    "Futsal Ekstraklasa": "Futsal Ekstraklasa",
    "I Liga PLF": "I Liga PLF",
    "II Liga PLF": "II Liga PLF",
    "III Liga PLF": "III Liga PLF",
}

FUTSAL_FEMALE_LEAGUES = {
    "Ekstraliga PLF": "Ekstraliga PLF K",
    "I Liga PLF kobiet": "I Liga PLF K",
    "II Liga PLF kobiet": "II Liga PLF K",
}

JUNIOR_MALE_LEAGUES = {
    "A1": "Junior A1",
    "A2": "Junior A2",
    "B1": "Junior Młodszy B1",
    "B2": "Junior Młodszy B2",
    "C1": "Trampkarz C1",
    "C2": "Trampkarz C2",
    # "D1": "Młodzik D1 U-13", # We don't need them yet
    # "D2": "Młodzik D2 U-12",
    # "E1": "Orlik E1 U-11",
    # "E2": "Orlik E2 U-10",
    # "F1": "Żak F1 U-9",
    # "F2": "Żak F2 U-8",
    # "G1": "Skrzat G1 U-7",
    # "G2": "Skrzat G2 U-6",
}

SENIOR_FEMALE_LEAGUES = {
    "Ekstraliga kobiet": "Ekstraliga K",
    "Pierwsza liga kobiet": "1 Liga K",
    "Druga liga kobiet": "2 Liga K",
    "Trzecia liga kobiet": "3 Liga K",
    "Czwarta liga kobiet": "4 Liga K",
}

JUNIOR_LNP_LEAGUES = [
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
    "D1",
    "D2",
    "E1",
    "E2",
    "F1",
    "F2",
    "G1",
    "G2",
    "CLJ U-19",
    "CLJ U-18",
    "CLJ U-17",
    "CLJ U-15",
]

CLJ_LEAGUES = {
    "CLJ U-19": "Clj U-19",
    "Liga Makroregionalna U-19": "Liga Makroregionalna U-19",
    "CLJ U-18": "Clj U-18",
    "CLJ U-17": "Clj U-17",
    "CLJ U-15": "Clj U-15",
    "Centralna Liga Juniorek U-17": "Clj U-17 K",
    "Centralna Liga Juniorek U-15": "Clj U-15 K",
}

LEAGUE_HIGHEST_PARENT_NAME_MAPPER = {
    **SENIOR_MALE_LEAGUES,
    **FUTSAL_MALE_LEAGUES,
    **JUNIOR_MALE_LEAGUES,
    **SENIOR_FEMALE_LEAGUES,
    **CLJ_LEAGUES,
    **FUTSAL_FEMALE_LEAGUES
}

U19 = JuniorAgeGroup.objects.get(name="u19")
U18 = JuniorAgeGroup.objects.get(name="u18")
U17 = JuniorAgeGroup.objects.get(name="u17")
U16 = JuniorAgeGroup.objects.get(name="u16")
U15 = JuniorAgeGroup.objects.get(name="u15")
U14 = JuniorAgeGroup.objects.get(name="u14")


JUNIOR_AGE_GROUPS = {
    "A1": U19,
    "A2": U18,
    "B1": U17,
    "B2": U16,
    "C1": U15,
    "C2": U14,
    "CLJ U-19": U19,
    "Liga Makroregionalna U-19": U19,
    "CLJ U-18": U18,
    "CLJ U-17": U17,
    "CLJ U-15": U15,
    "Centralna Liga Juniorek U-17": U17,
    "Centralna Liga Juniorek U-15": U15,
}

PARENT_UUID_REQUIRED = ["Ekstraklasa", "Ekstraliga K", "1 Liga", "2 liga"]

RE_ROMAN = r"([IΙ]X|[IΙ]V|V?[IΙ]{0,3})?"
