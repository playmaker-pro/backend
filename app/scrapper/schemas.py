import re as _re
import typing as _typing
from abc import ABCMeta
from enum import Enum as _Enum
from uuid import UUID as _UUID

from pydantic import BaseModel as _BaseModel
from pydantic.fields import Field as _Field

from clubs.management.commands.utils import unify_club_name, unify_team_name


class BaseModel(_BaseModel, metaclass=ABCMeta):
    __to_dict__ = {}

    def __init__(self, **kwargs) -> None:
        self.update_forward_refs()
        super().__init__(**kwargs)

    def __getitem__(self, item: _typing.Any) -> _typing.Any:
        return getattr(self, item)

    def dict(self, *args, **kwargs) -> dict:
        return super().dict(include=self.__to_dict__, exclude_unset=True)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        use_enum_values = True


class BaseListModel(_BaseModel, metaclass=ABCMeta):
    __root__: _typing.List[_BaseModel]

    def __iter__(self) -> _typing.Iterator:
        return iter(self.__root__ or [])

    def __getitem__(self, item: _typing.Any) -> _BaseModel:
        return self.__root__[item]

    def __len__(self) -> int:
        return len(self.__root__)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        use_enum_values = True


class Gender(str, _Enum):
    MALE = "Male"
    FEMALE = "Female"
    MIXED = "Mixed"


class LeagueType(str, _Enum):
    LEAGUE = "LEAGUE"
    CUP = "CUP"


class Seniority(str, _Enum):
    SENIOR = "Senior"
    JUNIOR = "Junior"
    CLJ = "Centralna Liga Juniorow"


class VoivodeshipSchema(BaseModel):
    name: str


class ClubSchema(BaseModel):
    __to_dict__ = {"name", "stadion_address"}
    __field__: dict

    mapper_id: _UUID = _Field(alias="id")
    name: str
    teams: _typing.Optional["TeamListSchema"] = []
    voivodeship: _typing.Optional["VoivodeshipSchema"]
    stadion_address: _typing.Optional[str] = _Field(alias="address")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        try:
            self._parse_name()
        except:
            pass

    def _parse_name(self) -> None:
        """Parse name and set abbreviation"""
        self.name = unify_club_name(self.name)


class TeamSchema(BaseModel):
    __to_dict__ = {
        "name",
        "age_category",
    }
    mapper_id: _UUID = _Field(alias="id")
    name: str
    abbreviation: _typing.Optional[str]
    logo: _typing.Optional[str]
    season: str
    league: _typing.Optional["BaseLeagueSchema"]
    age_category: _typing.Optional[str]
    seniority: _typing.Optional[Seniority]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._define_age_category()
        self._define_seniority()

        try:
            self._parse_name()
        except:
            pass

    def _parse_name(self) -> None:
        """Parse name and set abbreviation"""
        self.name = unify_team_name(self.name)

    def _define_age_category(self) -> None:
        """Define age category based on team name"""
        if self.league:
            if found_category := _re.search(
                r"U-\d{2}\b", self.league.name, _re.IGNORECASE
            ):
                self.age_category = found_category.group().upper().replace("-", "")

    def _define_seniority(self) -> None:
        """Define seniority or override if CLJ"""
        if self.league:
            if _re.search(r"U-\d{2}\b", self.league.name, _re.IGNORECASE):
                self.seniority = Seniority.CLJ
            elif not self.seniority and len(self.league.name) == 2:
                self.seniority = Seniority.JUNIOR
            elif not self.seniority:
                self.seniority = Seniority.SENIOR


class BaseLeagueSchema(BaseModel):
    mapper_id: str = _Field(alias="id")
    name: str


class LeagueSchema(BaseLeagueSchema):
    __to_dict__ = {"name", "league_type", "gender", "seniority"}
    gender: _typing.Optional[Gender]
    plays: _typing.Optional["LeaguePlayListSchema"] = []
    season: _typing.Optional[str]
    seniority: _typing.Optional[Seniority]
    league_type: _typing.Optional[LeagueType]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._define_type()
        self._define_season_name_for_plays()
        self._define_seniority()

    def _define_type(self) -> None:
        """Define League type based on name"""
        self.league_type = (
            LeagueType.CUP
            if _re.search(r"puchar", self.name, _re.IGNORECASE)
            else LeagueType.LEAGUE
        )

    def _define_season_name_for_plays(self) -> None:
        """Set season for each play within league"""
        if self.plays:
            for play in self.plays.__root__:
                play.season = self.season

    def _define_seniority(self) -> None:
        """Define seniority or override if CLJ"""
        if _re.search(r"U-\d{2}\b", self.name, _re.IGNORECASE):
            self.seniority = Seniority.CLJ
        elif not self.seniority and len(self.name) == 2:
            self.seniority = Seniority.JUNIOR
        elif not self.seniority:
            self.seniority = Seniority.SENIOR


class LeaguePlaySchema(BaseModel):
    __to_dict__ = {
        "name",
    }
    mapper_id: _UUID = _Field(alias="id")
    name: str
    season: _typing.Optional[str]
    voivodeship: _typing.Optional["VoivodeshipSchema"]


class LeaguePlayListSchema(BaseListModel):
    __root__: _typing.Optional[_typing.List[LeaguePlaySchema]] = []


class LeagueListSchema(BaseListModel):
    __root__: _typing.List[LeagueSchema]


class ClubListSchema(BaseListModel):
    __root__: _typing.List[ClubSchema]


class TeamListSchema(BaseListModel):
    __root__: _typing.Optional[_typing.List[TeamSchema]] = []


class MatchSchema(BaseModel):
    """We need nothing more but league, sex and play for now"""

    sex: _typing.Optional[Gender] = None
    league: LeagueSchema
    play: _typing.Optional[LeaguePlaySchema]


class MatchListSchema(BaseListModel):
    __root__: _typing.List["MatchSchema"]
