import logging

from functools import lru_cache

import easy_thumbnails
from clubs.models import League as CLeague
from clubs.models import Team as CTeam

from easy_thumbnails.files import get_thumbnailer
from profiles.models import PlayerProfile


logger = logging.getLogger(__name__)


class PlayerMapper:
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
    @classmethod
    @lru_cache()
    def get_team_obj(cls, team_name, league_obj) -> CTeam:
        try:
            team_obj = CTeam.objects.get(
                league=league_obj, mapping__icontains=team_name.lower()
            )
            return team_obj
        except CTeam.DoesNotExist:
            return None

    @classmethod
    @lru_cache()
    def get_url_pic_name(cls, team_name: str, league_obj: CLeague) -> tuple:
        """Returns tuple of (Url, Picture Url, name)"""
        obj = TeamMapper.get_team_obj(team_name, league_obj)
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
