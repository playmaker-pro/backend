from unidecode import unidecode

VOIVODESHIP_MAPPING = {
    "Silesia": "Śląskie",
    "Mazovia": "Mazowieckie",
    "Lesser Poland": "Małopolskie",
    "Podlasie": "Podlaskie",
    "Warmia-Masuria": "Warmińsko-mazurskie",
    "Lower Silesia": "Dolnośląskie",
    "Łódź Voivodeship": "Łódzkie",
    "Lubusz": "Lubuskie",
    "Opole Voivodeship": "Opolskie",
    "Pomerania": "Pomorskie",
    "Greater Poland": "Wielkopolskie",
    "West Pomerania": "Zachodniopomorskie",
    "Lublin": "Lubelskie",
    "Świętokrzyskie": "Świętokrzyskie",
    "Subcarpathia": "Podkarpackie",
    "Kujawsko-Pomorskie": "Kujawsko-Pomorskie",
}

CUSTOM_CITY_MAPPING = {
    "Warsaw": "Warszawa",
}


def match_voivodeship(search_query: str) -> list:
    """
    Matches the query to a list of voivodeships.

    The method compares the lowercase, unidecoded search_query with the lowercase, unidecoded voivodeship names
    stored in the `VOIVODESHIP_MAPPING` dictionary. This allows the search_query to be immune to Polish language
    letters and case sensitivity. If the query partially matches a voivodeship name, it is added to the
    list of matched queries.
    """
    matched_queries = []

    for key, value in VOIVODESHIP_MAPPING.items():
        if search_query.lower() in unidecode(value.lower()):
            matched_queries.append(key)
    return matched_queries


def handle_custom_city_mapping(city_name: str) -> str:
    """
    Handles the custom city mappings where the name_ascii field in django-cities-light does not match the Polish city names.
    If a match is found, the decoded_query is updated with the corresponding key from the CUSTOM_CITY_MAPPING.
    """
    for key, value in CUSTOM_CITY_MAPPING.items():
        if city_name.lower() in unidecode(value.lower()):
            city_name = key
    return city_name
