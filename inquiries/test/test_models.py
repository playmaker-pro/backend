import datetime
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import TestCase
from django.utils import timezone

from inquiries.models import (
    InquiryLogMessage,
    InquiryPlan,
    InquiryRequest,
    UserInquiryLog,
)
from premium.models import PremiumType
from roles import definitions
from users.models import User
from utils import testutils as utils
from utils.factories import CoachProfileFactory, PlayerProfileFactory
from utils.factories.inquiry_factories import InquiryRequestFactory
from utils.factories.user_factories import UserFactory

utils.silence_explamation_mark()


class TestModels(TestCase):
    """
    When Coach user is created we would like to add different plan than Player.

    When Player is created ->  default plan attached
    When Coach is created -> coache's plan should be added
    """

    def setUp(self):
        self.player = PlayerProfileFactory(
            user__email="username-player", user__declared_role=definitions.PLAYER_SHORT
        )
        self.coach = CoachProfileFactory(
            user__email="username-coach", user__declared_role=definitions.COACH_SHORT
        )

    def test_default_plan_should_exist(self):
        assert InquiryPlan.objects.get(default=True)

    def test_player_user_should_have_basic_plan(self):
        assert self.player.user.userinquiry.plan.default is True

    def test_plans_with_premium_profile(self):
        assert self.player.user.userinquiry.counter == 0
        assert self.player.user.userinquiry.limit == 2
        assert self.player.user.userinquiry.plan.type_ref == "BASIC"

        premium = self.player.premium_products.setup_premium_profile()

        assert self.player.has_premium_inquiries
        assert self.player.user.userinquiry.counter == 0
        assert self.player.user.userinquiry.limit == 12
        assert self.player.user.userinquiry.plan.type_ref == "BASIC"

        self.player.user.userinquiry.increment()

        assert self.player.user.userinquiry.counter == 1
        assert self.player.user.userinquiry.limit == 12
        assert self.player.user.userinquiry.counter_raw == 0
        assert self.player.user.userinquiry.premium_inquiries.current_counter == 1

        plan = InquiryPlan.objects.get(type_ref="PREMIUM_INQUIRIES_XXL")
        self.player.user.userinquiry.set_new_plan(plan)
        self.player.user.userinquiry.increment()

        assert self.player.user.userinquiry.counter == 2
        assert self.player.user.userinquiry.limit == 22
        assert self.player.user.userinquiry.counter_raw == 0
        assert self.player.user.userinquiry.premium_inquiries.current_counter == 2

        with patch(
            "django.utils.timezone.now",
            return_value=timezone.now() + timedelta(days=31),
        ):
            assert not self.player.has_premium_inquiries
            assert self.player.user.userinquiry.counter == 0
            assert self.player.user.userinquiry.limit == 12

    def test_premium_inquiries_will_refresh(self):
        assert self.player.user.userinquiry.counter == 0
        assert self.player.user.userinquiry.limit == 2
        assert not self.player.has_premium_inquiries

        self.player.premium_products.setup_premium_profile(PremiumType.YEAR)

        assert self.player.has_premium_inquiries
        assert self.player.user.userinquiry.counter == 0
        assert self.player.user.userinquiry.limit == 12

        self.player.user.userinquiry.increment()
        self.player.user.userinquiry.increment()

        assert self.player.user.userinquiry.counter == 2
        assert self.player.user.userinquiry.limit == 12
        assert self.player.user.userinquiry.premium_inquiries.current_counter == 2
        assert (
            self.player.user.userinquiry.premium_inquiries.counter_updated_at.date()
            == timezone.now().date()
        )

        with patch(
            "django.utils.timezone.now",
            return_value=timezone.now() + timedelta(days=31),
        ):
            assert self.player.has_premium_inquiries
            assert self.player.user.userinquiry.counter == 0
            assert self.player.user.userinquiry.limit == 12
            assert self.player.user.userinquiry.premium_inquiries.current_counter == 0
            assert (
                self.player.user.userinquiry.premium_inquiries.counter_updated_at.date()
                == timezone.now().date()
            )


class ModelMethodsRequest(TestCase):
    def setUp(self):
        self.player = User.objects.create(
            email="username-player", declared_role=definitions.PLAYER_SHORT
        )
        self.coach = User.objects.create(
            email="username-coach", declared_role=definitions.COACH_SHORT
        )
        self.request = InquiryRequest(sender=self.coach, recipient=self.player)

    def test__send_status_differs_from_role(self):
        self.request.send()
        self.request.save()
        assert self.request.status == InquiryRequest.STATUS_SENT
        assert self.request.status_display_for(self.player) == "OTRZYMANO"
        assert self.request.status_display_for(self.coach) == "WYSŁANO"


@pytest.mark.usefixtures("silence_mails")
class RewardOutdatedInquiryRequest(TestCase):
    def setUp(self) -> None:
        sender = UserFactory(userpreferences__gender="M")
        recipient = UserFactory(userpreferences__gender="K")
        self.inquiry_request = InquiryRequestFactory(sender=sender, recipient=recipient)
        sender.save()
        recipient.save()

        return super().setUp()

    def test_reward_sender(self) -> None:
        """
        Test if reward_sender method works correctly.
        Create InquiryRequest, set it's created_at to 30 days ago.
        reward_sender() should mark this inquiry as outdated as so
        should create UserInquiryLog as OUTDATED and decrease UserInquiry counter.
        """
        month_ago = datetime.datetime.now() - datetime.timedelta(days=30)

        self.inquiry_request.created_at = month_ago
        self.inquiry_request.save()
        self.inquiry_request.refresh_from_db()

        assert self.inquiry_request.sender.userinquiry.counter == 1

        self.inquiry_request.reward_sender()

        assert self.inquiry_request.sender.userinquiry.counter == 0
        assert (
            UserInquiryLog.objects.get(
                log_owner=self.inquiry_request.sender.userinquiry,
                ref=self.inquiry_request,
            ).message.log_type
            == InquiryLogMessage.MessageType.OUTDATED
        )
