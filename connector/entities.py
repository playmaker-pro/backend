from typing import Any, List, Optional

from pydantic import BaseModel

#
#   status for 25.11.2022
#


class Model(BaseModel):
    obj_id: Optional[str]  # _id from mongo

    def __init__(self, **data: Any):
        self.update_forward_refs()
        super().__init__(**data)

    def __getitem__(self, item):
        return getattr(self, item)


class VoivodeshipEntity(Model):
    id: str
    name: str


class BaseClubEntity(Model):
    id: str
    name: str


class ClubEntity(BaseClubEntity):
    teams: List["TeamEntity"]
    voivodeship: "VoivodeshipEntity" = None
    abbreviation: str = None
    address: str = None


class BaseTeamEntity(Model):
    id: str
    name: str
    abbreviation: Optional[str]
    logo: Optional[str]


class TeamEntity(BaseTeamEntity):
    season: str
    league: Optional["BaseLeagueEntity"]


class BaseLeagueEntity(Model):
    id: str
    name: str


class LeagueEntity(BaseLeagueEntity):
    gender: str
    plays: List["PlayEntity"]
    pm_id: int
    season: str
    seniority: Optional[str]


class PlayEntity(Model):
    id: str
    name: str
    voivodeship: Optional["VoivodeshipEntity"]


class TeamHistoryEntity(Model):
    club: BaseClubEntity
    teams: List["TeamEntity"]
