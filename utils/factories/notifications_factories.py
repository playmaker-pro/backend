import factory
from django.contrib.contenttypes.models import ContentType

from notifications.models import Notification

from . import user_factories


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    user = factory.SubFactory(user_factories.UserFactory)
    notification_type = factory.Iterator(Notification.NotificationType.values)
    event_type = factory.Faker("word")
    details = factory.Dict({})
    content = factory.Faker("sentence")
    is_read = False
    object_id = factory.SelfAttribute("user.id")  # Set default object_id to user's ID
    content_type = factory.LazyAttribute(
        lambda obj: ContentType.objects.get_for_model(obj.user.__class__)
    )

    @factory.post_generation
    def set_content_object(self, create, extracted, **kwargs):
        if extracted:
            self.content_type = ContentType.objects.get_for_model(extracted)
            self.object_id = extracted.pk
            self.save()
