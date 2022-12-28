from typing import List
from django.contrib.postgres.search import SearchVector
import django.core.exceptions
from collections import Counter

from .utils import unify_name, LNP_SOURCE, create_mapper, get_mapper, MapperEntity
from .base import BaseCommand
from .restore_database import Command as RestoreDatabase
from clubs.models import (
    Club,
    Team,
    TeamHistory,
    LeagueHistory,
    League,
    Season,
    Seniority,
    Gender,
)
import re
from django.db.models import Q
from .fix_new_structure import Command as FixNewStructure
from voivodeships.management.commands.add_voivodeships import Command as VoivoImport
from inquiries.models import InquiryRequest
from voivodeships.models import Voivodeships
from connector.entities import (
    TeamHistoryEntity,
    LeagueEntity,
    PlayEntity,
    TeamEntity,
    BaseClubEntity,
)
from mapper.enums import LEAGUE_HIGHEST_PARENT_NAME_MAPPER, JUNIOR_LNP_LEAGUES, PARENT_UUID_REQUIRED


class Command(BaseCommand):
    """
    Update database with scrapper objects (PM-519)
    """

    SEASONS_TO_FETCH = [
        "2022/2023",
        "2021/2022",
        "2020/2021",
    ]

    SENIOR, _ = Seniority.objects.get_or_create(name="seniorzy")
    JUNIOR, _ = Seniority.objects.get_or_create(name="juniorzy")

    MALE, _ = Gender.objects.get_or_create(name="mężczyźni")
    FEMALE, _ = Gender.objects.get_or_create(name="kobiety")

    def handle(self) -> None:
        scrapper_leagues: List[LeagueEntity] = self.service.get_leagues()
        scrapper_team_histories: List[
            TeamHistoryEntity
        ] = self.service.get_team_histories()

        RestoreDatabase()

        if not Voivodeships.objects.all():
            VoivoImport().handle()

        self.reset_inquiry_requests()
        self.clear_teams()
        self.clear_clubs()
        self.merge_clubs()

        self.map_league_history(scrapper_leagues)
        self.map_teamhistory(scrapper_team_histories)

        FixNewStructure()

    def reset_inquiry_requests(self) -> None:
        """
        Assign every inquiry request to USER
        """
        ir_list = InquiryRequest.objects.filter(
            category__in=[InquiryRequest.CATEGORY_CLUB, InquiryRequest.CATEGORY_TEAM]
        )
        for ir in ir_list:
            ir.category = InquiryRequest.CATEGORY_USER
            ir.save()

    def clear_teams(self) -> None:
        """
        Delete teams without manager/editor
        """
        teams = Team.objects.filter(Q(manager__isnull=True) & Q(editors__isnull=True))
        for team in teams:
            team.delete()

    def clear_clubs(self) -> None:
        """
        Delete clubs without teams or manager/editors
        """
        clubs = Club.objects.filter(
            Q(manager__isnull=True) & Q(editors__isnull=True) & Q(teams__isnull=True)
        )
        for club in clubs:
            club.delete()

    def unify_roman_decimals(self, val: str) -> str:
        """
        Transform roman digits to arabic
        """
        if " I" in val or "I " in val or "V " in val:
            return (
                val.replace("VII", "8")
                .replace("VII", "7")
                .replace("IV", "4")
                .replace("VI", "6")
                .replace("V", "5")
                .replace("III", "3")
                .replace("II", "2")
                .replace("I", "1")
            )
        return val

    def swap_lh_round(
            self, target: str, current_league_obj: League, current_season_obj: Season
    ) -> None:
        """
        Assign RW/RJ league
        """
        parent_league = current_league_obj.parent
        lost_league, _ = League.objects.get_or_create(
            name=target,
            parent=parent_league,
            highest_parent=parent_league.highest_parent,
        )
        try:
            lh_to_change = LeagueHistory.objects.get(
                league=parent_league, season=current_season_obj
            )
            lh_to_change.league = lost_league
            lh_to_change.save()
        except django.core.exceptions.ObjectDoesNotExist:
            pass

    def brute_search(
            self,
            name: str,
            model: Team or Club,
            l_highest_parent: str = None,
            unique_id: str = None,
    ) -> Team or Club:
        """
        Search Club/Team by name
        """

        def partial_search():
            model_obj = None
            base = model.objects.annotate(search_name=SearchVector("name"))
            result = base.filter(search_name=name)
            if len(result) == 1:
                return result[0]
            if l_highest_parent:
                result = result.filter(league__highest_parent__name=l_highest_parent)
            else:
                try:
                    direct = model.objects.get(name=name)
                    return direct
                except (
                        django.core.exceptions.MultipleObjectsReturned,
                        django.core.exceptions.ObjectDoesNotExist,
                ):
                    pass
            if len(result) > 1:
                res_list = [res.name for res in result]
                if res_list and res_list.count(res_list[0]) == len(res_list):
                    return result[0]
            elif len(result) == 1:
                model_obj = result[0]
            return model_obj

        try:
            target_mapper = get_mapper(unique_id)
            if target_mapper:
                if model is Club:
                    return model.objects.get(mapper=target_mapper)
                elif model is Team:
                    return model.objects.get(mapper=target_mapper)
        except django.core.exceptions.ObjectDoesNotExist:
            return partial_search()

    def unify_voivodeship_name(self, name: str) -> str:
        return name.lower().replace("-", "")

    def map_league_history(self, leagues: List[LeagueEntity]) -> None:
        """
        Get leagues from scrapper and assign them to webapp database, based on LeagueHistory
        """
        for season_name in self.SEASONS_TO_FETCH:
            local_season, _ = Season.objects.get_or_create(name=season_name)
            season_leagues: List[LeagueEntity] = list(
                filter(lambda league: league.season == season_name, leagues)
            )
            for league_obj in season_leagues:
                plays: List[PlayEntity] = league_obj.plays
                for play in plays:
                    name = play.name
                    try:
                        highest_parent = LEAGUE_HIGHEST_PARENT_NAME_MAPPER[
                            league_obj.name
                        ]
                    except KeyError:
                        continue

                    params = [highest_parent]
                    partial_name = (
                        re.sub(" +", " ", name).strip().replace('"', "").split(" ")
                    )

                    if play.voivodeship:
                        params.append(self.unify_voivodeship_name(play.voivodeship.name))

                    if "okręgowa" in partial_name and league_obj.pm_id in range(14, 28):
                        index_in = partial_name.index("okręgowa")
                        params.append(
                            self.unify_roman_decimals(
                                " ".join(partial_name[(index_in - 2): (index_in + 1)])
                            )
                        )
                    elif "wojewódzka" in partial_name and league_obj.pm_id in range(
                            14, 28
                    ):
                        index_in = partial_name.index("wojewódzka")
                        params.append(
                            self.unify_roman_decimals(
                                " ".join(partial_name[(index_in - 2): (index_in + 1)])
                            )
                        )

                    try:
                        if partial_name[0][-1] == ":":
                            params.append(partial_name[0].replace(":", ""))
                        elif partial_name[1][-1] == ":":
                            params.append(
                                " ".join(
                                    [partial_name[0], partial_name[1].replace(":", "")]
                                )
                            )
                    except IndexError:
                        pass

                    if "gr." in name:
                        try:
                            index_in = partial_name.index("gr.")
                            partial_name[index_in] = "Grupa"
                        except ValueError:
                            pass
                    if "grupa" in name:
                        try:
                            index_in = partial_name.index("grupa")
                            partial_name[index_in] = "Grupa"
                        except ValueError:
                            pass
                    if "GRUPA" in name:
                        try:
                            index_in = partial_name.index("GRUPA")
                            partial_name[index_in] = "Grupa"
                        except ValueError:
                            pass
                    if "zach." in partial_name or "zachodnia" in partial_name:
                        params.append("Zachód")
                    elif "wsch." in partial_name or "wschodnia" in partial_name:
                        params.append("Wschód")
                    elif "płd." in partial_name or "południowa" in partial_name:
                        params.append("Południe")
                    elif "płn." in partial_name or "północna" in partial_name:
                        params.append("Północ")

                    if "Grupa" in partial_name:
                        for index_in, phrase in enumerate(partial_name):
                            if phrase == "Grupa":
                                group = " ".join(partial_name[index_in: (index_in + 2)])
                                params.append(self.unify_roman_decimals(group))

                    if "baraż" in name.lower():
                        params.append("baraż")
                    elif "puchar" in name.lower():
                        params.append("puchar")
                    elif "mistrz" in name.lower():
                        params.append("mistrzowska")
                    elif "spad" in name.lower():
                        params.append("spadkowa")

                    if '"RW"' in name or '"RW ' in name or "(RW)" in name or "WIOSNA" in name or "WIOSENNA" in name:
                        params.append("RW")
                    elif '"RJ"' in name or '"RJ ' in name or "(RJ)" in name or "JESIEŃ" in name:
                        params.append("RJ")

                    params = list(Counter(params))

                    try:
                        target_league = League.objects.get(name=highest_parent)
                    except django.core.exceptions.ObjectDoesNotExist:
                        target_league = League.objects.create(
                            name=highest_parent, scrapper_autocreated=True
                        )
                    highest_parent_object = target_league
                    for child_league in params[1:]:
                        if highest_parent in PARENT_UUID_REQUIRED:
                            break
                        try:
                            temp_result = target_league.childs.get(name=child_league)
                            if temp_result:
                                target_league = temp_result
                        except django.core.exceptions.ObjectDoesNotExist:
                            target_league = League.objects.create(
                                name=child_league,
                                highest_parent=highest_parent_object,
                                parent=target_league,
                                scrapper_autocreated=True,
                            )

                    if "RW" in params:
                        self.swap_lh_round("RJ", target_league, local_season)
                    elif "RJ" in params:
                        self.swap_lh_round("RW", target_league, local_season)

                    try:
                        league_history = LeagueHistory.objects.get(
                            mapper=get_mapper(play.id)
                        )
                    except django.core.exceptions.ObjectDoesNotExist:
                        try:
                            league_history = LeagueHistory.objects.get(
                                league=target_league,
                                season=local_season,
                            )
                        except django.core.exceptions.ObjectDoesNotExist:
                            league_history = LeagueHistory.objects.create(
                                league=target_league,
                                season=local_season,
                                mapper=create_mapper(
                                    {"id": play.id, "related_type": "play", "database_source": "scrapper_mongodb", "desc": "LNP play uuid"},
                                    {"id": league_obj.id, "related_type": "league", "database_source": "scrapper_mongodb", "desc": "LNP league uuid (highest parent)"}
                                ),
                                league_name_raw=play.name,
                            )
                    target_mapper_entity = league_history.mapper.get_entity(source=LNP_SOURCE, related_type="play")
                    if (
                        target_mapper_entity
                        and target_mapper_entity.mapper_id != play.id
                    ):
                        curr_teams_count = len(
                            self.service.get_play_teams(target_mapper_entity.mapper_id)
                        )
                        new_teams_count = len(self.service.get_play_teams(play.id))
                        if new_teams_count < curr_teams_count:
                            continue
                        target_mapper_entity.mapper_id = play.id
                        target_mapper_entity.save()
                        if highest_parent in PARENT_UUID_REQUIRED:
                            lh_mapper_highest_parent_entity = league_history.mapper.get_entity(source=LNP_SOURCE, related_type="league")
                            lh_mapper_highest_parent_entity.mapper_id = league_obj.id
                            lh_mapper_highest_parent_entity.save()
                        league_history.league_name_raw = play.name
                        league_history.save()

    def map_teamhistory(self, team_histories: List[TeamHistoryEntity]) -> None:
        """
        Get Clubs/Teams(TeamHistory) from scrapper database, import into database
        """
        for team_history in team_histories:
            club: BaseClubEntity = team_history.club
            teams: List[TeamEntity] = team_history.teams
            for team in teams:
                if team.season not in self.SEASONS_TO_FETCH or "PAUZ" in team.name:
                    continue
                team_league = team.league
                try:
                    team_league_highest_parent = LEAGUE_HIGHEST_PARENT_NAME_MAPPER[
                        team_league.name
                    ]
                except KeyError:
                    continue
                team_name = unify_name(team.name, False)
                seniority = (
                    self.JUNIOR if team_league.name in JUNIOR_LNP_LEAGUES else self.SENIOR
                )
                gender = (
                    self.FEMALE
                    if team_league_highest_parent.endswith("K")
                    else self.MALE
                )
                team_obj = self.brute_search(
                    team_name,
                    Team,
                    l_highest_parent=team_league_highest_parent,
                    unique_id=team_history.obj_id,
                )

                club_name = unify_name(club.name)
                club_details = self.service.get_club_details(club.id)
                club_address = club_details.address
                voivo = club_details.voivodeship
                club_voivo = None
                if voivo:
                    try:
                        club_voivo = Voivodeships.objects.get(
                            name=voivo.name.capitalize()
                        )
                    except AttributeError:
                        pass

                def create_club():
                    return Club.objects.create(
                        name=club_name,
                        mapper=create_mapper({"id": club.id, "related_type": "club", "database_source": "scrapper_mongodb", "desc": "LNP club uuid"}),
                        scrapper_autocreated=True,
                        mapping=club.name,
                        voivodeship_obj=club_voivo,
                        stadion_address=club_address,
                    )

                def configure_club(obj: Club):
                    if not obj.mapper:
                        obj.create_mapper_obj()
                    MapperEntity.objects.get_or_create(target=obj.mapper, source=LNP_SOURCE, mapper_id=club.id)
                    obj.mapping = club.name
                    if not obj.stadion_address:
                        obj.stadion_address = club_address
                    if club_voivo:
                        obj.voivodeship_obj = club_voivo
                    obj.save()

                if not team_obj:
                    club_obj = self.brute_search(club_name, Club, unique_id=club.id)
                    if not club_obj:
                        club_obj = create_club()
                        configure_club(club_obj)
                    team_obj = Team.objects.create(
                        club=club_obj,
                        name=team_name,
                        mapper=create_mapper(
                            {
                                "id": team_history.obj_id,
                                "related_type": "team",
                                "database_source": "scrapper_mongodb",
                                "desc": "TeamHistory id as ObjectId in mongodb, immutable between seasons"
                            }
                        ),
                        scrapper_autocreated=True,
                        mapping=f"{team.name};",
                        visible=False,
                        seniority=seniority,
                        gender=gender,
                    )
                else:
                    team_obj.mapping = str(team_obj.mapping) + (
                        team.name if team.name not in str(team_obj.mapping) else ""
                    )
                    team_obj.seniority = seniority
                    team_obj.gender = gender
                    club_obj = (
                            self.brute_search(club_name, Club, unique_id=club.id)
                            or create_club()
                    )
                    configure_club(club_obj)

                if not team_obj.mapper:
                    team_obj.mapper = create_mapper(
                            {
                                "id": team_history.obj_id,
                                "related_type": "team",
                                "database_source": "scrapper_mongodb",
                                "desc": "TeamHistory id as ObjectId in mongodb, immutable between seasons"
                            }
                        )
                    team_obj.save()

                team_plays = self.service.get_team_plays(team.id)
                for league in team_plays:
                    try:
                        league_history = LeagueHistory.objects.get(
                            mapper=get_mapper(league.id)
                        )
                    except django.core.exceptions.ObjectDoesNotExist:
                        continue
                    try:
                        TeamHistory.objects.get(mapper=get_mapper(team.id))
                    except django.core.exceptions.ObjectDoesNotExist:
                        TeamHistory.objects.create(
                            team=team_obj,
                            team_name_raw=team.name,
                            mapper=create_mapper({"id": team.id, "related_type": "team history", "database_source": "scrapper_mongodb", "desc": "LNP team uuid"}),
                            league_history=league_history,
                            visible=False,
                        )

    def merge_clubs(self) -> None:
        """
        Merge clubs which are a single instance
        """
        def define_base_club(qs: List[Club]) -> Club:
            for club_obj in qs:
                if club_obj.mapper:
                    if club_obj.mapper.get_entities():
                        return club_obj
            else:
                return qs[0]

        club_list = Club.objects.all()
        for club in club_list:
            same_club_qs = list(Club.objects.filter(name__icontains=club.name))
            if len(same_club_qs) > 1:
                base_club = define_base_club(same_club_qs)
                teams = []
                editors = []
                for c in same_club_qs:
                    for team in c.teams.all():
                        teams.append(team)
                    for editor in c.editors.all():
                        editors.append(editor)
                    if c.manager:
                        editors.append(c.manager)
                for team in teams:
                    team.club = base_club
                    team.save()
                for editor in editors:
                    if editor not in base_club.editors.all():
                        base_club.editors.add(editor)
                base_club.save()
                for club_to_delete in same_club_qs:
                    if club_to_delete is not base_club:
                        club_to_delete.delete()
