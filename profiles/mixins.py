from functools import cached_property, lru_cache

from .utils import conver_vivo_for_api, supress_exception


class SoccerDisplayMixin:
    @property
    def display_club(self):
        if self.club_raw:
            return self.club_raw
        return self.club

    @property
    def display_team(self):
        if self.team_raw:
            return self.team_raw
        return self.team

    @property
    def display_league(self):
        if self.league_raw:
            return self.league_raw
        return self.league

    @property
    def display_voivodeship(self):
        if self.voivodeship_raw:
            return conver_vivo_for_api(self.voivodeship_raw)
        return conver_vivo_for_api(self.voivodeship)


class TeamObjectsDisplayMixin:
    """Exposes values to display on UI.

    Profile's team based mixin - object who has a team_object and club_object
    When link is broken excpetion should be supressed
    """

    def get_team_object_or_none(self):
        if self.team_object:
            return self.team_object

    @cached_property
    def get_team_object(self):
        return self.team_object

    @supress_exception
    @property
    def club_object(self):
        if self.get_team_object:
            return self.get_team_object.club

    @property
    @supress_exception
    def display_club(self):
        return self.get_team_object.club.display_club

    @property
    @supress_exception
    def display_team(self):
        return self.get_team_object.display_team

    @property
    @supress_exception
    def display_seniority(self):
        return self.get_team_object.display_seniority

    @property
    @supress_exception
    def display_name_junior(self):
        return self.get_team_object.display_name_junior

    @property
    @supress_exception
    def display_gender(self):
        return self.get_team_object.display_gender

    @property
    @supress_exception
    def display_voivodeship(self):
        return self.get_team_object.club.display_voivodeship

    @property
    @supress_exception
    def display_league(self):
        return self.get_team_object.display_league

    @property
    @supress_exception
    def display_league_top_parent(self):
        return self.get_team_object.display_league_top_parent

    @property
    @supress_exception
    def display_league_seniority_name(self):
        return self.get_team_object.display_league_seniority_name

    @property
    @supress_exception
    def display_league_group_name(self):
        return self.get_team_object.display_league_group_name

    @property
    @supress_exception
    def display_league_voivodeship(self):
        return self.get_team_object.display_league_voivodeship

    @property
    @supress_exception
    def get_league_permalink(self):
        return self.get_team_object.get_league_permalink

    @property
    @supress_exception
    def get_team_permalink(self):
        return self.get_team_object.get_permalink()
