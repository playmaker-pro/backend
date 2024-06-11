import factory
from django.contrib.contenttypes.models import ContentType

from followers.models import GenericFollow
from utils.factories import ProfileFactory, TeamFactory, UserFactory

from .base import CustomObjectFactory


class GenericFollowFactory(CustomObjectFactory):
    class Meta:
        model = GenericFollow

    user = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def content_type(self):
        return ContentType.objects.get_for_model(ProfileFactory._meta.model)

    @factory.lazy_attribute
    def object_id(self):
        followed_object = ProfileFactory.create()
        return followed_object.id
