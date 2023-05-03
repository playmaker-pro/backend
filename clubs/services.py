from typing import Optional

from .models import Club, Season, Team


class SeasonService:
    def get(self, name):
        season, _ = Season.objects.get_or_create(name=name)
        return season


class AdapterBase:
    def get_mapping_name(self, name: str) -> str:
        return f",,{name},,"


class TeamAdapter(AdapterBase):
    def match_name_or_mapping_with_code(self, name: str, code: str) -> Optional[Team]:
        try:
            return Team.objects.get(name__iexact=name, league__code=str(code))
        except Team.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return Team.objects.get(mapping__icontains=name, league__code=str(code))
            except Team.DoesNotExist:
                return None
