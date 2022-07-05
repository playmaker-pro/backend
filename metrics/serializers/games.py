import logging
from datetime import datetime

from clubs.models import League as CLeague
from data.models import Game as DGame
from metrics.mappers import PlayerMapper, TeamMapper

from .users import SimplePlayerProfileSerializer

logger = logging.getLogger(__name__)


class GameSerializer:
    """
    For given games data.Game(s) we are making serialization.
    host_team =
    guest_team =
    host_score = models.IntegerField(null=True)
    host_coach = models.ForeignKe
    host_team_name = models.TextField()
    guest_score = models.IntegerField(null=True)
    guest_coach = models.Foreign
    guest_team_name = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    : Return :
        {"name": "Kolejka 30",
            "games": [
                {
                    "guest_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                    "host_pic": "/media/league_pics/%25Y-%25m-%25d/29584_1000x.jpg.100x100_q85_crop.png",
                    "host": "Sokół I",
                    "guest": "Lechia Dzierżoniów",
                    "score": "2 - 1",
                    "date": "10.05 21:00",
                    "players": [ {}, {}]
                    "player_ids": []..
    """

    model = DGame

    @classmethod
    def serialize(cls, game, host_pic, guest_pic, league: CLeague):
        if isinstance(game, (cls.model, dict)):
            return cls.calculate(game, host_pic, guest_pic, league)
        raise RuntimeError(
            f"Wrong data type. Expected is {cls.model} instance or dict."
        )

    @classmethod
    def calculate(cls, game, host_pic, guest_pic, league: CLeague):

        h_url, h_pic, h_name = TeamMapper.get_url_pic_for_club(
            cls._get_attr(game, "host_team_name"), league
        )
        g_url, g_pic, g_name = TeamMapper.get_url_pic_for_club(
            cls._get_attr(game, "guest_team_name"), league
        )

        guest_score = cls._get_attr(game, "guest_score")
        host_score = cls._get_attr(game, "host_score")
        score = (
            f"{host_score} - {guest_score}"
            if host_score is not None and guest_score is not None
            else None
        )

        players_ids = cls._get_attr(game, "players_ids")

        return {
            "guest_pic": g_pic,
            "host_pic": h_pic,
            "date": cls.clean_date(cls._get_attr(game, "date")),
            "score": score,
            "host_url": h_url,
            "host": h_name,
            "guest": g_name,
            "guest_url": g_url,
            "guest_score": guest_score,
            "host_score": host_score,
            "players": SimplePlayerProfileSerializer.serialize(
                [
                    profile
                    for _id in players_ids
                    if (profile := PlayerMapper.get_player_profile_object(_id))
                    is not None
                ]
            ),
            # "player_ids": players_ids  # todo: disable that it is not needed right now.
        }

    @classmethod
    def clean_date(cls, date: datetime) -> str:
        date = cls._add_timezone_to_datetime(date)
        return cls._convert_datetime_to_string(date)

    @classmethod
    def _get_attr(cls, obj, name: str):
        if isinstance(obj, cls.model):
            return getattr(obj, name)
        elif isinstance(obj, dict):
            return obj.get(name)
        else:
            raise RuntimeError("Not supported data type.")

    @classmethod
    def _add_timezone_to_datetime(
        cls, date: datetime, hours_shift: int = 2
    ) -> datetime:
        """Two systems uses different date nottation. +2h is needed to shift"""
        from datetime import timedelta

        return date + timedelta(hours=hours_shift)

    @classmethod
    def _convert_datetime_to_string(cls, date: datetime) -> str:
        return date.strftime("%Y/%d/%m, %H:%M")


class GameRawSerializer:
    """
    {'date': '23/07/2021 18:00',
     'host': 'BRUK-BET Termalica Nieciecza',
     'guest': 'FKS Stal Mielec S. A.',
     'place': 'Stadion Sportowy BRUK-BET TERMALICA Nieciecza (Nieciecza 150)',
     'queue': '1 kolejka',
     'score': '1:1',
     'league': 'Ekstraklasa "PKO Bank Polski Ekstraklasa"',
     '_url_host': 'https://www2.laczynaspilka.pl/druzyna/bruk-bet-termalica-nieciecza,434083.html',
     '_url_guest': 'https://www2.laczynaspilka.pl/druzyna/fks-stal-mielec-s-a,450461.html',
     'game_action': 'relacja z meczu ›',
     '_url_game_relation': 'https://www2.laczynaspilka.pl/rozgrywki/mecz/bruk-bet-termalica-nieciecza,fks-stal-mielec-s-a,2980870.html'
    }
    """

    def serialize(self, obj, host_pic, guest_pic):
        obj["host_pic"] = host_pic
        obj["guest_pic"] = guest_pic
        return obj
