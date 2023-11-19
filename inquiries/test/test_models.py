import datetime

from django.test import TestCase

from inquiries.models import (
    InquiryLogMessage,
    InquiryPlan,
    InquiryRequest,
    UserInquiryLog,
)
from inquiries.plans import basic_plan, premium_plan
from roles import definitions
from users.models import User
from utils import testutils as utils
from utils.factories.inquiry_factories import InquiryRequestFactory

utils.silence_explamation_mark()


class InitialClassCreationTest(TestCase):
    """
    When Coach user is created we would like to add different plan than Player.

    When Player is created ->  default plan attached
    When Coach is created -> coache's plan should be added
    """

    def setUp(self):
        self.player = User.objects.create(
            email="username-player", declared_role=definitions.PLAYER_SHORT
        )
        self.coach = User.objects.create(
            email="username-coach", declared_role=definitions.COACH_SHORT
        )

    def test_basic_plans_from_settings_shoudl_exists(self):
        for plan in [basic_plan, premium_plan]:
            InquiryPlan.objects.get(**plan.dict())

    def test_player_user_should_have_basic_plan(self):
        assert self.player.userinquiry.plan.default is True


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


class RewardOutdatedInquiryRequest(TestCase):
    def setUp(self) -> None:
        self.inquiry_request = InquiryRequestFactory()

        # Resave to bind signals
        sender, recipient = self.inquiry_request.sender, self.inquiry_request.recipient
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
            ).message.message_type
            == InquiryLogMessage.MessageType.OUTDATED
        )
