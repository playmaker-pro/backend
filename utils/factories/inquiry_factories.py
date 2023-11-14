import factory

from inquiries.models import InquiryRequest
from utils.factories import UserFactory


class InquiryRequestFactory(factory.Factory):
    class Meta:
        model = InquiryRequest

    sender = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
