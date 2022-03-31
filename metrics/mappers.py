import logging

from functools import lru_cache

import easy_thumbnails
from clubs.models import League as CLeague
from clubs.models import Team as CTeam

from easy_thumbnails.files import get_thumbnailer
from profiles.models import PlayerProfile


logger = logging.getLogger(__name__)


class PlayerMapper:
    """Found player in profile.PlayerProfile and connects with ID from s38
    """

    @classmethod
    @lru_cache()
    def get_player_profile_object(cls, player_id: int) -> PlayerProfile:
        """
        :player_id: s38 data mapper id
        """
        try:
            obj = PlayerProfile.objects.get(data_mapper_id=player_id)
            return obj
        except PlayerProfile.DoesNotExist:
            return None
        except PlayerProfile.MultipleObjectsReturned:
            # send email to admin.
            return None


class TeamMapper:

    def __init__(self):
        self.team_object = None

    @lru_cache()
    def get_team_obj(self, team_name: str, league_obj: CLeague) -> CTeam:

        try:
            team_obj = CTeam.objects.get(
                league=league_obj, mapping__icontains=team_name.lower()
            )
            return team_obj

        except CTeam.MultipleObjectsReturned:

            msg = f"input data: team_name={team_name} league_obj={league_obj} " \
                  f"league_obj.id={league_obj.id} query used={team_name.lower()} "
            logger.debug(msg)
            print(msg)
        except CTeam.DoesNotExist:
            return None

    @lru_cache()
    def get_url_pic_name(self, team_name: str, league_obj: CLeague) -> tuple:
        """Returns tuple of (Url, Picture Url, name)"""

        obj = self.get_team_obj(team_name, league_obj)
        name = obj.name if obj else team_name
        url = obj.get_permalink() if obj else None
        picture = obj.picture if obj and obj.picture else "default_profile.png"
        try:
            pic = get_thumbnailer(picture)["nav_avatar"].url
        except easy_thumbnails.exceptions.InvalidImageFormatError as e:
            logger.error(f"Picture is: `{picture}`")
            logger.exception(picture)
            if obj.picture:
                raise RuntimeError(
                    f"picture={picture}, obj={obj} obj.picture={obj.picture}"
                )
            else:
                raise RuntimeError(f"picture={picture}, obj={obj}")

        return url, pic, name

