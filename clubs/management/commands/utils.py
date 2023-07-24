import os
from typing import Union

from clubs.models import Club
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

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
