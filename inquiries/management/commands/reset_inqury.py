from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from inquiries.models import UserInquiry

User = get_user_model()


class Command(BaseCommand):
    help = "Reset users limits."

    def handle(self, *args, **options):
        for inq in UserInquiry.objects.all():
            inq.reset_inquiries()
