from typing import Any

from rest_framework import serializers

from followers.models import GenericFollow
from profiles.api.managers import SerializersManager


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenericFollow
        fields = []

    def get_profile(self, instance: GenericFollow) -> Any:
        raise NotImplementedError()

    def to_representation(self, instance: GenericFollow) -> dict:
        """
        Object instance -> Dict of primitive datatypes.
        """
        profile = self.get_profile(instance)
        serializer_class = self.get_serializer_for_model(profile.__class__.__name__)
        serializer = serializer_class(profile, context=self.context)

        return serializer.data

    def get_serializer_for_model(self, model_name: str):
        """
        Retrieve the serializer class from a manager based on the model name.
        """
        return SerializersManager().get_serializer(model_name)


class FollowedListSerializer(FollowSerializer):
    """
    Serializer for listing followed objects.
    """

    def get_profile(self, instance: GenericFollow) -> Any:
        """
        Return the profile of the user who is being followed.
        """
        return instance.content_object


class FollowingListSerializer(FollowSerializer):
    """
    Serializer for listing followers.
    """

    def get_profile(self, instance: GenericFollow) -> Any:
        """
        Return the profile of the user who is following.
        """
        return instance.user.profile
