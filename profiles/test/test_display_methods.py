import pytest
from django.test import TestCase
from profiles import models
from users.models import User
from roles import definitions
import logging
from clubs.models import Team, Club
from profiles.test import utils


utils.silence_explamation_mark()


class ClubTeamDisplays(TestCase):
    def setUp(self):
        self.team = utils.get_club()

    def test_team_level_displays(self):
        assert self.team.display_team == 'TEAMX'
        assert self.team.display_club == 'CLUBX'
        assert self.team.display_voivodeship == 'VIVOX'
        assert self.team.display_league == 'LEAGUEX'
        assert self.team.display_seniority == 'SENIORITYX'
        assert self.team.display_gender == 'GENDERX'

    def test_club_level_displays(self):
        # assert self.team.club.display_team == 'TEAMX'
        assert self.team.club.club.display_club == 'CLUBX'
        assert self.team.club.club.display_voivodeship == 'VIVOX'


class ProfileLevelDisplay(TestCase):
    def setUp(self):
        self.club = utils.get_verified_user_club()
        self.coach = utils.get_verified_user_coach()
        
        assert self.coach.is_verified is True
        assert self.club.is_verified is True
        print(f'----> setUp {self.club.state} {self.coach.state}')

    def test_profile_club_level_displays(self):
        u = self.club 

        assert u.profile.display_club == 'CLUBX'
        assert u.profile.display_voivodeship == 'VIVOX'

    def test_profile_coach_level_displays(self):
        u = self.coach 
        assert u.profile.display_team == 'TEAMX'
        assert u.profile.display_club == 'CLUBX'
        assert u.profile.display_voivodeship == 'VIVOX'
        assert u.profile.display_league == 'LEAGUEX'
        assert u.profile.display_league == 'LEAGUEX'
        assert u.profile.display_seniority == 'SENIORITYX'
        assert u.profile.display_gender == 'GENDERX'
