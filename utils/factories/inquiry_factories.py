import factory

from inquiries import models as _models
from utils.factories import UserFactory as _UserFactory


class InquiryRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.InquiryRequest

    sender = factory.SubFactory(_UserFactory)
    recipient = factory.SubFactory(_UserFactory)


class InquiryPlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.InquiryPlan
        django_get_or_create = ("default",)

    name = "BASIC"
    description = "Basic plan"
    type_ref = "BASIC"
    limit = 2
    default = True


class UserInquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.UserInquiry
        django_get_or_create = ("user",)

    user = factory.SubFactory(_UserFactory)
    plan = factory.SubFactory(InquiryPlanFactory)

