import factory as _factory

from mailing import models as _models


class UserEmailOutboxFactory(_factory.django.DjangoModelFactory):
    class Meta:
        model = _models.UserEmailOutbox

    recipient = _factory.Faker("email")
    email_type = _factory.Faker("word")
