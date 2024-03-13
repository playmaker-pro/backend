from typing import List

from django.core.management.base import BaseCommand

from profiles.managers import ProfileManager
from profiles.models import PROFILE_MODELS


class Command(BaseCommand):
    """
    Match players with their videos based on data from csv file
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
