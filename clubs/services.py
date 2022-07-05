from .models import Team, Club, Season


class SeasonService:
    def get(self, name):
        season, _ = Season.objects.get_or_create(name=name)
        return season


class AdapterBase:
    def get_mapping_name(self, name):
        return f",,{name},,"


class TeamAdapter(AdapterBase):
    def match_name_or_mapping(self, name: str):
        try:
            return Team.objects.get(name__iexact=name)
        except Team.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return Team.objects.get(mapping__icontains=name)
            except Team.DoesNotExist:
                return None

    def match_name_or_mapping_with_code(self, name: str, code: str):
        try:
            return Team.objects.get(name__iexact=name, league__code=str(code))
        except Team.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return Team.objects.get(mapping__icontains=name, league__code=str(code))
            except Team.DoesNotExist:
                return None


class ClubAdapter(AdapterBase):
    def match_name_or_mapping(self, name: str):
        try:
            return Club.objects.get(name__iexact=name)
        except Club.DoesNotExist:
            name = self.get_mapping_name(name)
            try:
                return Club.objects.get(mapping__icontains=name)
            except Club.DoesNotExist:
                return None
