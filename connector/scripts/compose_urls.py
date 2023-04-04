from typing import List, Dict
from clubs.models import TeamHistory
from connector.scripts.base import BaseCommand
from mapper.models import MapperEntity
from pm_core.utils.url_provider.providers import (
    compose_team_url,
    compose_club_url,
    compose_league_url,
    LeagueMappingSchema,
    Gender,
)
from pm_core.utils.url_provider.mappers import MALE_LEAGUES, FEMALE_LEAGUES, ZPNs


class Command(BaseCommand):
    """
    Create mocked LNP urls for mappers (club, team, league)
    Based on enums above
    """

    def handle(self) -> None:
        self.build_team_urls()
        self.build_club_urls()
        self.build_league_urls(MALE_LEAGUES, Gender.MALE)
        self.build_league_urls(FEMALE_LEAGUES, Gender.FEMALE)

    def build_team_urls(self) -> None:
        """build team url"""
        entities: List[MapperEntity] = MapperEntity.objects.filter(
            related_type="team history"
        )

        for entity in entities:
            entity.url = compose_team_url(entity.mapper_id)
            print(f"New url: {entity.url}")
            entity.save()

    def build_club_urls(self) -> None:
        """build club url"""
        entities: List[MapperEntity] = MapperEntity.objects.filter(related_type="club")

        for entity in entities:
            entity.url = compose_club_url(entity.mapper_id)
            print(f"New url: {entity.url}")
            entity.save()

    def build_league_urls(self, leagues: List[Dict], gender: Gender) -> None:
        """
        create LNP urls for leagues
        it has to be separated function due leauge url complexity
        """
        for div in leagues:
            for league in div["leagues"]:
                entities: List[MapperEntity] = MapperEntity.objects.filter(
                    mapper_id=league["leagueId"]
                )

                if not entities:
                    continue

                for league_entity in entities:
                    teams_in_lh: List[TeamHistory] = TeamHistory.objects.filter(
                        league_history=league_entity.target.leaguehistory,
                        team__club__voivodeship_obj__isnull=False,
                    )
                    if not teams_in_lh:
                        continue

                    zpn = teams_in_lh[0].team.club.voivodeship_obj
                    try:
                        zpn_id: str = ZPNs[zpn.name]
                    except KeyError:
                        continue

                    play_entity = league_entity.target.get_entity(
                        related_type="play_entity"
                    )
                    league_obj = LeagueMappingSchema(
                        league_id=league["leagueId"],
                        play_id=play_entity.mapper_id,
                        voivodeship_id=zpn_id,
                        season=league_entity.target.leaguehistory.season.name,
                        gender=gender.value,
                    )

                    url: str = compose_league_url(league_obj, div)
                    print(f"New url: {url}")

                    play_entity.url = url
                    league_entity.url = url
                    league_entity.save()
                    play_entity.save()
