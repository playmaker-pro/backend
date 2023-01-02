from typing import List, Tuple
import re
from clubs.models import LeagueHistory, TeamHistory, Team, Season, Club
from connector.scripts.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from .utils import unify_team_name
from mapper.enums import SENIOR_MALE_LEAGUES, SENIOR_FEMALE_LEAGUES, JUNIOR_LNP_LEAGUES, FUTSAL_MALE_LEAGUES, \
    FUTSAL_FEMALE_LEAGUES, JUNIOR_MALE_LEAGUES


class Command(BaseCommand):

    def handle(self) -> None:
        # self.fix_teams()
        self.fix_clubs()
        self.fix_rounds()
        # self.fix_teams_numeration()  NOT READY DONT USE

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

    def fix_clubs(self) -> None:
        def merge(base_club: Club, to_remove: Club):
            if not base_club.mapper:
                base_club.create_mapper_obj()
            entities = to_remove.mapper.get_entities()
            for entity in entities:
                entity.target = base_club.mapper
                entity.save()
            teams = to_remove.teams.all()
            for team in teams:
                team.club = base_club
                team.save()
            editors = to_remove.editors.all()
            for editor in editors:
                base_club.editors.add(editor)
            if not base_club.manager and to_remove.manager:
                base_club.manager = to_remove.manager
            if not base_club.voivodeship and to_remove.voivodeship_obj:
                base_club.voivodeship_obj = to_remove.voivodeship_obj
            if not base_club.stadion_address and to_remove.stadion_address:
                base_club.stadion_address = to_remove.stadion_address
            base_club.save()
            to_remove.delete()

        clubs_to_fix = []
        for club in Club.objects.all():
            if not club.mapper or (club.mapper and not club.mapper.get_entities()):
                clubs_to_fix.append(club)
        for club in clubs_to_fix:
            partial_club_name = list(reversed(sorted(club.name.split(), key=len)))
            base_filter = Club.objects.exclude(id=club.id)
            direct_search = base_filter.filter(mapping__icontains=club.name)
            if len(direct_search) == 1:
                merge(club, direct_search[0])
            else:
                for n, phrase in enumerate(partial_club_name):
                    result = base_filter.filter(mapping__icontains=phrase)
                    if len(result) > 1:
                        try:
                            result = result.filter(mapping__icontains=partial_club_name[n + 1])
                        except IndexError:
                            try:
                                result = result.filter(mapping__icontains=partial_club_name[n - 1])
                            except IndexError:
                                continue
                            if len(result) == 1:
                                merge(club, result[0])

    def fix_teams(self) -> None:
        """
        Merge teams that have not been assigned correctly
        """
        teams_to_fix = Team.objects.filter(historical__isnull=True)\
            .filter(league__isnull=False)
        for team in teams_to_fix:
            if team.mapper and team.mapper.get_entities():
                continue
            team_name = unify_team_name(team.name)
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
                    league=team_league, season__name="2021/2022"
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
                    entities = target_team_history.team.mapper.get_entities()
                    for entity in entities:
                        entity.target = team.mapper
                        entity.save()
                    team.mapper.save()
                    team.save()
                    target_team_history.team.delete()
                    target_team_history.team = team
                    target_team_history.save()
                    break

    def decimal_to_roman(self, number: int) -> str:
        mapper = {
            2: "II",
            3: "III",
            4: "IV",
            5: "V",
            6: "VI",
            7: "VII",
            8: "VIII",
            9: "IX",
        }
        return mapper[number]

    def rename_teams_based_on_league(self, teams: List[Tuple[Team, str]], ordering: List[str]) -> None:

        sorted_teams = sorted(teams, key=(lambda tup: ordering.index(tup[1])))
        print(sorted_teams, ordering)

        index = 2
        for team, _ in sorted_teams[1:]:
            team_name = team.name
            parted_team_name = team_name.split()
            roman_counter = self.decimal_to_roman(index)
            if roman_counter not in parted_team_name:
                team_name = re.sub(r"\b([IΙ]X|[IΙ]V|V?[IΙ]{0,3})\b\.?", "", team_name)
                # print(team_name + " " + roman_counter)
                # team.name = team.name + " " + self.decimal_to_roman(index)
                # team.save()
            index += 1

    def fix_teams_numeration(self): ## NOT READY, DONT USE
        """
        Apply team hierarchy numeration based on league - "GKS Bełchatów", "GKS Bełchatów II" etc.
        """
        SENIOR_MALE_LEAGUE_NAMES = list(SENIOR_MALE_LEAGUES.values())
        SENIOR_FEMALE_LEAGUE_NAMES = list(SENIOR_FEMALE_LEAGUES.values())
        JUNIOR_LEAGUE_NAMES = list(JUNIOR_MALE_LEAGUES.values())
        FUTSAL_MALE_LEAGUE_NAMES = list(FUTSAL_MALE_LEAGUES.values())
        FUTSAL_FEMALE_LEAGUE_NAMES = list(FUTSAL_FEMALE_LEAGUES.values())

        clubs = Club.objects.filter(teams__isnull=False)
        for club in clubs:
            teams = club.teams.all()
            senior_male = []
            senior_female = []
            junior = []
            futsal_male = []
            futsal_female = []
            for team in teams:
                th = TeamHistory.objects.filter(team=team)\
                    .order_by("-league_history__season")
                if not th:
                    continue
                try:
                    l_highest_parent = th[0].league_history.league.highest_parent.name
                except AttributeError:
                    l_highest_parent = th[0].league_history.league.get_highest_parent()
                if l_highest_parent in SENIOR_MALE_LEAGUE_NAMES:
                    senior_male.append((team, l_highest_parent))
                elif l_highest_parent in SENIOR_FEMALE_LEAGUE_NAMES:
                    senior_female.append((team, l_highest_parent))
                elif l_highest_parent in JUNIOR_LEAGUE_NAMES:
                    junior.append((team, l_highest_parent))
                elif l_highest_parent in FUTSAL_MALE_LEAGUE_NAMES:
                    futsal_male.append((team, l_highest_parent))
                elif l_highest_parent in FUTSAL_FEMALE_LEAGUE_NAMES:
                    futsal_female.append((team, l_highest_parent))

            self.rename_teams_based_on_league(senior_male, SENIOR_MALE_LEAGUE_NAMES)
            self.rename_teams_based_on_league(senior_female, SENIOR_FEMALE_LEAGUE_NAMES)
            self.rename_teams_based_on_league(junior, JUNIOR_LEAGUE_NAMES)
            self.rename_teams_based_on_league(futsal_male, FUTSAL_MALE_LEAGUE_NAMES)
            self.rename_teams_based_on_league(futsal_female, FUTSAL_FEMALE_LEAGUE_NAMES)
