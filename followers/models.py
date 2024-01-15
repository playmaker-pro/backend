from django.conf import settings
from django.db import models


class Item(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="items")
    source_url = models.TextField()
    message = models.TextField(blank=True, null=True)
    pin_count = models.IntegerField(default=0)

    # class Meta:
    #    db_table = 'pinterest_example_item'


class Pin(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    influencer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="influenced_pins",
    )
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Muted cuz we don't use stream framework anymore

    # def create_activity(self):
    #     print("ere")
    #     # from stream_framework.activity import Activity
    #
    #     # from .verbs import Pin as PinVerb
    #
    #     activity = Activity(
    #         self.user.id,
    #         PinVerb,
    #         self.id,
    #         self.influencer.id,
    #         time=make_naive(self.created_at, pytz.utc),
    #         extra_context=dict(item_id=200),
    #     )
    #     print("activity", activity)
    #     return activity


class Follow(models.Model):

    """
    A simple table mapping who a user is following.
    For example, if user is Kyle and Kyle is following Alex,
    the target would be Alex.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following_set"
    )

    target = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="follower_set"
    )

    created_at = models.DateTimeField(auto_now_add=True)


from clubs.models import Team


class FollowTeam(models.Model):

    """
    A simple table mapping who a user is following.
    For example, if user is Kyle and Kyle is following Alex,
    the target would be Alex.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_team_set",
    )

    target = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="follower_team_set"
    )

    created_at = models.DateTimeField(auto_now_add=True)


from . import verbs
