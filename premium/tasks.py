from celery import shared_task

from premium.models import PremiumProduct, PremiumType


@shared_task
def reward_referrals_with_premium(premium_products_id):
    try:
        pp_object = PremiumProduct.objects.get(pk=premium_products_id)
    except PremiumProduct.DoesNotExist:
        return

    pp_object.setup_premium_profile(PremiumType.CUSTOM, 10)
