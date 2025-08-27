import logging

from celery import shared_task
from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask

logger = logging.getLogger("celery")


@shared_task
def premium_expired(premium_products_id: int):
    from mailing.schemas import EmailTemplateRegistry
    from mailing.services import MailingService
    from notifications.services import NotificationService
    from premium.models import PremiumProduct

    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        logger.error(
            f"PremiumProduct with id {premium_products_id} does not exist. Unable to process expiration."
        )
        return

    if pp_object.premium.is_trial:
        PeriodicTask.objects.create(
            name=f"Run one day after trial expiration [ {pp_object.pk=} ]",
            task="premium.tasks.encourage_to_try_premium",
            args=[pp_object.id],
            one_off=True,
            clocked=ClockedSchedule.objects.create(
                clocked_time=timezone.now() + timezone.timedelta(days=1)
            ),
        )

    if (
        pp_object.profile
        and pp_object.profile.meta.transfer_object
        and pp_object.profile.meta.transfer_object.is_anonymous
    ):
        pp_object.profile.meta.transfer_object.delete()

    mail_content = EmailTemplateRegistry.PREMIUM_EXPIRED()
    MailingService(mail_content).send_mail(pp_object.profile.user)
    NotificationService(pp_object.profile.meta).notify_premium_just_expired()


@shared_task
def encourage_to_try_premium(premium_products_id: int):
    """Send email to user one day after trial expiration to encourage checking premium options."""
    from mailing.schemas import EmailTemplateRegistry
    from mailing.services import MailingService
    from premium.models import PremiumProduct

    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        logger.error(
            f"PremiumProduct with id {premium_products_id} does not exist. Unable to send encouragement email."
        )
        return

    if not pp_object.premium.is_trial and pp_object.is_profile_premium:
        logger.info(
            f"User of PremiumProduct id {premium_products_id} has already upgraded to premium. No encouragement email sent."
        )
        return

    if user := pp_object.user:
        mail_content = EmailTemplateRegistry.GO_PREMIUM_AFTER_TRIAL()
        MailingService(mail_content).send_mail(user)
    else:
        logger.error(
            f"PremiumProduct with id {premium_products_id} has no associated user. Unable to send encouragement email."
        )
