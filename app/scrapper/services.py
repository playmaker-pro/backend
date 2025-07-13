import typing as _typing
from uuid import UUID as _UUID

import requests as _requests
from pydantic import BaseModel as _BaseModel

from app.http.http_service import HttpService as _HttpService
from app.scrapper import schemas as _schemas
from app.scrapper.urls import ScrapperURLs as _URLs

from . import config as _config


class ScrapperHttpService(_HttpService):
    # TODO: THIS SHOULD USE HTTP SERIVCE FROM PM-CORE BUT WE DONT HAVE VERSIONING YET
    _urls = _URLs()

    def _set_session(self) -> _requests.Session:
        """
        Create and return a new requests.Session object.
        Set authentication headers.

        :return: A new requests.Session object.
        """
        session = _requests.Session()
        session.headers.update(_config.scrapper.auth.get_authentication_headers())
        return session

    def _parse_list_response(
        self, model: _typing.Type[_BaseModel], response: _requests.Response
    ) -> _BaseModel:
        """
        Parse the response from a GET request into a Pydantic LIST model.

        :param model: The Pydantic model to parse the response into.
        :param response: The response from the GET request.
        :return: The parsed Pydantic model.
        """
        if not response.json():
            return model.parse_obj([])
        return model.parse_obj(response.json())

    def get_leagues(self) -> _schemas.LeagueListSchema:
        """
        Make a GET request to the leagues list URL and parse the response into a LeagueListSchema.

        :return: A LeagueListSchema parsed from the response.
        """
        response = self._get(self.urls.leagues_list)
        return self._parse_list_response(_schemas.LeagueListSchema, response)  # type: ignore

    def get_clubs(self) -> _schemas.ClubListSchema:
        """
        Make a GET request to the clubs list URL and parse the response into a ClubListSchema.

        :return: A ClubListSchema parsed from the response.
        """
        response = self._get(self.urls.clubs_list)
        return self._parse_list_response(_schemas.ClubListSchema, response)  # type: ignore

    def get_team_plays(self, team_id: _UUID) -> _schemas.LeaguePlayListSchema:
        """
        Make a GET request to the team plays URL and parse the response into a LeaguePlayListSchema.

        :param team_id: The ID of the team to get the plays for.
        :return: A LeaguePlayListSchema parsed from the response.
        """
        response = self._get(self.urls.team_plays(team_id))
        return self._parse_list_response(_schemas.LeaguePlayListSchema, response)  # type: ignore

    def get_team_matches(self, team_id: _UUID) -> _schemas.MatchListSchema:
        """
        Make a GET request to the team matches URL and parse the response into a MatchListSchema.

        :param team_id: The ID of the team to get the matches for.
        :return: A MatchListSchema parsed from the response.
        """
        response = self._get(self.urls.team_matches(team_id))
        return self._parse_list_response(_schemas.MatchListSchema, response)  # type: ignore
