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


class InquiryLogMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.InquiryLogMessage

    log_body = "Hello <>!"
    email_title = "Test Email Title with #r#"
    email_body = "Plain email content for <>"
    email_body_html = "<strong>HTML content for #rb#</strong>"
    send_mail = False
    log_type = _models.InquiryLogMessage.MessageType.ACCEPTED


class UserInquiryLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = _models.UserInquiryLog

    log_owner = factory.SubFactory(UserInquiryFactory)
    related_with = factory.LazyAttribute(lambda o: UserInquiryFactory(user=o.ref.sender))
    ref = factory.SubFactory(InquiryRequestFactory)
    message = factory.SubFactory(InquiryLogMessageFactory)

    @factory.lazy_attribute
    def related_with(self):
        return UserInquiryFactory(user=self.ref.sender)
