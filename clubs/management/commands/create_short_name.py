from django.core.management import BaseCommand
from clubs.models import Club, Team
import pandas as pd
from clubs.management.commands.utils import modify_name


class Command(BaseCommand):

    def handle(self, *args: any, **options: any) -> None:
        '''+ flaga ze przekonwerttowane'''
        teams = Team.objects.all()

        data = []
        for team in teams:
            modified_club_name = modify_name(team.club)
            team.club.short_name = modified_club_name
            team.club.save()

            modified_team_name = modify_name(team)
            team.short_name = modified_team_name
            team.save()

            data.append({'club_id': team.club.id, 'club_name': team.club.name, 'modified_club_name': modified_club_name,
                         'team_id': team.id, 'team_name': team.name, 'modified_team_name': modified_team_name})

        df = pd.DataFrame(data)
        df.to_csv('output.csv', index=False)
        # df_lks = df[df['club_name'].str.contains('LKS')]
        df_not_lks = df[~df['club_name'].str.contains('LKS')]
        df_not_lks.to_csv('output_without_lks.csv', index=False)