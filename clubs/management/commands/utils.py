import os
import re
from typing import List, Union

from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

from clubs.management.commands.club_name_processing_data import (
    EXCEPTIONS,
    EXCLUDED_PARTS,
    PHRASE_TO_REPLACE,
    WORDS_TO_REMOVE,
)
from clubs.models import Club, Team

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
            if team.league and team.league and team.league.name in LEAGUES:
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
                                (team, team.league.name) for team in club.teams.all()
                            ],
                        }
                    )
                    break

                clubs_dict[club.id] = {
                    "name": club.name,
                    "picture": club.picture.url if club.picture else None,
                    "team_name": team.name,
                    "team_league": team.league.name,
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


def rearrange_club_name_parts(
    club_name_list: List[str], parts_to_exclude: List[str]
) -> List[str]:
    """
    Rearrange the club name list based on the specified excluded parts.
    If an excluded part exists in the club name list, it moves the part
    to the beginning of the list.
    """
    for part in parts_to_exclude:
        if part in club_name_list:
            part_index = club_name_list.index(part)
            return [*club_name_list[part_index:], *club_name_list[:part_index]]
    return club_name_list


def remove_club_name_parts(
    club_name_list: List[str], parts_to_exclude: List[str], persistent_names: List[str]
) -> List[str]:
    """
    Remove specified parts from the Club name list unless the entire name
    is part of the persistent names or has less than three words.
    """
    # Continue only if the club name isn't in persistent names and has more than 2 words
    if " ".join(club_name_list) not in persistent_names and len(club_name_list) > 2:
        filtered_list = [
            word for word in club_name_list if word not in parts_to_exclude
        ]

        # If filtering results in a list with zero or one non-excluded word,
        # prioritize keeping the first excluded word and the last non-excluded word.
        if len(filtered_list) <= 1:
            # Find the first excluded word
            first_excluded = next(
                (word for word in club_name_list if word in parts_to_exclude), None
            )

            # Find the last non-excluded word, or just use the first excluded word if all are excluded.  # noqa: E501
            last_non_excluded = next(
                (
                    word
                    for word in reversed(club_name_list)
                    if word not in parts_to_exclude
                ),
                first_excluded,
            )

            # Combine the words, prioritizing the excluded word to come first.
            return (
                [first_excluded, last_non_excluded]
                if first_excluded != last_non_excluded
                else [first_excluded]
            )

        return filtered_list

    return club_name_list


def remove_club_name_duplicates(club_name_list: List[str]) -> List[str]:
    """
    Remove duplicate words from the club name list.
    """

    unique_words: List[str] = []
    for word in club_name_list:
        if word not in unique_words:
            unique_words.append(word)
    return unique_words


def handle_club_name_hyphen(club_name: str, persistent_names: List[str]) -> str:
    """
    Remove the first word after a hyphen if club name contains one and isn't an exception.  # noqa: E501
    """
    parts: List[str] = club_name.split("-")
    if len(parts) > 1 and not any(
        exception in club_name for exception in persistent_names
    ):
        _, *rest_parts = parts[1].split()
        club_name = f"{parts[0]} {' '.join(rest_parts)}"
    return club_name


def rearrange_and_cleanse_club_name(
    club_name: str, parts_to_exclude: List[str], persistent_names: List[str]
) -> str:
    """
    Rearrange the parts of the given club name based on the specified excluded parts,
    remove unwanted parts, and remove any duplicates. The order of operations is:
    1. Rearrange
    2. Remove unwanted parts
    3. Remove duplicates
    """
    club_name_list: List[str] = club_name.split()

    club_name_list = rearrange_club_name_parts(club_name_list, parts_to_exclude)
    club_name_list = remove_club_name_parts(
        club_name_list, parts_to_exclude, persistent_names
    )
    club_name_list = remove_club_name_duplicates(club_name_list)

    return " ".join(club_name_list)


def modify_club_name(
    club_name: str, parts_to_exclude: List[str], persistent_names: List[str]
) -> str:
    """
    Modify the club name to enhance its readability and brevity.

    The function performs the following operations:
    1. Handles any hyphens present in the name to ensure they don't disrupt the readability.  # noqa: E501
    2. Rearranges the name's components to prioritize important parts and removes any duplicates.  # noqa: E501
    """
    club_name = handle_club_name_hyphen(club_name, persistent_names)
    club_name = rearrange_and_cleanse_club_name(
        club_name, parts_to_exclude, persistent_names
    )
    return club_name


def append_futsal_suffix_and_team_number(
    obj: Union[Team, Club], club_short_name: str
) -> str:
    """
    Checks whether a Club or Team is playing in a futsal league,
    and adds a suffix to the name to indicate that it is
    playing in such a league if necessary. Also extracts the Team number
    from the given Team name, if it includes a Roman numeral from I to IV,
    to help distinguish Teams within a Club that share a similar name.
    """

    name_to_shorten: str = obj.name
    club_name: str = obj.club.name if isinstance(obj, Team) else name_to_shorten

    # Extracts the Team number from the given Team name, if it includes a Roman numeral from I to IV.  # noqa: E501
    team_number: str = next(
        (part for part in name_to_shorten.split() if part in ["I", "II", "III", "IV"]),
        "",
    )

    futsal = ""  # Initialize futsal suffix with an empty string
    futsal_leagues = ["Futsal", "PLF"]

    # Check if all teams assigned to the given Club object play in the Futsal league. If so, add a suffix to define  # noqa: E501
    # Club as a futsal Club
    if isinstance(obj, Club):
        teams = obj.teams.all()
        if teams and all(
            any(
                league in team.team_name_with_current_league
                for league in futsal_leagues
            )
            for team in teams
            if team.team_name_with_current_league
        ):
            if "Futsal" not in club_name:
                club_short_name += " (Futsal)"

    # Add a suffix to a Team name indicating that the Team is playing in a futsal league if the team's  # noqa: E501
    # Club is not defined as a futsal Club and the team is playing in a futsal league.
    elif isinstance(obj, Team) and not all(
        any(league in team.team_name_with_current_league for league in futsal_leagues)
        for team in obj.club.teams.all()
        if team.team_name_with_current_league
    ):
        futsal = (
            "(Futsal)"
            if any(
                league in obj.team_name_with_current_league for league in futsal_leagues
            )
            and "Futsal" not in club_short_name
            else ""
        )

    short_name = f"{club_short_name}{(' ' + team_number) if team_number else ''}{(' ' + futsal) if futsal else ''}"  # noqa: E501

    return short_name


def adjust_word_capitalization_in_club_name(
    club_name: str, parts_to_exclude: List[str], persistent_names: List[str]
) -> str:
    """
    Checks each word of given Club name to see if it is in all-uppercase format.
    If a word is all-uppercase and not in a list of excluded parts or exceptions,
    the function capitalizes the word and updates the modified Club name string
    """
    split_modified_club_name: List[str] = club_name.split()
    for i, word in enumerate(split_modified_club_name):
        if (
            word.isupper()
            and word not in parts_to_exclude
            and word not in persistent_names
        ):
            split_modified_club_name[i] = word.capitalize()
    club_short_name = " ".join(split_modified_club_name)
    return club_short_name


def generate_club_or_team_short_name(obj: Union[Team, Club]) -> str:
    """
    Given a Club or Team object, create a short name that is easier to display and read
    than the original name. The short name is created by removing common phrases
    or words found in Club/Team names that are often not specific to the Club/Team
    itself, and by using shortcuts for commonly used phrases in Club/Team names.
    Certain phrases can be excluded from removal or replacement if they are
    necessary for Club/Team recognizability.
    """

    name_to_shorten: str = obj.name
    club_name: str = (
        obj.club.name if (isinstance(obj, Team) and obj.club) else name_to_shorten
    )

    # Use regular expression to replace complete words with their corresponding replacements  # noqa: E501
    for key, value in PHRASE_TO_REPLACE.items():
        pattern = (
            r"\b" + re.escape(key) + r"\b"
        )  # Using re.escape to make sure special characters in key are treated as literals  # noqa: E501
        if re.search(pattern, club_name):
            club_name = re.sub(pattern, value, club_name)
            if club_name in EXCEPTIONS:
                break  # Exit loop if the result is in the exceptions list

    # If club_name is in exceptions, skip removing words
    if club_name not in EXCEPTIONS:
        # Remove common unnecessary phrases specified in words_to_remove from club_name
        club_name = " ".join([w for w in club_name.split() if w not in WORDS_TO_REMOVE])

    # Modify club name by rearranging excluded parts and removing duplicates
    club_short_name = modify_club_name(club_name, EXCLUDED_PARTS, EXCEPTIONS)

    # If club_short_name is not in exceptions, remove years (four-digit numbers) from the club_name  # noqa: E501
    if club_short_name not in EXCEPTIONS and len(club_short_name.split()) > 2:
        club_short_name = re.sub(r"\b\d{4}\b", "", club_short_name)

    # Capitalizes all uppercase words in club_short_name that are not in excluded_parts or exceptions  # noqa: E501
    club_short_name = adjust_word_capitalization_in_club_name(
        club_short_name, EXCLUDED_PARTS, EXCEPTIONS
    )

    # Adds a futsal suffix and extracts team number (if applicable) for the given object's name  # noqa: E501
    short_name = append_futsal_suffix_and_team_number(obj, club_short_name)

    return short_name
