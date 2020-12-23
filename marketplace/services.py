import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications import mail # import mail_role_change_request, mail_admins_about_new_user
from .models import AnnouncementPlan, AnnouncementUserQuota
from datetime import timedelta

logger = logging.getLogger(__name__)


class MarketPlaceService:

    def create_default_plans(self):
        for plan_opts in settings.ANNOUNCEMENT_DEFAULT_PLANS:
            days = int(plan_opts['days'])
            plan_opts['days'] = timedelta(days=days)
            AnnouncementPlan.objects.get_or_create(**plan_opts)

    def get_plan(self):
        return self._get_default_plan()

    def set_user_announcement_plan(self, user):
        plan = self.get_plan()
        if plan is None:
            subject = f'Błąd podczas nadawania planu dla użytkownika {user.email}'
            message = 'Są 2 plany do ogłoszeń z ustawieniem jako "default"!\n\nNapraw problem i przypisz plan (AnnouncementUserQuota) temu użytkownikowi: \n\n{user.email}\n\n'
            mail.notify_error_admins(subject, message)
            return
        # @todo moze tu zabezpieczyc ze jak juz istnieje to nie dodwawac
        AnnouncementUserQuota.objects.create(plan=plan, user=user)
        logger.info(f'User {user} announcement plan created.')

    def _get_default_plan(self):
        try:
            return AnnouncementPlan.objects.get(default=True)
        except AnnouncementPlan.MultipleObjectsReturned:
            # Only one default plan can be present
            return None
