from django.test import TestCase
from users.models import User
from profiles import models


class ProfileMethodsTests(TestCase):

    def test_profile_is_complete(self):
        pass


class ProfileAssigmentDuringUserCreationTests(TestCase):

    def test_users_profile_assigment(self):
        model_map = {
            'T': (models.CoachProfile, 'is_coach'),
            'P': (models.PlayerProfile, 'is_player'),
            'C': (models.ClubProfile, 'is_club'),
            'G': (models.GuestProfile, 'is_guest'),
            'SK': (models.ScoutProfile, 'is_scout'),
            'R': (models.ParentProfile, 'is_parent'),
            'M': (models.ManagerProfile, 'is_manager'),
            'K': (models.FanProfile, 'is_fan'),
            'S': (models.StandardProfile, 'is_standard'),
        }

        for role, (expected_model, is_method) in model_map.items():
            print(role, expected_model, is_method)
            username = f'michal{role}'
            user = User.objects.create(email=username, declared_role=role)
            assert getattr(user, is_method) is True
            assert isinstance(user.profile, expected_model)

    def test_profile_ready_for_verification(self):
        
        user = User.objects.create(email='username', declared_role='T')
        user.profile.VERIFICATION_FIELDS = ['bio']
        assert user.profile.is_ready_for_verification() is False
        user.profile.bio = 'bbbbbbb'
        user.profile.save()
        assert user.is_waiting_for_verification is True
        assert user.profile.is_ready_for_verification() is True

    def test_profile_is_complete(self):
        
        user = User.objects.create(email='username', declared_role='T')
        user.profile.COMPLETE_FIELDS = ['bio']
        assert user.profile.is_complete is False
        assert user.profile.percentage_completion == 0
        user.profile.bio = 'bbbbbbb'
        user.profile.save()
        assert user.profile.is_complete is True
        assert user.profile.percentage_completion == 100