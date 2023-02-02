from pm_core.services.models import PlayerBaseSchema, TeamSchema, BaseLeagueSchema

from mapper.models import Mapper
from profiles.models import PlayerProfile
from .exceptions import (
    PlayerHasNoMapperException,
    PlayerMapperEntityNotFoundException,
    ObjectNotFoundException,
)
from .base_adapter import BaseAdapter
import logging
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


class PlayerAdapterBase(BaseAdapter):
    def __init__(self, player: PlayerProfile, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.player: PlayerProfile = player

    def get_player_mapper(self) -> Mapper:
        """
        get mapper object from player
        """
        try:
            return self.player.mapper
        except ObjectDoesNotExist:
            raise PlayerHasNoMapperException(self.player.user.id)

    def get_player_data(self) -> PlayerBaseSchema:
        """
        Get player data
        """
        params = self.resolve_strategy()
        obj = self.api.get_player_data(self.player_uuid, params)

        if not obj:
            raise ObjectNotFoundException(self.player_uuid, PlayerBaseSchema)

        return obj

    @property
    def player_uuid(self) -> str:
        """
        uuid straight from LNP
        """
        mapper = self.get_player_mapper()
        params = {"database_source": "scrapper_mongodb", "related_type": "player"}
        mapper_entity = mapper.get_entity(**params)

        if not mapper_entity:
            raise PlayerMapperEntityNotFoundException(self.player.user.id, params)

        return mapper_entity.mapper_id


class PlayerDataAdapter(PlayerAdapterBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data: PlayerBaseSchema = self.get_player_data()

    def get_current_team(self) -> TeamSchema:
        """
        Get more information about player's team
        """
        params = self.resolve_strategy()
        team_id = self.data.team_id
        obj = self.api.get_team_data(team_id, params)

        if not obj:
            raise ObjectNotFoundException(team_id, PlayerBaseSchema)

        return obj

    def get_current_league(self) -> BaseLeagueSchema:
        """
        Get current player's league
        """
        current_team = self.get_current_team()
        return current_team.league

    def get_current_voivodeship(self):
        """
        Get current voivodeship
        """
        zpn = self.data.club.voivodeship

        if not zpn:
            params = self.resolve_strategy()
            club_data = self.api.get_club_data(self.data.club.id, params)
            zpn = club_data.voivodeship

        return zpn

    @property
    def player_data_exists(self) -> bool:
        """
        Check if player data exists
        """
        return bool(self.data)
