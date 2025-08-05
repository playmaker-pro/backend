from django.core.management.base import BaseCommand

from inquiries.models import InquiryRequest


class Command(BaseCommand):
    help = "Reward senders and notify recipients of outdated inquiries."

    def handle(self, *args, **options) -> None:
        """
        CASE1: Iterate over all READ inquiries that are older than 7 days
        and reward the sender with one bonus InquiryReqeust.

        CASE2: Iterate over all READ inquiries that are:
            - older than 3 days and recipient has not been notified yet
              about attempted inquiry
            - older than 6 days and recipient got already 1 reminder

        CASE3: Iterate over all UserInquiry objects, check if they reached the limit:
             If so: send email and create notification about exhausted inquiry pool.
             - email once per round
             - notification once per month
        """
        # CASE1
        for inquiry in InquiryRequest.objects.to_notify_sender_about_outdated():
            inquiry.reward_sender()

        # CASE2
        for inquiry in InquiryRequest.objects.to_remind_recipient_about_outdated():
            inquiry.notify_recipient_about_outdated()
