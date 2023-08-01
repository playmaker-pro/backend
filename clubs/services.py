from typing import Optional
from . import models


class SeasonService:
    def get(self, name):
        season, _ = models.Season.objects.get_or_create(name=name)
        return season


class AdapterBase:
    def get_mapping_name(self, name: str) -> str:
        return f",,{name},,"


class TeamAdapter(AdapterBase):
    def match_name_or_mapping_with_code(
        self, name: str, code: str
    ) -> Optional[models.Team]:
        try:
            return models.Team.objects.get(name__iexact=name, league__code=str(code))
        except models.Team.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return models.Team.objects.get(
                    mapping__icontains=name, league__code=str(code)
                )
            except models.Team.DoesNotExist:
                return None


class ClubService:
    def team_exist(self, team_id: int) -> Optional[models.Team]:
        """Return Team with given id if exists, None otherwise"""
        try:
            return models.Team.objects.get(id=team_id)
        except models.Team.DoesNotExist:
            return

    def club_exist(self, club_id: int) -> Optional[models.Club]:
        """Return Club with given id if exists, None otherwise"""
        try:
            return models.Club.objects.get(id=club_id)
        except models.Club.DoesNotExist:
            return

    def team_history_exist(self, th_id: int) -> Optional[models.TeamHistory]:
        """Return TeamHistory with given id if exists, None otherwise"""
        try:
            return models.TeamHistory.objects.get(id=th_id)
        except models.TeamHistory.DoesNotExist:
            return
