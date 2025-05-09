from celery import shared_task


@shared_task
def reward_referrals_with_premium(premium_products_id):
    from premium.models import PremiumProduct, PremiumType

    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        return

    setup_premium_profile(
        pp_object.profile.pk, pp_object.profile.__class__.__name__, PremiumType.MONTH
    )


@shared_task
def setup_premium_profile(
    profile_id: int, profile_class: str, premium_type: str, period: int = None
) -> None:
    from premium.models import PremiumProfile, PremiumType
    from profiles import models

    model = getattr(models, profile_class)
    profile = model.objects.get(pk=profile_id)

    premium_type = PremiumType(premium_type)
    pp_object = profile.premium_products

    premium, _ = PremiumProfile.objects.get_or_create(product=pp_object)

    if pp_object.trial_tested and premium_type == PremiumType.TRIAL:
        raise ValueError("Trial already tested or cannot be set.")

    if premium_type == PremiumType.CUSTOM and period:
        premium.setup_by_days(period)
    elif premium_type != PremiumType.CUSTOM:
        premium.setup(premium_type)
    else:
        raise ValueError("Custom period requires period value.")

    if not pp_object.trial_tested:
        pp_object.trial_tested = True
        pp_object.save(update_fields=["trial_tested"])

    if premium.is_trial and premium_type != PremiumType.TRIAL:
        pp_object.inquiries.reset_counter(reset_plan=False)


@shared_task
def premium_expired(premium_products_id: int):
    from notifications.services import NotificationService
    from premium.models import PremiumProduct

    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        return

    pp_object.premium.sent_email_that_premium_expired()
    NotificationService(pp_object.profile.meta).notify_premium_just_expired()
