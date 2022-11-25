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
