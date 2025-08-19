from celery import shared_task


@shared_task
def premium_expired(premium_products_id: int):
    from notifications.services import NotificationService
    from premium.models import PremiumProduct

    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        return

    if (
        pp_object.profile
        and pp_object.profile.meta.transfer_object
        and pp_object.profile.meta.transfer_object.is_anonymous
    ):
        pp_object.profile.meta.transfer_object.delete()

    pp_object.premium.sent_email_that_premium_expired()
    NotificationService(pp_object.profile.meta).notify_premium_just_expired()
