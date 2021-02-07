
import logging

import pytest
from django.test import TestCase
from profiles import models
from roles import definitions
from users.models import User
from utils import testutils as utils
from clubs.services import TeamAdapter, ClubAdapter


utils.silence_explamation_mark()


class TestClubAdapter(TestCase):
    def setUp(self):
        self.team = utils.get_team()
        self.adpt = TeamAdapter()

    def test_team_can_be_found_by_name_and_mapping(self):
        assert self.team == self.adpt.match_name_or_mapping('XXX')
        assert self.team == self.adpt.match_name_or_mapping('YYY')
        assert self.team == self.adpt.match_name_or_mapping('TEAMX')


class ClubClubAdapter(TestCase):
    def setUp(self):
        self.club = utils.get_team()
        self.adpt = ClubAdapter()

    def test_team_can_be_found_by_name_and_mapping(self):
        assert self.club == self.adpt.match_name_or_mapping('XXX')
        assert self.club == self.adpt.match_name_or_mapping('YYY')
        assert self.club == self.adpt.match_name_or_mapping('CLUBX')
