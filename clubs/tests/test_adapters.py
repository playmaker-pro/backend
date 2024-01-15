# import logging
#
# import pytest
# from django.test import TestCase
#
# from clubs.services import TeamAdapter
# from profiles import models
# from roles import definitions
# from users.models import User
# from utils import testutils as utils
#
# utils.silence_explamation_mark()

# todo (rkeisk): that is not being used anyware
# class TestTeamAdapter(TestCase):
#     def setUp(self):
#         self.team = utils.get_team()
#         self.adpt = TeamAdapter()

#     def test_team_can_be_found_by_name_and_mapping(self):
#         assert self.team == self.adpt.match_name_or_mapping("XXX")
#         assert self.team == self.adpt.match_name_or_mapping("YYY")
#         assert self.team == self.adpt.match_name_or_mapping("TEAMX")


# todo (rkeisk): that is not being used anyware
# class ClubClubAdapter(TestCase):
#     def setUp(self):
#         self.club = utils.get_club()
#         self.adpt = ClubAdapter()

#     def test_team_can_be_found_by_name_and_mapping(self):
#         print(self.club.mapping, self.club.name)
#         assert self.club == self.adpt.match_name_or_mapping("XXX")
#         assert self.club == self.adpt.match_name_or_mapping("YYY")
#         assert self.club == self.adpt.match_name_or_mapping("CLUBX")
