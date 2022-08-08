from django.core.management import BaseCommand
from clubs.models import Team, TeamHistory, Season
from profiles.models import PlayerProfile, CoachProfile
from django.db.models import Q


class Command(BaseCommand):
    """
    Migrate Team data into a TeamHistory data.
    """

    def handle(self, *args: any, **options: any) -> None:
        self.create_team_history_objects_based_on_team()
        self.create_profiles_connections()

    def create_profiles_connections(self):
        for player in PlayerProfile.objects.filter(
            Q(team_object__isnull=False) & Q(team_object__data_mapper_id__isnull=False)
        ):
            th = TeamHistory.objects.get(team=player.team_object)
            player.team_history_object = (
                th  # here when used only one object should be for team...
            )
            player.save()

        for player in CoachProfile.objects.filter(
            Q(team_object__isnull=False) & Q(team_object__data_mapper_id__isnull=False)
        ):
            player.team_history_object = TeamHistory.objects.get(
                team=player.team_object
            )  # here when used only one object should be for team...
            player.save()

    def create_team_history_objects_based_on_team(self):
        teams = Team.objects.filter(data_mapper_id__isnull=False)
        season, _ = Season.objects.get_or_create(name="2021/2022")
        for team in teams:
            TeamHistory.objects.get_or_create(
                team=team,
                autocreated=True,
                season=season,
                league=team.league,
                data_mapper_id=team.data_mapper_id,
            )
