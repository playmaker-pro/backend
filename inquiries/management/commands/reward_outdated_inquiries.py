from django.core.management.base import BaseCommand

from inquiries.models import InquiryRequest


class Command(BaseCommand):
    help = "Reward users that sent outdated inquiries."

    def handle(self, *args, **options) -> None:
        """
        Iterate over all inquiries that are outdated
        and reward the sender with one bonus InquiryReqeust.
        """
        for inquiry in InquiryRequest.objects.to_notify_about_outdated():
            inquiry.reward_sender()
