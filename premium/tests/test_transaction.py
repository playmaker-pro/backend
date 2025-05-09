from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from mailing.models import UserEmailOutbox
from payments.models import Transaction
from premium.models import PremiumType

pytestmark = pytest.mark.django_db


@pytest.fixture
def mck_tpay_parser():
    with patch("payments.providers.tpay.parsers.TpayTransactionParser") as mck:
        yield mck


def test_buy_premium(product_premium_player_month, player_profile):
    user = player_profile.user
    transaction = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.limit == 12
    assert player_profile.is_promoted
    assert player_profile.products.calculate_pm_score
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"


def test_buy_inquiries_for_profile_with_premium(
    player_profile, product_premium_player_month, product_inquiries_L
):
    user = player_profile.user
    transaction_premium = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction_premium.success()

    assert player_profile.is_premium
    assert player_profile.user.userinquiry.plan.type_ref == "BASIC"

    transaction_inquiries = Transaction.objects.create(
        product=product_inquiries_L, user=user
    )
    transaction_inquiries.success()
    player_profile.refresh_from_db()

    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_INQUIRIES_L"


def test_check_if_premium_inquiries_refresh(
    player_profile, mck_timezone_now, product_inquiries_L
):
    player_profile.setup_premium_profile(PremiumType.YEAR)
    user = player_profile.user
    primary_date = timezone.now().date()

    assert player_profile.is_premium
    assert player_profile.has_premium_inquiries
    assert player_profile.products.inquiries.is_active
    assert player_profile.products.inquiries.counter_updated_at.date() == primary_date
    assert player_profile.products.inquiries.valid_since.date() == primary_date
    assert player_profile.products.inquiries.current_counter == 0
    assert user.userinquiry.left == 12
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 2

    # increment 3x
    for _ in range(3):
        user.userinquiry.increment()

    assert player_profile.products.inquiries.current_counter == 1
    assert user.userinquiry.left == 9
    assert user.userinquiry.counter == 3
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2

    mck_timezone_now.return_value = (
        player_profile.products.inquiries.counter_updated_at
        + timedelta(days=30, hours=1)
    )
    new_current_date = timezone.now().date()

    assert user.userinquiry.left == 10
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2
    assert player_profile.products.inquiries.is_active

    current_updated_at_date = (
        player_profile.products.inquiries.counter_updated_at.date()
    )

    assert current_updated_at_date == new_current_date and current_updated_at_date == (
        primary_date + timedelta(days=30)
    )
    assert player_profile.products.inquiries.valid_since.date() == primary_date
    assert player_profile.products.inquiries.current_counter == 0

    # increment 10x
    for _ in range(10):
        user.userinquiry.increment()

    assert user.userinquiry.left == 0
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2
    assert player_profile.products.inquiries.current_counter == 10
    assert not user.userinquiry.can_make_request

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()

    assert user.userinquiry.left == 3
    assert user.userinquiry.left_to_show == 3
    assert user.userinquiry.limit == 15
    assert user.userinquiry.limit_to_show == 12
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 5
    assert player_profile.products.inquiries.current_counter == 10
    assert user.userinquiry.can_make_request

    mck_timezone_now.return_value = (
        player_profile.products.inquiries.counter_updated_at + timedelta(days=32)
    )
    new_current_date = timezone.now().date()
    player_profile.products.inquiries.check_refresh()
    user.userinquiry.refresh_from_db()

    assert user.userinquiry.left == 10
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2

    assert player_profile.products.inquiries.current_counter == 0


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
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == mck_timezone_now.return_value.date()
    )
    assert trial_premium_coach_profile.products.inquiries.current_counter == 0

    for _ in range(3):
        user.userinquiry.increment()

    assert user.userinquiry.left == 9
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 3
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2
    assert trial_premium_coach_profile.products.inquiries.current_counter == 1

    assert not UserEmailOutbox.objects.filter(
        recipient=trial_premium_coach_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()

    mck_timezone_now.return_value += timedelta(days=7, seconds=1)
    assert not trial_premium_coach_profile.is_premium

    assert UserEmailOutbox.objects.filter(
        recipient=trial_premium_coach_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()
    assert user.userinquiry.left == 0
    assert user.userinquiry.limit == 2
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2
    assert not trial_premium_coach_profile.has_premium_inquiries
    assert not trial_premium_coach_profile.products.inquiries.is_active
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == timezone.now().date() - timedelta(days=7, seconds=1)
    )

    trial_premium_coach_profile.setup_premium_profile(PremiumType.YEAR)
    trial_premium_coach_profile.refresh_from_db()

    assert trial_premium_coach_profile.has_premium_inquiries
    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 10
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2
    assert trial_premium_coach_profile.products.inquiries.is_active
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == timezone.now().date()
    )

    mck_timezone_now.return_value += timedelta(days=30, seconds=1)

    assert user.userinquiry.limit == 12
    assert user.userinquiry.left == 10
    assert user.userinquiry.counter == 2
    assert user.userinquiry.counter_raw == 2

    # increment 10x
    for _ in range(10):
        user.userinquiry.increment()

    assert user.userinquiry.left == 0
    assert user.userinquiry.limit == 12
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 2
    assert trial_premium_coach_profile.products.inquiries.current_counter == 10
    assert not user.userinquiry.can_make_request
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == timezone.now().date()
    )

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    assert user.userinquiry.left == 5
    assert user.userinquiry.limit == 17
    assert user.userinquiry.limit_to_show == 12
    assert user.userinquiry.left_to_show == 5
    assert user.userinquiry.counter == 12
    assert user.userinquiry.counter_raw == 2
    assert user.userinquiry.limit_raw == 7
    assert trial_premium_coach_profile.products.inquiries.current_counter == 10
    assert user.userinquiry.can_make_request

    assert (
        UserEmailOutbox.objects.filter(
            recipient=trial_premium_coach_profile.user.email,
            email_type="PREMIUM_EXPIRED",
        ).count()
        == 1
    )

    mck_timezone_now.return_value += timedelta(days=370, hours=1)

    assert not trial_premium_coach_profile.is_premium

    assert (
        UserEmailOutbox.objects.filter(
            recipient=trial_premium_coach_profile.user.email,
            email_type="PREMIUM_EXPIRED",
        ).count()
        == 2
    )

    assert user.userinquiry.left == 0
    assert user.userinquiry.limit == 2
    assert user.userinquiry.counter == 2


def test_try_trial_after_subscription(player_profile, mck_timezone_now):
    player_profile.setup_premium_profile(PremiumType.MONTH)

    assert player_profile.has_premium_inquiries
    assert player_profile.is_premium
    assert player_profile.is_promoted

    assert not UserEmailOutbox.objects.filter(
        recipient=player_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()

    mck_timezone_now.return_value += timedelta(days=30, hours=1)

    assert not player_profile.is_premium
    assert UserEmailOutbox.objects.filter(
        recipient=player_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()

    assert not player_profile.has_premium_inquiries
    assert not player_profile.is_premium
    assert not player_profile.is_promoted

    with pytest.raises(ValueError) as exc:
        player_profile.setup_premium_profile(PremiumType.TRIAL)

    assert str(exc.value) == "Trial already tested or cannot be set."


def test_double_trial(trial_premium_player_profile):
    assert trial_premium_player_profile.is_premium
    assert trial_premium_player_profile.products.trial_tested

    with pytest.raises(ValueError) as exc:
        trial_premium_player_profile.setup_premium_profile(PremiumType.TRIAL)

    assert str(exc.value) == "Trial already tested or cannot be set."


@pytest.mark.parametrize("period", (2, 56, 123))
def test_player_custom_period(player_profile, period, mck_timezone_now):
    player_profile.setup_premium_profile(PremiumType.CUSTOM, period=period)
    player_profile.refresh_from_db()

    assert player_profile.products.trial_tested
    assert player_profile.premium.subscription_lifespan == timedelta(days=period)
    assert player_profile.promotion.subscription_lifespan == timedelta(days=period)
    assert player_profile.products.inquiries.subscription_lifespan == timedelta(
        days=period
    )

    assert not UserEmailOutbox.objects.filter(
        recipient=player_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()

    mck_timezone_now.return_value += timedelta(days=period, hours=1)

    assert not player_profile.is_premium
    assert UserEmailOutbox.objects.filter(
        recipient=player_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()


@pytest.mark.parametrize("period", (2, 56, 123))
def test_custom_period(coach_profile, period, mck_timezone_now):
    coach_profile.setup_premium_profile(PremiumType.CUSTOM, period=period)
    coach_profile.refresh_from_db()

    assert coach_profile.products.trial_tested
    assert coach_profile.premium.subscription_lifespan.days == period
    assert coach_profile.promotion.subscription_lifespan.days == period
    assert coach_profile.products.inquiries.subscription_lifespan.days == period
    assert not UserEmailOutbox.objects.filter(
        recipient=coach_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()

    mck_timezone_now.return_value += timedelta(days=period, hours=1)
    assert not coach_profile.is_premium

    assert UserEmailOutbox.objects.filter(
        recipient=coach_profile.user.email, email_type="PREMIUM_EXPIRED"
    ).exists()
