from typing import List, Union
from django.contrib.postgres.search import SearchVector
import django.core.exceptions

from .utils import unify_name, NEW_LNP_SOURCE, NEW_ADDITIONAL_LNP_SOURCE, create_mapper, get_mapper, MapperEntity
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

PARENT_UUID_REQUIRED = ["Ekstraklasa", "Ekstraliga K", "1 Liga", "2 liga"]

JUNIOR_LEAGUES = [
    "A1",
    "A2",
    "B1",
    "B2",
    "C1",
    "C2",
    "D1",
    "D2",
    "E1",
    "E2",
    "F1",
    "F2",
    "G1",
    "G2",
    "CLJ U-19",
    "CLJ U-18",
    "CLJ U-17",
    "CLJ U-15",
]

LEAGUE_HIGHEST_PARENT_NAME_MAPPER = {
    "Ekstraklasa": "Ekstraklasa",
    "Ekstraliga kobiet": "Ekstraliga K",
    "Pierwsza liga": "1 Liga",
    "Pierwsza liga kobiet": "1 Liga K",
    "Druga liga": "2 liga",
    "Druga liga kobiet": "2 Liga K",
    "Trzecia liga": "3 Liga",
    "Trzecia liga kobiet": "3 Liga K",
    "Czwarta liga": "4 Liga",
    "Czwarta liga kobiet": "4 Liga K",
    "Piąta liga": "5 Liga",
    "Klasa okręgowa": "Klasa Okręgowa",
    "Klasa A": "A Klasa",
    "Klasa B": "B Klasa",
    "Klasa C": "C Klasa",
    "CLJ U-19": "Clj U-19",
    "CLJ U-18": "Clj U-18",
    "CLJ U-17": "Clj U-17",
    "CLJ U-15": "Clj U-15",
    "Centralna Liga Juniorek U-17": "Clj U-17 K",
    "Centralna Liga Juniorek U-15": "Clj U-15 K",
    "A1": "Junior A1",
    # "A2": "Junior A2",
    "B1": "Junior Młodszy B1",
    # "B2": "Junior Młodszy B2",
    "C1": "Trampkarz C1",
    # "C2": "Trampkarz C2",
    # "D1": "Młodzik D1 U-13", # We don't need them yet
    # "D2": "Młodzik D2 U-12",
    # "E1": "Orlik E1 U-11",
    # "E2": "Orlik E2 U-10",
    # "F1": "Żak F1 U-9",
    # "F2": "Żak F2 U-8",
    # "G1": "Skrzat G1 U-7",
    # "G2": "Skrzat G2 U-6",
    "Futsal Ekstraklasa": "Futsal Ekstraklasa",
    "I Liga PLF": "I Liga PLF",
    "II Liga PLF": "II Liga PLF",
    "III Liga PLF": "III Liga PLF",
}


class Command(BaseCommand):
    """
    Update database with scrapper objects (PM-519)
    """

    SEASONS_TO_FETCH = [
        # "2022/2023",
        "2021/2022",
        # "2020/2021",
    ]

    SENIOR, _ = Seniority.objects.get_or_create(name="seniorzy")
    JUNIOR, _ = Seniority.objects.get_or_create(name="juniorzy")

    MALE, _ = Gender.objects.get_or_create(name="mężczyźni")
    FEMALE, _ = Gender.objects.get_or_create(name="kobiety")

    def handle(self) -> None:
        scrapper_leagues: List[LeagueEntity] = self.http.get_leagues()
        scrapper_team_histories: List[
            TeamHistoryEntity
        ] = self.http.get_team_histories()

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
                    if "grupa" in name and "Grupa" not in name:
                        try:
                            index_in = partial_name.index("grupa")
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
                    else:
                        if "Grupa" in partial_name:
                            index_in = partial_name.index("Grupa")
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

                    if '"RW"' in name or '"RW ' in name or "(RW)" in name:
                        params.append("RW")
                    elif '"RJ"' in name or '"RJ ' in name or "(RJ)" in name:
                        params.append("RJ")

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
                            # scrapper_uuid=play.id
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
                                    NEW_LNP={"id": play.id, "desc": "LNP play uuid"},
                                    NEW_ADDITIONAL_LNP={"id": league_obj.id, "desc": "LNP league uuid (highest parent)"}
                                ),
                                # scrapper_uuid=play.id,
                                # scrapper_parent_uuid=league_obj.id,
                                league_name_raw=play.name,
                            )
                    if (
                        league_history.mapper
                        and league_history.mapper.get_entity(source=NEW_LNP_SOURCE)
                            # league_history.scrapper_uuid
                            # and league_history.scrapper_uuid != play.id
                    ):
                        lh_mapper_entity = league_history.mapper.get_entity(source=NEW_LNP_SOURCE)
                        curr_teams_count = len(
                            self.http.get_play_teams(lh_mapper_entity.mapper_id)
                        # self.http.get_play_teams(league_history.scrapper_uuid)
                        )
                        new_teams_count = len(self.http.get_play_teams(play.id))
                        if new_teams_count < curr_teams_count:
                            continue
                        lh_mapper_entity.mapper_id = play.id
                        lh_mapper_entity.save()
                        # league_history.scrapper_uuid = play.id
                        if highest_parent in PARENT_UUID_REQUIRED:
                            lh_mapper_additional_entity = league_history.mapper.get_entity(source=NEW_ADDITIONAL_LNP_SOURCE)
                            lh_mapper_additional_entity.mapper_id = league_obj.id
                            lh_mapper_additional_entity.save()
                            # league_history.scrapper_parent_uuid = league_obj.id
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
                    self.JUNIOR if team_league.name in JUNIOR_LEAGUES else self.SENIOR
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
                club_details = self.http.get_club_details(club.id)
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
                        mapper=create_mapper(NEW_LNP={"id": club.id, "desc": "LNP club uuid"}),
                        # scrapper_uuid=club.id,
                        scrapper_autocreated=True,
                        mapping=club.name,
                        voivodeship_obj=club_voivo,
                        stadion_address=club_address,
                    )

                def configure_club(obj: Club):
                    if not obj.mapper:
                        obj.create_mapper_obj()
                    MapperEntity.objects.get_or_create(target=obj.mapper, source=NEW_LNP_SOURCE, mapper_id=club.id)
                    # obj.scrapper_uuid = club.id
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
                            NEW_LNP={
                                "id": team_history.obj_id,
                                "desc": "TeamHistory id as ObjectId in mongodb, immutable between seasons"
                            }
                        ),
                        # scrapper_teamhistory_id=team_history.obj_id,
                        scrapper_autocreated=True,
                        mapping=f"{team.name}; ",
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
                            NEW_LNP={
                                "id": team_history.obj_id,
                                "desc": "TeamHistory id as ObjectId in mongodb, immutable between seasons"
                            }
                        )
                    team_obj.save()

                # if not team_obj.scrapper_teamhistory_id:
                #     team_obj.scrapper_teamhistory_id = team_history.obj_id
                #     team_obj.save()

                team_plays = self.http.get_team_plays(team.id)
                for league in team_plays:
                    try:
                        league_history = LeagueHistory.objects.get(
                            mapper=get_mapper(league.id)
                        )
                        # league_history = LeagueHistory.objects.get(
                        #     scrapper_uuid=league.id
                        # )
                    except django.core.exceptions.ObjectDoesNotExist:
                        continue
                    try:
                        TeamHistory.objects.get(mapper=get_mapper(team.id))
                    except django.core.exceptions.ObjectDoesNotExist:
                        TeamHistory.objects.create(
                            team=team_obj,
                            team_name_raw=team.name,
                            mapper=create_mapper(NEW_LNP={"id": team.id, "desc": "LNP team uuid"}),
                            # scrapper_team_uuid=team.id,
                            league_history=league_history,
                            visible=False,
                        )

    def merge_clubs(self) -> None:
        """
        Merge clubs which are a single instance
        """
        club_list = Club.objects.all()
        for club in club_list:
            same_club_qs = list(Club.objects.filter(name__icontains=club.name))
            if len(same_club_qs) > 1:
                base_club = same_club_qs[0]
                teams = []
                editors = []
                for c in same_club_qs:
                    for team in c.teams.all():
                        teams.append(team) if team not in teams else False
                    for editor in c.editors.all():
                        editors.append(editor) if editor not in editors else False
                    editors.append(c.manager) if c.manager else False
                for team in set(teams):
                    team.club = base_club
                    team.save()
                for editor in set(editors):
                    base_club.editors.add(editor)
                base_club.save()
                same_club_qs.pop(0)
                for club_to_delete in same_club_qs:
                    club_to_delete.delete()
