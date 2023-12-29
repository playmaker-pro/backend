from django.test import TestCase

from utils import testutils as utils

utils.silence_explamation_mark()


class ClubTeamDisplays(TestCase):
    def setUp(self):
        self.team = utils.get_team()

    def test_team_level_displays(self):
        assert self.team.display_team == "TEAMX"
        assert self.team.display_club == "CLUBX"
        assert self.team.display_voivodeship == "VIVOX"
        assert self.team.display_seniority == "SENIORITYX"
        assert self.team.display_gender == "GENDERX"
