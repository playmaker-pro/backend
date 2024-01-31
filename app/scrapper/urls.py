from typing import Callable as _Callable

from django.conf import settings as _settings

from app.http.urls import URLs

_config = _settings.ENV_CONFIG


class ScrapperURLs(URLs):
    """Urls for scrapper service"""

    _BASE_URL = _config.scrapper.scrapper_api_url
    CLUBS_URL: str = "clubs/all/"
    LEAGUES_URL: str = "leagues/all/"
    TEAM_PLAYS: str = "teams/{team_id}/plays/"
    TEAM_MATCHES: str = "teams/{team_id}/matches/"

    @property
    def clubs_list(self) -> str:
        """Subdir of clubs list url"""
        return self._compose_url(self.CLUBS_URL)

    @property
    def leagues_list(self) -> str:
        """Subdir of leagues list url"""
        return self._compose_url(self.LEAGUES_URL)

    @property
    def team_plays(self) -> _Callable:
        """Subdir of team plays url"""
        return lambda team_id: self._compose_url(self.TEAM_PLAYS).format(
            team_id=team_id
        )

    @property
    def team_matches(self) -> _Callable:
        """Subdir of team matches url"""
        return lambda team_id: self._compose_url(self.TEAM_MATCHES).format(
            team_id=team_id
        )
