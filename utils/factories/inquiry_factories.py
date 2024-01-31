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
        django_get_or_create = ("name",)

    name = "Basic"
    description = "Basic plan"
    limit = 5
    default = True


class UserInquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.UserInquiry
        django_get_or_create = ("user",)

    user = factory.SubFactory(_UserFactory)
    plan = factory.SubFactory(InquiryPlanFactory)


class InquiryContactFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.InquiryContact
        django_get_or_create = ("user",)

    user = factory.SubFactory(_UserFactory)
