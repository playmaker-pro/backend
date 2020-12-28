import logging
from .notify import notify_duplicated_default_annoucement_plan
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AnnouncementPlan, AnnouncementUserQuota
from datetime import timedelta


logger = logging.getLogger(__name__)


class MarketPlaceService:

    def create_default_plans(self):
        for plan_opts in settings.ANNOUNCEMENT_DEFAULT_PLANS:
            days = int(plan_opts['days'])
            plan_opts['days'] = timedelta(days=days)
            AnnouncementPlan.objects.get_or_create(**plan_opts)

    def set_user_plan(self, user):
        plan = self.get_plan()
        if plan is None:
            notify_duplicated_default_annoucement_plan(user)    
            return
        auq, created = AnnouncementUserQuota.objects.get_or_create(pk=user.pk, defaults={'plan': plan})
        suffix = 'already exists'
        if created:
            suffix = 'created'
        logger.info(f'User {user} announcement quota plan {suffix}.')

    def get_plan(self):
        return self._get_default_plan()

    def _get_default_plan(self):
        try:
            return AnnouncementPlan.objects.get(default=True)
        except AnnouncementPlan.MultipleObjectsReturned:
            # Only one default plan can be present
            
            return None
