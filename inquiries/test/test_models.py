import logging
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import TestCase

from inquiries.models import InquiryPlan, InquiryRequest, UserInquiry
from roles import definitions
from users.models import User
from utils import testutils as utils

utils.silence_explamation_mark()


class InitialClassCreationTest(TestCase):
    """
    When Coach user is created we would like to add different plan than Player.

    When Player is created ->  default plan attached
    When Coach is created -> coache's plan should be added
    """

    def setUp(self):
        with pytest.raises(InquiryPlan.DoesNotExist):
            InquiryPlan.objects.get(default=True)
        utils.create_system_user()
        self.player = User.objects.create(
            email="username-player", declared_role=definitions.PLAYER_SHORT
        )
        self.coach = User.objects.create(
            email="username-coach", declared_role=definitions.COACH_SHORT
        )

    def test_basic_plans_from_settings_shoudl_exists(self):
        for args in settings.INQUIRIES_INITAL_PLANS:
            InquiryPlan.objects.get(name=args["name"], default=args["default"])

    def test_player_user_should_have_basic_plan(self):
        assert self.player.userinquiry.plan.default is True


class ModelMethodsRequest(TestCase):
    def setUp(self):
        with pytest.raises(InquiryPlan.DoesNotExist):
            InquiryPlan.objects.get(default=True)
        utils.create_system_user()
        self.player = User.objects.create(
            email="username-player", declared_role=definitions.PLAYER_SHORT
        )
        self.coach = User.objects.create(
            email="username-coach", declared_role=definitions.COACH_SHORT
        )
        self.request = InquiryRequest(sender=self.coach, recipient=self.player)

    # DEPRECATED: PM-1015
    # @patch("stats.adapters.player.PlayerAdapter.__init__", "")
    # def test__status_display(self):
    #     assert self.request.status == InquiryRequest.STATUS_NEW

    def test__send_status_differs_from_role(self):
        self.request.send()
        self.request.save()
        assert self.request.status == InquiryRequest.STATUS_SENT
        assert self.request.status_display_for(self.player) == "OTRZYMANO"
        assert self.request.status_display_for(self.coach) == "WYSŁANO"
