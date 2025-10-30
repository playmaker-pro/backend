import logging

from django.core.management.base import BaseCommand

from mailing.schemas import EmailTemplateRegistry
from mailing.services import MailingService
from mailing.utils import build_email_context
from users.models import User

logger = logging.getLogger("commands")


class Command(BaseCommand):
    """
    Command to send confirmation links to non-verified users.
    """

    help = "Send confirmation links to non-verified users"

    def handle(self, *args, **options):
        users = User.objects.filter(is_email_verified=False)

        for user in users:
            mail_schema = EmailTemplateRegistry.CONFIRM_EMAIL
            context = build_email_context(user, mailing_type=mail_schema.mailing_type)
            MailingService(mail_schema(context)).send_mail(user)
