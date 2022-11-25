from clubs.models import LeagueHistory, TeamHistory, Team, Season
from connector.scripts.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from .utils import unify_name


class Command(BaseCommand):

    def handle(self) -> None:
        self.fix_teams()
        self.fix_rounds()

    def fix_rounds(self) -> None:
        """
        Re-assign RW/RJ rounds to asure leagues accuracy
        """
        all_rw_lhs = LeagueHistory.objects.filter(league__name="RW")
        for rw_lh in all_rw_lhs:
            parent_l = rw_lh.league.parent
            try:
                rj_l = parent_l.childs.get(name="RJ")
                rj_lh, _ = LeagueHistory.objects.get_or_create(
                    league=rj_l, season=rw_lh.season
                )
                parent_lh = LeagueHistory.objects.get(
                    league=parent_l, season=rw_lh.season
                )
            except ObjectDoesNotExist:
                continue
            if (
                    TeamHistory.objects.filter(league_history=parent_lh)
                    and not TeamHistory.objects.filter(league_history=rj_lh)
                    and TeamHistory.objects.filter(league_history=rw_lh)
            ):
                parent_lh.league = rj_l
                parent_lh.save()
                for th in TeamHistory.objects.filter(league_history=parent_lh):
                    th.save()

    def fix_teams(self) -> None:
        """
        Merge teams that have not been assigned correctly
        """
        teams_to_fix = Team.objects.filter(scrapper_teamhistory_id__isnull=True).filter(
            league__isnull=False
        )
        for team in teams_to_fix:
            team_name = unify_name(team.name, False)
            team_name_partial = team_name.split(" ")
            if "Warszawa" in team_name_partial:
                team_name_partial.append("W-Wa")
            team_name_partial = list(
                reversed(
                    sorted(
                        [word for word in team_name_partial if len(word) > 2], key=len
                    )
                )
            )
            team_league = team.league
            try:
                league_history = LeagueHistory.objects.get(
                    league=team_league, season=Season.objects.get(name="2021/2022")
                )
            except ObjectDoesNotExist:
                continue
            teams_within_league = TeamHistory.objects.filter(
                league_history=league_history
            )
            for phrase in team_name_partial:
                result = teams_within_league.filter(team__name__icontains=phrase)
                if len(result) == 1:
                    target_team_history = result[0]
                    if len(team_name_partial) > 1:
                        final_check = [
                            word.upper() in target_team_history.team.name.upper()
                            for word in team_name_partial
                            if word != phrase
                        ]
                        if not any(final_check):
                            continue
                    th_id = target_team_history.team.scrapper_teamhistory_id
                    target_team_history.team.delete()
                    target_team_history.delete()
                    target_team_history.team = team
                    team.scrapper_teamhistory_id = th_id
                    team.save()
                    target_team_history.save()
                    break
