import pytest

from django.test import TestCase
from notifications import models
from users.models import User
from roles import definitions
import logging

from users.models import User


class ClubTeamDisplays(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='username', declared_role=definitions.PLAYER_SHORT)

    def test_with_new_user_we_should_create_user_notifications(self):
        models.NotificationSetting.objects.get(user_id=self.user.id)

