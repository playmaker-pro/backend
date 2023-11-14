from django.test import TestCase

from utils.factories.user_factories import UserFactory
from utils.testutils import create_system_user


class TestSendEmails(TestCase):
    def setUp(self):
        create_system_user()
        self.user1 = UserFactory.objects.create(mute_signals=False)
        self.user2 = UserFactory.objects.create(mute_signals=False)
        # self.inquiry_request = InquiryRequestFactory(
        #     sender=self.user1, recipient=self.user2
        # )
