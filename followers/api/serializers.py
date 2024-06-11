from rest_framework import serializers

from followers.models import GenericFollow
from profiles.api.managers import SerializersManager


class FollowSerializers(serializers.ModelSerializer):

    class Meta:
        model = GenericFollow
        fields = []

    def to_representation(self, instance: GenericFollow) -> dict:
        """
        Object instance -> Dict of primitive datatypes.
        """
        followed_object = instance.content_type.get_object_for_this_type(
            pk=instance.object_id)
        model_name = followed_object.__class__.__name__
        serializer_class = self.get_serializer_for_model(model_name)

        if serializer_class:
            # Use the appropriate serializer for the followed object
            context = self.context
            serializer = serializer_class(followed_object, context=context)
            return serializer.data
        else:
            # Handle cases where no serializer is found
            return {"error": "No serializer available for this object type"}

    def get_serializer_for_model(self, model_name: str):
        """
        Retrieve the serializer class from a manager based on the model name.
        """
        return SerializersManager().get_serializer(model_name)

