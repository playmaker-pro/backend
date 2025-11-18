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


def test_buy_premium(product_premium_player_month, player_profile):
    user = player_profile.user
    transaction = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction.success()

    assert player_profile.is_premium
    # Player premium limit: 30 (premium overrides freemium limit of 10)
    assert player_profile.user.userinquiry.limit == 30
    assert player_profile.is_promoted
    assert player_profile.products.calculate_pm_score
    # Plan should be set to PREMIUM_PLAYER when premium is activated
    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_PLAYER"


def test_buy_inquiries_for_profile_with_premium(
    player_profile, product_premium_player_month, product_inquiries_L
):
    user = player_profile.user
    transaction_premium = Transaction.objects.create(
        product=product_premium_player_month, user=user
    )
    transaction_premium.success()

    assert player_profile.is_premium
    # Plan should be PREMIUM_PLAYER after activating premium
    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_PLAYER"

    transaction_inquiries = Transaction.objects.create(
        product=product_inquiries_L, user=user
    )
    transaction_inquiries.success()
    player_profile.refresh_from_db()

    # After buying package, plan changes to package plan
    assert player_profile.user.userinquiry.plan.type_ref == "PREMIUM_INQUIRIES_L"


def test_check_if_premium_inquiries_refresh(
    coach_profile, mck_timezone_now, product_inquiries_L
):
    coach_profile.setup_premium_profile(PremiumType.YEAR)
    user = coach_profile.user
    primary_date = mck_timezone_now.return_value.date()

    assert coach_profile.is_premium
    assert coach_profile.has_premium_inquiries
    assert coach_profile.products.inquiries.is_active
    assert coach_profile.products.inquiries.counter_updated_at.date() == primary_date
    assert coach_profile.products.inquiries.valid_since.date() == primary_date
    assert coach_profile.products.inquiries.current_counter == 0
    # Coach premium limit is 30 (overrides freemium limit of 5)
    assert user.userinquiry.left == 30
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert user.userinquiry.limit_raw == 5  # Freemium limit for coach

    # increment 3x (freemium limit is 5 for coaches, so premium not used yet)
    for _ in range(3):
        user.userinquiry.increment()

    assert coach_profile.products.inquiries.current_counter == 0  # Premium not used yet
    assert user.userinquiry.left == 27  # 30 - 3 freemium used
    assert user.userinquiry.counter == 3  # 3 freemium only
    assert user.userinquiry.counter_raw == 3  # 3 out of 5 freemium
    assert user.userinquiry.limit_raw == 5

    mck_timezone_now.return_value = (
        coach_profile.products.inquiries.counter_updated_at
        + timedelta(days=90, seconds=12)
    )
    new_current_date = mck_timezone_now.return_value.date()

    # After 90 days (coach reset cycle), premium counter resets to 0, but freemium counter stays at 3
    assert user.userinquiry.left == 27  # 30 - 3 freemium still used
    assert user.userinquiry.counter == 3  # Still 3 freemium (no reset)
    assert user.userinquiry.counter_raw == 3  # 3 out of 5 freemium
    assert user.userinquiry.limit_raw == 5
    assert coach_profile.products.inquiries.is_active

    current_updated_at_date = (
        coach_profile.products.inquiries.counter_updated_at.date()
    )
    expected = primary_date + timedelta(days=90)
    assert current_updated_at_date == new_current_date and current_updated_at_date == (
        expected
    )
    assert coach_profile.products.inquiries.valid_since.date() == primary_date
    assert coach_profile.products.inquiries.current_counter == 0

    # increment 7x more (2 freemium left + 5 to premium to reach 8 total premium)
    for _ in range(7):
        user.userinquiry.increment()

    # Used 10 total (5 freemium full + 5 premium)
    assert user.userinquiry.left == 20  # 30 - 10 used
    assert user.userinquiry.limit == 30
    assert (
        user.userinquiry.counter == 10
    )  # 5 freemium (full) + 5 premium
    assert user.userinquiry.counter_raw == 5  # Used all 5 freemium
    assert user.userinquiry.limit_raw == 5
    assert coach_profile.products.inquiries.current_counter == 5  # 5 premium used
    assert user.userinquiry.can_make_request  # Still have 20 premium left

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()
    user.userinquiry.refresh_from_db()

    transaction = Transaction.objects.create(product=product_inquiries_L, user=user)
    transaction.success()
    user.userinquiry.refresh_from_db()

    # Buying L product adds 3 to limit_raw (from plan.limit=3 in InquiryPlan)
    # Bought 2x L products, so: 5 (original) + 3 (first L) + 3 (second L) = 11
    # Packages ADD to premium limit: 30 (base) + 6 (packages) = 36
    # With counter at 10 (5 freemium + 5 premium): 36 - 10 = 26 left
    assert user.userinquiry.left == 26
    assert user.userinquiry.left_to_show == 26
    assert user.userinquiry.limit == 36  # Premium (30) + packages (6)
    assert user.userinquiry.limit_to_show == 36
    assert user.userinquiry.counter == 10  # 5 freemium + 5 premium
    assert user.userinquiry.counter_raw == 5
    assert user.userinquiry.limit_raw == 11  # 5 original + 3 from first L + 3 from second L
    assert coach_profile.products.inquiries.current_counter == 5
    assert user.userinquiry.can_make_request

    mck_timezone_now.return_value = (
        coach_profile.products.inquiries.counter_updated_at + timedelta(days=91)
    )
    new_current_date = mck_timezone_now.return_value.date()
    coach_profile.products.inquiries.check_refresh()
    user.userinquiry.refresh_from_db()
    coach_profile.refresh_from_db()

    # After 91 days, premium counter resets but freemium doesn't
    # Freemium was at 5 (full), stays at 5. Premium was at 5, resets to 0
    # Packages were bought so limit_raw=11 stays preserved after reset_plan
    # Limit includes package bonus: 30 (premium) + 6 (packages from limit_raw=11) = 36
    assert user.userinquiry.counter_raw == 5  # Freemium counter
    assert user.userinquiry.limit_raw == 11  # Packages preserved
    assert user.userinquiry.limit == 36  # Premium (30) + packages (6)
    assert user.userinquiry.left == 31  # 36 - 5 freemium (premium counter reset)
    assert user.userinquiry.counter == 5  # Only freemium (5)
    assert user.userinquiry.counter_raw == 5
    assert user.userinquiry.limit_raw == 11  # Still 11 from earlier (5 + 6 from 2x L products)

    assert coach_profile.products.inquiries.current_counter == 0


def test_premium_inquiries_on_trial(
    trial_premium_coach_profile, mck_timezone_now, product_inquiries_XL, outbox
):
    user = trial_premium_coach_profile.user

    assert trial_premium_coach_profile.has_premium_inquiries
    assert user.userinquiry.limit == 30  # Premium override (coach gets Club-like limit of 30)
    assert user.userinquiry.left == 30  # 30 - 0 used
    assert user.userinquiry.counter == 0
    assert user.userinquiry.counter_raw == 0
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == mck_timezone_now.return_value.date()
    )
    assert trial_premium_coach_profile.products.inquiries.current_counter == 0

    for _ in range(3):
        user.userinquiry.increment()

    assert user.userinquiry.left == 27  # 30 - 3 (all freemium, 3 out of 5)
    assert user.userinquiry.limit == 30  # Premium override for coach (Club-like)
    assert user.userinquiry.counter == 3  # 3 freemium only (5 max)
    assert user.userinquiry.counter_raw == 3  # 3 out of 5 freemium
    assert user.userinquiry.limit_raw == 5  # Coach freemium limit is 5
    assert trial_premium_coach_profile.products.inquiries.current_counter == 0  # No premium used yet

    outbox.clear()

    mck_timezone_now.return_value += timedelta(days=7, seconds=1)
    trial_premium_coach_profile.refresh_from_db()

    assert not trial_premium_coach_profile.is_premium
    assert len(outbox) == 1
    assert outbox[0].to[0] == trial_premium_coach_profile.user.email
    assert outbox[0].subject == "🕒 Koniec próbnej rundy – co dalej?"
    # After premium expires, counter_raw is reset to 0 by premium_expired task
    user.userinquiry.refresh_from_db()
    assert user.userinquiry.left == 5  # 5 - 0 (reset on expiration)
    assert user.userinquiry.limit == 5  # Back to freemium limit for coach
    assert user.userinquiry.counter == 0  # Reset on expiration
    assert user.userinquiry.counter_raw == 0  # Reset on expiration
    assert not trial_premium_coach_profile.has_premium_inquiries
    assert not trial_premium_coach_profile.products.inquiries.is_active
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == timezone.now().date() - timedelta(days=7, seconds=1)
    )

    trial_premium_coach_profile.setup_premium_profile(PremiumType.YEAR)
    trial_premium_coach_profile.refresh_from_db()
    user.userinquiry.refresh_from_db()

    assert trial_premium_coach_profile.has_premium_inquiries
    assert user.userinquiry.limit == 30  # Coach premium limit (Club-like)
    # Counter was reset when premium activated
    assert user.userinquiry.left == 30  # 30 - 0 (fresh start)
    assert user.userinquiry.counter == 0  # Reset on activation
    assert user.userinquiry.counter_raw == 0  # Reset on activation
    assert trial_premium_coach_profile.products.inquiries.is_active
    assert (
        trial_premium_coach_profile.products.inquiries.counter_updated_at.date()
        == timezone.now().date()
    )

    outbox.clear()  # Clear outbox before next increments

    mck_timezone_now.return_value += timedelta(days=30, seconds=1)

    # Premium counter NOT reset yet (coach uses 90-day cycle like clubs)
    # After 30 days, nothing changes (need 90 days for reset)
    assert user.userinquiry.limit == 30  # Coach premium limit (Club-like)
    assert user.userinquiry.left == 30  # 30 - 0 (no inquiries used yet)
    assert user.userinquiry.counter == 0  # No inquiries used yet
    assert user.userinquiry.counter_raw == 0

    # increment 10x (all go to freemium first, then premium)
    for _ in range(10):
        user.userinquiry.increment()

    # With new logic: limit=30, counter=10 (5 freemium + 5 premium)
    assert user.userinquiry.left == 20  # 30 - 10
    assert user.userinquiry.limit == 30  # Coach premium limit (override, Club-like)
    assert user.userinquiry.counter == 10  # 5 freemium + 5 premium
    assert user.userinquiry.counter_raw == 5  # All 5 freemium used
    assert user.userinquiry.limit_raw == 5  # Coach freemium limit
    assert trial_premium_coach_profile.products.inquiries.current_counter == 5  # Premium counter
    assert user.userinquiry.can_make_request  # Still 17 left

    transaction = Transaction.objects.create(product=product_inquiries_XL, user=user)
    transaction.success()

    # Packages ADD to premium limit: 30 (base) + 5 (XL package) = 35
    # Counter unchanged: 10 (5 freemium + 5 premium)
    assert user.userinquiry.left == 25  # 35 - 10
    assert user.userinquiry.limit == 35  # Premium (30) + package (5)
    assert user.userinquiry.limit_to_show == 35
    assert user.userinquiry.left_to_show == 25  # 35 - 10
    assert user.userinquiry.counter == 10  # Unchanged (5 freemium + 5 premium)
    assert user.userinquiry.counter_raw == 5  # Freemium
    assert user.userinquiry.limit_raw == 10  # 5 original + 5 from XL
    assert user.userinquiry.can_make_request

    mck_timezone_now.return_value += timedelta(days=370, hours=1)

    assert not trial_premium_coach_profile.is_premium
    assert outbox[-1].to[0] == trial_premium_coach_profile.user.email
    # After premium expires, counter and limit are reset by premium_expired task
    user.userinquiry.refresh_from_db()
    assert user.userinquiry.left == 5  # 5 - 0 (reset on expiration)
    assert user.userinquiry.limit == 5  # Back to freemium limit
    assert user.userinquiry.counter_raw == 0  # Reset on expiration
    assert user.userinquiry.counter == 0  # Reset on expiration


def test_try_trial_after_subscription(player_profile, mck_timezone_now, outbox):
    player_profile.setup_premium_profile(PremiumType.MONTH)

    assert player_profile.has_premium_inquiries
    assert player_profile.is_premium
    assert player_profile.is_promoted

    outbox.clear()

    mck_timezone_now.return_value += timedelta(days=30, hours=1)

    assert not player_profile.is_premium
    assert outbox[-1].to[0] == player_profile.user.email
    assert outbox[-1].subject == "⚠️ Twoje Premium wygasło – odnów je teraz!"
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
def test_player_custom_period(player_profile, period, mck_timezone_now, outbox):
    player_profile.setup_premium_profile(PremiumType.CUSTOM, period=period)
    player_profile.refresh_from_db()

    assert player_profile.products.trial_tested
    assert player_profile.premium.subscription_lifespan == timedelta(days=period)
    assert player_profile.promotion.subscription_lifespan == timedelta(days=period)
    assert player_profile.products.inquiries.subscription_lifespan == timedelta(
        days=period
    )

    mck_timezone_now.return_value += timedelta(days=period, hours=1)

    assert not player_profile.is_premium
    assert outbox[-1].to[0] == player_profile.user.email
    assert outbox[-1].subject == "⚠️ Twoje Premium wygasło – odnów je teraz!"


@pytest.mark.parametrize("period", (2, 56, 123))
def test_custom_period(coach_profile, period, mck_timezone_now, outbox):
    coach_profile.setup_premium_profile(PremiumType.CUSTOM, period=period)
    coach_profile.refresh_from_db()

    assert coach_profile.products.trial_tested
    assert coach_profile.premium.subscription_lifespan.days == period
    assert coach_profile.promotion.subscription_lifespan.days == period
    assert coach_profile.products.inquiries.subscription_lifespan.days == period

    mck_timezone_now.return_value += timedelta(days=period, hours=1)

    assert not coach_profile.is_premium
    assert outbox[-1].to[0] == coach_profile.user.email
    assert outbox[-1].subject == "⚠️ Twoje Premium wygasło – odnów je teraz!"
