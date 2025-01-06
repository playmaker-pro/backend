from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from payments.models import Transaction
from premium.models import PremiumType

pytestmark = pytest.mark.django_db


@pytest.fixture
def mck_tpay_parser():
    with patch("payments.providers.tpay.parsers.TpayTransactionParser") as mck:
        yield mck


def test_buy_L_inquiries(product_inquiries_L, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_L.name
    assert user.userinquiry.limit == 5
    assert user.userinquiry.left == 5


def test_buy_XL_inquiries(product_inquiries_XL, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_XL.name
    assert user.userinquiry.limit == 7
    assert user.userinquiry.left == 7


def test_buy_XXL_inquiries(product_inquiries_XXL, player_profile):
    user = player_profile.user
    transaction = Transaction.objects.create(product=product_inquiries_XXL, user=user)
    transaction.success()

    assert user.userinquiry.plan.type_ref == product_inquiries_XXL.name
    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 12


def test_buy_premium(product_premium_player_month, player_profile):
    user = player_profile.user

    transaction = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.is_promoted
    assert player_profile.premium_products.calculate_pm_score
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_buy_inquiries_for_profile_with_premium(
    player_profile, product_premium_player_month
):
    user = player_profile.user
    transaction_premium = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction_premium.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_check_if_premium_inquiries_refresh(
    player_profile, mck_timezone_now, product_inquiries_L
):
    player_profile.premium_products.setup_premium_profile(PremiumType.YEAR)
    user = player_profile.user
    primary_date = timezone.now().date()

    assert player_profile.is_premium
    assert player_profile.has_premium_inquiries
    assert player_profile.premium_products.inquiries.is_active
    assert (
        player_profile.premium_products.inquiries.counter_updated_at.date()
        == primary_date
    )
    assert player_profile.premium_products.inquiries.valid_since.date() == primary_date
    assert player_profile.premium_products.inquiries.current_counter == 0
    assert user.userinquiry.left == 12
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 2

    # increment 3x
    for _ in range(3):
        user.userinquiry.increment()

    assert player_profile.premium_products.inquiries.current_counter == 3
    assert user.userinquiry.left == 9
    assert user.userinquiry.counter == 3
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 2

    mck_timezone_now.return_value = (
        player_profile.premium_products.inquiries.counter_updated_at
        + timedelta(days=30, hours=1)
    )
    new_current_date = timezone.now().date()

    assert user.userinquiry.left == 12
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 2
    assert player_profile.premium_products.inquiries.is_active

    current_updated_at_date = (
        player_profile.premium_products.inquiries.counter_updated_at.date()
    )

    assert (
        current_updated_at_date == new_current_date
        and current_updated_at_date == primary_date + timedelta(days=30, hours=1)
    )
    assert player_profile.premium_products.inquiries.valid_since.date() == primary_date
    assert player_profile.premium_products.inquiries.current_counter == 0

    # increment 12x
    for _ in range(12):
        user.userinquiry.increment()

    assert user.userinquiry.left == 0
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2
    assert player_profile.premium_products.inquiries.current_counter == 10
    assert not user.userinquiry.can_make_request

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()

    assert user.userinquiry.left == 3
    assert user.userinquiry.limit == 15
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 5
    assert player_profile.premium_products.inquiries.current_counter == 10
    assert user.userinquiry.can_make_request

    mck_timezone_now.return_value = (
        player_profile.premium_products.inquiries.counter_updated_at
        + timedelta(days=30, hours=1)
    )
    new_current_date = timezone.now().date()

    assert user.userinquiry.left == 13
    assert user.userinquiry.limit == 15
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 5

    current_updated_at_date = (
        player_profile.premium_products.inquiries.counter_updated_at.date()
    )

    assert (
        current_updated_at_date == new_current_date
        and current_updated_at_date == primary_date + timedelta(days=60, hours=2)
    )
    assert player_profile.premium_products.inquiries.current_counter == 0


def test_premium_inquiries_on_trial(
    trial_premium_coach_profile, mck_timezone_now, product_inquiries_XL
):
    user = trial_premium_coach_profile.user

    assert trial_premium_coach_profile.has_premium_inquiries
    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 12
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert (
        trial_premium_coach_profile.premium_products.inquiries.counter_updated_at.date()
        == timezone.now().date()
    )
    assert trial_premium_coach_profile.premium_products.inquiries.current_counter == 0

    for _ in range(3):
        user.userinquiry.increment()

    assert user.userinquiry.left == 9
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 3
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 2
    assert trial_premium_coach_profile.premium_products.inquiries.current_counter == 3

    mck_timezone_now.return_value += timedelta(days=7, hours=1)

    assert user.userinquiry.left == 2
    assert user.userinquiry.limit == 2
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert not trial_premium_coach_profile.has_premium_inquiries
    assert not trial_premium_coach_profile.premium_products.inquiries.is_active
    assert (
        trial_premium_coach_profile.premium_products.inquiries.counter_updated_at.date()
        == timezone.now().date() - timedelta(days=7, hours=1)
    )

    trial_premium_coach_profile.premium_products.setup_premium_profile(PremiumType.YEAR)
    trial_premium_coach_profile.refresh_from_db()

    assert trial_premium_coach_profile.has_premium_inquiries
    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 9
    assert user.userinquiry.counter == 3
    assert user.userinquiry.counter_raw == 0
    assert trial_premium_coach_profile.premium_products.inquiries.is_active
    assert (
        trial_premium_coach_profile.premium_products.inquiries.counter_updated_at.date()
        == (timezone.now() - timedelta(days=7, hours=1)).date()
    )

    mck_timezone_now.return_value += timedelta(days=30, hours=1)

    # increment 12x
    for _ in range(11):
        user.userinquiry.increment()

    assert user.userinquiry.left == 1
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 11
    assert user.userinquiry.counter_raw == 1
    assert user.userinquiry.limit_raw == 2
    assert trial_premium_coach_profile.premium_products.inquiries.current_counter == 10
    assert user.userinquiry.can_make_request
    assert (
        trial_premium_coach_profile.premium_products.inquiries.counter_updated_at.date()
        == timezone.now().date()
    )

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    assert user.userinquiry.left == 6
    assert user.userinquiry.limit == 17
    assert user.userinquiry.counter == 11
    assert user.userinquiry.counter_raw == 1
    assert user.userinquiry.limit_raw == 7
    assert trial_premium_coach_profile.premium_products.inquiries.current_counter == 10
    assert user.userinquiry.can_make_request

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    assert user.userinquiry.left == 11
    assert user.userinquiry.limit == 22
    assert user.userinquiry.counter == 11
    assert user.userinquiry.counter_raw == 1
    assert user.userinquiry.limit_raw == 12


def test_try_trial_after_subscription(player_profile, mck_timezone_now):
    player_profile.premium_products.setup_premium_profile(PremiumType.MONTH)

    assert player_profile.has_premium_inquiries
    assert player_profile.is_premium
    assert player_profile.is_promoted

    mck_timezone_now.return_value += timedelta(days=30, hours=1)

    assert not player_profile.has_premium_inquiries
    assert not player_profile.is_premium
    assert not player_profile.is_promoted

    with pytest.raises(ValueError) as exc:
        player_profile.premium_products.setup_premium_profile(PremiumType.TRIAL)

    assert (
        str(exc.value) == "Cannot activate trial, you already had valid subscription."
    )
