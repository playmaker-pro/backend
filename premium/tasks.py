from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django_celery_beat.models import ClockedSchedule, PeriodicTask

from mailing.utils import build_email_context

logger = get_task_logger(__name__)


@shared_task
def premium_expired(premium_products_id: int):
    from mailing.schemas import EmailTemplateRegistry
    from mailing.services import MailingService
    from mailing.utils import build_email_context
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
        mail_content = EmailTemplateRegistry.TRIAL_END
    else:
        mail_content = EmailTemplateRegistry.PREMIUM_EXPIRED

    if (
        pp_object.profile
        and pp_object.profile.meta.transfer_object
        and pp_object.profile.meta.transfer_object.is_anonymous
    ):
        pp_object.profile.meta.transfer_object.is_anonymous = False
        pp_object.profile.meta.transfer_object.save()
    
    # Update UserInquiry plan back to freemium and reset packages when premium expires
    try:
        from inquiries.services import InquireService
        if pp_object.profile and pp_object.profile.user and hasattr(pp_object.profile.user, 'userinquiry'):
            profile_type = pp_object.profile.__class__.__name__
            plan = InquireService.get_plan_for_profile_type(profile_type, is_premium=False)
            pp_object.profile.user.userinquiry.plan = plan
            # Reset counter and limit_raw to freemium when premium expires
            # Per requirements: all inquiries and packages are lost when premium expires
            pp_object.profile.user.userinquiry.counter_raw = 0
            pp_object.profile.user.userinquiry.limit_raw = plan.limit if plan else 5
            pp_object.profile.user.userinquiry.save(update_fields=['plan', 'counter_raw', 'limit_raw'])
    except Exception as e:
        logger.error(f"Failed to update inquiry plan on premium expiration: {str(e)}")
    
    # Reset premium inquiry counter and validity when premium expires
    # Per requirements: unused inquiries and packages are lost when premium expires
    try:
        from premium.models import PremiumInquiriesProduct
        inquiries_product = PremiumInquiriesProduct.objects.filter(product=pp_object).first()
        if inquiries_product:
            # Reset counter to 0 and clear validity dates so is_active returns False
            inquiries_product.current_counter = 0
            inquiries_product.valid_until = None
            inquiries_product.save()
    except Exception as e:
        logger.error(f"Failed to reset inquiry counter on premium expiration: {str(e)}")

    context = build_email_context(
        pp_object.profile.user, mailing_type=mail_content.mailing_type
    )
    MailingService(mail_content(context)).send_mail(pp_object.profile.user)
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
        mail_content = EmailTemplateRegistry.TRIAL_END
        context = build_email_context(user, mailing_type=mail_content.mailing_type)
        MailingService(mail_content(context)).send_mail(user)
    else:
        logger.error(
            f"PremiumProduct with id {premium_products_id} has no associated user. Unable to send encouragement email."
        )
