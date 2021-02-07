from .models import Team, Club


class TeamAdapter:

    def match_name_or_mapping(self, name: str):
        try:
            return Team.objects.get(name__iexact=name)
        except Team.DoesNotExist:
            name += ','
            try:
                return Team.objects.get(mapping__icontains=name)
            except Team.DoesNotExist:
                return None


class ClubAdapter:

    def match_name_or_mapping(self, name: str):
        try:
            return Club.objects.get(name__iexact=name)
        except Club.DoesNotExist:
            name += ','
            try:
                return Club.objects.get(mapping__icontains=name)
            except Club.DoesNotExist:
                return None
