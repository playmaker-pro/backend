import logging
import random
import string

import django.core.exceptions
from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandParser

from app.errors import ForbiddenInProduction
from backend.settings.config import Environment
from profiles.models import ClubProfile, CoachProfile, PlayerProfile

User = get_user_model()
logger: logging.Logger = logging.getLogger("mocker")


class Command(BaseCommand):
    PHONE_NR = "111 222 333"

    def random_email_address(self):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(12)) + "@playmaker.pro"

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Parse arguments:
        --force - force run script without warning
        """
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="Force run script, avoid warning",
        )

    def is_production(self) -> bool:
        """Check current configuration,"""
        if settings.CONFIGURATION is Environment.PRODUCTION:
            raise ForbiddenInProduction

    def handle(self, **options):
        self.is_production()
        if options.get("force", False):
            return self.wipe_sensitive_data()

        print(
            "------------------------------------------------------------------------------"
        )
        print(
            "  THIS COMMAND WILL PERMAMENTLY DELETE ALL EMAIL ADDRESSES AND PHONE NUMBERS  "
        )
        print(
            "               MAKE SURE YOU ARE WORKING ON DEV/QA DATABASE                   "
        )
        print(
            "                      DO NOT USE IT ON PRODUCTION ENV                         "
        )
        print(
            "                    TO CONFIRM AND RUN SCRIPT, TYPE: OK                       "
        )
        print(
            "------------------------------------------------------------------------------"
        )

        user_input = input(">> ").upper()
        if user_input == "OK":
            return self.wipe_sensitive_data()

    def wipe_sensitive_data(self):
        users = User.objects.filter(is_staff=False, is_superuser=False)
        for user in users:
            old_email = user.email
            new_email = self.random_email_address()
            user.email = new_email
            try:
                user.save()
                logger.info(
                    f"Changed <User, ID: {user.pk}> email: {old_email} -> {new_email}."
                )
            except django.core.exceptions.ObjectDoesNotExist as e:
                logger.error(e)

        for email_obj in EmailAddress.objects.all():
            old_email = email_obj.email
            new_email = self.random_email_address()
            email_obj.email = new_email
            try:
                email_obj.save()
                logger.info(
                    f"Changed <EmailAddress, ID: {email_obj.pk}> email: {old_email} -> {new_email}."
                )
            except django.core.exceptions.ObjectDoesNotExist as e:
                logger.error(e)

        for playerprofile in PlayerProfile.objects.all():
            old_phone = playerprofile.phone
            old_agent_phone = playerprofile.agent_phone
            playerprofile.phone = self.PHONE_NR
            playerprofile.agent_phone = self.PHONE_NR
            try:
                playerprofile.save()
                logger.info(
                    f"Changed <PlayerProfile, ID: {playerprofile.pk}> phone number: {old_phone} -> {self.PHONE_NR}"
                )
                logger.info(
                    f"Changed <PlayerProfile, ID: {playerprofile.pk}> agent_phone number: {old_agent_phone} -> {self.PHONE_NR}"
                )
            except django.core.exceptions.ObjectDoesNotExist as e:
                logger.error(e)

        for coachprofile in CoachProfile.objects.filter(phone__isnull=False):
            old_phone = coachprofile.phone
            coachprofile.phone = self.PHONE_NR
            try:
                coachprofile.save()
                logger.info(
                    f"Changed <CoachProfile, ID: {coachprofile.pk}> phone number: {old_phone} -> {self.PHONE_NR}"
                )
            except django.core.exceptions.ObjectDoesNotExist as e:
                logger.error(e)

        for clubprofile in ClubProfile.objects.filter(phone__isnull=False):
            old_phone = clubprofile.phone
            clubprofile.phone = self.PHONE_NR
            try:
                clubprofile.save()
                logger.info(
                    f"Changed <ClubProfile, ID: {clubprofile.pk}> phone number: {old_phone} -> {self.PHONE_NR}"
                )
            except django.core.exceptions.ObjectDoesNotExist as e:
                logger.error(e)
