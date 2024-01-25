import factory

from inquiries import models as _models
from inquiries.plans import basic_plan
from utils.factories import UserFactory as _UserFactory


class InquiryRequestFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.InquiryRequest

    sender = factory.SubFactory(_UserFactory)
    recipient = factory.SubFactory(_UserFactory)


class InquiryPlanFactory(factory.django.DjangoModelFactory):
    _plan = basic_plan

    class Meta:
        model = _models.InquiryPlan
        django_get_or_create = ("name",)

    name = _plan.name
    description = _plan.description
    limit = _plan.limit
    default = _plan.default


class UserInquiryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.UserInquiry
        django_get_or_create = ("user",)

    user = factory.SubFactory(_UserFactory)
    plan = factory.SubFactory(InquiryPlanFactory)
