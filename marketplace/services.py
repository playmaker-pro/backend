import logging
from datetime import timedelta

from django.conf import settings

from .models import AnnouncementPlan, AnnouncementUserQuota

# from .notify import notify_duplicated_default_annoucement_plan

logger = logging.getLogger(__name__)


class MarketPlaceService:
    def create_default_plans(self):
        for plan_opts in settings.ANNOUNCEMENT_DEFAULT_PLANS:
            logger.info(f"marketplace plan: {plan_opts}")
            opts = plan_opts.copy()
            days = int(opts["days"])
            opts["days"] = timedelta(days=days)
            AnnouncementPlan.objects.get_or_create(**opts)

    def set_user_plan(self, user):
        plan = self.get_plan()
        if plan is None:
            # notify_duplicated_default_annoucement_plan(user)
            return
        auq, created = AnnouncementUserQuota.objects.get_or_create(
            pk=user.pk, defaults={"plan": plan}
        )
        suffix = "already exists"
        if created:
            suffix = "created"
        logger.info(f"User {user} announcement quota plan {suffix}.")

    def get_plan(self):
        return self._get_default_plan()

    def _get_default_plan(self, retry=True):
        try:
            return AnnouncementPlan.objects.get(default=True)
        except AnnouncementPlan.DoesNotExist:
            logger.debug(
                "AnnouncementPlan.DoesNotExist so we are creating default plans form settings."
            )
            self.create_default_plans()
            if retry:
                return self._get_default_plan(
                    retry=False
                )  # this prevent any infinitve loop if there is no plans defined in settings.
        except AnnouncementPlan.MultipleObjectsReturned:
            # Only one default plan can be present
            logger.error(
                "AnnouncementPlan.MultipleObjectsReturned - there can be only one Default AnnouncementPlan"
            )
            return None
