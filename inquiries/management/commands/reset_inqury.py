from django.core.management.base import BaseCommand, CommandError

from inquiries.models import UserInquiry
from profiles.views import (
    get_profile_model,
)  # @todo this shoudl goes to utilities, views and commands are using this utility
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):
    help = "Reset users limits."

    def handle(self, *args, **options):
        for inq in UserInquiry.objects.all():
            inq.reset()
