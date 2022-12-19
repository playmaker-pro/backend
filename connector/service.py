import json
from typing import List, Union
import requests
from connector.entities import (
    TeamHistoryEntity,
    PlayEntity,
    ClubEntity,
    BaseTeamEntity,
    LeagueEntity,
)
from .urls import URL

# paths
TEAM_HISTORY_FILEPATH = "connector/scripts/teamhistories.json"
LEAGUES_FILEPATH = "connector/scripts/leagues.json"
CLUBS_FILEPATH = "connector/scripts/clubs.json"
TABLES_FILEPATH = "connector/scripts/tables.json"


class HttpService:
    def __init__(self):
        self.session: requests.Session = requests.session()
        self.urls: URL = URL()

    def get(self, url) -> Union[requests.Response, None]:

        response = self.session.get(url)
        response.raise_for_status()

        return response

    def get_team_histories(self) -> List[TeamHistoryEntity]:
        response = self.get(self.urls.TEAM_HISTORIES)
        if not response.json():
            return []
        return [TeamHistoryEntity(**th) for th in response.json()]

    def get_team_plays(self, team_id: str) -> List[PlayEntity]:
        url = self.urls.TEAM_PLAYS.format(team_id=team_id)
        response = self.get(url)
        if not response.json():
            return []
        return [PlayEntity(**play) for play in response.json()]

    def get_club_details(self, club_id: str) -> Union[ClubEntity, None]:
        url = self.urls.CLUB_DETAILS.format(club_id=club_id)
        response = self.get(url)
        if not response.json():
            return None
        return ClubEntity(**response.json())

    def get_play_teams(self, play_id: str) -> List[BaseTeamEntity]:
        url = self.urls.PLAY_TEAMS.format(play_id=play_id)
        response = self.get(url)
        if not response.json():
            return []
        return [BaseTeamEntity(**team) for team in response.json()]

    def get_leagues(self) -> List[LeagueEntity]:
        response = self.get(self.urls.LEAUGES)
        if not response.json():
            return []
        return [LeagueEntity(**league) for league in response.json()]


class JsonService:

    def get_team_histories(self) -> List[TeamHistoryEntity]:
        return [TeamHistoryEntity(**th) for th in json.load(open(TEAM_HISTORY_FILEPATH))]

    def get_team_plays(self, team_id: str) -> List[PlayEntity]:
        tables = json.load(open(TABLES_FILEPATH))

        plays = []
        for table in tables:
            result = list(filter(lambda row: row["team"]["id"] == team_id, table["rows"]))
            if result:
                plays.append(table["play"])

        return [PlayEntity(**play) for play in plays]

    def get_club_details(self, club_id: str) -> Union[ClubEntity, None]:
        clubs = json.load(open(CLUBS_FILEPATH))
        result = list(filter(lambda club: club["id"] == club_id, clubs))
        if result:
            return ClubEntity(**result[0])

    def get_play_teams(self, play_id: str) -> List[BaseTeamEntity]:
        tables = json.load(open(TABLES_FILEPATH))
        result = list(filter(lambda table: table["play"]["id"] == play_id, tables))
        if result:
            return [BaseTeamEntity(**row["team"]) for row in result[0]["rows"]]
        else:
            return []

    def get_leagues(self) -> List[LeagueEntity]:
        return [LeagueEntity(**league) for league in json.load(open(LEAGUES_FILEPATH))]
