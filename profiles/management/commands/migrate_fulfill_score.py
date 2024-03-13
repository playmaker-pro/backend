from django.core.management.base import BaseCommand

from profiles.managers import ProfileManager
from profiles.models import PROFILE_MODELS


class Command(BaseCommand):
    """
    Populate the data_fulfill_status field for all profiles.

    This command iterates over all profile models specified in PROFILE_MODELS
    and calculates the data fulfillment status for each profile using the
    ProfileManager's get_data_score method. The calculated status is then
    assigned to the data_fulfill_status field of each profile instance and
    saved to the database.

    The data fulfillment status is determined based on various acceptance
    criteria, including verification stage completion and the presence of
    essential profile data such as last name, first name, birth date, etc.
    Additionally, profiles may achieve level 0 fulfillment if they have either
    a populated profile picture or a pm_score value.
    """

    def handle(self, *args, **kwargs) -> None:
        loop_able_profiles = []

        for ProfileModel in PROFILE_MODELS:
            instances = list(ProfileModel.objects.all())
            loop_able_profiles.extend(instances)

        for profile in loop_able_profiles:
            manager = ProfileManager()
            profile.data_fulfill_status = manager.get_data_score(profile)
            profile.save()
