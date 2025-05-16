from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class GenericFollowManager(models.Manager):
    def with_existing_objects(self, user):
        """
        Return GenericFollow instances where the followed object exists.
        """
        return [
            follow
            for follow in self.get_queryset().filter(user=user)
            if follow.followed_object_exists()
        ]


class GenericFollow(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="followed_by"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)
    objects = GenericFollowManager()

    def followed_object_exists(self) -> bool:
        """
        Check if the followed object exists.
        """
        ModelClass = self.content_type.model_class()
        return ModelClass.objects.filter(pk=self.object_id).exists()

    def __str__(self):
        return f"{self.user} -- follows -- {self.content_object.user}"
