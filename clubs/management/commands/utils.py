import os
from typing import Union

from clubs.models import Club, Team
from .club_name_processing_data import excluded_parts, exceptions, phrase_to_replace, words_to_remove
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from functools import reduce
from django.db.models import Q

LEAGUES = [
    "Ekstraklasa",
    "1 Liga",
    "2 Liga",
    "3 Liga",
    "4 Liga",
    "5 Liga",
    "Klasa Okręgowa",
    "A Klasa",
    "B Klasa",
]

PATH_TO_LOG = os.path.dirname(__file__)
PATH_TO_FILE = os.path.join(PATH_TO_LOG, "result_herbs.txt")

PATH_TO_FLAGS = rf"/home/playmakerpro/Herby/renamed"


def get_club_without_img(clubs: Club, herbs: bool = False) -> Union[list, dict]:
    """Return clubs without herbs"""

    clubs_dict = {}
    herbs_list = []

    for club in clubs:
        for team in club.teams.all():
            if (
                team.league
                and team.league.highest_parent
                and team.league.highest_parent.name in LEAGUES
            ):
                if herbs:
                    herbs_list.append(
                        {
                            "name": club.name,
                            "picture": True if club.picture else None,
                            "club_id": club.id,
                            "voivodeship": club.voivodeship.name
                            if club.voivodeship
                            else None,
                            "team_name": [
                                (team, team.league.highest_parent.name)
                                for team in club.teams.all()
                            ],
                        }
                    )
                    break

                clubs_dict[club.id] = {
                    "name": club.name,
                    "picture": club.picture.url if club.picture else None,
                    "team_name": team.name,
                    "team_league": team.league.highest_parent.name,
                }
                break

    if herbs:
        return herbs_list

    return clubs_dict


def change_club_image(clubs: Club, clubs_matched: dict) -> None:

    for club in clubs:
        club_id = str(club.id)

        if clubs_matched.get(club_id) and not club.picture:

            try:
                file_name = clubs_matched[club_id]["file_name"]
                club.picture.save(
                    file_name, File(open(PATH_TO_FLAGS + file_name, "rb"))
                )

            except ObjectDoesNotExist:
                pass


def create_short_name(obj: Union[Team, Club]) -> str:
    """
    Given a Club or Team object, create a short name that is easier to read and remember
    than the original name. The short name is created by removing common phrases or words
    found in Club/Team names that are often not specific to the team itself, and by using
    shortcuts for commonly used phrases in Club/Team names. Certain phrases can be excluded
    from removal or replacement if they are necessary for team/club recognizability.
    """

    name_to_modify = obj.name
    club_name = obj.club.name if isinstance(obj, Team) else name_to_modify

    # Replace the words in the given club_name with their corresponding replacements,
    # which can be used to create shortcuts for common prefixes or phrases.
    club_name = reduce(
        lambda s, kv: s.replace(*kv), phrase_to_replace.items(), club_name
    )
    print(club_name)

    # Remove common unnecessary phrases specified in words_to_remove from club_name
    # and join the remaining words into a new Club short name.
    club_short_name = " ".join(
        [w for w in club_name.split() if w not in words_to_remove]
    )
    print(club_short_name)

    # Rearrange and modify the given Club name by moving certain excluded parts (e.g. common sport Club prefixes)
    # to the beginning of the name and removing any duplicate or unnecessary words.
    # Specifically, this code checks if any excluded part is present in the Club name and, if so,
    # moves it to the front of the name while maintaining the order of the other words.
    # It also removes any duplicates and ensures that only unique words remain in the final modified Club name.
    parts = club_short_name.split("-")
    if len(parts) > 1 and not any(exclude in club_short_name for exclude in exceptions):
        _, *rest_parts = parts[1].split()
        club_short_name = f"{parts[0]} {' '.join(rest_parts)}"

    split_modified_club_name = club_short_name.split()
    if club_short_name not in exceptions:
        for part in excluded_parts:
            if part in split_modified_club_name:
                part_index = split_modified_club_name.index(part)
                club_short_name = " ".join(
                    [
                        *split_modified_club_name[part_index:],
                        *split_modified_club_name[:part_index],
                    ]
                )
            else:
                club_short_name = " ".join(split_modified_club_name)

            split_modified_club_name = club_short_name.split()
            if len(split_modified_club_name) > 2:
                if part in split_modified_club_name:
                    split_modified_club_name.remove(part)

            unique_words = []
            for w in split_modified_club_name:
                if w not in unique_words:
                    unique_words.append(w)
            club_short_name = " ".join(unique_words)

    # Checks each word to see if it is in all-uppercase format.
    # If a word is all-uppercase and not in a list of excluded parts or exceptions,
    # the function capitalizes the word and updates the modified Club name string
    split_modified_club_name = club_short_name.split()
    for i, word in enumerate(split_modified_club_name):
        if word.isupper() and word not in excluded_parts and word not in exceptions:
            split_modified_club_name[i] = word.capitalize()
    club_short_name = " ".join(split_modified_club_name)

    # Check if all teams assigned to the given Club object play in the Futsal league.
    # If they do, modify the Club's name to indicate that it is a Futsal club by appending
    # the string "(Futsal)" to the Club name.
    if isinstance(obj, Club):
        teams = obj.teams.all()
        futsal_leagues = ["Futsal", "PLF"]
        query = Q()
        for league in futsal_leagues:
            query |= Q(
                historical__league_history__league__highest_parent__name__contains=league
            )

        if 0 < teams.count() == teams.filter(query).distinct().count():
            if "Futsal" not in club_name:
                club_short_name = club_short_name + " (Futsal)"

    # Extracts the Team number from the given Team name, if it includes a Roman numeral from I to IV.
    # This helps distinguish Teams within a Club that share a similar name.
    team_number = next(
        (part for part in name_to_modify.split() if part in ["I", "II", "III", "IV"]),
        "",
    )

    # Add a suffix to a Team name indicating that the Team is playing in a futsal league if the team's
    # Club is not defined as a futsal Club and the team is playing in a futsal league.
    if isinstance(obj, Team) and not all(
        "Futsal" in team.team_name_with_current_league
        or "PLF" in team.team_name_with_current_league
        for team in obj.club.teams.all()
        if team.team_name_with_current_league
    ):
        team_number = (
            "(Futsal)"
            if any(
                league_name in obj.team_name_with_current_league
                for league_name in ["Futsal", "PLF"]
            )
            and "Futsal" not in obj.club.name
            else team_number
        )

    short_name = club_short_name + " " + team_number if team_number else club_short_name

    return short_name
