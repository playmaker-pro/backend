import random
import string

from django.contrib.auth import get_user_model
from connector.scripts.base import BaseCommand
from allauth.account.models import EmailAddress
from profiles.models import PlayerProfile, CoachProfile, ClubProfile

User = get_user_model()


class Command(BaseCommand):

    PHONE_NR = "111 222 333"

    def random_email_address(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(12)) + "@playmaker.pro"

    def handle(self):

        print("------------------------------------------------------------------------------")
        print("  THIS COMMAND WILL PERMAMENTLY DELETE ALL EMAIL ADDRESSES AND PHONE NUMBERS  ")
        print("               MAKE SURE YOU ARE WORKING ON DEV/QA DATABASE                   ")
        print("                      DO NOT USE IT ON PRODUCTION ENV                         ")
        print("                    TO CONFIRM AND RUN SCRIPT, TYPE: OK                       ")
        print("------------------------------------------------------------------------------")

        user_input = input(">> ").upper()
        if user_input == "OK":
            self.wipe_sensitive_data()

    def wipe_sensitive_data(self):

        users = User.objects.filter(is_staff=False, is_superuser=False)
        for user in users:
            user.email = self.random_email_address()
            user.save()

        for email_obj in EmailAddress.objects.all():
            email_obj.email = self.random_email_address()
            email_obj.save()

        for playerprofile in PlayerProfile.objects.all():
            playerprofile.phone = self.PHONE_NR
            playerprofile.agent_phone = self.PHONE_NR
            playerprofile.save()

        for coachprofile in CoachProfile.objects.all():
            coachprofile.phone = self.PHONE_NR
            coachprofile.save()

        for clubprofile in ClubProfile.objects.all():
            clubprofile.phone = self.PHONE_NR
            clubprofile.save()

