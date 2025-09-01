# from typing import List

# from django.conf import settings
# from django.contrib.auth import get_user_model
# from django.core.management import call_command
# from django.test import TestCase

# from app import errors
# from app.management.commands.mock_database import Command as Mocker
# from backend.settings.config import Environment
# from clubs import models as clubs_models
# from profiles import models as profiles_models
# from utils.testutils import RunWithDifferentEnvironment

# User = get_user_model()


# class TestMockDatabaseCommand(TestCase):
#     @classmethod
#     def call(cls, *args) -> None:
#         """Method's calling script with given arguments"""
#         call_command("mock_database", *args)

#     @property
#     def script_passed(self) -> User:
#         """
#         Script always starts with creating superuser
#         If superuser doesn't exist - something went wrong with script
#         """
#         return User.objects.filter(is_superuser=True)

#     @property
#     def users(self) -> List[User]:
#         """Get all common users"""
#         return User.objects.filter(is_superuser=False).exclude(
#             email=settings.SYSTEM_USER_EMAIL
#         )

#     @property
#     def seasons(self) -> List[clubs_models.Season]:
#         """Get all seasons"""
#         return clubs_models.Season.objects.all()

#     @property
#     def playerprofiles(self) -> List[profiles_models.PlayerProfile]:
#         """Get all player_profiles"""
#         return profiles_models.PlayerProfile.objects.all()

#     @property
#     def coachprofiles(self) -> List[profiles_models.CoachProfile]:
#         """Get all coach_profiles"""
#         return profiles_models.CoachProfile.objects.all()

#     @property
#     def clubprofiles(self) -> List[profiles_models.ClubProfile]:
#         """Get all club_profiles"""
#         return profiles_models.ClubProfile.objects.all()

#     @property
#     def scoutprofiles(self) -> List[profiles_models.ScoutProfile]:
#         """Get all scout_profiles"""
#         return profiles_models.ScoutProfile.objects.all()

#     @property
#     def guestprofiles(self) -> List[profiles_models.GuestProfile]:
#         """Get all guest_profiles"""
#         return profiles_models.GuestProfile.objects.all()

#     @property
#     def clubs(self) -> List[clubs_models.Club]:
#         """Get all clubs"""
#         return clubs_models.Club.objects.all()

#     @property
#     def teams(self) -> List[clubs_models.Team]:
#         """Get all teams"""
#         return clubs_models.Team.objects.all()

#     @property
#     def teamhistories(self) -> List[clubs_models.TeamHistory]:
#         """Get all team_histories"""
#         return clubs_models.TeamHistory.objects.all()

#     @property
#     def leagues(self) -> List[clubs_models.League]:
#         """Get all leagues"""
#         return clubs_models.League.objects.all()

#     @property
#     def leaguehistories(self) -> List[clubs_models.LeagueHistory]:
#         """Get all league_histories"""
#         return clubs_models.LeagueHistory.objects.all()

#     def test_stop_if_production_env(self) -> None:
#         """Set production environment temporarily, script should fail"""
#         with RunWithDifferentEnvironment(Environment.PRODUCTION, self.call) as _script:
#             assert isinstance(_script.run(), errors.ForbiddenInProduction)
#         assert not self.script_passed

#     def test_setup_all(self) -> None:
#         """Mock everything"""
#         count = 2
#         self.call("--all", "-count", count)

#         assert self.script_passed
#         assert self.users
#         assert self.playerprofiles
#         assert self.coachprofiles
#         assert self.clubprofiles
#         assert self.scoutprofiles
#         assert self.guestprofiles
#         assert self.seasons
#         assert self.clubs
#         assert self.teams
#         assert self.leagues
#         assert self.leaguehistories
#         assert self.teamhistories

#     def test_setup_profiles(self) -> None:
#         """Mock all profiles, users are created by itself"""

#         count = 2
#         self.call(
#             "--profiles",
#             "-count",
#             count,
#         )

#         assert self.script_passed
#         assert self.users
#         assert self.playerprofiles
#         assert self.coachprofiles
#         assert self.clubprofiles
#         assert self.scoutprofiles
#         assert self.guestprofiles
#         assert not self.seasons
#         assert not self.clubs
#         assert not self.teams
#         assert not self.leagues
#         assert not self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_users(self) -> None:
#         """Mock blank users"""

#         count = 2
#         self.call(
#             "--users",
#             "-count",
#             count,
#         )

#         assert self.script_passed
#         assert self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert not self.seasons
#         assert not self.clubs
#         assert not self.teams
#         assert not self.leagues
#         assert not self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_clubs(self) -> None:
#         """Mock teams and clubs"""

#         count = 2
#         self.call(
#             "--teams",
#             "-count",
#             count,
#         )

#         assert self.script_passed
#         assert not self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert self.seasons
#         assert self.clubs
#         assert self.teams
#         assert self.leagues
#         assert self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_leagues(self) -> None:
#         """Mock leagues"""

#         count = 2
#         self.call(
#             "--leagues",
#             "-count",
#             count,
#         )

#         assert self.script_passed
#         assert not self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert not self.seasons
#         assert not self.clubs
#         assert not self.teams
#         assert self.leagues
#         assert not self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_historical(self) -> None:
#         """Mock teams, clubs, seasons, leagues, leaguehistories, teamhistories"""
#         count = 2
#         self.call(
#             "--histories",
#             "-count",
#             count,
#         )

#         assert self.script_passed
#         assert not self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert self.seasons
#         assert self.clubs
#         assert self.teams
#         assert self.leagues
#         assert self.leaguehistories
#         assert self.teamhistories

#     def test_setup_admin_from_dict(self) -> None:
#         """Mock admin user from dictionary"""
#         data = {
#             "User": [
#                 {
#                     "first_name": "admin",
#                     "last_name": "admin",
#                     "password": "admin",
#                     "is_staff": True,
#                     "is_superuser": True,
#                     "email": "admin@playmaker.pro",
#                 }
#             ],
#         }
#         Mocker.mock_from_json(data)
#         assert self.script_passed
#         assert not self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert not self.seasons
#         assert not self.clubs
#         assert not self.teams
#         assert not self.leagues
#         assert not self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_profiles_from_dict(self) -> None:
#         """Mock each profile from dictionary"""
#         data = {
#             "PlayerProfile": [
#                 {
#                     "user": {
#                         "first_name": "gdsfg",
#                         "last_name": "gsdfg",
#                         "email": "gfdsgdsf@playmaker.pro",
#                     },
#                 }
#             ],
#             "CoachProfile": [
#                 {
#                     "user": {
#                         "first_name": "hfdg",
#                         "last_name": "xvcbxc",
#                         "email": "fasdf@playmaker.pro",
#                     },
#                 }
#             ],
#             "ClubProfile": [
#                 {
#                     "user": {
#                         "first_name": "asfas",
#                         "last_name": "dfasd",
#                         "email": "gsdfssgds@playmaker.pro",
#                     },
#                 }
#             ],
#             "ScoutProfile": [
#                 {
#                     "user": {
#                         "first_name": "qwe",
#                         "last_name": "rewr",
#                         "email": "rertwe@playmaker.pro",
#                     },
#                 }
#             ],
#             "GuestProfile": [
#                 {
#                     "user": {
#                         "first_name": "twert",
#                         "last_name": "Nortwertwewak",
#                         "email": "treyyy@playmaker.pro",
#                     },
#                 }
#             ],
#         }
#         Mocker.mock_from_json(data)

#         assert not self.script_passed  # we did not defined admin in data dictionary
#         assert self.users
#         assert self.playerprofiles
#         assert self.coachprofiles
#         assert self.clubprofiles
#         assert self.scoutprofiles
#         assert self.guestprofiles
#         assert self.seasons
#         assert not self.clubs
#         assert not self.teams
#         assert not self.leagues
#         assert not self.leaguehistories
#         assert not self.teamhistories

#     def test_setup_teamhistories_from_dict(self) -> None:
#         """Mock teamhistories from dictionary"""
#         data = {
#             "TeamHistory": [
#                 {
#                     "team": {"name": "Team 1", "club": {"name": "Club 1"}},
#                     "league_history": {
#                         "league": {"name": "League 1"},
#                         "season": {"name": "2022/2023"},
#                     },
#                 },
#                 {
#                     "team": {"name": "Team 1", "club": {"name": "Club 1"}},
#                     "league_history": {
#                         "league": {"name": "League 1"},
#                         "season": {"name": "2021/2022"},
#                     },
#                 },
#             ],
#         }
#         Mocker.mock_from_json(data)

#         assert not self.script_passed  # we did not defined admin in data dictionary
#         assert not self.users
#         assert not self.playerprofiles
#         assert not self.coachprofiles
#         assert not self.clubprofiles
#         assert not self.scoutprofiles
#         assert not self.guestprofiles
#         assert self.seasons
#         assert self.clubs
#         assert self.teams
#         assert self.leagues
#         assert self.leaguehistories
#         assert self.teamhistories
